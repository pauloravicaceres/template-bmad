"""Fase 4F-E4: como máximo una HU abierta por proyecto (`ai.hu_lifecycle.mode = enforce`).

Una HU queda abierta desde su GITOPS-BRANCH-CREATE autorizado hasta que su GITOPS-MERGE-CLOSE se completa y se
verifica en Git. Varios agentes pueden trabajar en la HU abierta y varios proyectos (repositorios independientes)
pueden avanzar en paralelo; lo que nunca ocurre es abrir una segunda HU en el mismo proyecto.

Fuentes (todas en vivo, nunca un único indicio):
- Observación E3 (hu_lifecycle.observe): Git, macros del tracker y eventos SQLite del watcher.
- Reserva autoritativa `hu_authority` en el SQLite del proyecto: free | opening | active | closing |
  reconcile_required. Sobrevive a reinicios y cubre la ventana entre la decisión y la confirmación en Git.
- Operaciones `hu_op:<id>` (id estable derivado del evento del watcher de la línea): requested -> reserved ->
  confirmed | rejected | failed | not_executed | reconcile_required (| reconciled por un humano).

El watcher es la autoridad: con el lock `hu` del proyecto revalida, reserva, ejecuta la macro, verifica Git y
confirma; el lock nunca se mantiene durante una espera humana ni una llamada a modelos. El preflight del Control
Center usa las mismas reglas en solo lectura y es informativo. Un fallo de observación nunca autoriza nada.

Un BRANCH-CREATE (o MERGE-CLOSE) rechazado no ejecuta Git, no despacha ninguna instrucción posterior del mismo bloque
del tracker, termina su evento (sin in_flight) y emite un bloque WATCHER con @HUMANO:. Reconocer el evento o
reiniciar el watcher no convierte el rechazo en autorización: las instrucciones dependientes solo se despachan si la
operación del bloque está `confirmed`.

Repositorios compartidos (worktrees enlazados al mismo git-common-dir): sus ramas son visibles desde varios proyectos
y E4 no puede atribuirlas ni excluir a otro proyecto; se rechaza con HU_SHARED_REPOSITORY en lugar de suponer
aislamiento. El lock es por proyecto (directorio de estado del workspace): nunca hay un bloqueo global.
"""
import argparse
from contextlib import contextmanager
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import NamedTuple

from .errors import ReconciliationRequired
from .hu_lifecycle import (_IN_PROGRESS, AUTHORITY, GATE, OP_PREFIX, RESOLUTION_PREFIX, GitReader, _event, _git_for_hu,
                           _previous_records, git_evidence, gitops_macro, macro_evidence, observe, op_key_for,
                           resolution_fingerprint)
from .hu_naming import is_feature_branch, is_hu_id
from .state import ProjectLock, StateStore, project_lock

LOCK = 'hu'
LOCK_TIMEOUT = 15.0
NOTICE_PREFIX = 'hu-notice-'
HISTORY_LIMIT = 200
RESOLUTIONS = ('active', 'closed', 'abandoned')

# Códigos estables (watcher, Control Center y CLI).
ALLOWED = 'HU_OPEN_ALLOWED'
RESUME = 'HU_OPEN_RESUME'
CLOSE_ALLOWED = 'HU_CLOSE_ALLOWED'
ANOTHER_OPEN = 'HU_ANOTHER_OPEN'
OPENING = 'HU_OPENING_IN_PROGRESS'
CLOSING = 'HU_CLOSING_IN_PROGRESS'
RECONCILE = 'HU_RECONCILE_REQUIRED'
UNKNOWN = 'HU_STATE_UNKNOWN'
SHARED = 'HU_SHARED_REPOSITORY'
INVALID = 'HU_INVALID_BRANCH'
CLOSE_MISMATCH = 'HU_CLOSE_MISMATCH'
NOTHING_TO_CLOSE = 'HU_NOTHING_TO_CLOSE'
# Otra HU ocupa el proyecto (409 en el Control Center); el resto es un estado incierto o no demostrable (423).
CONFLICT_CODES = frozenset({ANOTHER_OPEN, OPENING, CLOSING})


class HULockBusy(ReconciliationRequired):
    """Otro proceso retiene el lock `hu` del proyecto; no se abrió ni cerró nada."""


class GitUnreadable(ReconciliationRequired):
    """Git no pudo leerse: nunca equivale a "sin cambios" ni a "sin HU abierta"."""


class Decision(NamedTuple):
    verdict: str                 # allow | resume | reject
    code: str
    status: str                  # estado del proyecto según la vista E4
    hu: str | None               # HU solicitada
    open_hu: str | None          # HU abierta o en curso del proyecto
    message: str
    causes: tuple = ()
    op: str | None = None

    @property
    def rejected(self):
        return self.verdict == 'reject'

    def to_dict(self):
        return {**self._asdict(), 'causes': list(self.causes)}

    @classmethod
    def from_dict(cls, data):
        return cls(**{**{key: data.get(key) for key in cls._fields}, 'causes': tuple(data.get('causes') or ())})


