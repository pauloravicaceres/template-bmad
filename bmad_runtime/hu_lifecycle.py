"""Ciclo de vida observado de las historias de usuario (HU) por proyecto — Fase 4F-E3 (OBSERVE) y base de E4.

Cruza fuentes con responsabilidades separadas y no modifica ninguna:
- Git (solo lectura): ramas `feat/NNN-nombre`, HEAD, operación en curso y evidencia de integración en la base.
- Tracker: macros `@WATCHER: GITOPS-BRANCH-CREATE/MERGE-CLOSE` (instrucciones GitOps).
- SQLite del proyecto: eventos del watcher que ejecutaron esas macros, cursor del tracker, alerta de conflicto
  (journal de tracker_io) y la observación anterior.
- Documentos HU: solo contexto; su existencia nunca prueba apertura ni cierre.

El resultado es observado, no autoritativo: no bloquea aperturas, no cierra HUs ni cambia el despacho. En modo
`enforce` (Fase 4F-E4) hu_enforcement.py combina esta observación con su reserva persistente para autorizar o
rechazar BRANCH-CREATE y MERGE-CLOSE; aquí solo se excluyen las macros que nunca se ejecutaron (rechazadas, fallidas
sin cambios o suprimidas) y se aplican las resoluciones humanas registradas (`hu_resolution:<hu>`).
Con evidencia insuficiente o contradictoria el estado es `unknown` o `reconcile_required`; una observación fallida
se registra como `unknown` y nunca como "sin HU abierta". Un cambio de HEAD no cierra nada y una rama cerrada
puede seguir existiendo.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .errors import ConfigurationError
from .hu_naming import HU_ID, is_feature_branch
from .state import StateStore

STATES = ('unknown', 'opening', 'active', 'closing', 'closed', 'reconcile_required')
OPEN_STATES = frozenset({'opening', 'active', 'closing', 'reconcile_required'})
PROJECT_STATUSES = ('no_open_hu', 'one_open_hu', 'reconcile_required', 'unknown')
MODES = ('observe', 'off', 'enforce')
SUMMARY = 'hu_lifecycle'
PREFIX = 'hu_lifecycle:'
BASE_CANDIDATES = ('dev', 'main', 'master')      # mismo orden que workflow.get_base_branch
MERGE_LOG_LIMIT = 2000
_READ_ONLY = frozenset({'rev-parse', 'symbolic-ref', 'for-each-ref', 'rev-list', 'log', 'merge-base'})
# Variables que redirigirían Git a otro repositorio o índice distinto del workspace observado.
_GIT_REDIRECTS = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
                  'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE', 'GIT_CEILING_DIRECTORIES')
_IN_PROGRESS = ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply')
_MERGED_FEATURE = re.compile(rf"feat/({HU_ID})(?![\w-])")
CONFLICT_ALERT = 'tracker_append:gitops-conflict:'   # op_id de workflow.gitops_merge_close
# Fase 4F-E4 (hu_enforcement.py). Claves SQLite compartidas con la observación.
AUTHORITY = 'hu_authority'            # reserva autoritativa: como máximo una HU abierta por proyecto
OP_PREFIX = 'hu_op:'                  # una operación de apertura/cierre por evento del watcher (id estable)
RESOLUTION_PREFIX = 'hu_resolution:'  # reconciliación humana explícita, ligada a la evidencia que resolvió
GATE = 'hu_gate'                      # metadato del evento del watcher de una macro GitOps procesada en enforce
NOT_EXECUTED_OPS = frozenset({'rejected', 'failed', 'not_executed'})
NOT_EXECUTED_OUTCOMES = frozenset({'rejected', 'suppressed'})


def op_key_for(event_key):
    """Clave estable de la operación E4 asociada al evento `event:<sha256>` de una línea del tracker."""
    return OP_PREFIX + StateStore.fingerprint(event_key)[:32]


def gitops_macro(line, action):
    """Rama de una macro GitOps (`BRANCH-CREATE` / `MERGE-CLOSE`) solo si la línea ES la orden.

    La macro debe abrir la línea (tras viñetas y el prefijo `- **Handoff:**`); una mención en prosa no cuenta.
    Contrato único del watcher (workflow.macro_gitops) y de esta observación.
    """
    clean = re.sub(r"^\s*(?:[-*]\s+)*(?:\*\*Handoff:\*\*\s*)?", "", line)
    match = re.match(rf"@WATCHER:\s*GITOPS-{action}\s+([^\s`'\"]+)", clean.strip())
    return match.group(1) if match else None


def policy_from_config(value):
    """`ai.hu_lifecycle`: {"mode": "observe"|"off"|"enforce"}; observe por defecto.

    enforce solo debe activarse explícitamente (project.json de un proyecto aislado o configuración de pruebas).
    """
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - {'mode'}:
        raise ConfigurationError('ai.hu_lifecycle accepts only mode.')
    mode = value.get('mode', 'observe')
    if mode not in MODES:
        raise ConfigurationError('ai.hu_lifecycle.mode must be observe, off or enforce.')
    return {'mode': mode}


def load_policy(context):
    """Política efectiva del proyecto (config del motor + override de project.json), solo lectura.

    Sin project.json (fixtures, proyectos sin overrides) se usa la del motor. Un project.json presente pero ilegible
    o inválido lanza ConfigurationError: nunca degrada en silencio un proyecto en enforce a observe (Fase 4F-E4.1)."""
    from .config import effective_config
    from .context import read_json
    try:
        ai = effective_config(context).get('ai', {})
    except ConfigurationError:
        if context.legacy or (Path(context.workspace_root) / 'project.json').exists():
            raise
        path = context.engine_root / 'config_bmad.json'
        ai = read_json(path).get('ai', {}) if path.exists() else {}
    return policy_from_config(ai.get('hu_lifecycle') if isinstance(ai, dict) else None)


def _digest(value, size=16):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:size]


def _same_path(a, b):
    return os.path.normcase(str(Path(a).resolve())) == os.path.normcase(str(Path(b).resolve()))


# ----------------------------------------------------------------------------------------------- Git
class GitReader:
    """Git de solo lectura acotado al repositorio propio del workspace; nunca sube a un repositorio padre."""

    def __init__(self, root, timeout=20):
        self.root = Path(root)
        self.timeout = timeout

    def __call__(self, *args):
        if not args or args[0] not in _READ_ONLY:
            raise ValueError(f'hu_lifecycle only runs read-only Git commands, not {args[:1]}.')
        env = {key: value for key, value in os.environ.items() if key not in _GIT_REDIRECTS}
        # Sin locks opcionales (no refresca el índice) ni prompts; el techo impide usar un repositorio padre.
        env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_CEILING_DIRECTORIES=str(self.root.parent))
        result = subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=self.timeout, env=env)
        return result.returncode, result.stdout


def git_evidence(root, git=None):
    """Instantánea Git del workspace (solo lectura). `available=False` con causa si no puede leerse."""
    root = Path(root)
    if not (root / '.git').exists():
        return {'available': False, 'cause': 'no_repository'}
    git = git or GitReader(root)
    try:
        return _git_snapshot(root, git)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {'available': False, 'cause': 'git_unreadable'}


def _git_snapshot(root, git):
    code, out = git('rev-parse', '--show-toplevel', '--absolute-git-dir', '--git-common-dir')
    parts = out.splitlines()
    if code or len(parts) < 3:
        return {'available': False, 'cause': 'git_unreadable'}
    if not _same_path(parts[0], root):
        return {'available': False, 'cause': 'foreign_toplevel'}
    git_dir = Path(parts[1])
    common_dir = Path(parts[2]) if Path(parts[2]).is_absolute() else root / parts[2]
    # Worktrees enlazados al mismo almacén de refs (incluido el principal que los aloja): ramas compartidas.
    linked = common_dir / 'worktrees'
    linked = sorted(item.name for item in linked.iterdir() if item.is_dir()) if linked.is_dir() else []
    code, out = git('symbolic-ref', '-q', 'HEAD')
    head = out.strip()[len('refs/heads/'):] if code == 0 and out.startswith('refs/heads/') else None
    code, out = git('for-each-ref', '--format=%(refname)%00%(objectname)', 'refs/heads')
    if code:
        return {'available': False, 'cause': 'branches_unreadable'}
    branches = {}
    for line in out.splitlines():
        name, _, sha = line.partition('\0')
        branches[name[len('refs/heads/'):]] = sha.strip()
    base = next((name for name in BASE_CANDIDATES if name in branches), None)
    operations = [name for name in _IN_PROGRESS if (git_dir / name).exists()]
    merge_head = None
    if 'MERGE_HEAD' in operations:
        merge_head = ((git_dir / 'MERGE_HEAD').read_text(encoding='utf-8', errors='replace').split() or [None])[0]
    merges, truncated = {}, False
    if base:
        code, out = git('log', base, '--merges', f'--max-count={MERGE_LOG_LIMIT}', '--format=%H%x00%P%x00%s', '--')
        rows = [line.split('\0') for line in out.splitlines() if line.count('\0') == 2] if code == 0 else []
        truncated = len(rows) >= MERGE_LOG_LIMIT
        for sha, parents, subject in rows:
            for hu in set(_MERGED_FEATURE.findall(subject)) if subject.startswith('Merge ') else ():
                entry = merges.setdefault(hu, {'commits': [], 'parents': set()})
                if len(entry['commits']) < 5:
                    entry['commits'].append(sha[:12])
                entry['parents'].update(parents.split()[1:])
    # Ramas feat/ con nombre fuera de contrato y trabajo sin integrar en la base (o sin base que lo demuestre):
    # pueden ser una HU abierta fuera del watcher. E3 solo las informa; enforce no puede declarar libre el proyecto.
    invalid_unmerged = []
    for name in sorted(name for name in branches if name.startswith('feat/') and not is_feature_branch(name)):
        count = None
        if base:
            code, out = git('rev-list', '--count', f'{base}..{name}', '--')
            count = int(out.strip()) if code == 0 and out.strip().isdigit() else None
        if count != 0:
            invalid_unmerged.append(name)
    features = {}
    for name, sha in branches.items():
        if not is_feature_branch(name):
            continue
        ahead = None
        if base:
            code, out = git('rev-list', '--count', f'{base}..{name}', '--')
            ahead = int(out.strip()) if code == 0 and out.strip().isdigit() else None
        features[name[len('feat/'):]] = {'tip': sha, 'ahead': ahead}
    return {
        'available': True, 'head': head, 'base': base, 'operations': operations, 'merge_head': merge_head,
        # Identidad del almacén de refs: dos workspaces con el mismo id comparten ramas (worktrees).
        'repository': _digest(os.path.normcase(str(common_dir.resolve()))),
        'worktree': not _same_path(git_dir, common_dir),
        'linked_worktrees': len(linked),
        'shared': not _same_path(git_dir, common_dir) or bool(linked),
        'features': features, 'merges': merges, 'merge_log_truncated': truncated,
        'invalid_branches': sorted(name for name in branches if name.startswith('feat/') and not is_feature_branch(name)),
        'invalid_unmerged': invalid_unmerged,
    }


def _git_for_hu(snapshot, hu):
    branch = snapshot['features'].get(hu)
    merges = snapshot['merges'].get(hu, {'commits': [], 'parents': set()})
    tip = branch['tip'] if branch else None
    return {
        'exists': branch is not None,
        'tip': tip[:12] if tip else None,
        'ahead': branch['ahead'] if branch else None,
        # Integración exacta: una merge en la base cuyo padre fusionado es la punta actual de la rama.
        'tip_merged': bool(tip) and tip in merges['parents'],
        # Mensajes de merge que citan la rama: evidencia parcial (puede ser un cierre anterior o externo).
        'merge_commits': list(merges['commits']),
        'head': snapshot['head'] == f'feat/{hu}',
        'merge_in_progress': bool(tip) and snapshot['merge_head'] == tip,
    }


# ------------------------------------------------------------------------------------ Tracker + SQLite
def _read_tracker(path, retries=3, sleep=time.sleep):
    from .watcher_service import read_tracker
    for attempt in range(retries):
        snapshot = read_tracker(path)
        if snapshot.stable and not snapshot.error:
            return snapshot
        if attempt + 1 < retries:
            sleep(0.2)
    return snapshot


def _event(store, number, line):
    """Registro SQLite del evento del watcher para la línea `number` (mismo fingerprint que begin_line)."""
    if store is None:
        return None, None
    for text in dict.fromkeys((line, line.rstrip('\n'))):
        key = 'event:' + StateStore.fingerprint(number, text)
        record = store.get(key)
        if record is not None:
            return key, record
    return 'event:' + StateStore.fingerprint(number, line), None


def not_executed(store, key, record):
    """Macro procesada que no abrió ni cerró nada: rechazada/suprimida (E4) u operación fallida sin cambios."""
    if record.get('outcome') in NOT_EXECUTED_OUTCOMES:
        return True
    if store is not None and record.get(GATE):
        operation = store.get(op_key_for(key))
        return bool(operation) and operation.get('state') in NOT_EXECUTED_OPS
    return False


def macro_evidence(context, store, sleep=time.sleep, limit=None):
    """Macros GitOps del tracker agrupadas por HU, con el estado SQLite de cada evento del watcher.

    `limit` acota a las líneas anteriores a ese índice (E4 decide una macro con el historial previo, sin ella misma
    ni las posteriores). Las macros que nunca se ejecutaron quedan en `excluded_macros`, fuera de la inferencia.
    """
    path = context.tracker_path
    snapshot = _read_tracker(path, sleep=sleep)
    if snapshot.error or not snapshot.stable:
        return {'available': False, 'cause': 'tracker_' + (snapshot.error or 'unstable')}
    cursor = ((store.get('tracker_cursor') if store else None) or {}).get('count')
    by_hu, invalid, excluded = {}, [], {}
    for number, line in enumerate(snapshot.lines if limit is None else snapshot.lines[:limit]):
        for action, macro in (('create', 'BRANCH-CREATE'), ('close', 'MERGE-CLOSE')):
            branch = gitops_macro(line, macro)
            if not branch:
                continue
            if not is_feature_branch(branch):
                invalid.append(number + 1)       # el watcher la rechaza sin crear ni cerrar nada
                continue
            key, record = _event(store, number, line)
            record = record or {}
            if record and not_executed(store, key, record):
                excluded.setdefault(branch[len('feat/'):], []).append(number + 1)
                continue
            entry = {'action': action, 'line': number + 1, 'event': key, 'event_state': record.get('state'),
                     'acknowledged': bool(record.get('acknowledged')),
                     # Macro procesada en enforce: solo su operación E4 confirmada prueba la apertura o el cierre.
                     'gated': bool(record.get(GATE)),
                     'op_state': (store.get(op_key_for(key)) or {}).get('state') if record.get(GATE) and store else None,
                     # Sin registro: pendiente si el cursor no la ha alcanzado; omitida si quedó atrás.
                     'unprocessed': None if record else ('pending' if cursor is None or number >= cursor else 'skipped')}
            if action == 'close' and key and store is not None:
                alert = store.get(CONFLICT_ALERT + key[len('event:'):][:64])
                entry['conflict_alert'] = alert.get('state') if alert else None
            by_hu.setdefault(branch[len('feat/'):], []).append(entry)
    return {'available': True, 'exists': path.exists(), 'cursor': cursor, 'store': store is not None,
            'macros': by_hu, 'invalid_macros': invalid, 'excluded_macros': excluded}


# ------------------------------------------------------------------------------------------- Inferencia
def _event_view(macros, action):
    """Evento SQLite de la última macro `action` de la HU (o None)."""
    entry = next((m for m in reversed(macros) if m['action'] == action), None)
    if entry is None:
        return None
    view = {key: entry[key] for key in ('line', 'event', 'event_state', 'acknowledged', 'unprocessed')}
    if entry.get('gated'):
        view['op_state'] = entry.get('op_state')
    if 'conflict_alert' in entry:
        view['conflict_alert'] = entry['conflict_alert']
    return view


def infer(git, macros, previous=None, *, merge_log_truncated=False):
    """Estado observado de una HU a partir de su evidencia Git y de sus macros (con estado SQLite).

    Devuelve (estado, certeza high|medium|low, causas). Nunca deduce `closed` sin instrucción de cierre en el
    tracker, ejecución registrada por el watcher y evidencia Git de integración.
    """
    last_create = next((m for m in reversed(macros) if m['action'] == 'create'), None)
    last_close = next((m for m in reversed(macros) if m['action'] == 'close'), None)
    last = macros[-1]['action'] if macros else None
    exists, merged_tip, merge_commits = git['exists'], git['tip_merged'], bool(git['merge_commits'])
    current = last_close if last == 'close' else last_create
    stale = [m['line'] for m in macros if m['event_state'] == 'in_flight' and m is not current]
    causes = ['stale_event_in_flight'] if stale else []

    def result(state, certainty, *extra):
        found = causes + list(extra)
        if exists and not git['head'] and state in OPEN_STATES:
            found.append('head_elsewhere')      # informativo: HEAD no abre ni cierra una HU
        if git['head'] and state == 'closed':
            found.append('head_on_closed_branch')
        return state, ('low' if stale and certainty == 'high' else certainty), found

    if last is None:
        if not exists:
            if previous and previous.get('observed_state') == 'closed':
                return result('closed', 'low', 'previous_observation_only')
            return result('unknown', 'low', 'evidence_disappeared')
        if previous and previous.get('observed_state') == 'closed' and merged_tip:
            return result('closed', 'low', 'previous_observation_only', 'branch_retained')
        if merged_tip:
            return result('unknown', 'medium', 'untracked_branch', 'integrated')
        return result('unknown', 'low', 'untracked_branch', 'unmerged' if git['ahead'] else 'no_commits')

    if last == 'create':
        event = last_create
        if event['event_state'] == 'in_flight':
            return result('opening', 'medium', 'event_in_flight', 'branch_present' if exists else 'branch_absent')
        if event['event_state'] is None and event['unprocessed'] == 'pending':
            return result('opening', 'high', 'create_pending')
        if event['event_state'] == 'done':
            ack = ['event_acknowledged'] if event['acknowledged'] else []
            if event.get('gated') and event.get('op_state') != 'confirmed':
                # Evento terminado (p. ej. reconocido) sin apertura E4 verificada: nunca `active` por la rama.
                return result('reconcile_required', 'high', 'open_unconfirmed',
                              f"op_{event.get('op_state') or 'missing'}", *ack)
            if exists and merged_tip:
                return result('reconcile_required', 'high', 'merged_outside_watcher', 'branch_retained', *ack)
            if exists:
                return result('active', 'medium' if ack else 'high', *ack, *([] if git['ahead'] else ['no_commits']))
            if merge_commits:
                return result('reconcile_required', 'high', 'merged_outside_watcher', 'branch_absent', *ack)
            return result('reconcile_required', 'high', 'branch_absent', *ack)
        if event['event_state'] is not None:
            return result('unknown', 'low', f"event_{event['event_state']}")
        # Instrucción anterior al cursor sin evento: el watcher no la ejecutó (histórico ignorado o estado nuevo).
        not_run = 'create_not_executed_by_watcher'
        if exists and merged_tip:
            return result('reconcile_required', 'medium', not_run, 'merged_outside_watcher', 'branch_retained')
        if exists:
            return result('active', 'medium', not_run)
        return result('unknown', 'low', not_run, 'branch_absent', *(['merge_commit_found'] if merge_commits else []))

    event = last_close
    ack = ['close_acknowledged'] if event['acknowledged'] else []
    if event['event_state'] is None and event['unprocessed'] == 'pending':
        return result('closing', 'high', 'close_pending')
    if event['event_state'] == 'in_flight':
        if event.get('conflict_alert') or git['merge_in_progress']:
            return result('reconcile_required', 'high', 'merge_conflict',
                          *(['conflict_alert_' + event['conflict_alert']] if event.get('conflict_alert') else []),
                          *(['merge_in_progress'] if git['merge_in_progress'] else []))
        if merged_tip or (not exists and merge_commits):
            # Merge hecho pero el evento no terminó: evidencia parcial, nunca un cierre automático.
            return result('reconcile_required', 'medium', 'close_interrupted_after_merge')
        if exists:
            return result('closing', 'low', 'event_in_flight')
        return result('reconcile_required', 'medium', 'branch_absent_without_merge')
    if event['event_state'] == 'done':
        if event.get('gated') and event.get('op_state') != 'confirmed':
            # Cierre E4 sin operación confirmada (conflicto reconocido, fusión manual): nunca `closed` por mensajes.
            return result('reconcile_required', 'high', 'close_unconfirmed',
                          f"op_{event.get('op_state') or 'missing'}", *ack)
        if not exists and merge_commits:
            return result('closed', 'medium' if ack else 'high', *ack)
        if exists and merged_tip:
            return result('closed', 'medium', 'branch_retained', *ack)
        if exists:
            return result('reconcile_required', 'high', 'close_done_branch_unmerged', *ack)
        return result('reconcile_required', 'medium', 'merge_evidence_missing', *ack,
                      *(['merge_log_truncated'] if merge_log_truncated else []))
    if event['event_state'] is not None:
        return result('unknown', 'low', f"event_{event['event_state']}")
    not_run = 'close_not_executed_by_watcher'
    if (not exists and merge_commits) or merged_tip:
        return result('unknown', 'low', not_run, *(['branch_retained'] if exists else []))
    return result('reconcile_required', 'medium', not_run, 'branch_unmerged' if exists else 'branch_absent_without_merge')


def _previous_records(store, prefix=PREFIX):
    if store is None:
        return {}
    rows = store.db.execute('SELECT id,data FROM records WHERE id >= ? AND id < ?', (prefix, prefix[:-1] + ';'))
    return {key[len(prefix):]: json.loads(raw) for key, raw in rows}


def resolution_fingerprint(resolution, git_hu, macros):
    """Evidencia a la que se ata una reconciliación humana: si cambia (nuevas macros, rama que reaparece o se mueve
    tras un cierre), la resolución deja de aplicarse y la HU vuelve a inferirse."""
    evidence = {'exists': git_hu['exists'], 'tip_merged': git_hu['tip_merged'],
                'creates': [m['line'] for m in macros if m['action'] == 'create'],
                'closes': [m['line'] for m in macros if m['action'] == 'close']}
    if resolution != 'active':
        evidence['tip'] = git_hu['tip']
    return _digest(evidence, 64)


def _documents(context, hu):
    try:
        return {'hu_file': (context.docs_dir / 'business-analyst' / f'{hu}.md').is_file(),
                'spec_dir': (context.specs_dir / hu).is_dir()}
    except (OSError, ConfigurationError):
        return None


def observe(context, store=None, *, git=None, sleep=time.sleep, limit=None):
    """Observación en vivo de un proyecto. Lee Git, tracker y SQLite; no escribe nada en ninguno.

    `limit`: solo las líneas del tracker anteriores a ese índice (decisión E4 de la macro en esa línea)."""
    snapshot = git_evidence(context.workspace_root, git)
    tracker = macro_evidence(context, store, sleep=sleep, limit=limit)
    previous = _previous_records(store)
    resolutions = _previous_records(store, RESOLUTION_PREFIX)
    observation = {'project_id': context.project_id, 'mode': 'observe', 'authoritative': False,
                   'git': {key: snapshot[key] for key in ('available', 'cause', 'head', 'base', 'operations',
                                                          'repository', 'worktree', 'shared', 'invalid_branches',
                                                          'invalid_unmerged')
                           if key in snapshot},
                   'tracker': {key: tracker[key] for key in ('available', 'cause', 'exists', 'cursor', 'store',
                                                             'invalid_macros') if key in tracker},
                   'hus': {}}
    if tracker.get('excluded_macros'):
        observation['tracker']['excluded_macros'] = tracker['excluded_macros']
    if snapshot['available'] and tracker['available']:
        excluded = tracker['excluded_macros']
        for hu in sorted(set(tracker['macros']) | set(snapshot['features']) | set(previous) | set(resolutions)):
            macros = tracker['macros'].get(hu, [])
            git_hu = _git_for_hu(snapshot, hu)
            if not macros and not git_hu['exists'] and (hu in excluded or hu not in previous):
                continue        # solo macros que nunca se ejecutaron (o una resolución sin rastro): nunca se abrió
            state, certainty, causes = infer(git_hu, macros, previous.get(hu),
                                             merge_log_truncated=snapshot['merge_log_truncated'])
            resolution = resolutions.get(hu)
            if resolution and resolution.get('fingerprint') == resolution_fingerprint(
                    resolution.get('resolution'), git_hu, macros):
                state, certainty = resolution['observed_state'], 'medium'
                causes = ['human_reconciled:' + resolution['resolution']]
            if snapshot['worktree'] and not macros:
                causes.append('shared_repository')      # rama visible por compartir refs: quizá de otro proyecto
            observation['hus'][hu] = {
                'project_id': context.project_id, 'hu': hu, 'branch': f'feat/{hu}', 'base': snapshot['base'],
                'observed_state': state, 'authoritative': False, 'certainty': certainty, 'causes': causes,
                'evidence': {
                    'git': git_hu,
                    'tracker': {'creates': [m['line'] for m in macros if m['action'] == 'create'],
                                'closes': [m['line'] for m in macros if m['action'] == 'close'],
                                'last': macros[-1]['action'] if macros else None},
                    # La observación anterior influye en la inferencia, pero no se copia aquí: el registro ya la
                    # conserva en previous_state y copiarla haría que cada registro cambiase el siguiente.
                    'sqlite': {'create': _event_view(macros, 'create'), 'close': _event_view(macros, 'close')},
                    'documents': _documents(context, hu)}}
    observation.update(summarize(observation, snapshot))
    return observation


def summarize(observation, snapshot):
    """Estado del proyecto: no_open_hu solo cuando Git y tracker son legibles y ninguna HU queda abierta o dudosa."""
    if not observation['git']['available']:
        return {'status': 'unknown', 'open': [], 'unresolved': [], 'certainty': 'low',
                'causes': ['git_' + observation['git']['cause']]}
    if not observation['tracker']['available']:
        return {'status': 'unknown', 'open': [], 'unresolved': [], 'certainty': 'low',
                'causes': [observation['tracker']['cause']]}
    hus = observation['hus']
    open_hu = sorted(hu for hu, data in hus.items() if data['observed_state'] in OPEN_STATES)
    unknown = sorted(hu for hu, data in hus.items() if data['observed_state'] == 'unknown')
    # Una rama desconocida sin integrar puede ser una HU abierta fuera del watcher.
    potential = open_hu + [hu for hu in unknown if 'integrated' not in hus[hu]['causes']
                           and hus[hu]['evidence']['git']['exists']]
    causes = []
    if snapshot['shared']:
        causes.append('shared_repository')
    if snapshot['invalid_branches']:
        causes.append('invalid_feature_branches')
    if observation['tracker']['invalid_macros']:
        causes.append('invalid_gitops_macros')
    attributed = any(data['evidence']['git']['merge_in_progress'] for data in hus.values())
    if snapshot['operations'] and not attributed:
        causes.append('git_operation_in_progress')
    if not observation['tracker']['store'] and hus:
        causes.append('no_state_store')
    reconcile = [hu for hu in open_hu if hus[hu]['observed_state'] == 'reconcile_required']
    if reconcile:
        status, certainty = 'reconcile_required', 'high'
    elif len(potential) > 1:
        status, certainty = 'reconcile_required', 'high'
        causes.append('multiple_open_hu')
    elif unknown or 'git_operation_in_progress' in causes:
        status, certainty = 'unknown', 'low'
    elif open_hu:
        status, certainty = 'one_open_hu', hus[open_hu[0]]['certainty']
    else:
        status, certainty = 'no_open_hu', 'high' if not causes else 'medium'
    return {'status': status, 'open': open_hu, 'unresolved': sorted(set(unknown) | set(reconcile)),
            'certainty': certainty, 'causes': causes}


# ------------------------------------------------------------------------------------------ Persistencia
def _summary_record(observation):
    return {key: observation[key] for key in ('project_id', 'mode', 'authoritative', 'status', 'open', 'unresolved',
                                              'certainty', 'causes', 'git', 'tracker')}


def _versioned(previous, data, state_key, reason, now):
    fingerprint = _digest(data, 64)
    if previous and previous.get('fingerprint') == fingerprint:
        return None
    changed = not previous or previous.get(state_key) != data[state_key]
    return {**data, 'fingerprint': fingerprint, 'observed_at': now, 'reason': reason,
            'changed_at': now if changed else previous.get('changed_at', now),
            'previous_state': (previous or {}).get(state_key) if changed else previous.get('previous_state')}


def record(store, observation, reason, now=None):
    """Guarda la observación con claves estables (`hu_lifecycle`, `hu_lifecycle:<hu>`); solo escribe lo que cambió.

    Repetir la misma observación (cada poll, cada reinicio) no añade ni reescribe registros. Devuelve cuántos
    registros escribió. Nunca toca event/queued/dispatch/tracker_append.
    """
    now = time.time() if now is None else now
    items = []
    for hu, data in observation['hus'].items():
        entry = _versioned(store.get(PREFIX + hu), data, 'observed_state', reason, now)
        if entry:
            items.append((PREFIX + hu, entry))
    summary = _versioned(store.get(SUMMARY), _summary_record(observation), 'status', reason, now)
    if summary:
        items.append((SUMMARY, summary))
    if items:
        store.put_many(items)
    return len(items)


def failed_observation(context, exc):
    return {'project_id': getattr(context, 'project_id', None), 'mode': 'observe', 'authoritative': False,
            'status': 'unknown', 'open': [], 'unresolved': [], 'certainty': 'low',
            'causes': [f'observation_failed:{type(exc).__name__}'], 'git': None, 'tracker': None, 'hus': {}}


def observe_runtime(rt, reason):
    """Hook del watcher: observa y registra en el SQLite del proyecto. Nunca lanza ni decide nada.

    Devuelve (observación, registros escritos), o None en modo off. Si la observación falla se registra
    `unknown` con su causa: un fallo jamás equivale a "sin HU abierta".
    """
    policy = rt.config.data.get('hu_lifecycle') or {'mode': 'observe'}
    if policy.get('mode') == 'off' or rt.state is None:      # enforce también observa y registra
        return None
    try:
        observation = observe(rt.context, rt.state)
    except Exception as exc:     # observación best-effort: el watcher sigue con su comportamiento actual
        observation = failed_observation(rt.context, exc)
    try:
        written = record(rt.state, observation, reason)
    except Exception:
        written = 0
    return observation, written


def shared_repositories(observations):
    """project_id -> otros proyectos observados con el mismo almacén de refs Git (sus ramas no son independientes)."""
    owners = {}
    for item in observations:
        repository = (item.get('git') or {}).get('repository')
        if repository:
            owners.setdefault(repository, []).append(item['project_id'])
    return {project: sorted(set(group) - {project}) for group in owners.values() if len(group) > 1 for project in group}


# ------------------------------------------------------------------------------------------------- CLI
def status(context, evidence=False):
    """Estado en vivo + último registro, abriendo el SQLite en solo lectura (no crea directorios, tablas ni locks)."""
    store = StateStore.open_readonly(context)
    try:
        live = observe(context, store)
        recorded = store.get(SUMMARY) if store else None
    finally:
        if store:
            store.close()
    hus = {hu: (data if evidence else {key: data[key] for key in ('observed_state', 'certainty', 'causes')})
           for hu, data in live['hus'].items()}
    return {'project_id': context.project_id, 'workspace': str(context.workspace_root),
            'status': live['status'], 'open': live['open'], 'unresolved': live['unresolved'],
            'certainty': live['certainty'], 'causes': live['causes'], 'authoritative': False,
            'git': live['git'], 'tracker': live['tracker'], 'hus': hus,
            'recorded': {key: recorded.get(key) for key in ('status', 'open', 'observed_at', 'changed_at', 'reason')}
            if recorded else None,
            'drift': bool(recorded) and (recorded.get('status'), recorded.get('open')) != (live['status'], live['open'])}


def main(argv=None):
    from .context import add_project_arguments, read_json, resolve_context
    parser = argparse.ArgumentParser(description='Ciclo de vida observado de las HU por proyecto (modo OBSERVE; '
                                                 'solo lectura: no escribe Git, tracker ni SQLite).')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Engine root.')
    add_project_arguments(parser)
    parser.add_argument('--status', action='store_true', required=True, help='Muestra el estado observado en vivo.')
    parser.add_argument('--all', action='store_true', help='Todos los proyectos registrados en config_bmad.json.')
    parser.add_argument('--evidence', action='store_true', help='Incluye la evidencia completa de cada HU.')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    if args.all:
        if args.workspace or args.project:
            parser.error('--all no admite --workspace/--project.')
        config = args.root.resolve() / 'config_bmad.json'
        registry = (read_json(config) if config.exists() else {}).get('projects', {})
        targets = [{'project': name} for name in sorted(registry)] if isinstance(registry, dict) else []
    else:
        targets = [{'workspace': args.workspace, 'project': args.project}]
    results = []
    for target in targets:
        try:
            results.append(status(resolve_context(args.root, **target), args.evidence))
        except Exception as exc:
            results.append({'project_id': target.get('project'), 'status': 'unknown', 'authoritative': False,
                            'causes': [f'observation_failed:{type(exc).__name__}'], 'error': str(exc)})
    shared = shared_repositories(results)
    for item in results:
        if item['project_id'] in shared:
            item['shared_repository_with'] = shared[item['project_id']]
    print(json.dumps(results if args.all else results[0], ensure_ascii=False, indent=2))
    return 1 if any('error' in item for item in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
