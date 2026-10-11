"""Persistence and provider-neutral boundaries used by the legacy BMAD workflow."""
import json
import os
import time
from typing import NamedTuple

from .errors import ReconciliationRequired
from .state import StateStore

# Traceability metadata for queued handoffs; the canonical `state` field keeps its meaning.
HANDOFF_STAGES = ('detectado', 'reservado', 'despachado', 'confirmado', 'fallido', 'requiere_intervencion')

# Operator-driven session maintenance (maintenance.py). The watcher holds SESSION_LOCK during each
# tick and advertises SESSION_PROTOCOL in its heartbeat; maintenance holds the lock for a whole operation.
SESSION_LOCK = 'sessions'
SESSION_PROTOCOL = 'sessions-lock/1'
WATCHER_HEARTBEAT_S = 30
# FAILED = nothing changed in the agent; any other non-COMPLETED state blocks until reconciled.
MAINTENANCE_FINAL = ('COMPLETED', 'FAILED')


def maintenance_records(state):
    rows = state.db.execute("SELECT id,data FROM records WHERE id LIKE 'maintenance:%'")
    return [json.loads(data) for _, data in rows]


def maintenance_blocks(state):
    """{agent: op_id} for maintenance operations that are incomplete or uncertain and not yet reconciled."""
    return {op['agent']: op['op_id'] for op in maintenance_records(state)
            if op.get('state') not in MAINTENANCE_FINAL and not op.get('resolution')}


# Owned agents in these states are held, never dispatched to; only 'ready' agents receive tasks.
HOLD_STATES = ('starting', 'awaiting_trust', 'unverified', 'maintenance')


def protocol_violations(state):
    """Unresolved blocks written by an agent without a watcher dispatch (H11)."""
    rows = state.db.execute("SELECT id,data FROM records WHERE id LIKE 'protocol_violation:%'")
    return [(key, data) for key, data in ((key, json.loads(raw)) for key, raw in rows) if data.get('state') != 'done']


def authorized_block(state, agent, index, followups):
    """Dispatch key that authorizes the agent's tracker block at `index`, or None."""
    follow = (followups or {}).get(agent) or {}
    event = follow.get('event_id')
    if event and follow.get('bloques_al_despachar', float('inf')) <= index:
        dispatch = state.get('dispatch:' + event) or {}
        if dispatch.get('state') == 'done' and dispatch.get('agent_id') == agent:
            return 'dispatch:' + event
    for key, raw in state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'"):
        data = json.loads(raw)
        if data.get('agent_id') == agent and data.get('confirmed_block') == index:
            return key
    return None


def audit_blocks(state, authors, agent_of, followups):
    """Every agent-authored tracker block must answer a watcher dispatch; the tracker is not a work queue.

    `authors` are the block authors in tracker order; `agent_of` maps an author to an agent (None for
    WATCHER, humans and headless sessions). Returns the new violations; history before the first audit
    (older SQLite states) is not judged retroactively.
    """
    saved = state.get('block_audit')
    if saved is None or saved.get('count', 0) > len(authors):
        state.put('block_audit', {'count': len(authors)})
        return []
    found = []
    for index in range(saved['count'], len(authors)):
        agent = agent_of(authors[index])
        if not agent or authorized_block(state, agent, index, followups):
            continue
        record = {'state': 'requiere_intervencion', 'agent_id': agent, 'author': authors[index][:120],
                  'block_index': index, 'reason': 'block_without_dispatch', 'time': time.time()}
        state.put(f'protocol_violation:{index}', record)
        found.append(record)
    state.put('block_audit', {'count': len(authors)})
    return found


def watcher_heartbeat(state, started):
    state.put('watcher', {'pid': os.getpid(), 'protocol': SESSION_PROTOCOL, 'started': started,
                          'heartbeat': time.time()})


def watcher_participation(state, now=None):
    """None when a running watcher advertises the coordination protocol recently; otherwise the reason."""
    beat = state.get('watcher')
    if not beat or beat.get('protocol') != SESSION_PROTOCOL:
        return 'watcher_without_coordination'
    if (now if now is not None else time.time()) - beat.get('heartbeat', 0) > WATCHER_HEARTBEAT_S:
        return 'watcher_heartbeat_stale'
    return None


class TrackerSnapshot(NamedTuple):
    lines: list            # nonblank newline-terminated lines, as read_lines() returns them
    tail: str | None       # unterminated last line, possibly still being written
    stable: bool           # size and mtime unchanged while reading
    error: str | None = None