# ------------------------------------------------------------------------------------------------ política
def project_view(authority, observation):
    """Estado del proyecto para E4: no_open_hu | one_open_hu | opening | closing | reconcile_required | unknown.

    La reserva manda mientras está en curso o pendiente de reconciliar; si dice `active` y la observación no lo
    corrobora (otra HU, ninguna, o duda) el resultado es reconcile_required, nunca "libre"."""
    authority = authority or {}
    state, hu = authority.get('state'), authority.get('hu')
    causes = list(observation.get('causes') or [])
    status = observation.get('status', 'unknown')
    open_hu = list(observation.get('open') or [])

    def view(result, current, extra=()):
        return {'status': result, 'hu': current, 'causes': causes + list(extra),
                'authority': state or 'free', 'observed': status}

    if state == 'reconcile_required':
        return view('reconcile_required', hu, ['authority_reconcile_required', *authority.get('causes', [])])
    if state in ('opening', 'closing'):
        return view(state, hu, [f'authority_{state}'])
    # Ramas feat/ fuera de contrato con trabajo sin integrar: no se puede demostrar que el proyecto esté libre.
    unattributed = [f'unattributed_feature_branch:{name}'
                    for name in (observation.get('git') or {}).get('invalid_unmerged') or []]
    if unattributed and status not in ('unknown', 'reconcile_required'):
        return view('unknown', hu if state == 'active' else (open_hu[0] if len(open_hu) == 1 else None), unattributed)
    if status in ('unknown', 'reconcile_required'):
        current = open_hu[0] if len(open_hu) == 1 else (hu if state == 'active' else None)
        return view(status, current, [f'unresolved:{name}' for name in observation.get('unresolved') or []])
    if state == 'active' and (status != 'one_open_hu' or open_hu != [hu]):
        return view('reconcile_required', hu, ['authority_observation_mismatch'])
    if status == 'one_open_hu':
        current = open_hu[0]
        observed = observation['hus'][current]['observed_state']
        return view({'opening': 'opening', 'closing': 'closing'}.get(observed, 'one_open_hu'), current)
    return view('no_open_hu', None)


def _detail(view):
    return ', '.join(view['causes']) or view['status']


def decide_open(view, hu, *, shared=False):
    """Tabla de E4 para BRANCH-CREATE de `hu` sobre la vista del proyecto."""
    status, current = view['status'], view['hu']

    def decision(verdict, code, message):
        return Decision(verdict, code, status, hu, current, message, tuple(view['causes']))

    if not hu or not is_hu_id(hu):
        return decision('reject', INVALID, 'La rama solicitada no cumple feat/NNN-nombre-en-kebab-case; no se crea '
                                           'ninguna rama.')
    if shared:
        return decision('reject', SHARED, f'El repositorio Git del proyecto comparte ramas con otros worktrees y no se '
                                          f'puede demostrar el aislamiento: no se abre {hu}.')
    if status == 'no_open_hu':
        return decision('allow', ALLOWED, f'El proyecto no tiene HU abierta: se autoriza abrir {hu}.')
    if status in ('one_open_hu', 'opening') and current == hu:
        return decision('resume', RESUME, f'{hu} ya es la HU abierta del proyecto: se reanuda sin abrir otra.')
    if status == 'one_open_hu':
        return decision('reject', ANOTHER_OPEN, f'El proyecto mantiene abierta la HU {current}; solo puede haber una '
                                                f'HU abierta hasta completar y verificar su cierre (MERGE-CLOSE). No se '
                                                f'abre {hu}.')
    if status == 'opening':
        return decision('reject', OPENING, f'La apertura de la HU {current} está en curso o pendiente de confirmar; '
                                           f'no se abre {hu}.')
    if status == 'closing':
        return decision('reject', CLOSING, f'El cierre de la HU {current} está en curso o sin verificar; no se abre '
                                           f'{hu} hasta que Git confirme la integración.')
    if status == 'reconcile_required':
        return decision('reject', RECONCILE, f'El ciclo de vida de HU del proyecto requiere reconciliación humana '
                                             f'({_detail(view)}); no se abre {hu}.')
    return decision('reject', UNKNOWN, f'No se puede demostrar el estado de las HU del proyecto ({_detail(view)}); '
                                       f'un estado incierto nunca autoriza abrir {hu}.')


def decide_close(view, hu, *, shared=False):
    """MERGE-CLOSE de `hu`: solo sobre la HU abierta del proyecto y con el resto de la evidencia en orden."""
    status, current = view['status'], view['hu']

    def decision(verdict, code, message):
        return Decision(verdict, code, status, hu, current, message, tuple(view['causes']))

    if not hu or not is_hu_id(hu):
        return decision('reject', INVALID, 'La rama a cerrar no cumple feat/NNN-nombre-en-kebab-case; no se fusiona '
                                           'nada.')
    if shared:
        return decision('reject', SHARED, f'El repositorio Git del proyecto comparte ramas con otros worktrees y no se '
                                          f'puede demostrar el aislamiento: no se cierra {hu}.')
    if status == 'one_open_hu' and current == hu:
        return decision('allow', CLOSE_ALLOWED, f'{hu} es la HU abierta del proyecto: se autoriza su cierre.')
    if status == 'no_open_hu':
        return decision('reject', NOTHING_TO_CLOSE, f'El proyecto no tiene ninguna HU abierta: no se cierra {hu}.')
    if status == 'one_open_hu':
        return decision('reject', CLOSE_MISMATCH, f'La HU abierta del proyecto es {current}, no {hu}: no se fusiona '
                                                  'ninguna rama.')
    if status in ('opening', 'closing'):
        code = OPENING if status == 'opening' else CLOSING
        return decision('reject', code, f'La HU {current} tiene una {"apertura" if status == "opening" else "fusión"} '
                                        f'en curso o sin verificar; no se cierra {hu}.')
    if status == 'reconcile_required':
        return decision('reject', RECONCILE, f'El ciclo de vida de HU requiere reconciliación humana ({_detail(view)}); '
                                             f'no se cierra {hu}.')
    return decision('reject', UNKNOWN, f'No se puede demostrar el estado de las HU ({_detail(view)}); no se cierra {hu}.')


