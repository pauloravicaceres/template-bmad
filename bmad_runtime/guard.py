"""Context budget, loop guard and progress ledger. Observes the watcher; it is not a second orchestrator.

Facts are `progress:` events in the workspace SQLite; verdicts are recomputed from them, so a restarted watcher
reaches the same result, and the current verdict per rule is kept in `guard_alert:<rule>:<agent>`. Metrics carry
their quality: measured (read by the runtime or reported by the provider), estimated (computed) or unavailable.
The guard never clears, rotates, retries, answers dialogs or interrupts an active operation; in `enforce` mode a
PAUSE or REQUIRES_INTERVENTION only holds new dispatches to the agents involved.
"""
import argparse
from datetime import datetime
import functools
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import time
import uuid

from .config import AGENT_PHASES
from .context import add_project_arguments, resolve_context
from .errors import BMADRuntimeError, ConfigurationError

LEVELS = ('NORMAL', 'WARNING', 'PAUSE', 'REQUIRES_INTERVENTION')
HOLDING = ('PAUSE', 'REQUIRES_INTERVENTION')   # levels that hold new dispatches in enforce mode
EVENT_KINDS = ('dispatched', 'work_started', 'artifacts_changed', 'handoff_confirmed', 'task_completed',
               'no_progress', 'recoverable_error', 'repeated_error', 'permission_blocked', 'delivery_uncertain',
               'clarification_requested', 'headless_run')
# Only verified artifact changes count as progress; an accepted delivery or a confirmed block does not.
PROGRESS = ('artifacts_changed', 'task_completed')
ERRORS = ('recoverable_error', 'repeated_error')
USAGE_METRICS = {'input_tokens': 'max_input_tokens', 'output_tokens': 'max_output_tokens', 'cost_usd': 'max_cost_usd'}
# Usage of a headless run with guard.headless_usage, normalized by the provider: input_tokens counts every prompt
# token, cached ones included; cached_input_tokens and cache_write_tokens are the cache share the CLI reports.
HEADLESS_METRICS = ('input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens', 'turns',
                    'cost_usd', 'context_window')
RULES = ('repeated_instruction', 'handoff_cycle', 'repeated_error', 'no_progress', 'repeated_clarification',
         'permission_blocked', 'delivery_uncertain', 'attempts', 'operation_duration', 'consecutive_operations',
         'operations_per_session', 'usage_limit')
ARTIFACT_MAX_BYTES = 16_777_216
# Characters per token of framework text (contracts, task files), measured against each CLI's structured usage:
# Claude 2.03-2.12, Codex 3.85 (Phase 4D.2). Providers never measured keep the generic 4. Still an estimate.
CHARS_PER_TOKEN = {'claude': 2.1, 'codex': 3.85}
EVALUATE_EVERY_S = 30
_NONE = {'', 'ninguno', 'ninguna', 'n/a', 'na', 'no', '-'}