def read_tracker(path):
    """Read complete lines only, with the same universal-newline view as Path.read_text."""
    try:
        before = path.stat()
    except FileNotFoundError:
        return TrackerSnapshot([], None, True)
    except OSError:
        return TrackerSnapshot([], None, False)
    try:
        data = path.read_bytes()
        after = path.stat()
    except OSError:
        # Removed or locked by the writer between calls: read again later.
        return TrackerSnapshot([], None, False)
    stable = before.st_size == after.st_size == len(data) and before.st_mtime_ns == after.st_mtime_ns
    cut = data.rfind(b'\n') + 1
    try:
        head = data[:cut].decode('utf-8')
    except UnicodeDecodeError:
        return TrackerSnapshot([], None, stable, 'invalid_utf8')
    head = head.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line for line in head.splitlines(keepends=True) if line.strip()]
    try:
        tail = data[cut:].decode('utf-8').rstrip('\r')
    except UnicodeDecodeError:
        # The writer stopped in the middle of a multibyte character.
        return TrackerSnapshot(lines, None, False)
    return TrackerSnapshot(lines, tail if tail.strip() else None, stable)


def prefix_matches(lines, count, digest):
    if count > len(lines):
        return False
    prefix = lines[:count]
    if StateStore.fingerprint(*prefix) == digest:
        return True
    # Cursors saved by the previous reader may end in a line without newline.
    return bool(prefix) and prefix[-1].endswith('\n') and StateStore.fingerprint(*prefix[:-1], prefix[-1][:-1]) == digest


def same_line(line, digest):
    return StateStore.fingerprint(line) == digest or (line.endswith('\n') and StateStore.fingerprint(line[:-1]) == digest)


def tracker_verified(context, state):
    """Read-only check of the tracker against the processed history; returns a problem code or None."""
    integrity = state.get('tracker_integrity')
    if integrity and integrity.get('state') != 'done':
        return 'tracker_integrity_' + str(integrity.get('reason', 'unknown'))
    saved = state.get('tracker_cursor')
    if saved is None:
        return 'tracker_cursor_missing'
    snapshot = read_tracker(context.tracker_path)
    if not snapshot.stable:
        return 'tracker_changing'
    if snapshot.error:
        return 'tracker_' + snapshot.error
    lines, count, digest = snapshot.lines, saved['count'], saved['prefix_hash']
    if prefix_matches(lines, count, digest):
        pending = len(lines) > count or snapshot.tail is not None
    elif snapshot.tail and prefix_matches(lines + [snapshot.tail + '\n'], count, digest):
        pending = len(lines) + 1 > count
    else:
        return 'tracker_rewritten'
    # Lines the watcher has not processed yet may hold handoffs for any agent.
    return 'tracker_unprocessed_lines' if pending else None


def mark_handoff(state, event_id, stage, **details):
    if stage not in HANDOFF_STAGES:
        raise ValueError(f'Unknown handoff stage: {stage}')
    key = 'queued:' + event_id
    data = state.get(key)
    if data is None:
        return
    state.put(key, {**data, **details, 'stage': stage, 'stages': {**data.get('stages', {}), stage: time.time()}})