def mode_of(rt):
    return (rt.config.data.get('hu_lifecycle') or {}).get('mode', 'observe')


@contextmanager
def hu_lock(context, timeout=LOCK_TIMEOUT, poll=0.05):
    """Exclusión mutua por proyecto (`<estado>/hu.lock`); el SO la libera si el proceso muere."""
    lock = ProjectLock(context, LOCK)
    deadline = time.monotonic() + timeout
    while not lock.acquire():
        if time.monotonic() >= deadline:
            raise HULockBusy(f'Otro proceso retiene el lock de HU del proyecto más de {timeout:g}s; no se abrió ni '
                             'cerró ninguna HU.')
        time.sleep(poll)
    try:
        yield
    finally:
        lock.release()


def block_start(lines, number):
    """Índice de la cabecera `### [` del bloque del tracker que contiene la línea `number`."""
    start = min(number, len(lines) - 1)
    while start > 0 and not lines[start].startswith('### ['):
        start -= 1
    return max(start, 0)


def scope_arguments(context):
    return '' if context.legacy else f' --workspace "{context.workspace_root}" --project {context.project_id}'


# --------------------------------------------------------------------------------------------- Git (lectura)
def _git(git, *args):
    try:
        return git(*args)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise GitUnreadable(f'Git no legible ({type(exc).__name__}).') from exc


def branch_tip(git, name):
    code, out = _git(git, 'rev-parse', '-q', '--verify', f'refs/heads/{name}^{{commit}}')
    if code not in (0, 1):
        raise GitUnreadable(f'No se pudo leer refs/heads/{name}.')
    return (out.strip() or None) if code == 0 else None


def head_branch(git):
    code, out = _git(git, 'symbolic-ref', '-q', 'HEAD')
    return out.strip()[len('refs/heads/'):] if code == 0 and out.startswith('refs/heads/') else None


def is_ancestor(git, commit, ref):
    code, _ = _git(git, 'merge-base', '--is-ancestor', commit, ref)
    if code not in (0, 1):
        raise GitUnreadable(f'No se pudo comprobar si {commit[:12]} está integrado en {ref}.')
    return code == 0


def operation_in_progress(git):
    code, out = _git(git, 'rev-parse', '--absolute-git-dir')
    if code or not out.strip():
        raise GitUnreadable('No se pudo localizar el directorio Git.')
    return [name for name in _IN_PROGRESS if (Path(out.strip()) / name).exists()]


def _history(record, entry):
    return [*(record.get('history') or [])[-(HISTORY_LIMIT - 1):], entry]


def notice_block(op, decision, scope='', now=None):
    """Bloque WATCHER (con @HUMANO:) que explica el rechazo; nunca contiene una macro GitOps como orden."""
    from datetime import datetime
    when = datetime.fromtimestamp(time.time() if now is None else now)
    opening = op['kind'] == 'open'
    accion = ('no se creó la rama ni se cambió de rama' if opening else 'no se fusionó ni se cerró ninguna rama')
    return (f"\n### [{when:%d-%m-%Y}] WATCHER\n- **Hora:** {when:%H:%M:%S}\n"
            f"- **Mensaje:** 🛑 HU BLOQUEADA ({decision.code}): se rechazó la {'apertura' if opening else 'fusión'} de "
            f"{op['branch']} solicitada en la línea {op['line'] + 1} del tracker (sin contar líneas vacías). "
            f"{decision.message} Por eso {accion} y "
            "no se despachó ninguna instrucción de ese bloque.\n"
            f"- **Handoff:** @HUMANO: Revisa la evidencia con python -m bmad_runtime.hu_enforcement{scope} --inspect. "
            "Cierra o reconcilia la HU abierta antes de volver a solicitar la operación con una nueva aprobación; "
            f"reconocer este evento no la autoriza. Operación: {op['key']}.\n")