def _observer(default=None):
    """Observation never stops the flow it observes: a failed record is reported, not raised."""
    def decorate(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                print(f'⚠️ [Guard] {method.__name__} no registrado: {type(exc).__name__}: {exc}')
                return default() if callable(default) else default
        return wrapper
    return decorate


def metric(value=None, quality='unavailable', source=None):
    """A metric never travels without its quality; unavailable values are None, never zero."""
    if quality not in ('measured', 'estimated', 'unavailable'):
        raise ValueError(quality)
    return {'value': None if quality == 'unavailable' else value, 'quality': quality, 'source': source}


def normalize(text):
    """Instruction/error text without volatile parts (times, dates, ids, terminal codes)."""
    text = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', ' ', str(text or '')).lower()
    text = re.sub(r'\[bmad[^\]]*\]', ' ', text)
    text = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\b|\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b|\b[0-9a-f]{12,64}\b', ' ', text)
    return ' '.join(text.split())


def estimate_tokens(chars, provider, what):
    ratio = CHARS_PER_TOKEN.get(provider, 4)
    return metric(math.ceil(chars / ratio), 'estimated', f'{what}_chars/{ratio:g}')


def signature(*parts):
    return hashlib.sha256('\x1f'.join(normalize(part) for part in parts).encode('utf-8')).hexdigest()[:16]


def _key(stamp):
    return f'progress:{int(stamp * 1e9):020d}'


def load_events(store, since=0.0):
    rows = store.db.execute("SELECT id,data FROM records WHERE id >= ? AND id < 'progress;' ORDER BY id",
                            (_key(max(since, 0)),))
    return [json.loads(data) for _, data in rows]


def _records(store, prefix):
    rows = store.db.execute('SELECT id,data FROM records WHERE id >= ? AND id < ?', (prefix, prefix[:-1] + ';'))
    return {key: json.loads(data) for key, data in rows}


def level_for(count, thresholds):
    for level, name in (('REQUIRES_INTERVENTION', 'intervention'), ('PAUSE', 'pause'), ('WARNING', 'warning')):
        if count >= thresholds[name]:
            return level
    return 'NORMAL'


def _cycle(sequence):
    """(pattern, repetitions) of the longest repeated tail cycle of 2 or 3 agents in a dispatch sequence."""
    best = ([], 0)
    for size in (2, 3):
        pattern = sequence[-size:]
        if len(pattern) < size or len(set(pattern)) < 2:
            continue
        count, end = 0, len(sequence)
        while end - size >= 0 and sequence[end - size:end] == pattern:
            count, end = count + 1, end - size
        if count > best[1]:
            best = (pattern, count)
    return best


RECOMMENDATIONS = {
    'repeated_instruction': 'Revisa el tracker y el panel: la misma instrucción vuelve sin avance verificable. '
                            'Corrige o reformula el handoff.',
    'handoff_cycle': 'Los handoffs circulan entre los mismos agentes sin cambios en artefactos. Revisa el último '
                     'dictamen y decide el siguiente paso manualmente.',
    'repeated_error': 'El mismo error se repite. Inspecciona los avisos del watcher y el panel; nada se reintenta '
                      'solo.',
    'no_progress': 'El agente termina turnos sin bloque o sin cambios en sus artefactos declarados. Revisa su panel.',
    'repeated_clarification': 'Se pide aclaración humana sobre el mismo asunto. Respóndela de forma explícita en el '
                              'tracker antes de continuar.',
    'permission_blocked': 'El agente espera un permiso o diálogo: respóndelo manualmente en su panel; nunca se '
                          'aprueba de forma automática.',
    'delivery_uncertain': 'La entrega pudo llegar al agente. Inspecciona el panel y reconcilia con '
                          'python -m bmad_runtime.state; nunca se reintenta automáticamente.',
    'attempts': 'Hubo más intentos de entrega de los permitidos. Reconcilia los anteriores antes de despachar.',
    'operation_duration': 'Operación activa más larga que su presupuesto. No se interrumpe; revisa el panel.',
    'consecutive_operations': 'Muchas operaciones seguidas al mismo agente. Revisa si el flujo avanza como se espera.',
    'usage_limit': 'Consumo medido por el proveedor por encima del presupuesto configurado.',
}
ACK = 'Tras revisarlo: python -m bmad_runtime.guard --acknowledge {rule}:{agent} --confirm.'


class Guard:
    def __init__(self, config, factory, state, *, clock=time.time):
        self.config, self.factory, self.state, self.clock = config, factory, state, clock
        self.settings = config.data['guard']
        self._marker, self._evaluated, self._last_event, self._recommended = None, 0.0, 0.0, 0.0
        # Usage limits only where the provider reports that metric; anything else would be invented.
        for agent in AGENT_PHASES:
            selection, provider = factory.resolve(agent=agent)
            budget = self.budget(agent, selection.provider)
            for name, limit in USAGE_METRICS.items():
                if budget[limit] is not None and name not in getattr(provider, 'measured_usage', frozenset()):
                    raise ConfigurationError(f'guard {limit} for {agent}: {selection.provider} does not report '
                                             f'{name}; leave it null.')

    @property
    def mode(self):
        return self.settings['mode']

    @property
    def enabled(self):
        return self.mode != 'off' and self.state is not None

    def budget(self, agent, provider=None):
        if provider is None:
            provider = self.factory.resolve(agent=agent)[0].provider
        return {**self.settings['budget'], **self.settings['providers'].get(provider, {}),
                **self.settings['agents'].get(agent, {})}

    # Ledger --------------------------------------------------------------------------------------
    @_observer()
    def event(self, kind, agent=None, **detail):
        if not self.enabled:
            return None
        if kind not in EVENT_KINDS:
            raise ValueError(f'Unknown progress event: {kind}')
        # Strictly increasing within the process: streaks and acknowledgements depend on event order.
        now = max(self.clock(), self._last_event + 1e-6)
        self._last_event = now
        data = {'state': 'done', 'kind': kind, 'agent': agent, 'time': now, **detail}
        self.state.put(f'{_key(now)}:{uuid.uuid4().hex[:6]}', data)
        return data

    @_observer()
    def error(self, agent, reason, **detail):
        """Recoverable error; the same signature seen again inside the window is recorded as repeated."""
        if not self.enabled:
            return None
        sig = signature(agent or '', reason)
        since = max(self.clock() - self.settings['window_seconds'], self._ack_time('repeated_error', agent))
        seen = any(e.get('signature') == sig for e in load_events(self.state, since) if e['kind'] in ERRORS)
        return self.event('repeated_error' if seen else 'recoverable_error', agent, signature=sig,
                          reason=str(reason)[:300], **detail)

    def _ack_time(self, rule, agent, store=None):
        return ((store or self.state).get(f'guard_ack:{rule}:{agent or "*"}') or {}).get('time', 0)

    @_observer()
    def on_dispatch(self, agent, message, event_id):
        """A task accepted by the agent (not completed). Sizes injected by the runtime are estimates."""
        if not self.enabled:
            return None
        dispatch = self.state.get('dispatch:' + event_id) or {}
        owned = self.state.get('agent:' + agent) or {}
        context = self.config.context
        injected = None
        if dispatch.get('task_file') and context is not None:
            try:
                injected = len(context.output(dispatch['task_file']).read_text(encoding='utf-8'))
            except (OSError, ConfigurationError):
                injected = None
        return self.event('dispatched', agent, event_id=event_id, instruction=signature(message),
                          attempt=dispatch.get('attempt', 1), provider=dispatch.get('provider'),
                          session={'run_id': owned.get('run_id'), 'generation': owned.get('generation', 1)},
                          metrics={'task_prompt_tokens': estimate_tokens(injected, dispatch.get('provider'), 'task_file')
                                   if injected else metric(source='task_file'),
                                   **self._usage_unavailable()})

    @staticmethod
    def _usage_unavailable():
        return {name: metric(source='provider') for name in USAGE_METRICS}

    @_observer()
    def on_dispatch_failure(self, agent, event_id, reason):
        record = (self.state.get('dispatch:' + event_id) or {}) if self.enabled else {}
        if record.get('state') not in (None, 'done', 'not_delivered'):
            return self.event('delivery_uncertain', agent, event_id=event_id, reason=str(reason)[:300])
        return self.error(agent, 'dispatch_failed:' + str(reason), event_id=event_id)

    @_observer()
    def on_confirmed(self, agent, event_id, summary, block_fields, started):
        """Confirmed block: progress only when declared artifacts changed during the task."""
        if not self.enabled:
            return None
        now = self.clock()
        verdict = self._artifacts(summary, started)
        duration = metric(round(now - started, 3), 'measured', 'runtime_clock') if started else metric(source='followup')
        progress = 'verified' if verdict['changed'] else ('unverifiable' if not verdict['declared'] else 'none')
        self.event('handoff_confirmed', agent, event_id=event_id, progress=progress, artifacts=verdict,
                   metrics={'duration_s': duration, **self._usage_unavailable()})
        if verdict['changed']:
            self.event('artifacts_changed', agent, event_id=event_id, paths=verdict['changed'])
            if not verdict['missing']:
                self.event('task_completed', agent, event_id=event_id, evidence='confirmed_block+artifacts_changed')
        elif verdict['declared']:
            self.event('no_progress', agent, event_id=event_id, reason='confirmed_without_artifact_change')
        handoff, issues = block_fields.get('handoff', ''), block_fields.get('puntos abiertos', '')
        if 'humano' in handoff.lower() and issues.strip(' .').lower() not in _NONE:
            self.event('clarification_requested', agent, event_id=event_id, subject=signature(issues))
        return progress

    def _artifacts(self, summary, started):
        declared = [item.get('path', '') for item in (summary or {}).get('artifacts') or []]
        result = {'declared': declared, 'changed': [], 'unchanged': [], 'missing': []}
        context = self.config.context
        seen = self.state.get('guard_artifacts') or {}
        for path in declared:
            try:
                target = context.output(path)
                info = target.stat() if target.is_file() else None
            except (OSError, ConfigurationError):
                info = None
            if info is None:
                result['missing'].append(path)
                continue
            digest = (hashlib.sha256(target.read_bytes()).hexdigest()[:32] if info.st_size <= ARTIFACT_MAX_BYTES
                      else f'size:{info.st_size}:{info.st_mtime_ns}')
            # Written during this task (mtime) and different from the last confirmed version (content).
            fresh = started is None or info.st_mtime >= started - 2
            result['changed' if fresh and seen.get(path) != digest else 'unchanged'].append(path)
            seen[path] = digest
        if declared:
            self.state.put('guard_artifacts', dict(list(seen.items())[-500:]))
        return result

    @_observer()
    def on_headless(self, operation, run_key, status):
        """SpecKit run: duration measured by the runtime; usage only from the CLI's structured result
        (guard.headless_usage), otherwise unavailable."""
        if not self.enabled:
            return None
        record = self.state.get(run_key) or {}
        duration = record.get('duration_ms')
        agent = 'speckit.' + operation
        usage = record.get('usage') if isinstance(record.get('usage'), dict) else {}
        self.event('headless_run', agent, run=run_key, status=status, provider=record.get('provider'),
                   metrics={'duration_s': metric(duration / 1000, 'measured', 'runtime_clock')
                            if isinstance(duration, (int, float)) else metric(source='runner'),
                            **self._usage_unavailable(), **usage})
        if status != 'success':
            self.error(agent, 'headless:' + str(status), run=run_key)

    # Evaluation ----------------------------------------------------------------------------------
    def evaluate(self, store=None, now=None, *, history=None, budgets=True):
        """Findings above NORMAL, recomputed from SQLite only (no Herdr, no files).

        `history` and budgets=False replay the loop rules at a past instant (calibration): budget rules read the
        current followup and session records, so they cannot be replayed.
        """
        store = store or self.state
        now = self.clock() if now is None else now
        loop = self.settings['loop']
        window = now - self.settings['window_seconds']
        history = load_events(store, 0) if history is None else history
        recent = [e for e in history if window <= e['time'] <= now]
        # Only reviews already made at `now` count (equal to every review in a live evaluation).
        acks = {key[len('guard_ack:'):]: data.get('time', 0) for key, data in _records(store, 'guard_ack:').items()
                if data.get('time', 0) <= now}
        ack = lambda rule, agent: acks.get(f'{rule}:{agent or "*"}', 0)
        findings = []

        def add(rule, agent, count, thresholds, summary, **evidence):
            level = level_for(count, thresholds)
            if level != 'NORMAL':
                findings.append({'rule': rule, 'agent': agent, 'level': level,
                                 'evidence': {'summary': summary, 'count': count, **evidence}})

        last_progress = {}
        for e in recent:
            if e['kind'] in PROGRESS:
                last_progress[e['agent']] = e['time']
        agents = sorted({e['agent'] for e in recent if e.get('agent')})
        for agent in agents:
            mine = [e for e in recent if e.get('agent') == agent]
            # Identical instruction to the same agent with no verified progress in between.
            since = max(ack('repeated_instruction', agent), last_progress.get(agent, 0))
            groups = {}
            for e in mine:
                if e['kind'] == 'dispatched' and e['time'] > since:
                    groups.setdefault(e['instruction'], []).append(e.get('event_id'))
            if groups:
                sig, ids = max(groups.items(), key=lambda item: len(item[1]))
                add('repeated_instruction', agent, len(ids), loop['repeated_instruction'],
                    f'{len(ids)} despachos con la misma instrucción sin avance verificable', instruction=sig,
                    events=[i[:12] for i in ids if i][-5:])
            groups = {}
            for e in mine:
                if e['kind'] in ERRORS and e['time'] > ack('repeated_error', agent):
                    groups.setdefault(e['signature'], []).append(e.get('reason'))
            if groups:
                sig, reasons = max(groups.items(), key=lambda item: len(item[1]))
                add('repeated_error', agent, len(reasons), loop['repeated_error'],
                    f'{len(reasons)} errores equivalentes: {reasons[-1]}', signature=sig)
            streak = 0
            for e in mine:
                if e['time'] <= ack('no_progress', agent):
                    continue
                if e['kind'] in PROGRESS:
                    streak = 0
                elif e['kind'] == 'no_progress':
                    streak += 1
            add('no_progress', agent, streak, loop['no_progress'],
                f'{streak} turnos o entregas seguidas sin avance verificable')
            groups = {}
            for e in mine:
                if e['kind'] == 'clarification_requested' and e['time'] > ack('repeated_clarification', agent):
                    groups.setdefault(e['subject'], []).append(e.get('event_id'))
            if groups:
                sig, ids = max(groups.items(), key=lambda item: len(item[1]))
                add('repeated_clarification', agent, len(ids), loop['repeated_clarification'],
                    f'{len(ids)} solicitudes de aclaración sobre el mismo asunto', subject=sig)
            blocked = [e for e in mine if e['kind'] == 'permission_blocked' and e['time'] > ack('permission_blocked', agent)]
            add('permission_blocked', agent, len(blocked), {'warning': 1, 'pause': 10 ** 9, 'intervention': 3},
                f'{len(blocked)} bloqueos por permisos o diálogos', reasons=[e.get('reason') for e in blocked][-3:])
            uncertain = [e for e in mine if e['kind'] == 'delivery_uncertain' and e['time'] > ack('delivery_uncertain', agent)]
            add('delivery_uncertain', agent, len(uncertain), {'warning': 1, 'pause': 1, 'intervention': 1},
                'entrega incierta: no se reintenta', events=[(e.get('event_id') or '')[:12] for e in uncertain][-3:])
            if budgets and agent in AGENT_PHASES:
                findings += self._budget_findings(agent, mine, history, store, now, ack)
        # Cycles are workspace-wide: count repetitions after the last verified progress of any agent.
        since = max([ack('handoff_cycle', None), *last_progress.values()])
        sequence = [e['agent'] for e in recent if e['kind'] == 'dispatched' and e['time'] > since]
        pattern, repetitions = _cycle(sequence)
        if pattern:
            add('handoff_cycle', '*', repetitions, loop['handoff_cycle'],
                f'{repetitions} ciclos {" -> ".join(pattern)} sin cambios en artefactos', agents=sorted(set(pattern)))
        for finding in findings:
            finding['recommendation'] = self._recommend(finding)
        return findings

    def _budget_findings(self, agent, mine, history, store, now, ack):
        budget, findings = self.budget(agent), []
        dispatched = [e for e in mine if e['kind'] == 'dispatched']
        if dispatched and dispatched[-1].get('attempt', 1) > budget['max_attempts'] and \
                dispatched[-1]['time'] > ack('attempts', agent):
            findings.append({'rule': 'attempts', 'agent': agent, 'level': 'PAUSE', 'evidence': {
                'summary': f'intento {dispatched[-1]["attempt"]} de entrega (máximo {budget["max_attempts"]})',
                'attempt': metric(dispatched[-1]['attempt'], 'measured', 'dispatch_record')}})
        follow = (store.get('followup') or {}).get(agent) or {}
        started = follow.get('inicio', follow.get('despachado'))
        if isinstance(started, (int, float)) and now - started > budget['max_operation_seconds']:
            findings.append({'rule': 'operation_duration', 'agent': agent, 'level': 'WARNING', 'evidence': {
                'summary': f'operación activa desde hace {int(now - started)} s (presupuesto '
                           f'{budget["max_operation_seconds"]} s); no se interrumpe',
                'duration_s': metric(round(now - started, 1), 'measured', 'runtime_clock')}})
        all_dispatched = [e for e in history if e['kind'] == 'dispatched']
        tail = 0
        for e in reversed(all_dispatched):
            if e['agent'] != agent or e['time'] <= ack('consecutive_operations', agent):
                break
            tail += 1
        if tail >= budget['max_consecutive_operations']:
            findings.append({'rule': 'consecutive_operations', 'agent': agent, 'level': 'WARNING', 'evidence': {
                'summary': f'{tail} despachos consecutivos al mismo agente', 'count': tail}})
        owned = store.get('agent:' + agent) or {}
        session = {'run_id': owned.get('run_id'), 'generation': owned.get('generation', 1)}
        operations = sum(1 for e in all_dispatched if e['agent'] == agent and e.get('session') == session)
        if owned.get('run_id') and operations >= budget['max_operations_per_session']:
            findings.append({'rule': 'operations_per_session', 'agent': agent, 'level': 'WARNING', 'evidence': {
                'summary': f'{operations} tareas en la sesión actual (generación {session["generation"]}); '
                           f'presupuesto {budget["max_operations_per_session"]}',
                'count': operations, 'session': session}})
        for e in mine:
            for name, limit in USAGE_METRICS.items():
                value = (e.get('metrics') or {}).get(name) or {}
                if value.get('quality') == 'measured' and budget[limit] is not None and \
                        value['value'] > budget[limit] and e['time'] > ack('usage_limit', agent):
                    findings.append({'rule': 'usage_limit', 'agent': agent, 'level': 'WARNING', 'evidence': {
                        'summary': f'{name} medido {value["value"]} > {budget[limit]}', name: value}})
        return findings

    def _recommend(self, finding):
        rule, agent = finding['rule'], finding['agent']
        if rule == 'operations_per_session':
            from .services import clear_supported
            _, provider = self.factory.resolve(agent=agent)
            action = 'CLEAR' if clear_supported(provider) else 'ROTATE'
            source = getattr(self.config, 'source', None)
            override = f' --config "{source}"' if source else ''
            return (f'Contexto acumulado: revisa python -m bmad_runtime.maintenance --plan-clear{override} y, si {agent} es '
                    f'ELIGIBLE, aplica {action} manual con --confirm (guard --status muestra el comando exacto). '
                    'Nada se limpia ni rota automáticamente.')
        text = RECOMMENDATIONS[rule]
        if finding['level'] in ('PAUSE', 'REQUIRES_INTERVENTION') and rule in (
                'repeated_instruction', 'no_progress', 'handoff_cycle'):
            text += (' Si el contexto del agente está degradado, consulta maintenance --plan-clear y aplica '
                     'CLEAR/ROTATE manual.')
        return text + ' ' + ACK.format(rule=rule, agent=agent)

    @_observer(list)
    def tick(self, force=False):
        """Re-evaluate when new events exist (or every EVALUATE_EVERY_S); returns alerts whose level rose."""
        if not self.enabled:
            return []
        now = self.clock()
        row = self.state.db.execute("SELECT MAX(id) FROM records WHERE id >= 'progress:' AND id < 'progress;'").fetchone()
        if not force and row[0] == self._marker and now - self._evaluated < EVALUATE_EVERY_S:
            return []
        self._marker, self._evaluated = row[0], now
        cutoff = now - self.settings['retention_days'] * 86400
        with self.state.db:
            self.state.db.execute("DELETE FROM records WHERE id >= 'progress:' AND id < ?", (_key(cutoff),))
        return self._persist(self.evaluate(now=now), now)

    @_observer(list)
    def announce_recommendations(self, sessions, force=False):
        """New recommendations for the watcher to print; persisted so a restart never repeats them. Never acts."""
        if not self.enabled:
            return []
        now = self.clock()
        if not force and now - self._recommended < EVALUATE_EVERY_S:
            return []
        self._recommended = now
        found = [entry for entry in recommendations(self, sessions, self.state).values()
                 if entry['status'] == 'recommended']
        new, updates = [], []
        for entry in found:
            key = 'guard_recommendation:' + entry['agent']
            previous = self.state.get(key) or {}
            if previous.get('key') == entry['key'] and previous.get('step', 0) >= entry['step']:
                continue   # same session, cause and evidence: already announced
            record = {**entry, 'state': 'done', 'announced': now, 'mode': self.mode}
            updates.append((key, record))
            new.append(record)
        if updates:
            self.state.put_many(updates)
            self._log_recommendations(new)
        return new

    def _log_recommendations(self, entries):
        context = self.config.context
        try:
            path = context.output('logs/guard.log')
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8', newline='\n') as handle:
                for entry in entries:
                    handle.write(json.dumps({'at': entry['announced'], 'project_id': context.project_id,
                                             'type': 'recommendation', 'text': describe_recommendation(entry),
                                             **entry}, ensure_ascii=False) + '\n')
        except (OSError, ConfigurationError) as exc:
            print(f'⚠️ [Guard] logs/guard.log no actualizado: {exc}')

    def _persist(self, findings, now):
        current = _records(self.state, 'guard_alert:')
        raised, updates = [], []
        for finding in findings:
            key = f'guard_alert:{finding["rule"]}:{finding["agent"]}'
            previous = current.pop(key, None)
            active = previous and previous.get('state') == 'open'
            # Records written by earlier versions (or edited by hand) may miss fields: never fail on them.
            before = previous.get('level') if active and previous.get('level') in LEVELS else 'NORMAL'
            alert = {**finding, 'state': 'open', 'mode': self.mode, 'updated': now,
                     'first_seen': previous.get('first_seen', now) if active else now,
                     'agents': finding['evidence'].get('agents') or [finding['agent']]}
            if not active or LEVELS.index(finding['level']) > LEVELS.index(before):
                raised.append(alert)
            # The mode can change across a restart (observe -> enforce): the stored alert must tell the truth.
            if not active or (previous.get('level'), previous.get('evidence'), previous.get('mode')) != \
                    (alert['level'], alert['evidence'], alert['mode']):
                updates.append((key, alert))
        for key, previous in current.items():
            if previous.get('state') == 'open':
                updates.append((key, {**previous, 'state': 'done', 'resolved': now,
                                      'resolution': previous.get('resolution') or 'condition_cleared'}))
        if updates:
            self.state.put_many(updates)
        self._log(raised)
        return raised

    def _log(self, alerts):
        # Operator-facing trail; the tracker is never used for alerts.
        context = self.config.context
        if not alerts or context is None:
            return
        try:
            path = context.output('logs/guard.log')
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8', newline='\n') as handle:
                for alert in alerts:
                    handle.write(json.dumps({'at': alert['updated'], 'project_id': context.project_id,
                                             'text': describe(alert), **alert}, ensure_ascii=False) + '\n')
        except (OSError, ConfigurationError) as exc:
            # SQLite keeps the alert; only the text trail is missing.
            print(f'⚠️ [Guard] logs/guard.log no actualizado: {exc}')

    def hold(self, agent):
        """Open PAUSE/REQUIRES_INTERVENTION alert that holds new dispatches to `agent` (enforce mode only)."""
        if not self.enabled or self.mode != 'enforce':
            return None
        for alert in _records(self.state, 'guard_alert:').values():
            if alert.get('state') == 'open' and alert.get('level') in HOLDING and agent in alert.get('agents', []):
                # The watcher checks holds before its first tick after a restart: the stored mode may be stale.
                return {**alert, 'mode': self.mode}
        return None

    def acknowledge(self, rule, agent):
        """Operator reviewed the evidence: earlier events stop counting for this rule; nothing is retried."""
        if rule not in RULES:
            raise ConfigurationError(f'Unknown guard rule: {rule}')
        now = max(self.clock(), self._last_event + 1e-6)
        self._last_event = now
        key = f'guard_alert:{rule}:{agent}'
        alert = self.state.get(key)
        updates = [(f'guard_ack:{rule}:{agent}', {'state': 'done', 'time': now, 'by': 'operator'})]
        if alert and alert.get('state') == 'open':
            updates.append((key, {**alert, 'state': 'done', 'resolved': now, 'resolution': 'acknowledged'}))
        self.state.put_many(updates)
        return alert


def mode_effect(alert, mode=None):
    """What the alert does under `mode` (default: the mode stored with it)."""
    mode = mode or alert.get('mode')
    if mode == 'enforce' and alert.get('level') in HOLDING:
        return 'modo enforce: nuevos despachos retenidos para ' + ', '.join(alert.get('agents') or [alert['agent']])
    if mode == 'enforce':
        return 'modo enforce: aviso, no retiene despachos'
    if mode == 'observe':
        return 'modo observación: no se retiene ningún despacho'
    return 'guard desactivado'


def describe(alert):
    return (f"[Guard {alert['level']}] {alert['rule']} · {alert['agent']}: {alert['evidence']['summary']} "
            f"({mode_effect(alert)}). {alert['recommendation']}")


def availability(provider, headless_usage=False):
    """Interactive metrics (top level) and Spec Kit headless metrics ('headless') with their quality."""
    measured = getattr(provider, 'measured_usage', frozenset())
    reported = getattr(provider, 'headless_usage', frozenset())

    def headless(name):
        if name not in reported:
            return 'unavailable'
        quality = 'estimated (precio de lista del CLI; no es facturación)' if name == 'cost_usd' else 'measured'
        return quality if headless_usage else 'unavailable (activable con guard.headless_usage)'
    return {'duration_s': 'measured (runtime_clock)', 'attempts': 'measured (dispatch_record)',
            'task_prompt_tokens': f"estimated (task_file_chars/{CHARS_PER_TOKEN.get(provider.identifier, 4):g}; no es consumo)",
            **{name: 'measured' if name in measured else 'unavailable' for name in USAGE_METRICS},
            'headless': {'duration_s': 'measured (runtime_clock)', **{name: headless(name) for name in HEADLESS_METRICS}}}


def report(runtime, store, now=None):
    guard = Guard(runtime.config, runtime.factory, None)
    providers, budgets = {}, {}
    for agent in AGENT_PHASES:
        selection, provider = runtime.factory.resolve(agent=agent)
        providers.setdefault(selection.provider, availability(provider, guard.settings['headless_usage']))
        if store is None or store.get('agent:' + agent):
            budgets[agent] = guard.budget(agent, selection.provider)
    findings = guard.evaluate(store, time.time() if now is None else now) if store else []
    alerts = [alert for alert in _records(store, 'guard_alert:').values() if alert.get('state') == 'open'] if store else []
    return {'mode': guard.mode, 'project_id': runtime.context.project_id, 'workspace': str(runtime.context.workspace_root),
            'metrics_by_provider': providers, 'findings': findings, 'open_alerts': alerts, 'budgets': budgets}


def _iso(stamp):
    try:
        return datetime.fromtimestamp(stamp).astimezone().isoformat(timespec='seconds') if stamp else None
    except (OSError, OverflowError, ValueError, TypeError):
        # A diagnosis never fails on a malformed timestamp (Windows rejects some ranges).
        return None


def _total(values, name, quality):
    """Sum of one metric over events, only for values of that quality; unavailable when there are none."""
    found = [item[name]['value'] for item in values
             if (item.get(name) or {}).get('quality') == quality and isinstance(item[name].get('value'), (int, float))]
    return metric(round(sum(found), 3), quality, f'{len(found)} eventos') if found else metric(source='ledger')


def _metrics_of(events, kind):
    return [e.get('metrics') or {} for e in events if e['kind'] == kind]


def session_work(history, name, owned):
    """(session, event ids dispatched to it, its events). A dispatch belongs to the session (launch + generation)
    that received it; CLEAR/ROTATE or a new launch starts another one."""
    session = {'run_id': owned.get('run_id'), 'generation': owned.get('generation', 1)}
    current = {e.get('event_id') for e in history
               if e.get('agent') == name and e['kind'] == 'dispatched' and e.get('session') == session}
    return session, current, [e for e in history if e.get('agent') == name and e.get('event_id') in current]


RECOMMENDATION_CAUSE = 'operations_per_session'
# Every condition is already part of ELIGIBLE in the plan; the grouping only explains which one failed.
CONDITIONS = (('no_pending_or_uncertain_handoffs', ('pending_tasks', 'uncertain_dispatch', 'unconfirmed_tasks',
                                                    'last_handoff_', 'handoff_', 'followup_active', 'headless_',
                                                    'no_handoff')),
              ('tracker_integrity', ('tracker_', 'protocol_violation')),
              ('no_maintenance_in_progress', ('maintenance_pending',)),
              ('not_refreshed_since_last_task', ('session_already_fresh',)),
              ('owned_idle_agent', ('not_owned_or_not_ready', 'awaiting_trust', 'herdr_')),
              ('session_summary', ('summary_',)))


def _checks(reasons):
    checks = {name: [] for name, _ in CONDITIONS}
    checks['other'] = []
    for reason in reasons:
        if reason == 'all_checks_passed':
            continue
        group = next((name for name, prefixes in CONDITIONS if reason.startswith(prefixes)), 'other')
        checks[group].append(reason)
    return {name: found or 'ok' for name, found in checks.items() if found or name != 'other'}


def maintenance_command(context, *args, config=None):
    """Exact command for a human to review and run from the engine root; never run by the runtime.

    `config` is the explicit --config file the recommending process was started with: the command keeps it (absolute
    path) so maintenance plans with the same thresholds and providers. None keeps the engine default config_bmad.json.
    """
    scope = [] if context.legacy else ['--workspace', f'"{context.workspace_root}"', '--project', context.project_id]
    override = ['--config', f'"{config}"'] if config else []
    return ' '.join([f'"{sys.executable}"', '-B', '-m', 'bmad_runtime.maintenance', *args, *scope, *override])


def recommendations(guard, sessions, store, *, names=None, plan=None, history=None):
    """Per owned agent: whether CLEAR/ROTATE is recommended now. Read-only; the operator decides and runs it.

    Recommended only when the tasks of the current session reach max_operations_per_session and the agent is
    ELIGIBLE in the same plan as maintenance --plan-clear (no pending or uncertain handoff, tracker verified, no
    maintenance in progress, owned idle agent, complete summary). Token usage is never a trigger: interactive
    sessions do not report it.
    """
    context, config = guard.config.context, getattr(guard.config, 'source', None)
    history = load_events(store) if history is None else history
    names = names or [name for name in AGENT_PHASES if store.get('agent:' + name)]
    entries = {}
    for name in names:
        owned = store.get('agent:' + name) or {}
        selection, _ = guard.factory.resolve(agent=name)
        session, current, work = session_work(history, name, owned)
        threshold = guard.budget(name, selection.provider)['max_operations_per_session']
        entry = {'agent': name, 'provider': selection.provider, 'model': selection.model,
                 'generation': session['generation'], 'run_id': session['run_id'], 'cause': RECOMMENDATION_CAUSE,
                 'operations': len(current), 'threshold': threshold}
        entries[name] = entry
        if not owned.get('run_id') or len(current) < threshold:
            entry['status'] = 'below_threshold'
            continue
        if plan is None:
            plan = {row['agent']: row for row in sessions.plan(store, names=names)}
        row = plan.get(name) or {'eligibility': 'NOT_ELIGIBLE', 'reasons': ['not_planned']}
        entry['checks'] = _checks(row.get('reasons') or [])
        if row.get('eligibility') != 'ELIGIBLE' or row.get('proposed_action') not in ('CLEAR', 'ROTATE'):
            entry.update(status='blocked', reasons=row.get('reasons'))
            continue
        operation = row['proposed_action']
        confirmed = [e for e in work if e['kind'] == 'handoff_confirmed']
        entry.update(
            status='recommended', operation=operation,
            # New evidence = a new session, or another full budget of tasks in the same one.
            key=f"{session['run_id']}:{session['generation']}:{RECOMMENDATION_CAUSE}", step=len(current) // threshold,
            reason=f"{len(current)} tareas en la generación {session['generation']} de la sesión (umbral {threshold}); "
                   f"agente ELIGIBLE para {operation}",
            evidence={'tasks_dispatched': len(current), 'tasks_confirmed': len(confirmed),
                      'verified_progress': sum(1 for e in confirmed if e.get('progress') == 'verified'),
                      'no_progress_events': sum(1 for e in work if e['kind'] == 'no_progress'),
                      'last_confirmed_task': row.get('last_confirmed_task'), 'herdr_status': row.get('herdr_status'),
                      'duration_s': _total(_metrics_of(confirmed, 'handoff_confirmed'), 'duration_s', 'measured'),
                      'task_prompt_tokens': _total(_metrics_of(work, 'dispatched'), 'task_prompt_tokens', 'estimated'),
                      **{usage: metric(source='provider') for usage in USAGE_METRICS}},
            commands={'cwd': str(context.engine_root), 'config': config and str(config),
                      'review': maintenance_command(context, '--plan-clear', config=config),
                      'apply': maintenance_command(context, '--' + operation.lower(), name, '--confirm', config=config)})
    return entries


def _with_announcement(entry, previous, config=None):
    if entry.get('status') == 'recommended':
        repeated = bool(previous) and previous.get('key') == entry['key'] and previous.get('step', 0) >= entry['step']
        entry = {**entry, 'announced_at': _iso(previous.get('announced')) if repeated else None}
    # The watcher announced with its own --config: a report built from another file (other threshold or providers)
    # must say so, whatever status it computed. Records from earlier versions do not name their file: no warning.
    commands = (previous or {}).get('commands') or {}
    current = str(config) if config else None
    if 'config' in commands and commands['config'] != current:
        entry = {**entry, 'config_warning': (
            f"La última recomendación del watcher usó la configuración {commands['config'] or 'predeterminada'}; "
            f"este informe usa {current or 'la predeterminada'} (umbral y proveedores pueden diferir). "
            "Usa el mismo --config que el watcher.")}
    return entry


def describe_recommendation(entry):
    return (f"[Guard RECOMENDACIÓN] {entry['operation']} {entry['agent']} ({entry['provider']}): {entry['reason']}. "
            f"No se ejecuta automáticamente. Revisa: {entry['commands']['review']} ; si procede, desde "
            f"{entry['commands']['cwd']}: {entry['commands']['apply']}")


def status(runtime, store, now=None, names=None):
    """Read-only diagnosis per agent: session, work since the last maintenance, metrics with their quality, alerts,
    holds and CLEAR/ROTATE eligibility. Reads SQLite and `herdr agent list` (via the plan); writes nothing."""
    from .services import contract_path
    from .watcher_service import HOLD_STATES, maintenance_blocks, maintenance_records, watcher_participation
    now = time.time() if now is None else now
    guard = Guard(runtime.config, runtime.factory, None)
    history = load_events(store)
    # Records from earlier versions may miss fields: the key still names the rule and the agent.
    alerts = [{'level': 'NORMAL', **a, 'rule': a.get('rule') or key.split(':')[1],
               'agent': a.get('agent') or key.split(':', 2)[2], 'evidence': a.get('evidence') or {}}
              for key, a in _records(store, 'guard_alert:').items() if a.get('state') == 'open']
    watcher = watcher_participation(store, now) or 'active'

    def mode_of(alert):
        # A running watcher may use another --config: the mode it enforces is the one it stored on the alert.
        return alert['mode'] if watcher == 'active' and alert.get('mode') in ('observe', 'enforce') else guard.mode
    operations = sorted(maintenance_records(store), key=lambda op: (op.get('states') or {}).get('REQUESTED', 0))
    blocked = maintenance_blocks(store)
    followup = store.get('followup') or {}
    names = names or [name for name in AGENT_PHASES if store.get('agent:' + name)]
    # Eligibility comes from the same plan as maintenance --plan-clear: one source of truth.
    plan = {row['agent']: row for row in runtime.sessions.plan(store, names=names)} if names else {}
    advice = recommendations(guard, runtime.sessions, store, names=names, plan=plan, history=history) if names else {}
    agents = []
    for name in names:
        selection, _ = runtime.factory.resolve(agent=name)
        owned = store.get('agent:' + name) or {}
        session, current, work = session_work(history, name, owned)
        confirmed = [e for e in work if e['kind'] == 'handoff_confirmed']
        follow = followup.get(name) or {}
        started = follow.get('inicio', follow.get('despachado'))
        mine_alerts = [a for a in alerts if name in (a.get('agents') or [a.get('agent')])]
        ops = [op for op in operations if op.get('agent') == name]
        holds = [{'source': 'guard', 'rule': a['rule'], 'level': a['level'], 'reason': a['evidence'].get('summary'),
                  'holds_dispatch': mode_of(a) == 'enforce', 'effect': mode_effect(a, mode_of(a)),
                  'release': ACK.format(rule=a['rule'], agent=a['agent'])}
                 for a in mine_alerts if a.get('level') in HOLDING]
        if name in blocked:
            op = next(op for op in ops if op['op_id'] == blocked[name])
            holds.append({'source': 'maintenance', 'op_id': op['op_id'][:12], 'kind': op.get('kind'),
                          'level': 'REQUIRES_INTERVENTION', 'state': op.get('state'), 'holds_dispatch': True,
                          'reason': ((op.get('errors') or [{}])[-1].get('error') or 'operación sin estado final'),
                          'release': f'python -m bmad_runtime.maintenance --reconcile {name} --confirm'})
        if owned.get('state') in HOLD_STATES:
            holds.append({'source': 'agent_state', 'state': owned['state'], 'holds_dispatch': True,
                          'reason': owned.get('blocker') or owned['state'],
                          'release': f'python -m bmad_runtime.maintenance --reconcile {name} --confirm'})
        try:
            contract = len(contract_path(runtime.context, name).read_text(encoding='utf-8'))
        except OSError:
            contract = None
        last_op = ops[-1] if ops else None
        row = plan.get(name) or {}
        agents.append({
            'agent': name, 'provider': selection.provider, 'model': selection.model,
            'record_state': owned.get('state'),
            'session': {**session, 'session_name': owned.get('session_name'),
                        'refreshed_at': owned.get('session_refreshed_at'), 'verified_at': owned.get('verified_at')},
            'last_maintenance': last_op and {'op_id': last_op['op_id'][:12], 'kind': last_op.get('kind'),
                                             'state': last_op.get('state'), 'result': last_op.get('result'),
                                             'resolution': last_op.get('resolution')},
            'since_last_maintenance': {
                'tasks_dispatched': len(current), 'tasks_confirmed': len(confirmed),
                'verified_progress': sum(1 for e in confirmed if e.get('progress') == 'verified'),
                'no_progress_events': sum(1 for e in work if e['kind'] == 'no_progress'),
                'errors': sum(1 for e in work if e['kind'] in ERRORS),
                'budget': guard.budget(name, selection.provider)['max_operations_per_session']},
            'duration': {'accumulated_s': _total(_metrics_of(confirmed, 'handoff_confirmed'), 'duration_s', 'measured'),
                         'active_operation_s': metric(round(now - started, 1), 'measured', 'runtime_clock')
                         if isinstance(started, (int, float)) else metric(source='followup')},
            'metrics': {'task_prompt_tokens': _total(_metrics_of(work, 'dispatched'), 'task_prompt_tokens', 'estimated'),
                        'contract_chars': metric(contract, 'measured', 'state/contracts') if contract
                        else metric(source='state/contracts'),
                        'contract_tokens': estimate_tokens(contract, selection.provider, 'contract')
                        if contract else metric(source='state/contracts'),
                        **{usage: metric(source='provider') for usage in USAGE_METRICS}},
            'alerts': [{'rule': a['rule'], 'level': a['level'], 'summary': a['evidence'].get('summary'),
                        'first_seen': _iso(a.get('first_seen')), 'stored_mode': a.get('mode'),
                        'effect': mode_effect(a, mode_of(a))} for a in mine_alerts],
            'holds': holds,
            'eligibility': {key: row.get(key) for key in ('eligibility', 'proposed_action', 'reasons', 'herdr_status')},
            'recommendation': _with_announcement(advice[name], store.get('guard_recommendation:' + name),
                                                 getattr(runtime.config, 'source', None)),
        })
    runs = [e for e in history if e['kind'] == 'headless_run'][-10:]
    return {'mode': guard.mode, 'read_only': True, 'project_id': runtime.context.project_id,
            'workspace': str(runtime.context.workspace_root), 'generated_at': _iso(now),
            'headless_usage': guard.settings['headless_usage'],
            # A stopped watcher leaves its last followups behind: their active time is then stale.
            'watcher': watcher, 'watcher_modes': sorted({mode_of(a) for a in alerts}) if watcher == 'active' else [],
            'agents': agents,
            'workspace_alerts': [{'rule': a['rule'], 'agent': a['agent'], 'level': a['level'],
                                  'summary': a['evidence'].get('summary'), 'effect': mode_effect(a, mode_of(a))}
                                 for a in alerts if not set(a.get('agents') or [a.get('agent')]) & set(names)],
            'headless_runs': [{'operation': e['agent'], 'status': e.get('status'), 'provider': e.get('provider'),
                               'at': _iso(e['time']),
                               'metrics': {k: {'value': v.get('value'), 'quality': v.get('quality')}
                                           for k, v in (e.get('metrics') or {}).items()}} for e in runs]}


# Calibration: a provider-specific threshold is proposed only above these sample sizes.
MIN_DISPATCHES = 30
MIN_EPISODES = 5
REPLAY_LIMIT = 2000


def _episodes(guard, store, history):
    """Replay the loop rules after every ledger event: (rule, agent) alert episodes and how each one ended."""
    acks = [(key[len('guard_ack:'):], data.get('time', 0)) for key, data in _records(store, 'guard_ack:').items()]
    providers, active, done = {}, {}, []
    for index, event in enumerate(history):
        if event['kind'] == 'dispatched' and event.get('provider'):
            providers[event['agent']] = event['provider']
        found = {(f['rule'], f['agent']): f for f in
                 guard.evaluate(store, event['time'], history=history[:index + 1], budgets=False)}
        for key, finding in found.items():
            episode = active.setdefault(key, {'rule': key[0], 'agent': key[1], 'start': event['time'],
                                              'peak': 'NORMAL', 'provider': providers.get(key[1])})
            if LEVELS.index(finding['level']) > LEVELS.index(episode['peak']):
                episode['peak'] = finding['level']
            episode['last'] = event['time']
        for key in [key for key in active if key not in found]:
            episode = active.pop(key)
            reviewed = any(rule == f'{key[0]}:{key[1] or "*"}' and episode['last'] <= stamp <= event['time']
                           for rule, stamp in acks)
            episode['ended_by'] = ('acknowledged' if reviewed else 'progress' if event['kind'] in PROGRESS
                                   else 'other:' + event['kind'])
            episode['seconds'] = round(event['time'] - episode['start'], 1)
            done.append(episode)
    for episode in active.values():
        done.append({**episode, 'ended_by': 'open', 'seconds': None})
    return done, providers


def calibrate(runtime, store):
    """Read-only replay of the ledger in observe semantics: alert frequency, self-resolved PAUSE (would have held a
    dispatch in enforce), legitimate repetitions, cycles, errors and recovery after CLEAR/ROTATE. Writes nothing;
    proposes a threshold only with enough evidence."""
    from collections import Counter
    from .watcher_service import maintenance_records
    guard = Guard(runtime.config, runtime.factory, None)
    full = load_events(store)
    history = full[-REPLAY_LIMIT:]
    episodes, providers = _episodes(guard, store, history)
    by_rule = {}
    for rule in sorted({e['rule'] for e in episodes}):
        mine = [e for e in episodes if e['rule'] == rule]
        by_rule[rule] = {'episodes': len(mine), 'peak': dict(Counter(e['peak'] for e in mine)),
                         'ended_by': dict(Counter(e['ended_by'] for e in mine)),
                         # Without an operator review, progress ended it: enforce would have held a dispatch for it.
                         'holding_self_resolved': sum(1 for e in mine if e['peak'] in HOLDING and e['ended_by'] == 'progress')}
    by_provider = {}
    for provider in sorted(set(providers.values())):
        agents = sorted(agent for agent, value in providers.items() if value == provider)
        mine = [e for e in history if e.get('agent') in agents]
        dispatched = sum(1 for e in mine if e['kind'] == 'dispatched')
        reasons = Counter(e.get('reason') for e in mine if e['kind'] == 'no_progress')
        by_provider[provider] = {
            'agents': agents, 'dispatches': dispatched,
            'confirmed': dict(Counter(e.get('progress') for e in mine if e['kind'] == 'handoff_confirmed')),
            'no_progress_by_reason': dict(reasons),
            'turn_without_block_per_dispatch': round(reasons['turn_without_block'] / dispatched, 2) if dispatched else None,
            'errors': dict(Counter(e['kind'] for e in mine if e['kind'] in ERRORS)),
            'permission_blocked': sum(1 for e in mine if e['kind'] == 'permission_blocked'),
            'delivery_uncertain': sum(1 for e in mine if e['kind'] == 'delivery_uncertain'),
            'alert_episodes': dict(Counter(e['rule'] for e in episodes if e.get('provider') == provider))}
    # Same instruction to the same agent: legitimate when verified progress separates the repetitions.
    repeats = {'legitimate': 0, 'without_progress': 0}
    for agent in {e.get('agent') for e in history if e['kind'] == 'dispatched'}:
        seen = {}
        for e in (e for e in history if e.get('agent') == agent):
            if e['kind'] in PROGRESS:
                seen = {sig: True for sig in seen}
            elif e['kind'] == 'dispatched':
                if e.get('instruction') in seen:
                    repeats['legitimate' if seen[e['instruction']] else 'without_progress'] += 1
                seen[e.get('instruction')] = False
    recovery = []
    operations = sorted(maintenance_records(store), key=lambda op: (op.get('states') or {}).get('REQUESTED', 0))
    for index, op in enumerate(operations):
        finished = (op.get('states') or {}).get('COMPLETED')
        if op.get('kind') not in ('CLEAR', 'ROTATE') or not finished:
            continue
        if not history or finished < history[0]['time']:
            # The ledger (4C) or the replayed sample starts later: nothing to attribute.
            recovery.append({'op_id': op['op_id'][:12], 'kind': op['kind'], 'agent': op['agent'],
                             'provider': op.get('provider'), 'completed_at': _iso(finished),
                             'outcome': 'before_ledger'})
            continue
        # Only the tasks this session received: up to the agent's next maintenance operation.
        until = min([(later.get('states') or {}).get('REQUESTED', math.inf) for later in operations[index + 1:]
                     if later.get('agent') == op['agent'] and later.get('kind') in ('CLEAR', 'ROTATE')] or [math.inf])
        after = [e for e in history if e.get('agent') == op['agent'] and finished < e['time'] < until]
        task = next((e for e in after if e['kind'] == 'dispatched'), None)
        confirmed = task and next((e for e in after if e['kind'] == 'handoff_confirmed'
                                   and e.get('event_id') == task.get('event_id')), None)
        recovery.append({'op_id': op['op_id'][:12], 'kind': op['kind'], 'agent': op['agent'],
                         'provider': op.get('provider'), 'completed_at': _iso(finished),
                         'next_task': (task.get('event_id') or '')[:12] if task else None,
                         'outcome': (confirmed or {}).get('progress') or ('pending' if task else 'no_task'),
                         'no_progress_before_confirmation': sum(
                             1 for e in after if e['kind'] == 'no_progress' and task and
                             e.get('event_id') == task.get('event_id'))})
    announced = Counter()
    try:
        for line in runtime.context.output('logs/guard.log').read_text(encoding='utf-8').splitlines():
            item = json.loads(line)
            announced[f"{item.get('rule')}:{item.get('level')}:{item.get('mode')}"] += 1
    except (OSError, ValueError, ConfigurationError):
        pass
    verdicts, proposals = [], []
    for provider, stats in by_provider.items():
        if stats['dispatches'] < MIN_DISPATCHES:
            verdicts.append({'scope': provider, 'verdict': 'insufficient_evidence',
                             'detail': f"{stats['dispatches']} despachos < {MIN_DISPATCHES}: se mantienen los umbrales globales"})
            continue
        for rule, count in stats['alert_episodes'].items():
            mine = [e for e in episodes if e['rule'] == rule and e.get('provider') == provider]
            needless = sum(1 for e in mine if e['peak'] in HOLDING and e['ended_by'] == 'progress')
            if count >= MIN_EPISODES and rule in guard.settings['loop'] and needless / count >= 0.3:
                proposals.append({'scope': provider, 'rule': rule, 'current': guard.settings['loop'][rule],
                                  'proposal': 'subir pause e intervention en 1 para este proveedor',
                                  'evidence': f'{needless}/{count} episodios PAUSE+ resueltos por avance sin revisión'})
        verdicts.append({'scope': provider, 'verdict': 'evaluated', 'detail': f"{stats['dispatches']} despachos"})
    times = [e['time'] for e in history]
    return {'mode': guard.mode, 'read_only': True, 'project_id': runtime.context.project_id,
            'workspace': str(runtime.context.workspace_root),
            'sample': {'events': len(full), 'replayed': len(history), 'truncated': len(full) > len(history),
                       'from': _iso(min(times)) if times else None, 'to': _iso(max(times)) if times else None},
            'thresholds': guard.settings['loop'], 'alerts_by_rule': by_rule, 'by_provider': by_provider,
            'repeated_instructions': repeats, 'recovery_after_maintenance': recovery,
            'announced_alerts': dict(announced), 'verdicts': verdicts, 'proposals': proposals,
            'notes': ['Replay de reglas de bucle; las de presupuesto dependen del estado actual y no se reproducen.',
                      f'Umbral por proveedor solo con >= {MIN_DISPATCHES} despachos y >= {MIN_EPISODES} episodios.']}


def main(root, argv=None):
    """Read-only report by default; --acknowledge RULE:AGENT --confirm records an operator review."""
    from .runtime import Runtime
    from .state import StateStore
    parser = argparse.ArgumentParser(description='Context budget and loop guard: read-only report, or acknowledge an '
                                                 'alert after review. Never clears, rotates or retries.')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--acknowledge', metavar='RULE:AGENT', help='Mark the evidence of an alert as reviewed.')
    action.add_argument('--status', action='store_true', help='Read-only diagnosis per agent: session, work since the '
                                                              'last maintenance, metrics, alerts, holds, eligibility.')
    action.add_argument('--calibrate', action='store_true', help='Read-only replay of the ledger: alert frequency, '
                                                                 'self-resolved alerts, recovery after maintenance.')
    parser.add_argument('--agent', metavar='ROL', action='append', help='Limit --status to these roles.')
    parser.add_argument('--confirm', action='store_true', help='Authorize --acknowledge.')
    parser.add_argument('--config', type=Path, help='Same configuration file as the watcher (default: config_bmad.json).')
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    if args.agent and (not args.status or set(args.agent) - set(AGENT_PHASES)):
        parser.error('--agent needs --status and a known role.')
    if args.confirm and not args.acknowledge:
        parser.error('--confirm only authorizes --acknowledge; the reports are read-only.')
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    store = rt = None
    try:
        context = resolve_context(root, workspace=args.workspace, project=args.project, config_path=args.config)
        if args.acknowledge:
            rule, _, agent = args.acknowledge.partition(':')
            if not args.confirm or not agent or (agent != '*' and agent not in AGENT_PHASES
                                                 and not agent.startswith('speckit.')):
                parser.error('--acknowledge needs RULE:AGENT (AGENT is a role, speckit.<op> or *) and --confirm.')
            rt = Runtime(root, config_path=args.config, context=context)
            alert = rt.guard.acknowledge(rule, agent)
            print(json.dumps({'acknowledged': f'{rule}:{agent}', 'alert_level': alert and alert['level']},
                             ensure_ascii=False))
            return 0
        # Read-only: no locks, no state writes, no prompts to agents.
        store = StateStore.open_readonly(context)
        runtime = Runtime(root, config_path=args.config, context=context, persist=False)
        if store is not None and args.status:
            result = status(runtime, store, names=args.agent)
        elif store is not None and args.calibrate:
            result = calibrate(runtime, store)
        else:
            result = report(runtime, store)
        if store is None:
            result['reason'] = 'state_missing'
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if store:
            store.close()
        if rt:
            rt.close()


if __name__ == '__main__':
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
