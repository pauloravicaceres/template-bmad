"""Journaled appends to a project tracker for engine-side (Python) writers.

The watcher, the Control Center and the utilities append complete blocks through TrackerWriter:
one interprocess lock per project (`<state>/tracker.lock`), a SQLite journal record per operation
(`tracker_append:<op_id>`) and a read-back check. Agent CLIs still edit the tracker directly and do
not take the lock, so the journal is also re-verified: a journaled block that disappeared was lost
by an external rewrite. Losses and uncertain appends stop the writer until a human resolves them
explicitly; nothing is repaired or re-appended automatically.

Completed vs. uncertain append (crash between the file write and the SQLite confirmation): the
journal records offset, length and SHA-256 of the exact bytes *before* writing. On recovery the
bytes are searched from that offset: found complete -> `done`; a truncated copy at the end of the
file -> `uncertain`; nothing -> `not_written` (the same op_id may be appended again).

Delivery state (`state`) and human handling are separate fields (Fase 4F-E1.1):

- `done` is only ever set from evidence: the journaled bytes were read back from the tracker.
- `lost` (was done, bytes gone) and `uncertain` (partial or unverifiable write) are incidents. An
  open incident stops every Python write to the tracker.
- `acknowledged` records that a human reviewed the incident; it never changes `state`, never
  unblocks writes and never authorizes writing the operation again.
- `resolution` closes an incident only through an explicit operation under the lock:
  `verified_present` (reconcile found a complete copy -> `done`), `reissue_authorized` (acknowledged,
  lost and verified absent; the producer may write the same op_id once more -> `reissued`) or
  `loss_accepted` (acknowledged, lost and verified absent; the op_id is never written again).
- A replay (`done` returned again for the same op_id) is answered only after the journaled bytes are
  found in the tracker; otherwise the operation becomes `lost`.
- `history` keeps every incident transition with the evidence it replaced; nothing is deleted.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import threading
import time
from typing import NamedTuple
import uuid

from .errors import ReconciliationRequired
from .state import ProjectLock, StateStore

JOURNAL = 'tracker_append:'
INDEX = 'tracker_journal:'
DEFAULT_TIMEOUT = 5.0
RECENT = 200          # done appends re-verified on every check; older ones are covered by the watcher cursor
INCIDENT = ('uncertain', 'lost')
RELEASED = ('reissue_authorized', 'loss_accepted')     # resolutions after which an incident no longer blocks
_FINGERPRINT = ('offset', 'length', 'sha256', 'head', 'first', 'norm_sha256', 'norm_length', 'norm_head', 'norm_first',
                'body_sha256')
_EVIDENCE = ('state', *_FINGERPRINT, 'journaled_offset', 'time', 'attempt', 'reason', 'detected', 'source')
_HUMAN = ('acknowledged', 'acknowledged_state', 'resolution')
_HEAD = 64
_OP_ID = re.compile(r'^[A-Za-z0-9:_.-]{1,128}$')
_HUMAN_HEADER = re.compile(rb'^### \[[^\]\n]*\]\s+HUMANO\b', re.IGNORECASE | re.MULTILINE)


class TrackerBusy(ReconciliationRequired):
    """Another writer kept the tracker lock past the timeout; nothing was written."""


class TrackerIntegrityError(ReconciliationRequired):
    """A journaled append is uncertain or was removed by an external rewrite; inspect before continuing."""

    def __init__(self, message, operations=()):
        super().__init__(message)
        self.operations = list(operations)


class TrackerConflict(ReconciliationRequired):
    """The precondition of an append no longer holds (e.g. another human decision was recorded first)."""


class AppendResult(NamedTuple):
    op_id: str
    offset: int
    length: int
    replayed: bool = False
    reissued: bool = False


def state_dir_for(tracker_path):
    """State directory that ProjectContext pairs with this tracker (handoffs -> state, docs -> .bmad-runtime)."""
    parent = Path(tracker_path).resolve().parent
    if parent.name == 'handoffs':
        return parent.parent / 'state'
    if parent.name == 'docs':
        return parent.parent / '.bmad-runtime'
    return parent / '.bmad-runtime'


def no_human_block_since(offset):
    """Precondition: no human decision was appended after byte `offset` (read before a human reviewed)."""
    def check(data):
        if _HUMAN_HEADER.search(data, min(offset, len(data))):
            return 'Otra decisión humana se registró en el tracker mientras revisabas; vuelve a ejecutar la aprobación.'
        return None
    return check


def tracker_command(action, op_key, scope=''):
    """Exact state CLI order (from the engine root) for one reconciliation step of a journaled append."""
    return f'python -m bmad_runtime.state{scope} --{action} {op_key} --confirm'


def acknowledge_command(op_key, scope=''):
    return tracker_command('acknowledge', op_key, scope)


def resolution_kind(record):
    return (record.get('resolution') or {}).get('kind')


def is_open_incident(record):
    """Lost/uncertain append without an explicit releasing resolution: blocks every Python tracker write."""
    return record.get('state') in INCIDENT and resolution_kind(record) not in RELEASED


def _legacy_ack(record):
    """Pre-E1.1 --acknowledge rewrote a lost/uncertain append as `done`: such a record proves no delivery."""
    return record.get('state') == 'done' and bool(record.get('acknowledged')) and 'acknowledged_state' not in record


def _history(record, event, **details):
    entry = {'at': time.time(), 'event': event, 'from': record.get('state'), **details}
    return [*record.get('history', []), entry]


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _fingerprint(payload):
    norm = payload.replace(b'\r\n', b'\n')
    return {'sha256': _sha(payload), 'length': len(payload), 'head': _sha(payload[:_HEAD]), 'first': payload[0],
            'norm_sha256': _sha(norm), 'norm_length': len(norm), 'norm_head': _sha(norm[:_HEAD]), 'norm_first': norm[0]}


def _scan(data, start, length, digest, head, first):
    """('present', pos) for a complete copy at or after `start`, ('partial', pos) for one cut at EOF, else ('absent', None)."""
    partial = None
    marker = bytes([first])
    position = data.find(marker, max(start, 0))
    while position >= 0:
        if _sha(data[position:position + min(_HEAD, length)]) == head:
            if _sha(data[position:position + length]) == digest:
                return 'present', position
            if position + length > len(data) and partial is None:
                partial = position
        position = data.find(marker, position + 1)
    return ('partial', partial) if partial is not None else ('absent', None)


def locate(data, record, start=None):
    """Where the journaled bytes of `record` are in `data`, searching from `start` (default: its offset).

    Tolerates a CRLF normalization of the whole file (reported at the journaled offset)."""
    offset = record['offset']
    if offset + record['length'] <= len(data) and _sha(data[offset:offset + record['length']]) == record['sha256']:
        return 'present', offset
    status, position = _scan(data, offset if start is None else start, record['length'], record['sha256'],
                             record['head'], record['first'])
    if status != 'absent' or b'\r' not in data:
        return status, position
    found, _ = _scan(data.replace(b'\r\n', b'\n'), 0, record['norm_length'], record['norm_sha256'],
                     record['norm_head'], record['norm_first'])
    return ('present', offset) if found == 'present' else ('absent', None)


def _all(data, length, digest, head, first):
    found, partial, marker = [], False, bytes([first])
    position = data.find(marker)
    while position >= 0:
        if _sha(data[position:position + min(_HEAD, length)]) == head:
            if _sha(data[position:position + length]) == digest:
                found.append(position)
            elif position + length > len(data):
                partial = True
        position = data.find(marker, position + 1)
    return found, partial


def evidence(data, record):
    """Whole-file evidence for a reconciliation: (complete copies, a truncated copy ends the file).

    A CRLF normalization of the whole file still counts as a complete copy."""
    found, partial = _all(data, record['length'], record['sha256'], record['head'], record['first'])
    if not found and b'\r' in data:
        found, _ = _all(data.replace(b'\r\n', b'\n'), record['norm_length'], record['norm_sha256'],
                        record['norm_head'], record['norm_first'])
    return len(found), partial


class TrackerWriter:
    """Single path for Python writes to one tracker. Safe across processes and threads; not re-entrant
    across two writer objects of the same tracker in one thread (that would wait for its own lock)."""

    def __init__(self, tracker_path, state_dir=None, *, timeout=None, grace=2.0, poll=0.05, scope=''):
        self.path = Path(tracker_path)
        self.state_dir = Path(state_dir) if state_dir else state_dir_for(tracker_path)
        self.timeout = DEFAULT_TIMEOUT if timeout is None else float(timeout)
        self.grace = grace
        self.poll = poll
        self.scope = scope          # ' --workspace "W" --project P' in the reconciliation commands it prints
        self.identity = os.path.normcase(str(self.path.resolve()))
        self._index_key = INDEX + _sha(self.identity.encode('utf-8'))[:16]
        self._thread = threading.RLock()
        self._depth = 0
        self._lock = None

    @classmethod
    def for_context(cls, context, **options):
        if not context.legacy:
            options.setdefault('scope', f' --workspace "{context.workspace_root}" --project {context.project_id}')
        return cls(context.tracker_path, context.state_dir, **options)

    @classmethod
    def for_runtime(cls, rt, **options):
        options.setdefault('timeout', rt.config.data['tracker'].get('lock_timeout_seconds', DEFAULT_TIMEOUT))
        return cls.for_context(rt.context, **options)

    # ----------------------------------------------------------------- locking
    @contextmanager
    def locked(self):
        """Hold the project tracker lock; raises TrackerBusy after `timeout` seconds. Never held by callers
        across provider calls, prompts or network operations."""
        deadline = time.monotonic() + self.timeout
        if not self._thread.acquire(timeout=max(self.timeout, 0)):
            raise TrackerBusy(f'El tracker está ocupado por otro hilo más de {self.timeout:g}s; no se escribió nada.')
        try:
            if self._depth == 0:
                lock = ProjectLock.at(self.state_dir / 'tracker.lock')
                while not lock.acquire():
                    if time.monotonic() >= deadline:
                        raise TrackerBusy(f'Otro proceso retiene el lock del tracker más de {self.timeout:g}s; '
                                          'no se escribió nada. Reintenta cuando termine.')
                    time.sleep(self.poll)
                self._lock = lock
            self._depth += 1
            try:
                yield self
            finally:
                self._depth -= 1
                if self._depth == 0:
                    lock, self._lock = self._lock, None
                    lock.release()
        finally:
            self._thread.release()

    @contextmanager
    def _store(self):
        store = StateStore.in_directory(self.state_dir)
        try:
            yield store
        finally:
            store.close()

    # ----------------------------------------------------------------- reading
    def read_bytes(self):
        try:
            return self.path.read_bytes()
        except FileNotFoundError:
            return b''

    def read(self):
        return self.read_bytes().decode('utf-8', errors='replace')

    # ----------------------------------------------------------------- journal
    def _index(self, store):
        index = store.get(self._index_key) or {}
        return {'tracker': self.identity, 'pending': list(index.get('pending', [])),
                'recent': list(index.get('recent', [])), 'problems': list(index.get('problems', []))}

    def _save(self, store, key, record, index):
        store.put_many([(key, record), (self._index_key, index)])

    def _finish(self, store, key, record, state, event=None, note=None, **details):
        """Record a delivery state; incident transitions are appended to `history`. Entering an incident drops its
        previous resolution, and a new incident (from a non-incident state) also its acknowledgement: both stay in
        `history`, never in force."""
        index = self._index(store)
        index['pending'] = [k for k in index['pending'] if k != key]
        before = record.get('state')
        if state == 'done':
            index['recent'] = ([k for k in index['recent'] if k != key] + [key])[-RECENT:]
            index['problems'] = [k for k in index['problems'] if k != key]
            if resolution_kind(record) == 'reissue_authorized' and 'resolution' not in details:
                details['resolution'] = {**record['resolution'], 'kind': 'reissued', 'at': time.time()}
        elif state in INCIDENT and key not in index['problems']:
            index['problems'].append(key)
        if event or state in INCIDENT or before in INCIDENT or details.get('recovered'):
            entry = dict(note or {})
            if state in INCIDENT:
                dropped = ('resolution',) if before in INCIDENT else _HUMAN
                previous = {k: record[k] for k in dropped if record.get(k)}
                if previous:
                    entry['previous'] = previous
                record = {k: v for k, v in record.items() if k not in dropped}
            record = {**record, 'history': _history(record, event or f'{before}->{state}', to=state, **entry)}
        record = {**record, **details, 'state': state, 'updated': time.time()}
        self._save(store, key, record, index)
        return record

    def _problems(self, store, persist=False):
        """Open incidents (lost/uncertain without a releasing resolution); acknowledging does not close one.
        Closed ones leave the index (only under the lock)."""
        index = self._index(store)
        open_keys = [key for key in index['problems'] if is_open_incident(store.get(key) or {})]
        if persist and open_keys != index['problems']:
            index['problems'] = open_keys
            store.put(self._index_key, index)
        return open_keys

    def _raise_problems(self, keys):
        key = keys[0]
        raise TrackerIntegrityError(
            'El tracker tiene escrituras del motor inciertas o perdidas por una reescritura externa: '
            + ', '.join(keys[:5]) + '. No se escribe ni despacha nada hasta resolverlas; reconocerlas solo registra '
            'la revisión, no confirma la entrega ni reemite. Con el watcher detenido: inspecciona el tracker, '
            'reconoce con ' + tracker_command('acknowledge', key, self.scope) + ', verifica la evidencia con '
            + tracker_command('reconcile', key, self.scope) + ' y, solo si no queda copia, autoriza una reemisión '
            'con ' + tracker_command('authorize-reissue', key, self.scope) + ' o cierra la pérdida con '
            + tracker_command('accept-loss', key, self.scope) + '. Nada se reescribe automáticamente.', keys)

    def _recover(self, store, raise_problems=True):
        index = self._index(store)
        if index['pending']:
            data = self.read_bytes()
            for key in list(index['pending']):
                record = store.get(key)
                if not record or record.get('state') != 'in_flight':
                    index = self._index(store)
                    index['pending'] = [k for k in index['pending'] if k != key]
                    store.put(self._index_key, index)
                    continue
                status, position = locate(data, record)
                if status == 'present':
                    self._finish(store, key, {**record, 'offset': position}, 'done', recovered=True)
                elif status == 'partial' or len(data) < record['offset']:
                    self._finish(store, key, record, 'uncertain',
                                 reason='partial_write' if status == 'partial' else 'tracker_shrank')
                else:
                    self._finish(store, key, record, 'not_written', recovered=True)
        problems = self._problems(store, persist=True)
        if problems and raise_problems:
            self._raise_problems(problems)

    def missing(self, store=None):
        """Recent `done` appends whose bytes are no longer in the tracker (read-only)."""
        if store is None:
            with self._store() as own:
                return self.missing(own)
        data = self.read_bytes()
        absent = []
        for key in self._index(store)['recent']:
            record = store.get(key)
            if not record or record.get('state') != 'done':
                continue
            if locate(data, record, start=0)[0] != 'present':
                absent.append(key)
        return absent

    def mark_lost(self, keys, store=None):
        """Record the given journaled appends as lost (under the lock) and raise TrackerIntegrityError."""
        if store is None:
            with self.locked(), self._store() as own:
                return self.mark_lost(keys, own)
        for key in keys:
            record = store.get(key)
            if record and record.get('state') == 'done':
                self._finish(store, key, record, 'lost', reason='missing_from_tracker', detected=time.time())
        self._raise_problems(list(keys))

    def _verify(self, store, grace):
        deadline = time.monotonic() + grace
        while True:
            absent = self.missing(store)
            if not absent:
                return
            if time.monotonic() >= deadline:
                self.mark_lost(absent, store)
            time.sleep(min(0.25, max(grace, 0.01)))

    def recover(self, grace=None):
        """Resolve interrupted appends and verify recent ones; raises TrackerIntegrityError on any problem."""
        with self.locked(), self._store() as store:
            self._recover(store)
            self._verify(store, self.grace if grace is None else grace)

    def audit(self):
        """Non-blocking check for long-running readers: (absent_keys, open_problem_keys)."""
        with self._store() as store:
            return self.missing(store), self._problems(store)

    def describe(self, op_id):
        with self._store() as store:
            return store.get(JOURNAL + op_id)

    def status(self, op_id):
        """Journaled delivery state; 'unverified' for a pre-E1.1 acknowledgement that rewrote an incident as done."""
        record = self.describe(op_id)
        if not record:
            return None
        return 'unverified' if _legacy_ack(record) else record.get('state')

    def delivered(self, op_id):
        """True only when the operation is `done` and its journaled bytes are in the tracker now. Callers that
        decide on a replay hold the lock (e.g. the Control Center transaction)."""
        record = self.describe(op_id)
        return bool(record) and record.get('state') == 'done' and \
            locate(self.read_bytes(), record, start=0)[0] == 'present'

    # ----------------------------------------------------------------- reconciliation (explicit, human)
    def _with_lock(self, store, action, op_key):
        key = op_key if op_key.startswith(JOURNAL) else JOURNAL + op_key
        if store is not None:          # the caller already holds the tracker lock (state CLI)
            return action(store, key)
        with self.locked(), self._store() as own:
            return action(own, key)

    def _record(self, store, key):
        record = store.get(key)
        if not record or record.get('tracker') != self.identity:
            raise ReconciliationRequired(f'No existe la operación {key} en el journal de este tracker.')
        return record

    def _copies(self, record):
        """Evidence of the journaled bytes and, after a failed reissue, of the originally lost ones."""
        data = self.read_bytes()
        copies, partial = evidence(data, record)
        if record.get('lost_evidence'):
            more, cut = evidence(data, record['lost_evidence'])
            copies, partial = copies + more, partial or cut
        return copies, partial

    def acknowledge(self, op_key, store=None):
        """Register that a human reviewed a lost/uncertain append. Changes neither its state nor the blocking."""
        def action(store, key):
            record = self._record(store, key)
            if _legacy_ack(record):
                raise ReconciliationRequired(f'{key} se reconoció con el modelo anterior; verifica su evidencia con '
                                             + tracker_command('reconcile', key, self.scope) + '.')
            if record.get('state') not in INCIDENT:
                raise ReconciliationRequired(f'{key} está {record.get("state")}: no hay incidencia que reconocer.')
            if record.get('acknowledged'):
                return record
            record = {**record, 'acknowledged': time.time(), 'acknowledged_state': record['state'],
                      'history': _history(record, 'acknowledged')}
            store.put(key, record)
            return record
        return self._with_lock(store, action, op_key)

    def reconcile(self, op_key, store=None):
        """Re-check the evidence of one append under the lock. A complete copy -> `done` (verified_present);
        a truncated copy -> `uncertain`; nothing -> `lost`. Never writes the tracker."""
        def action(store, key):
            self._recover(store, raise_problems=False)
            record = self._record(store, key)
            state, legacy = record.get('state'), _legacy_ack(record)
            if state not in INCIDENT and not legacy:
                if state != 'done' or locate(self.read_bytes(), record, start=0)[0] == 'present':
                    return {'op': key, 'outcome': 'no_incident', 'state': state}
                record = self._finish(store, key, record, 'lost', reason='missing_from_tracker', detected=time.time())
            if legacy:      # the earlier incident survives only as the pre-E1.1 fields: no delivery proof
                record = {**{k: v for k, v in record.items() if k != 'acknowledged'}, 'state': 'lost',
                          'history': _history(record, 'legacy_acknowledgement', acknowledged=record['acknowledged'])}
            data = self.read_bytes()
            own, partial = evidence(data, record)
            lost = record.get('lost_evidence')
            original, cut = evidence(data, lost) if lost else (0, False)
            copies, partial = own + original, partial or cut
            if copies:
                # Verified against the bytes actually found: the journaled ones, or the originally lost ones.
                found = record if own else {**record, **lost}
                self._finish(store, key, found, 'done', event='reconciled_present', note={'copies': copies},
                             resolution={'kind': 'verified_present', 'at': time.time()})
                return {'op': key, 'outcome': 'present', 'state': 'done', 'copies': copies}
            outcome, target = ('partial', 'uncertain') if partial else ('absent', 'lost')
            if record.get('state') != target or legacy:
                record = self._finish(store, key, record, target, event=f'reconciled_{outcome}',
                                      reason='partial_copy' if partial else 'verified_absent')
            else:
                record = {**record, 'history': _history(record, f'reconciled_{outcome}')}
                store.put(key, record)
            return {'op': key, 'outcome': outcome, 'state': target, 'copies': 0,
                    'acknowledged': bool(record.get('acknowledged'))}
        return self._with_lock(store, action, op_key)

    def _release(self, store, key, kind):
        record = self._record(store, key)
        if record.get('state') != 'lost' or _legacy_ack(record):
            raise ReconciliationRequired(f'{key} está {record.get("state")}: solo una pérdida verificada admite esta '
                                         'resolución. Ejecuta antes ' + tracker_command('reconcile', key, self.scope) + '.')
        if not record.get('acknowledged'):
            raise ReconciliationRequired(f'{key} no está reconocida: inspecciona el tracker y ejecuta antes '
                                         + tracker_command('acknowledge', key, self.scope) + '.')
        copies, partial = self._copies(record)
        if copies or partial:
            raise ReconciliationRequired(f'{key} tiene {"una copia" if copies else "un fragmento"} en el tracker: no '
                                         'se autoriza nada. Ejecuta ' + tracker_command('reconcile', key, self.scope) + '.')
        if resolution_kind(record) == kind:
            return record
        record = {**record, 'resolution': {'kind': kind, 'at': time.time(), 'verified_absent': True},
                  'history': _history(record, kind, previous_resolution=record.get('resolution'))}
        index = self._index(store)
        index['problems'] = [k for k in index['problems'] if k != key]
        self._save(store, key, record, index)
        return record

    def authorize_reissue(self, op_key, store=None):
        """Acknowledged + lost + verified absent: the producer may write this op_id once more (auditable)."""
        return self._with_lock(store, lambda store, key: self._release(store, key, 'reissue_authorized'), op_key)

    def accept_loss(self, op_key, store=None):
        """Acknowledged + lost + verified absent: close the incident; the op_id is never written again."""
        return self._with_lock(store, lambda store, key: self._release(store, key, 'loss_accepted'), op_key)

    # ----------------------------------------------------------------- writing
    def append(self, text, *, op_id=None, source='python', precondition=None):
        """Append `text` as complete lines. Idempotent per op_id: a `done` op whose bytes are still in the tracker
        is not written again (replayed). A lost/uncertain op is never written again unless a human authorized one
        reissue; then the body may differ (e.g. a new timestamp) and the lost bytes must still be absent.

        `precondition(data: bytes) -> str | None` runs under the lock; a message aborts without writing.
        """
        op_id = op_id or uuid.uuid4().hex
        if not _OP_ID.match(op_id):
            raise ValueError('op_id must match [A-Za-z0-9:_.-]{1,128}.')
        body = (text if text.endswith('\n') else text + '\n').encode('utf-8')
        key = JOURNAL + op_id
        with self.locked(), self._store() as store:
            self._recover(store)
            self._verify(store, self.grace)
            existing = store.get(key)
            data = self.read_bytes()
            carry = {}
            if existing:
                if existing.get('tracker') != self.identity:
                    raise ReconciliationRequired(f'La operación {op_id} ya existe para otro tracker.')
                state, kind = existing['state'], resolution_kind(existing)
                if kind == 'reissue_authorized' and state in ('lost', 'not_written'):
                    lost = existing.get('lost_evidence') or {k: existing[k] for k in _FINGERPRINT}
                    copies, partial = evidence(data, lost)
                    if copies:
                        # The lost bytes came back: they are the delivery; writing again would leave two copies.
                        self._finish(store, key, {**existing, **lost}, 'done', event='original_found_before_reissue',
                                     resolution={**existing['resolution'], 'kind': 'verified_present', 'at': time.time()})
                        return AppendResult(op_id, lost['offset'], lost['length'], True)
                    if partial:
                        self._finish(store, key, existing, 'uncertain', reason='partial_copy_before_reissue')
                        self._raise_problems([key])
                    carry = {**{k: existing[k] for k in _HUMAN if k in existing}, 'lost_evidence': lost,
                             'history': _history(existing, 'reissue', previous={k: existing.get(k) for k in _EVIDENCE})}
                elif kind == 'loss_accepted':
                    raise TrackerIntegrityError(
                        f'La operación {op_id} se perdió y su pérdida se cerró explícitamente: no se reemite. Para '
                        'reemitirla una vez: ' + tracker_command('authorize-reissue', key, self.scope) + '.', [key])
                elif state in INCIDENT or state == 'in_flight':
                    self._raise_problems([key])
                elif state == 'done':
                    if locate(data, existing, start=0)[0] != 'present':
                        # Older than the verification window, or acknowledged with the pre-E1.1 model: never a replay.
                        self._finish(store, key, existing, 'lost', reason='missing_on_replay', detected=time.time())
                        self._raise_problems([key])
                    if existing.get('body_sha256') != _sha(body):
                        raise ReconciliationRequired(f'La operación {op_id} ya existe con otro contenido.')
                    return AppendResult(op_id, existing['offset'], existing['length'], True)
                elif existing.get('body_sha256') != _sha(body):
                    raise ReconciliationRequired(f'La operación {op_id} ya existe con otro contenido.')
            if precondition:
                failure = precondition(data)
                if failure:
                    raise TrackerConflict(failure)
            payload = (b'\n' if data and not data.endswith(b'\n') else b'') + body
            record = {**carry, 'state': 'in_flight', 'op_id': op_id, 'source': source, 'tracker': self.identity,
                      'offset': len(data), 'journaled_offset': len(data), 'body_sha256': _sha(body),
                      **_fingerprint(payload), 'attempt': (existing or {}).get('attempt', 0) + 1, 'time': time.time()}
            index = self._index(store)
            index['pending'] = [k for k in index['pending'] if k != key] + [key]
            self._save(store, key, record, index)
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open('ab') as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            except BaseException:
                self._recover_one(store, key, record)
                raise
            status, position = locate(self.read_bytes(), record)
            if status != 'present':
                self._finish(store, key, record, 'uncertain', reason='readback_mismatch')
                self._raise_problems([key])
            self._finish(store, key, {**record, 'offset': position}, 'done', event='reissued' if carry else None)
            return AppendResult(op_id, position, len(payload), reissued=bool(carry))

    def _recover_one(self, store, key, record):
        try:
            status, position = locate(self.read_bytes(), record)
            if status == 'present':
                self._finish(store, key, {**record, 'offset': position}, 'done')
            elif status == 'partial':
                self._finish(store, key, record, 'uncertain', reason='partial_write')
            else:
                self._finish(store, key, record, 'not_written')
        except Exception:
            pass  # the record stays in_flight and is resolved by the next _recover()

    def replace_for_tests(self, content):
        """Rewrite the whole tracker under the lock. Test fixtures only: production code never rewrites it."""
        with self.locked():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_bytes(content.encode('utf-8'))