# ------------------------------------------------------------------------------------------------- enforcer
class Enforcer:
    """Autoridad E4 del watcher para un proyecto. Todas las escrituras van al SQLite del proyecto (ProjectContext)."""

    def __init__(self, context, store, *, writer=None, git=None, lock_timeout=LOCK_TIMEOUT, sleep=time.sleep):
        self.context, self.store = context, store
        self._writer = writer
        self.git = git or GitReader(context.workspace_root)
        self.lock_timeout = lock_timeout
        self.sleep = sleep

    @classmethod
    def for_runtime(cls, rt, **options):
        from .tracker_io import TrackerWriter
        options.setdefault('writer', lambda: TrackerWriter.for_runtime(rt))
        return cls(rt.context, rt.state, **options)

    def lock(self):
        return hu_lock(self.context, self.lock_timeout)

    def view(self, limit=None):
        """(vista E4, observación) en vivo; con `limit`, solo el historial anterior a esa línea del tracker."""
        observation = observe(self.context, self.store, git=self.git, sleep=self.sleep, limit=limit)
        return project_view(self.store.get(AUTHORITY), observation), observation

    def authority(self):
        return self.store.get(AUTHORITY) or {'state': 'free', 'hu': None, 'history': []}

    @staticmethod
    def _transition(authority, state, hu, op_key, reason, **extra):
        now = time.time()
        hu = hu if state != 'free' else None
        record = {key: authority[key] for key in ('last_closed', 'last_resolution') if key in authority}
        record.update(state=state, hu=hu, branch=f'feat/{hu}' if hu else None, op=op_key, reason=reason, updated=now,
                      history=_history(authority, {'at': now, 'from': authority.get('state', 'free'), 'to': state,
                                                   'hu': hu, 'op': op_key, 'reason': reason}), **extra)
        return record

    @staticmethod
    def _op(op, state, event=None, **details):
        now = time.time()
        entry = {'at': now, 'from': op.get('state'), 'to': state, **({'event': event} if event else {})}
        return {**op, **details, 'state': state, 'updated': now, 'history': _history(op, entry)}

    def _new_op(self, op_key, kind, hu, branch, number, event_key):
        existing = self.store.get(op_key)
        if existing:
            return existing
        return {'key': op_key, 'kind': kind, 'hu': hu, 'branch': branch, 'line': number, 'event': event_key,
                'project_id': self.context.project_id, 'state': 'requested', 'created': time.time(), 'history': []}

    def _safe_view(self, limit):
        """(vista, repositorio compartido, observación); una observación fallida es `unknown`, nunca libre."""
        try:
            view, observation = self.view(limit=limit)
            return view, bool((observation.get('git') or {}).get('shared')), observation
        except Exception as exc:
            return ({'status': 'unknown', 'hu': None, 'causes': [f'observation_failed:{type(exc).__name__}'],
                     'authority': (self.store.get(AUTHORITY) or {}).get('state', 'free'), 'observed': 'unknown'},
                    False, {'git': {}})

    # ----------------------------------------------------------------------------- apertura
    def open(self, event_key, number, branch, create):
        """BRANCH-CREATE autoritativo: lock, revalidación, reserva, Git, verificación y confirmación."""
        op_key = op_key_for(event_key)
        existing = self.store.get(op_key)
        if existing and existing.get('state') in ('confirmed', 'rejected') and existing.get('decision'):
            return Decision.from_dict(existing['decision'])           # idempotente: nada se repite
        with self.lock():
            hu = branch[len('feat/'):] if is_feature_branch(branch) else None
            op = self._new_op(op_key, 'open', hu, branch, number, event_key)
            view, shared, _ = self._safe_view(number)
            decision = decide_open(view, hu, shared=shared)._replace(op=op_key)
            if decision.rejected:
                return self._reject(op, decision, view)
            authority = self.authority()
            try:
                tip_before = branch_tip(self.git, branch)
            except GitUnreadable:
                return self._reject(op, decision._replace(verdict='reject', code=UNKNOWN, message=(
                    f'Git no es legible para verificar {branch}; un estado incierto nunca autoriza abrir {hu}.')), view)
            op = self._op(op, 'reserved', decision=decision.to_dict(), view=view, tip_before=tip_before,
                          authority_before={key: authority.get(key) for key in ('state', 'hu', 'op')})
            # La reserva queda persistida antes de tocar Git: ningún otro proceso abre otra HU mientras exista.
            self.store.put_many([(op_key, op),
                                 (AUTHORITY, self._transition(authority, 'opening', hu, op_key, decision.code))])
            try:
                create(branch)
            except BaseException as exc:
                self._open_failed(op_key, hu, branch, tip_before, exc)
                raise
            self._confirm_open(op_key, hu, branch, decision)
        return decision

    def _confirm_open(self, op_key, hu, branch, decision):
        op, authority = self.store.get(op_key), self.authority()
        try:
            tip, head = branch_tip(self.git, branch), head_branch(self.git)
        except GitUnreadable:
            tip, head = None, None
        if tip and head == branch:
            outcome = 'resumed' if decision.verdict == 'resume' else 'opened'
            self.store.put_many([
                (op_key, self._op(op, 'confirmed', outcome=outcome, tip=tip, confirmed=time.time())),
                (AUTHORITY, self._transition(authority, 'active', hu, op_key, outcome))])
            return
        self.store.put_many([
            (op_key, self._op(op, 'reconcile_required', cause='git_verification_failed', tip=tip, head=head)),
            (AUTHORITY, self._transition(authority, 'reconcile_required', hu, op_key, 'git_verification_failed',
                                         causes=['git_verification_failed']))])
        raise ReconciliationRequired(f'GitOps no pudo verificar {branch} tras crearla (rama {tip or "ausente"}, HEAD '
                                     f'{head or "desconocido"}); la HU queda pendiente de reconciliación.')

    def _restore(self, op, reason):
        before = op.get('authority_before') or {}
        state = before.get('state') or 'free'
        return self._transition(self.authority(), state, before.get('hu'), before.get('op'), reason)

    def _open_failed(self, op_key, hu, branch, tip_before, exc):
        op = self.store.get(op_key)
        cause = type(exc).__name__
        try:
            changed = branch_tip(self.git, branch) != tip_before
        except GitUnreadable:
            changed = None
        if changed is False:
            # Git no cambió la rama: la apertura no ocurrió. La reserva vuelve a su estado anterior.
            items = [(op_key, self._op(op, 'failed', cause=cause)), (AUTHORITY, self._restore(op, 'open_failed'))]
        else:
            reason = 'open_failed_after_git_change' if changed else 'open_failed_git_unreadable'
            items = [(op_key, self._op(op, 'reconcile_required', cause=cause, reason=reason)),
                     (AUTHORITY, self._transition(self.authority(), 'reconcile_required', hu, op_key, reason,
                                                  causes=[reason]))]
        try:
            self.store.put_many(items)
        except Exception:
            pass                       # la reserva sigue en opening: fail-closed hasta recover()

    # ------------------------------------------------------------------------------- cierre
    def _decide_close(self, hu, number):
        view, shared, observation = self._safe_view(number)
        return decide_close(view, hu, shared=shared), view, observation

    def close(self, event_key, number, branch, merge, confirm=None):
        """MERGE-CLOSE autoritativo. `confirm` (espera humana) corre sin el lock; la fusión, con él."""
        op_key = op_key_for(event_key)
        existing = self.store.get(op_key)
        if existing and existing.get('state') in ('confirmed', 'rejected') and existing.get('decision'):
            return Decision.from_dict(existing['decision'])
        hu = branch[len('feat/'):] if is_feature_branch(branch) else None
        op = self._new_op(op_key, 'close', hu, branch, number, event_key)
        decision, view, _ = self._decide_close(hu, number)
        if decision.rejected:
            with self.lock():
                return self._reject(op, decision._replace(op=op_key), view)
        if confirm:
            try:
                confirm(branch)
            except BaseException:
                with self.lock():
                    self.store.put(op_key, self._op(op, 'not_executed', cause='close_not_confirmed'))
                raise
        with self.lock():
            decision, view, observation = self._decide_close(hu, number)
            decision = decision._replace(op=op_key)
            if decision.rejected:
                return self._reject(op, decision, view)
            base = (observation.get('git') or {}).get('base')
            try:
                tip_before = branch_tip(self.git, branch)
                base_before = branch_tip(self.git, base) if base else None
            except GitUnreadable:
                tip_before = base_before = None
            if not (base and tip_before and base_before):
                return self._reject(op, decision._replace(verdict='reject', code=UNKNOWN, message=(
                    f'No hay evidencia Git suficiente (rama {branch}, base {base or "-"}) para fusionar {hu}.')), view)
            authority = self.authority()
            op = self._op(op, 'reserved', decision=decision.to_dict(), view=view, tip_before=tip_before, base=base,
                          base_before=base_before,
                          authority_before={key: authority.get(key) for key in ('state', 'hu', 'op')})
            self.store.put_many([(op_key, op),
                                 (AUTHORITY, self._transition(authority, 'closing', hu, op_key, decision.code))])
            try:
                merge(branch)
            except BaseException as exc:
                self._close_failed(op_key, hu, branch, exc)
                raise
            self._confirm_close(op_key, hu, branch)
        return decision

    def _confirm_close(self, op_key, hu, branch):
        op, authority = self.store.get(op_key), self.authority()
        try:
            merged = is_ancestor(self.git, op['tip_before'], op['base'])
            merge_commit, remaining = branch_tip(self.git, op['base']), branch_tip(self.git, branch)
        except GitUnreadable:
            merged, merge_commit, remaining = None, None, None
        if merged:
            closed = {'hu': hu, 'op': op_key, 'tip': op['tip_before'], 'base': op['base'], 'merge_commit': merge_commit,
                      'at': time.time()}
            self.store.put_many([
                (op_key, self._op(op, 'confirmed', outcome='closed', merge_commit=merge_commit,
                                  branch_deleted=remaining is None, confirmed=time.time())),
                (AUTHORITY, self._transition(authority, 'free', None, op_key, 'closed', last_closed=closed))])
            return
        reason = 'merge_not_verified' if merged is False else 'git_unreadable_after_merge'
        self.store.put_many([
            (op_key, self._op(op, 'reconcile_required', cause=reason)),
            (AUTHORITY, self._transition(authority, 'reconcile_required', hu, op_key, reason, causes=[reason]))])
        raise ReconciliationRequired(f'Git no demuestra que {branch} se integrara en {op["base"]}; el cierre de {hu} '
                                     'queda pendiente de reconciliación.')

    def _close_failed(self, op_key, hu, branch, exc):
        op = self.store.get(op_key)
        try:
            merged = is_ancestor(self.git, op['tip_before'], op['base'])
            busy = operation_in_progress(self.git)
            unchanged = (branch_tip(self.git, branch) == op['tip_before']
                         and branch_tip(self.git, op['base']) == op['base_before'])
        except GitUnreadable:
            merged, busy, unchanged = None, None, False
        if merged:
            reason = 'close_interrupted_after_merge'
        elif isinstance(exc, SystemExit) or busy:
            reason = 'merge_conflict'                 # el watcher abortó la fusión y pidió intervención humana
        elif merged is False and unchanged:
            reason = None
        else:
            reason = 'close_failed_unclear'
        if reason is None:
            items = [(op_key, self._op(op, 'failed', cause=type(exc).__name__)),
                     (AUTHORITY, self._restore(op, 'close_failed'))]
        else:
            items = [(op_key, self._op(op, 'reconcile_required', cause=type(exc).__name__, reason=reason)),
                     (AUTHORITY, self._transition(self.authority(), 'reconcile_required', hu, op_key, reason,
                                                  causes=[reason]))]
        try:
            self.store.put_many(items)
        except Exception:
            pass

    # --------------------------------------------------------------------------- rechazo y bloques
    def _reject(self, op, decision, view):
        """Rechazo persistente e idempotente: operación `rejected`, evento terminado y aviso pendiente de emitir."""
        if decision.verdict != 'reject':
            decision = decision._replace(verdict='reject')
        notice = {'op_id': NOTICE_PREFIX + op['key'][len(OP_PREFIX):], 'state': 'pending',
                  'text': notice_block(op, decision, scope_arguments(self.context))}
        op = self._op(op, 'rejected', decision=decision.to_dict(), view=view, notice=notice)
        event = self.store.get(op['event']) or {}
        event = {**event, 'state': 'done', 'outcome': 'rejected', 'hu_op': op['key'], 'updated': time.time()}
        self.store.put_many([(op['key'], op), (op['event'], event)])
        return decision

    def notify(self, op_key):
        """Emite (una vez) el bloque WATCHER del rechazo con TrackerWriter; tras una caída se reemite el mismo texto."""
        op = self.store.get(op_key) or {}
        notice = op.get('notice')
        if not notice or notice.get('state') == 'delivered' or self._writer is None:
            return False
        result = self._writer().append(notice['text'], op_id=notice['op_id'], source='watcher')
        self.store.put(op_key, {**op, 'notice': {**notice, 'state': 'delivered', 'offset': result.offset,
                                                 'delivered_at': time.time()}})
        return True

    def pending_notices(self):
        rows = self.store.db.execute('SELECT id,data FROM records WHERE id >= ? AND id < ?',
                                     (OP_PREFIX, OP_PREFIX[:-1] + ';'))
        return [key for key, raw in rows if (json.loads(raw).get('notice') or {}).get('state') == 'pending']

    def suppressed_by(self, lines, number):
        """Operación E4 no confirmada de una macro anterior del mismo bloque (o None): sus instrucciones no se despachan.

        Solo cuentan macros procesadas en enforce (evento con `hu_gate`); un evento reconocido sin operación confirmada
        sigue bloqueando su bloque."""
        for index in range(block_start(lines, number), number):
            line = lines[index]
            if not (gitops_macro(line, 'BRANCH-CREATE') or gitops_macro(line, 'MERGE-CLOSE')):
                continue
            key, record = _event(self.store, index, line)
            if not record or not record.get(GATE):
                continue
            op_key = op_key_for(key)
            if (self.store.get(op_key) or {}).get('state') != 'confirmed':
                return op_key
        return None

    def suppress(self, event_key, op_key):
        event = self.store.get(event_key) or {}
        self.store.put(event_key, {**event, 'state': 'done', 'outcome': 'suppressed', 'hu_op': op_key,
                                   'updated': time.time()})

    def cancel_block_tasks(self, tasks, lines, number, op_key):
        """Retira de la cola (sin despacharlas) las tareas de líneas anteriores del bloque rechazado."""
        start, kept = block_start(lines, number), []
        for task in tasks:
            key = 'queued:' + task['event_id']
            record = self.store.get(key) or {}
            if start <= record.get('line_number', -1) < number and record.get('state') != 'done':
                self.store.put(key, {**record, 'state': 'done', 'outcome': 'suppressed', 'hu_op': op_key,
                                     'failure': 'hu_gate_rejected', 'stage': 'fallido',
                                     'stages': {**record.get('stages', {}), 'fallido': time.time()}})
            else:
                kept.append(task)
        return kept

    # ------------------------------------------------------------------------------- arranque
    def recover(self):
        """Resuelve una reserva interrumpida (opening/closing) con evidencia Git; ante duda, reconcile_required.

        Nunca ejecuta Git de escritura ni marca eventos: un evento in_flight sigue exigiendo su reconocimiento."""
        with self.lock():
            authority = self.store.get(AUTHORITY)
            if not authority or authority.get('state') not in ('opening', 'closing'):
                return None
            op_key, hu = authority.get('op'), authority.get('hu')
            op = self.store.get(op_key) or {}
            branch = authority.get('branch') or f'feat/{hu}'
            try:
                if authority['state'] == 'opening':
                    tip, before = branch_tip(self.git, branch), op.get('tip_before')
                    if tip:
                        outcome, op_state, auth = 'recovered', 'confirmed', ('active', hu)
                    elif before is None:
                        outcome, op_state, auth = 'not_executed', 'not_executed', None
                    else:
                        outcome, op_state, auth = 'branch_disappeared', 'reconcile_required', ('reconcile_required', hu)
                else:
                    if operation_in_progress(self.git):
                        outcome = 'merge_in_progress'
                    elif op.get('tip_before') and is_ancestor(self.git, op['tip_before'], op['base']):
                        outcome = 'close_interrupted_after_merge'
                    elif (op.get('tip_before') and branch_tip(self.git, branch) == op['tip_before']
                          and branch_tip(self.git, op['base']) == op.get('base_before')):
                        outcome = 'not_executed'
                    else:
                        outcome = 'close_interrupted_unclear'
                    op_state = 'not_executed' if outcome == 'not_executed' else 'reconcile_required'
                    auth = None if outcome == 'not_executed' else ('reconcile_required', hu)
            except GitUnreadable:
                return {'state': authority['state'], 'hu': hu, 'outcome': 'git_unreadable'}
            new_authority = (self._restore(op, outcome) if auth is None else
                             self._transition(authority, auth[0], auth[1], op_key, outcome,
                                              **({'causes': [outcome]} if auth[0] == 'reconcile_required' else {})))
            items = [(AUTHORITY, new_authority)]
            if op:
                items.append((op_key, self._op(op, op_state, event='recovery', recovery=outcome)))
            self.store.put_many(items)
            return {'state': new_authority['state'], 'hu': hu, 'outcome': outcome}

    def hydration_branch(self):
        """Rama a reactivar al arrancar: solo la HU abierta demostrada (reserva y Git de acuerdo); nunca una apertura
        rechazada, una rama desaparecida o un estado dudoso: entonces HEAD no se mueve."""
        view = self._safe_view(None)[0]
        return f"feat/{view['hu']}" if view['status'] == 'one_open_hu' and view['hu'] else None