class WatcherService:
    def __init__(self, runtime, *, clock=time.monotonic):
        self.runtime = runtime
        self.clock = clock
        settings = runtime.config.data['tracker']
        self.settle_seconds = settings['settle_seconds']
        self.rewrite_grace_seconds = settings['rewrite_grace_seconds']
        self._tail = None        # (text, first seen) of the unterminated last line
        self._disturbed = None   # first time the tracker disagreed with the cursor

    def read_lines(self):
        path = self.runtime.context.tracker_path
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding='utf-8').splitlines(keepends=True) if line.strip()]

    def _consistent(self, lines, cursor):
        saved = self.runtime.state.get('tracker_cursor')
        if saved is None:
            return len(lines) >= cursor
        return prefix_matches(lines, saved['count'], saved['prefix_hash'])

    def _with_tail(self, snapshot, cursor):
        if snapshot.tail is None:
            self._tail = None
            return snapshot.lines
        candidate = snapshot.lines + [snapshot.tail + '\n']
        now = self.clock()
        if self._tail is None or self._tail[0] != snapshot.tail:
            self._tail = (snapshot.tail, now)
        # Already consumed before a restart or rewrite: it is part of the verified history.
        if len(snapshot.lines) < cursor and self._consistent(candidate, cursor):
            return candidate
        # A writer may never add the final newline; accept the line once it stops changing.
        if now - self._tail[1] >= self.settle_seconds:
            return candidate
        return snapshot.lines

    def _reason(self, lines, cursor):
        if not self.runtime.context.tracker_path.exists():
            return 'missing'
        saved = self.runtime.state.get('tracker_cursor')
        return 'shorter' if len(lines) < (saved['count'] if saved else cursor) else 'rewritten'

    def poll(self, cursor):
        """Lines consistent with the processed history, or None while the tracker is in flux."""
        snapshot = read_tracker(self.runtime.context.tracker_path)
        if not snapshot.stable:
            return None
        lines = self._with_tail(snapshot, cursor)
        if snapshot.error is None and self._consistent(lines, cursor):
            self._disturbed = None
            return lines
        reason = snapshot.error or self._reason(lines, cursor)
        now = self.clock()
        if self._disturbed is None:
            self._disturbed = now
            print(f'⚠️ [Tracker] Lectura inconsistente con el historial procesado ({reason}); '
                  f'se espera hasta {self.rewrite_grace_seconds}s antes de suspender.')
        if now - self._disturbed < self.rewrite_grace_seconds:
            return None
        self.suspend(reason, cursor, len(lines))

    def suspend(self, reason, cursor, observed):
        # Recorded in SQLite, never in the tracker under reconciliation.
        self.runtime.state.put('tracker_integrity', {
            'state': 'requiere_intervencion', 'stage': 'requiere_intervencion', 'reason': reason,
            'cursor': cursor, 'observed_lines': observed, 'time': time.time()})
        raise ReconciliationRequired(
            f'Tracker history changed before the saved cursor ({reason}); processing suspended without dispatching. '
            'Restore the tracker or reconcile with python -m bmad_runtime.state before resuming.')

    def startup_lines(self, sleep=time.sleep):
        saved = self.runtime.state.get('tracker_cursor')
        cursor = saved['count'] if saved else 0
        deadline = self.clock() + self.rewrite_grace_seconds + 2
        while True:
            lines = self.poll(cursor)
            if lines is not None:
                integrity = self.runtime.state.get('tracker_integrity')
                if integrity and integrity['state'] != 'done':
                    self.runtime.state.finish('tracker_integrity', 'done')
                return lines
            if self.clock() >= deadline:
                raise ReconciliationRequired('Tracker kept changing during startup; retry when writers are idle.')
            sleep(0.25)

    def begin_line(self, number, line):
        key = 'event:' + StateStore.fingerprint(number, line)
        return key, self.runtime.state.claim(key)

    def complete_line(self, key):
        self.runtime.state.finish(key, 'done')

    def restore_cursor(self, lines, fallback):
        saved = self.runtime.state.get('tracker_cursor')
        if saved is None:
            return fallback
        count = saved['count']
        if not prefix_matches(lines, count, saved['prefix_hash']):
            self.suspend('shorter' if count > len(lines) else 'rewritten', count, len(lines))
        return count

    def save_cursor(self, lines, count):
        self.runtime.state.put('tracker_cursor', {'count': count, 'prefix_hash': StateStore.fingerprint(*lines[:count])})

    def pending_tasks(self, lines):
        tasks = []
        for key, data in self.runtime.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'"):
            event = json.loads(data)
            if event['state'] == 'done':
                continue
            index = event['line_number']
            if index >= len(lines) or not same_line(lines[index], event['line_hash']):
                raise ReconciliationRequired('Queued tracker line changed; reconcile before restarting.')
            # Only dispatch instructions are persisted by reference. Never re-run
            # extraction (which includes non-idempotent SDD/Git operations).
            text = lines[index][event['start']:event['end']].strip()
            tasks.append({'agente': event['agent_id'], 'mensaje': text, 'event_id': key[7:]})
        return tasks

    def enqueue(self, line_number, line, task):
        event_id = StateStore.fingerprint(line_number, task['agente'], task['mensaje'])
        key = 'queued:' + event_id
        if self.runtime.state.get(key) is None:
            start = line.find(task['mensaje'])
            if start < 0:
                raise ReconciliationRequired('Task must reference the exact tracker line.')
            self.runtime.state.put(key, {'state': 'queued', 'agent_id': task['agente'],
                                        'line_number': line_number, 'line_hash': StateStore.fingerprint(line),
                                        'start': start, 'end': start + len(task['mensaje']),
                                        'stage': 'detectado', 'stages': {'detectado': time.time()}})
        return {**task, 'event_id': event_id}

    def mark(self, task, stage, **details):
        mark_handoff(self.runtime.state, task['event_id'], stage, **details)

    def dispatched(self, task):
        self.runtime.state.finish('queued:' + task['event_id'], 'done')
        dispatch = self.runtime.state.get('dispatch:' + task['event_id']) or {}
        # despachado = accepted by the agent (lifecycle change observed); confirmado comes from its tracker block.
        self.mark(task, 'despachado', **{key: dispatch[key] for key in ('task_file', 'delivery') if key in dispatch})

    def failed(self, task, reason):
        # A dispatch claim that never finished may have reached the agent: never retry it blindly.
        record = self.runtime.state.get('dispatch:' + task['event_id'])
        uncertain = record and record['state'] not in {'done', 'not_delivered'}
        self.mark(task, 'requiere_intervencion' if uncertain else 'fallido', failure=reason)