# ------------------------------------------------------------------------------------- Control Center
def preflight(context, hu, *, git=None):
    """Mismas reglas que el watcher, en solo lectura (SQLite ro, Git de lectura). Informativo: el watcher revalida."""
    store = None
    try:
        store = StateStore.open_readonly(context)
        observation = observe(context, store, git=git)
        authority = store.get(AUTHORITY) if store else None
    except Exception as exc:
        return Decision('reject', UNKNOWN, 'unknown', hu, None,
                        f'No se pudo observar el ciclo de vida de HU ({type(exc).__name__}); un estado incierto '
                        f'nunca autoriza abrir {hu}.', (f'preflight_failed:{type(exc).__name__}',))
    finally:
        if store:
            store.close()
    view = project_view(authority, observation)
    return decide_open(view, hu, shared=bool((observation.get('git') or {}).get('shared')))


# ------------------------------------------------------------------------------------ reconciliación humana
def _operations(store, hu=None):
    found = []
    for key, data in _previous_records(store, OP_PREFIX).items():
        if hu is None or data.get('hu') == hu:
            found.append({'key': OP_PREFIX + key, **{name: data.get(name) for name in (
                'kind', 'hu', 'branch', 'line', 'state', 'outcome', 'cause', 'reason', 'tip_before', 'base',
                'created', 'updated')}, 'code': (data.get('decision') or {}).get('code'),
                'notice': (data.get('notice') or {}).get('state')})
    return sorted(found, key=lambda item: item.get('created') or 0)


def _close_proof(git, snapshot, hu, store):
    """Evidencia Git de integración de la HU en la base (nunca mensajes, HEAD ni borrado de rama)."""
    base = snapshot.get('base')
    branch = snapshot['features'].get(hu)
    if not base:
        return None
    if branch:
        if is_ancestor(git, branch['tip'], base):
            return {'kind': 'branch_tip_integrated', 'tip': branch['tip'][:12], 'base': base}
        return None                     # rama presente sin integrar: no hay cierre
    for op in reversed(_operations(store, hu) if store else []):
        if op['kind'] == 'close' and op.get('tip_before') and is_ancestor(git, op['tip_before'], base):
            return {'kind': 'recorded_close_tip_integrated', 'tip': op['tip_before'][:12], 'base': base,
                    'op': op['key']}
    return None


def propose(observation, hu, proof):
    data = observation['hus'].get(hu) or {}
    if proof:
        return 'closed'
    return 'active' if ((data.get('evidence') or {}).get('git') or {}).get('exists') else 'abandoned'


def inspect(context, store, *, git=None):
    """Evidencia Git, tracker y SQLite, causa de cada inconsistencia y propuesta por HU (solo lectura)."""
    reader = git or GitReader(context.workspace_root)
    observation = observe(context, store, git=reader)
    authority = store.get(AUTHORITY) if store else None
    view = project_view(authority, observation)
    snapshot = git_evidence(context.workspace_root, reader)
    proposals = {}
    for hu in sorted(set(observation.get('unresolved') or []) | set(observation.get('open') or [])
                     | ({authority['hu']} if authority and authority.get('hu') else set())):
        try:
            proof = _close_proof(reader, snapshot, hu, store) if snapshot.get('available') else None
        except GitUnreadable:
            proof = None
        data = observation['hus'].get(hu) or {}
        proposals[hu] = {'observed_state': data.get('observed_state'), 'causes': data.get('causes'),
                         'proposal': propose(observation, hu, proof), 'close_proof': proof}
    return {'project_id': context.project_id, 'workspace': str(context.workspace_root), 'view': view,
            'authority': authority, 'observation': {key: observation.get(key) for key in (
                'status', 'open', 'unresolved', 'certainty', 'causes', 'git', 'tracker')},
            'hus': {hu: {key: data[key] for key in ('observed_state', 'certainty', 'causes', 'evidence')}
                    for hu, data in observation['hus'].items()},
            'operations': _operations(store) if store else [],
            'resolutions': _previous_records(store, RESOLUTION_PREFIX) if store else {},
            'proposals': proposals}


def reconcile(context, store, hu, target, *, reason='', actor=None, confirm=False, git=None):
    """Resolución humana explícita de una HU (`active`, `closed` o `abandoned`), ligada a la evidencia actual.

    No crea ni elimina ramas ni toca el tracker. `closed` exige evidencia Git de integración; `abandoned`, que la
    rama ya no exista; `active`, que la rama exista sin integrar y no haya otra HU abierta. Sin `confirm` solo
    devuelve el plan."""
    if target not in RESOLUTIONS:
        raise ReconciliationRequired(f'Resolución desconocida {target!r}; usa una de {", ".join(RESOLUTIONS)}.')
    if not is_hu_id(hu or ''):
        raise ReconciliationRequired(f'{hu!r} no es un identificador de HU NNN-nombre-en-kebab-case.')
    reader = git or GitReader(context.workspace_root)
    snapshot = git_evidence(context.workspace_root, reader)
    if not snapshot.get('available'):
        raise ReconciliationRequired(f'Git no legible ({snapshot.get("cause")}): no se reconcilia nada.')
    if snapshot['operations']:
        raise ReconciliationRequired(f'Hay una operación Git en curso ({", ".join(snapshot["operations"])}); termínala '
                                     'o abórtala manualmente antes de reconciliar.')
    tracker = macro_evidence(context, store)
    if not tracker.get('available'):
        raise ReconciliationRequired(f'Tracker no legible ({tracker.get("cause")}): no se reconcilia nada.')
    observation = observe(context, store, git=reader)
    authority = (store.get(AUTHORITY) if store else None) or {'state': 'free', 'hu': None, 'history': []}
    git_hu, macros = _git_for_hu(snapshot, hu), tracker['macros'].get(hu, [])
    proof = _close_proof(reader, snapshot, hu, store)
    others = sorted((set(observation.get('open') or []) | set(observation.get('unresolved') or [])) - {hu})
    if target == 'closed' and not proof:
        raise ReconciliationRequired(f'La evidencia Git no demuestra que feat/{hu} esté integrada en '
                                     f'{snapshot.get("base") or "la base"}: no se declara closed. Si la HU se descarta, '
                                     'elimina la rama manualmente y usa --as abandoned.')
    if target == 'abandoned' and git_hu['exists']:
        raise ReconciliationRequired(f'feat/{hu} sigue existiendo: abandoned exige que un humano la haya eliminado '
                                     '(o usa --as closed si está integrada).')
    if target == 'active':
        if not git_hu['exists'] or proof:
            raise ReconciliationRequired(f'active exige que feat/{hu} exista sin integrar en la base.')
        holder = authority.get('hu') if authority.get('state') not in (None, 'free') else None
        if others or (holder and holder != hu):
            raise ReconciliationRequired(f'Hay otras HU abiertas o sin resolver ({", ".join(others or [holder])}); '
                                         f'resuélvelas antes de declarar activa {hu}.')
    data = observation['hus'].get(hu) or {}
    plan = {'project_id': context.project_id, 'hu': hu, 'resolution': target,
            'from_state': data.get('observed_state'), 'causes': data.get('causes'),
            'evidence': {'git': git_hu, 'close_proof': proof,
                         'tracker': {'creates': [m['line'] for m in macros if m['action'] == 'create'],
                                     'closes': [m['line'] for m in macros if m['action'] == 'close']}},
            'authority_before': {key: authority.get(key) for key in ('state', 'hu', 'op')}}
    if not confirm:
        return {'dry_run': True, **plan}
    if not reason or not reason.strip():
        raise ReconciliationRequired('La reconciliación exige --reason con la justificación.')
    now = time.time()
    key = RESOLUTION_PREFIX + hu
    previous = store.get(key) or {}
    resolution = {**plan, 'observed_state': 'active' if target == 'active' else 'closed',
                  'fingerprint': resolution_fingerprint(target, git_hu, macros), 'reason': reason.strip(),
                  'actor': actor, 'at': now,
                  'history': _history(previous, {name: previous.get(name) for name in ('resolution', 'at', 'actor',
                                                                                       'reason')})
                  if previous else []}
    holder = authority.get('hu')
    if target == 'active':
        new_authority = Enforcer._transition(authority, 'active', hu, None, 'human_reconciled:active',
                                             last_resolution={'hu': hu, 'resolution': target, 'at': now})
    elif holder == hu and authority.get('state') not in (None, 'free'):
        new_authority = Enforcer._transition(authority, 'free', None, None, f'human_reconciled:{target}',
                                             last_resolution={'hu': hu, 'resolution': target, 'at': now})
    else:
        new_authority = None
    items = [(key, resolution)]
    if new_authority:
        items.append((AUTHORITY, new_authority))
    for op in _operations(store, hu):
        if op['state'] in ('reconcile_required', 'reserved'):
            items.append((op['key'], Enforcer._op(store.get(op['key']), 'reconciled', event='human_reconciled',
                                                  resolution=key)))
    store.put_many(items)
    return {'dry_run': False, **plan,
            'authority_after': {name: (new_authority or authority).get(name) for name in ('state', 'hu', 'op')}}


def _actor(explicit=None):
    if explicit:
        return explicit
    try:
        return os.environ.get('BMAD_ACTOR') or getpass.getuser()
    except Exception:
        return None


def main(argv=None):
    from .context import add_project_arguments, resolve_context
    parser = argparse.ArgumentParser(description='Una HU abierta por proyecto (Fase 4F-E4): inspección y '
                                                 'reconciliación humana explícita. Nunca crea ni elimina ramas.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Engine root.')
    add_project_arguments(parser)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--inspect', action='store_true',
                        help='Evidencia Git/tracker/SQLite y propuestas (solo lectura).')
    action.add_argument('--reconcile', metavar='HU', help='HU (NNN-nombre-en-kebab-case) a reconciliar.')
    parser.add_argument('--as', dest='target', choices=RESOLUTIONS, help='Resolución basada en evidencia.')
    parser.add_argument('--reason', default='', help='Justificación (obligatoria con --confirm).')
    parser.add_argument('--actor', help='Identidad del solicitante (por defecto BMAD_ACTOR o el usuario del SO).')
    parser.add_argument('--confirm', action='store_true', help='Aplica la reconciliación; sin él es un dry-run.')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    context = resolve_context(args.root, workspace=args.workspace, project=args.project)
    if args.inspect:
        store = StateStore.open_readonly(context)
        try:
            print(json.dumps(inspect(context, store), ensure_ascii=False, indent=2, default=str))
        finally:
            if store:
                store.close()
        return 0
    if not args.target:
        parser.error('--reconcile requiere --as active|closed|abandoned.')
    try:
        if not args.confirm:
            store = StateStore.open_readonly(context)
            try:
                result = reconcile(context, store, args.reconcile, args.target)
            finally:
                if store:
                    store.close()
        else:
            # Con el watcher detenido (su lock) y el lock de HU: ninguna apertura o cierre corre a la vez.
            with project_lock(context, 'watcher'), hu_lock(context):
                store = StateStore(context)
                try:
                    result = reconcile(context, store, args.reconcile, args.target, reason=args.reason,
                                       actor=_actor(args.actor), confirm=True)
                finally:
                    store.close()
    except ReconciliationRequired as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
