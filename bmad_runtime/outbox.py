"""Fase 4F-E5: outbox durable para las respuestas de los agentes (opt-in con `ai.outbox.mode`; por defecto `direct`).

Modos:
- direct (por defecto): los agentes escriben su bloque en el tracker, como antes de E5.
- both (transición): cada despacho fija y persiste su canal: outbox para los agentes de `ai.outbox.agents`, direct
  para el resto. Una respuesta por el canal no asignado, o por los dos, nunca se acepta en silencio.
- outbox: todo agente interactivo publica su bloque en el outbox y el watcher es el único que lo escribe en el tracker.
El canal es un atributo del despacho: cambiar de modo y reiniciar no reinterpreta los despachos existentes.

Por despacho el watcher persiste `outbox:<event_id>:<attempt>` ANTES de enviar la tarea: ruta asignada
(`<BMAD_HANDOFFS>/outbox/<event24>-<attempt>.md`), agente, autores de bloque admitidos, proyecto y un nonce. El
agente publica un único archivo con exactamente:

    <!-- BMAD-OUTBOX v1 event_id=<64 hex> attempt=<n> agent=<rol> project=<id> nonce=<32 hex> -->
    ### [DD-MM-YYYY] <Autor del rol>
    - **Hora:** ...
    <!-- BMAD-OUTBOX-END nonce=<32 hex> -->

Publicación: la marca final con el nonce del despacho es la confirmación verificable de que el archivo está completo;
sin ella el archivo está `writing` y nunca se lee como respuesta. Quien pueda, publica con rename atómico
(`<archivo>.tmp` -> `<archivo>`); los temporales y los archivos ocultos no se leen. Con la marca presente el contenido
debe repetirse idéntico tras `settle_seconds` antes de validarse.

Estados: expected -> writing -> ready -> validating -> ingesting -> confirmed | rejected | reconcile_required.
Recibido (ready), validado (ingesting: intención persistida con el bloque exacto), incorporado (journal de
TrackerWriter `done` con sus bytes presentes) y handoff confirmado (queued `confirmado` + outbox `confirmed` en una
sola transacción SQLite) son hitos distintos. La identidad es la del despacho persistido (event_id + attempt), nunca
el hash del contenido ni lo que declare el archivo: el rol autorizado sale del registro del watcher. La ingesta usa
solo TrackerWriter con op_id `outbox:<event_id>:<attempt>` (idempotente y recuperable tras una caída entre el tracker
y SQLite); una pérdida o una escritura incierta nunca se repara aquí.

Rechazos e incertidumbres dejan un bloque WATCHER con @HUMANO: y retienen los despachos hasta que un humano los
reconoce o resuelve (`python -m bmad_runtime.outbox`). Reconocer no es entregar: el handoff sigue sin confirmar. Nada
se borra del outbox: los archivos son evidencia.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time

from .config import TRACKER_AUTHORS
from .errors import ConfigurationError, ReconciliationRequired
from .state import ProjectLock, StateStore

MODES = ('direct', 'both', 'outbox')
PREFIX = 'outbox:'
ORPHAN_PREFIX = 'outbox_orphan:'
NOTICE_PREFIX = 'outbox-notice-'
LOCK = 'outbox'
OBSERVING = ('expected', 'writing', 'ready')
ACTIVE = (*OBSERVING, 'validating', 'ingesting')
INCIDENT_STATES = ('rejected', 'reconcile_required')
STATES = (*ACTIVE, 'confirmed', *INCIDENT_STATES)
# The task never reached the agent: nothing to review, no notice and no hold.
SILENT_REASONS = ('dispatch_not_delivered',)
DEFAULT_MAX_BYTES = 65536
DEFAULT_SETTLE_SECONDS = 2
HISTORY_LIMIT = 50

# Macros that only one role may emit. Mirrors the current contracts (constitution, PM, Code Review, SA); it grants
# nothing new. No agent answers /speckit.clarify: that is the human's reply.
MACRO_AUTHORITY = {
    'GITOPS-BRANCH-CREATE': ('product-manager',),
    'GITOPS-MERGE-CLOSE': ('code-review',),
    'SDD-FREEZE': ('solutions-architect',),
    'SPECKIT-CLARIFY': (),
    # Fase D starts from QA Tech's @DEV-BACK/@DEV-FRONT orders; its contract forbids invoking Spec Kit directly.
    'SPEC-KIT': (),
}
_MACROS = tuple((name, re.compile(pattern, re.IGNORECASE)) for name, pattern in (
    ('GITOPS-BRANCH-CREATE', r'@WATCHER:\s*GITOPS-BRANCH-CREATE'),
    ('GITOPS-MERGE-CLOSE', r'@WATCHER:\s*GITOPS-MERGE-CLOSE'),
    ('SDD-FREEZE', r'@WATCHER:\s*SDD-FREEZE'),
    ('SPECKIT-CLARIFY', r'@WATCHER:\s*/speckit\.clarify'),
    ('SPEC-KIT', r'@SPEC-KIT:')))

_EVENT = re.compile(r'[0-9a-f]{64}')
BEGIN = re.compile(r'^<!-- BMAD-OUTBOX v1 event_id=([0-9a-f]{64}) attempt=([1-9][0-9]{0,5}) agent=([a-z][a-z-]{1,40}) '
                   r'project=([A-Za-z0-9][A-Za-z0-9_-]{0,63}) nonce=([0-9a-f]{32}) -->$')
END = re.compile(r'^<!-- BMAD-OUTBOX-END nonce=([0-9a-f]{32}) -->$')
_END_BYTES = re.compile(rb'<!-- BMAD-OUTBOX-END nonce=[0-9a-f]{32} -->\s*\Z')
_HEADER = re.compile(r'^### \[(\d{2}-\d{2}-\d{4})\] (\S.*)$')
_AUTHORS = re.compile(r'^###\s+\[[^\]]+\]\s+(.+)$', re.MULTILINE)     # workflow.autores_en_tracker
_FIELD = re.compile(r'^\s*-\s+\*\*([^*\n]+?):\*\*')
_CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_ORPHAN_NAME = re.compile(r'([0-9a-f]{24})-([1-9][0-9]{0,5})\.md')
_REPARSE = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


# ------------------------------------------------------------------------------------------------- policy
def policy_from_config(value):
    """`ai.outbox`: {"mode": direct|both|outbox, "agents": [...] (only both), "max_bytes", "settle_seconds"}."""
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - {'mode', 'agents', 'max_bytes', 'settle_seconds'}:
        raise ConfigurationError('ai.outbox accepts only mode, agents, max_bytes and settle_seconds.')
    mode = value.get('mode', 'direct')
    if mode not in MODES:
        raise ConfigurationError('ai.outbox.mode must be direct, both or outbox.')
    agents = value.get('agents', [])
    if not isinstance(agents, list) or any(not isinstance(item, str) for item in agents) or \
            len(set(agents)) != len(agents):
        raise ConfigurationError('ai.outbox.agents must be a list of distinct agent identifiers.')
    unknown = set(agents) - set(TRACKER_AUTHORS)
    if unknown:
        raise ConfigurationError(f'ai.outbox.agents accepts only interactive agents: {sorted(unknown)}')
    if agents and mode != 'both':
        raise ConfigurationError('ai.outbox.agents applies only to mode both; outbox migrates every interactive agent.')
    max_bytes = value.get('max_bytes', DEFAULT_MAX_BYTES)
    if type(max_bytes) is not int or not 1024 <= max_bytes <= 1_048_576:
        raise ConfigurationError('ai.outbox.max_bytes must be an integer between 1024 and 1048576.')
    settle = value.get('settle_seconds', DEFAULT_SETTLE_SECONDS)
    if type(settle) is not int or not 0 <= settle <= 60:
        raise ConfigurationError('ai.outbox.settle_seconds must be an integer between 0 and 60.')
    return {'mode': mode, 'agents': sorted(agents), 'max_bytes': max_bytes, 'settle_seconds': settle}


def channel_for(policy, agent):
    """Channel assigned to a new dispatch: 'outbox' or 'direct'. Agents without a block author are always direct."""
    policy = policy or {}
    if agent not in TRACKER_AUTHORS:
        return 'direct'
    mode = policy.get('mode', 'direct')
    return 'outbox' if mode == 'outbox' or (mode == 'both' and agent in policy.get('agents', ())) else 'direct'


def record_key(event_id, attempt):
    return f'{PREFIX}{event_id}:{int(attempt)}'


def op_id_for(event_id, attempt):
    return f'outbox:{event_id}:{int(attempt)}'


def file_name(event_id, attempt):
    return f'{event_id[:24]}-{int(attempt)}.md'


def scope_arguments(context):
    return '' if context.legacy else f' --workspace "{context.workspace_root}" --project {context.project_id}'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _history(record, entry):
    return [*(record.get('history') or [])[-(HISTORY_LIMIT - 1):], entry]


# ------------------------------------------------------------------------------------------------- filesystem
def outbox_dir(context):
    return context.handoffs_dir / 'outbox'


def _is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & _REPARSE)


def safe_directory(context, create=False):
    """The project's outbox directory, or None when absent. Every component under the workspace must be a real
    directory (no symlink or junction): a link could make the watcher read outside the authorized workspace."""
    directory = outbox_dir(context)
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    current = context.workspace_root
    for part in directory.relative_to(context.workspace_root).parts:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return None
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise ReconciliationRequired(f'El outbox del proyecto atraviesa un enlace o un archivo ({current}); no se '
                                         'lee ninguna respuesta hasta corregirlo.')
    if os.path.normcase(os.path.realpath(directory)) != os.path.normcase(str(directory)):
        raise ReconciliationRequired(f'El outbox del proyecto resuelve fuera de su ruta ({directory}); no se lee nada.')
    return directory


def read_delivery(path, limit):
    """(status, reason, data): absent | busy | invalid (with reason) | data. Bounded read, never follows links."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return 'absent', None, None
    if _is_link(info):
        return 'invalid', 'symlink', None
    if not stat.S_ISREG(info.st_mode):
        return 'invalid', 'not_regular_file', None
    if info.st_size > limit:
        return 'invalid', 'too_large', None
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return 'absent', None, None
    except OSError:
        return 'busy', None, None             # the writer still holds it (Windows sharing): read it later
    with os.fdopen(descriptor, 'rb') as handle:
        opened = os.fstat(handle.fileno())
        if info.st_ino and opened.st_ino and (opened.st_ino, opened.st_dev) != (info.st_ino, info.st_dev):
            return 'busy', None, None         # replaced between lstat and open (e.g. an atomic publication)
        data = handle.read(limit + 1)
    if len(data) > limit:
        return 'invalid', 'too_large', None
    return 'data', None, data


def complete(data):
    """Explicit publication protocol: the file ends with a whole end marker line."""
    return bool(data) and bool(_END_BYTES.search(data))


# ------------------------------------------------------------------------------------------------- contract
def begin_marker(record):
    return (f'<!-- BMAD-OUTBOX v1 event_id={record["event_id"]} attempt={record["attempt"]} agent={record["agent"]} '
            f'project={record["project_id"]} nonce={record["nonce"]} -->')


def end_marker(record):
    return f'<!-- BMAD-OUTBOX-END nonce={record["nonce"]} -->'


def task_rule(record):
    """Output contract of one outbox dispatch, written into its task file (replaces the tracker rule there)."""
    authors = ' o '.join(f'"{name}"' for name in record['authors'])
    return ('CANAL DE SALIDA: OUTBOX (en esta tarea reemplaza la regla REGISTRO EN EL TRACKER). No escribas en '
            f'BMAD_TRACKER. Publica tu resultado como un único bloque tracker-logger en el archivo nuevo {record["path"]} '
            '(relativo a WORKSPACE_ROOT), creado con tu herramienta de edición, con exactamente estas líneas en este '
            f'orden:\n{begin_marker(record)}\n### [DD-MM-YYYY] {record["authors"][0]}\n'
            '<campos de tu bloque: Hora, Artefacto generado, Estado, Puntos Abiertos y Handoff>\n'
            f'{end_marker(record)}\n'
            'Copia las dos marcas tal cual. Escribe la marca final solo con el bloque completo: es tu confirmación de '
            'publicación; después no edites el archivo. Si ese archivo ya existe, tu entrega ya está publicada: no lo '
            'reescribas ni crees otro. Si puedes mover archivos sin shell (p. ej. apply_patch), '
            f'escribe antes {record["path"]}.tmp y renómbralo a la ruta final. Un solo bloque, con autor {authors}, '
            'y solo las macros que tu rol tiene autorizadas. El watcher valida el archivo, lo incorpora al tracker y '
            'confirma el handoff; un bloque tuyo escrito en el tracker, otro autor o un segundo bloque invalidan la '
            'entrega.\n')


def validate(data, record):
    """(reason, None) when the delivery is invalid, (None, block text) when it may be appended to the tracker.

    Identity and role come from the persisted dispatch (`record`); the file only has to agree with it."""
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return 'invalid_utf8', None
    if _CONTROL.search(text):
        return 'control_characters', None
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    content = [index for index, line in enumerate(lines) if line.strip()]
    if len(content) < 3:
        return 'incomplete_structure', None
    begin = BEGIN.match(lines[content[0]].strip())
    if not begin:
        return 'missing_begin_marker', None
    event_id, attempt, agent, project, nonce = begin.groups()
    if project != record['project_id']:
        return 'other_project', None
    if (event_id, int(attempt)) != (record['event_id'], record['attempt']):
        return 'identity_mismatch', None
    if agent != record['agent']:
        return 'role_mismatch', None
    if not secrets.compare_digest(nonce, record['nonce']):
        return 'nonce_mismatch', None
    end = END.match(lines[content[-1]].strip())
    if not end:
        return 'missing_end_marker', None
    if not secrets.compare_digest(end.group(1), record['nonce']):
        return 'nonce_mismatch', None
    body = [line.rstrip() for line in lines[content[0] + 1:content[-1]]]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if any('BMAD-OUTBOX' in line or '<!-- BMAD-' in line for line in body):
        return 'embedded_marker', None
    if not body:
        return 'empty_block', None
    header = _HEADER.match(body[0])
    if not header:
        return 'missing_header', None
    try:
        datetime.strptime(header.group(1), '%d-%m-%Y')
    except ValueError:
        return 'invalid_header_date', None
    author = header.group(2).strip()
    if re.search(r'HUMANO|WATCHER', author, re.IGNORECASE):
        return 'forged_author', None
    if not any(author.lower().startswith(name.lower()) for name in record['authors']):
        return 'role_mismatch', None
    if any('###' in line for line in body[1:]):
        return 'multiple_blocks', None
    fields = {re.sub(r'^\W+', '', match.group(1)).strip().lower() for match in map(_FIELD.match, body) if match}
    if 'hora' not in fields:
        return 'missing_field_hora', None
    if 'handoff' not in fields and not any(line.lstrip().startswith('@') for line in body[1:]):
        return 'missing_handoff', None
    for name, pattern in _MACROS:
        if record['agent'] not in MACRO_AUTHORITY[name] and any(pattern.search(line) for line in body):
            return f'unauthorized_macro:{name}', None
    return None, '\n' + '\n'.join(body) + '\n'


def block_index(data, offset):
    """Index (in workflow.autores_en_tracker order) of the block appended at byte `offset`."""
    return len(_AUTHORS.findall(data[:offset].decode('utf-8', errors='replace')))


# ------------------------------------------------------------------------------------------------- records
def expect(store, context, *, event_id, attempt, agent, policy, now=None):
    """Persist the expected delivery of a dispatch before its task is sent; idempotent per (event, attempt)."""
    if agent not in TRACKER_AUTHORS:
        raise ConfigurationError(f'{agent} has no tracker block author; it cannot use the outbox.')
    if not _EVENT.fullmatch(event_id or ''):
        raise ConfigurationError('Outbox dispatches need a 64-hex event id.')
    key = record_key(event_id, attempt)
    existing = store.get(key)
    if existing:
        return existing
    directory = safe_directory(context, create=True)
    path = directory / file_name(event_id, attempt)
    if os.path.lexists(path):
        raise ReconciliationRequired(f'El outbox ya contiene {path.name} antes del despacho; nunca se sobrescribe ni se '
                                     'lee como respuesta. Revísalo antes de continuar.')
    try:
        offset = context.tracker_path.stat().st_size
    except FileNotFoundError:
        offset = 0
    now = time.time() if now is None else now
    record = {'key': key, 'state': 'expected', 'channel': 'outbox', 'event_id': event_id, 'attempt': int(attempt),
              'agent': agent, 'authors': list(TRACKER_AUTHORS[agent]), 'project_id': context.project_id,
              'workspace': str(context.workspace_root), 'path': path.relative_to(context.workspace_root).as_posix(),
              'nonce': secrets.token_hex(16), 'dispatch': 'dispatch:' + event_id, 'queued': 'queued:' + event_id,
              'op_id': op_id_for(event_id, attempt), 'tracker_offset': offset,
              'max_bytes': (policy or {}).get('max_bytes', DEFAULT_MAX_BYTES),
              'settle_seconds': (policy or {}).get('settle_seconds', DEFAULT_SETTLE_SECONDS),
              'created': now, 'updated': now, 'history': [{'at': now, 'to': 'expected'}]}
    store.put(key, record)
    return record


def abandon(store, key, reason='dispatch_not_delivered'):
    """The task never reached the agent: close its expected delivery (silent, nothing to review)."""
    record = store.get(key)
    if record and record.get('state') == 'expected':
        now = time.time()
        store.put(key, {**record, 'state': 'rejected', 'reason': reason, 'updated': now,
                        'history': _history(record, {'at': now, 'from': 'expected', 'to': 'rejected', 'reason': reason})})


def for_dispatch(store, event_id):
    """Outbox record of the dispatch of `event_id`, or None when that dispatch uses the direct channel."""
    dispatch = store.get('dispatch:' + str(event_id)) or {}
    if dispatch.get('channel') != 'outbox' or not dispatch.get('outbox'):
        return None
    return store.get(dispatch['outbox'])


def escalate(store, key, reason):
    """The vigilante gave up waiting (agent finished without a published response). Never confirms anything."""
    record = store.get(key)
    if record and record.get('state') in OBSERVING and not record.get('escalated'):
        now = time.time()
        store.put(key, {**record, 'escalated': {'reason': reason, 'at': now}, 'updated': now,
                        'history': _history(record, {'at': now, 'event': 'escalated', 'reason': reason})})


def _rows(store, prefix):
    rows = store.db.execute('SELECT id,data FROM records WHERE id >= ? AND id < ?', (prefix, prefix[:-1] + ';'))
    return [(key, json.loads(raw)) for key, raw in rows]


def records(store):
    return _rows(store, PREFIX)


def orphans(store):
    return _rows(store, ORPHAN_PREFIX)


def is_incident(record):
    """Unresolved rejection or uncertainty: holds every dispatch until a human acknowledges/resolves it."""
    state = record.get('state')
    if state == 'reconcile_required':
        return True
    return state == 'rejected' and record.get('reason') not in SILENT_REASONS and not record.get('acknowledged')


def incidents(store):
    return [(key, record) for key, record in records(store) + orphans(store) if is_incident(record)]


_ROLE_REASONS = ('role_mismatch', 'forged_author')
_DUPLICATE_REASONS = ('direct_and_outbox', 'already_confirmed', 'wrong_channel', 'late_after_escalation')


def describe(record):
    """Operator category of an outbox record (pending, incomplete, invalid, wrong role, duplicate, confirmed, ...)."""
    state, reason = record.get('state'), str(record.get('reason') or '')
    if state == 'expected':
        return 'no_response' if record.get('escalated') else 'pending_response'
    if state == 'writing':
        return 'incomplete_file'
    if state in ('ready', 'validating'):
        return 'received'
    if state == 'ingesting':
        return 'ingesting'
    if state == 'confirmed':
        return 'confirmed'
    if state == 'rejected':
        if reason in SILENT_REASONS:
            return 'not_delivered'
        if reason in _ROLE_REASONS or reason.startswith('unauthorized_macro'):
            return 'wrong_role'
        if reason in ('other_project', 'unknown_identity'):
            return 'foreign_or_unknown'
        if reason in _DUPLICATE_REASONS or reason == 'stale_attempt':
            return 'duplicate_delivery'
        return 'invalid_file'
    return 'duplicate_delivery' if reason in _DUPLICATE_REASONS else 'uncertain_delivery'


def notice_text(record, scope='', now=None):
    """WATCHER block with @HUMANO: for a rejected/uncertain delivery; it never carries a macro or another token."""
    when = datetime.fromtimestamp(time.time() if now is None else now)
    who = record.get('agent') or 'un agente desconocido'
    where = record.get('path') or f'outbox/{record.get("name")}'
    outcome = 'rechazada' if record['state'] == 'rejected' else 'pendiente de reconciliación'
    return (f"\n### [{when:%d-%m-%Y}] WATCHER\n- **Hora:** {when:%H:%M:%S}\n"
            f"- **Mensaje:** 🛑 OUTBOX: la respuesta de {who} en {where} quedó {outcome} ({record['reason']}). No se "
            "incorporó al tracker, no se confirmó el handoff y no se despachó nada de ella.\n"
            f"- **Handoff:** @HUMANO: Revisa la evidencia con python -m bmad_runtime.outbox{scope} --status y, con el "
            f"watcher detenido, resuelve la entrega {record['key']}. Reconocerla no la entrega ni la reintenta.\n")


# ------------------------------------------------------------------------------------------------- ingestion
class OutboxIngestor:
    """Watcher side: observes the expected deliveries, validates them and appends them with TrackerWriter."""

    def __init__(self, context, store, writer_factory, *, clock=time.time, scope=None, scan_orphans=True):
        self.context, self.store = context, store
        self.writer_factory = writer_factory
        self.clock = clock
        self.scope = scope_arguments(context) if scope is None else scope
        # direct mode without outbox history keeps the pre-E5 behaviour: files there are not audited.
        self.scan_orphans = scan_orphans

    @classmethod
    def for_runtime(cls, rt, **options):
        from .tracker_io import TrackerWriter
        return cls(rt.context, rt.state, lambda: TrackerWriter.for_runtime(rt), **options)

    def pending(self):
        return [record for _, _, record in sorted((record.get('created', 0), key, record)
                                                  for key, record in records(self.store)
                                                  if record.get('state') in ACTIVE)]

    def tick(self, on_confirmed=None, on_problem=None):
        """One pass under the project `outbox` lock; returns the records that reached a final state now."""
        if not self.scan_orphans and not records(self.store) and not orphans(self.store):
            return []                         # direct mode, no outbox history: nothing to do, nothing created
        lock = ProjectLock(self.context, LOCK)
        if not lock.acquire():
            return []
        try:
            finished = []
            for record in self.pending():
                record = self._step(self.store.get(record['key']) or record)
                if record['state'] == 'confirmed':
                    finished.append(record)
                    if on_confirmed:
                        on_confirmed(record)
                elif is_incident(record):
                    finished.append(record)
                    if on_problem:
                        on_problem(record)
            if self.scan_orphans or records(self.store):
                finished += self._scan_orphans()
            self.notify_pending()
            return finished
        finally:
            lock.release()

    # ---------------------------------------------------------------------------------------- transitions
    def _put(self, record, state, event=None, extra_items=(), **fields):
        now = self.clock()
        entry = {'at': now, 'from': record.get('state'), 'to': state, **({'event': event} if event else {}),
                 **({'reason': fields['reason']} if 'reason' in fields else {})}
        changed = state != record.get('state') or event
        record = {**record, **fields, 'state': state, 'updated': now,
                  **({'history': _history(record, entry)} if changed else {})}
        self.store.put_many([(record['key'], record), *extra_items])
        return record

    def _incident(self, record, state, reason, **fields):
        """Rejection or uncertainty: notice persisted (pending) and handoff marked, in one transaction."""
        items = []
        queued = self.store.get(record['queued']) if record.get('queued') else None
        if queued and queued.get('stage') != 'confirmado':
            items.append((record['queued'], {**queued, 'stage': 'requiere_intervencion', 'failure': f'outbox:{reason}',
                                             'stages': {**queued.get('stages', {}),
                                                        'requiere_intervencion': self.clock()}}))
        notice = {'state': 'pending', 'op_id': NOTICE_PREFIX + _sha(record['key'].encode())[:32],
                  'text': notice_text({**record, 'state': state, 'reason': reason}, self.scope, self.clock())}
        return self._put(record, state, extra_items=items, reason=reason, notice=notice, **fields)

    def _step(self, record):
        if record['state'] in OBSERVING:
            record = self._observe(record)
        if record['state'] == 'validating':
            record = self._validate(record)
        if record['state'] == 'ingesting':
            record = self._ingest(record)
        return record

    def _path(self, record):
        directory = safe_directory(self.context)
        if directory is None:
            return None
        path = self.context.output(record['path'])
        if path.parent != directory or path.name != file_name(record['event_id'], record['attempt']):
            raise ReconciliationRequired(f'{record["key"]}: ruta asignada fuera del outbox del proyecto.')
        return path

    def _observe(self, record):
        path = self._path(record)
        if path is None:
            return record
        status, reason, data = read_delivery(path, record['max_bytes'])
        if status in ('absent', 'busy'):
            return record
        now = self.clock()
        if status == 'invalid':
            return self._incident(record, 'rejected', reason, received=now)
        if not complete(data):
            if record['state'] != 'writing' or record.get('size') != len(data):
                return self._put(record, 'writing', size=len(data), seen=now)
            return record
        digest = _sha(data)
        if record['state'] == 'ready' and record.get('sha256') == digest:
            if now - record['ready_at'] >= record['settle_seconds']:
                return self._put(record, 'validating', validating_at=now)
            return record
        record = self._put(record, 'ready', event='content_changed' if record['state'] == 'ready' else None,
                           sha256=digest, size=len(data), ready_at=now, received=record.get('received') or now)
        return self._put(record, 'validating', validating_at=now) if record['settle_seconds'] <= 0 else record

    def _authorization(self, record):
        """(state, reason) when the persisted dispatch does not authorize this delivery, else None."""
        dispatch = self.store.get(record['dispatch']) or {}
        if dispatch.get('agent_id') != record['agent'] or dispatch.get('channel') != 'outbox' or \
                dispatch.get('outbox') != record['key']:
            return 'rejected', 'dispatch_mismatch'
        if dispatch.get('attempt', 1) != record['attempt']:
            return 'rejected', 'stale_attempt'
        if dispatch.get('state') == 'not_delivered':
            return 'rejected', 'response_without_delivery'
        if dispatch.get('state') != 'done':
            return 'reconcile_required', 'dispatch_uncertain'
        queued = self.store.get(record['queued']) or {}
        if not queued:
            return 'rejected', 'unknown_handoff'
        if queued.get('acknowledged'):
            return 'reconcile_required', 'handoff_acknowledged'
        if queued.get('stage') == 'confirmado':
            return 'reconcile_required', 'already_confirmed'
        if record.get('escalated') or queued.get('stage') in ('fallido', 'requiere_intervencion'):
            return 'reconcile_required', 'late_after_escalation'
        return None

    def _direct_block(self, record, writer):
        """True when the agent also wrote a block straight into the tracker after the dispatch (both channels).

        Blocks this ingestor appended (any delivery, journaled `done`) are not the agent's direct writes."""
        data = writer.read_bytes()
        start = record['tracker_offset']
        if start > len(data):
            return True                       # tracker shrank since the dispatch: cannot correlate with certainty
        ingested = []
        for _, other in records(self.store):
            if other.get('state') in ('ingesting', 'confirmed', 'reconcile_required'):
                journal = writer.describe(other['op_id'])
                if journal and journal.get('state') == 'done':
                    ingested.append((journal['offset'], journal['offset'] + journal['length']))
        kept, cursor = [], start
        for begin, end in sorted(ingested):
            if end <= cursor:
                continue
            kept.append(data[cursor:max(begin, cursor)])
            cursor = max(cursor, end)
        kept.append(data[cursor:])
        segment = b''.join(kept).decode('utf-8', errors='replace')
        return any(any(author.strip().lower().startswith(name.lower()) for name in record['authors'])
                   for author in _AUTHORS.findall(segment))

    def _validate(self, record):
        denied = self._authorization(record)
        if denied:
            return self._incident(record, *denied)
        path = self._path(record)
        status, reason, data = read_delivery(path, record['max_bytes']) if path else ('absent', None, None)
        if status == 'invalid':
            return self._incident(record, 'rejected', reason)
        if status != 'data' or not complete(data) or _sha(data) != record['sha256']:
            # Changed or vanished after it looked complete: back to observation, nothing is read as a response.
            return self._put(record, 'writing', event='changed_before_validation')
        reason, block = validate(data, record)
        if reason:
            return self._incident(record, 'rejected', reason, validated_at=self.clock())
        if self._direct_block(record, self.writer_factory()):
            return self._incident(record, 'reconcile_required', 'direct_and_outbox')
        # Ingestion intent: the exact bytes and their operation id, persisted before touching the tracker.
        return self._put(record, 'ingesting', block=block, block_sha256=_sha(block.encode('utf-8')),
                         validated_at=self.clock())

    def _ingest(self, record):
        from .tracker_io import TrackerBusy, TrackerIntegrityError, resolution_kind
        writer = self.writer_factory()
        op_id = record['op_id']
        journal = writer.describe(op_id)
        status = writer.status(op_id)
        if journal and (status == 'unverified' or (status in ('lost', 'uncertain') and
                                                   resolution_kind(journal) != 'reissue_authorized')):
            return self._incident(record, 'reconcile_required', f'tracker_append_{status}')
        if status != 'done':
            denied = self._authorization(record)
            if denied:
                return self._incident(record, *denied)
            if self._direct_block(record, writer):
                return self._incident(record, 'reconcile_required', 'direct_and_outbox')
            try:
                writer.append(record['block'], op_id=op_id, source='outbox:' + record['agent'])
            except TrackerBusy:
                return record                 # retried on the next tick with the same op_id
            except TrackerIntegrityError:
                raise                         # an open tracker incident stops the watcher (TrackerWriter rule)
            except ReconciliationRequired:
                return self._incident(record, 'reconcile_required', 'tracker_op_conflict')
        if not writer.delivered(op_id):
            return self._incident(record, 'reconcile_required', 'tracker_block_missing')
        journal = writer.describe(op_id)
        return self._confirm(record, journal, block_index(writer.read_bytes(), journal['offset']))

    def _confirm(self, record, journal, index):
        queued = self.store.get(record['queued']) or {}
        if not queued:
            return self._incident(record, 'reconcile_required', 'unknown_handoff')
        if queued.get('stage') == 'confirmado' and queued.get('outbox') != record['key']:
            return self._incident(record, 'reconcile_required', 'already_confirmed')
        now = self.clock()
        items = []
        if queued.get('stage') != 'confirmado':
            # Same index the direct channel records: audit_blocks authorizes the appended block by it.
            items.append((record['queued'], {**queued, 'stage': 'confirmado', 'confirmed_block': index,
                                             'channel': 'outbox', 'outbox': record['key'],
                                             'stages': {**queued.get('stages', {}), 'confirmado': now}}))
        return self._put(record, 'confirmed', extra_items=items, delivered_offset=journal['offset'],
                         delivered_length=journal['length'], block_index=index, delivered_at=now, confirmed_at=now)

    # ---------------------------------------------------------------------------------------- orphans/notices
    def _scan_orphans(self):
        """Files without an expected delivery are never ingested; each one (and each new content) is an incident."""
        directory = safe_directory(self.context)
        if directory is None:
            return []
        # A file for an attempt that never reached its agent is not a response: it is audited as an orphan.
        known = {Path(record['path']).name for _, record in records(self.store)
                 if record.get('path') and record.get('reason') not in SILENT_REASONS}
        found = []
        with os.scandir(directory) as entries:
            names = sorted(entry.name for entry in entries)
        for name in names:
            if name.startswith('.') or name.endswith('.tmp') or name in known:
                continue
            status, reason, data = read_delivery(directory / name, DEFAULT_MAX_BYTES * 16)
            if status in ('absent', 'busy'):
                continue
            evidence = {'kind': reason or 'file', 'size': len(data) if data is not None else None,
                        'sha256': _sha(data) if data is not None else None}
            key = ORPHAN_PREFIX + _sha(name.encode('utf-8'))[:32]
            existing = self.store.get(key) or {}
            if existing and all(existing.get(field) == value for field, value in evidence.items()):
                continue
            base = {'key': key, 'name': name, 'state': 'detected', 'detected': self.clock(),
                    'history': existing.get('history', [])}
            found.append(self._incident(base, 'rejected', self._orphan_reason(name), **evidence))
        return found

    def _orphan_reason(self, name):
        match = _ORPHAN_NAME.fullmatch(name)
        if not match:
            return 'unknown_identity'
        prefix = 'dispatch:' + match.group(1)
        dispatches = [json.loads(raw) for _, raw in self.store.db.execute(
            'SELECT id,data FROM records WHERE id >= ? AND id < ?', (prefix, prefix + 'g'))]
        if not dispatches:
            return 'unknown_identity'
        return 'stale_attempt' if any(item.get('channel') == 'outbox' for item in dispatches) else 'wrong_channel'

    def notify_pending(self):
        """Append (once) the WATCHER notice of every incident; after a crash the same text and op_id are reissued."""
        from .tracker_io import TrackerBusy
        sent = 0
        for key, record in records(self.store) + orphans(self.store):
            notice = record.get('notice') or {}
            if notice.get('state') != 'pending':
                continue
            try:
                result = self.writer_factory().append(notice['text'], op_id=notice['op_id'], source='watcher')
            except TrackerBusy:
                return sent
            current = self.store.get(key) or record
            self.store.put(key, {**current, 'notice': {**notice, 'state': 'delivered', 'offset': result.offset,
                                                       'delivered_at': self.clock()}})
            sent += 1
        return sent


# ------------------------------------------------------------------------------------------------- operator
def acknowledge(store, key):
    """Record that a human reviewed a rejected delivery (or orphan file). It is never delivered nor retried."""
    record = store.get(key) if key.startswith((PREFIX, ORPHAN_PREFIX)) else None
    if not record:
        raise ReconciliationRequired(f'No existe la entrega {key}.')
    if record.get('state') != 'rejected':
        raise ReconciliationRequired(f'{key} está {record.get("state")}: solo una entrega rechazada se reconoce; una '
                                     'incierta se resuelve con --reject.')
    if record.get('acknowledged'):
        return record
    now = time.time()
    record = {**record, 'acknowledged': now, 'updated': now,
              'history': _history(record, {'at': now, 'event': 'acknowledged'})}
    store.put(key, record)
    return record


def reject(store, writer, key):
    """Close an uncertain delivery without ingesting it; only when its tracker operation was never delivered."""
    record = store.get(key) if key.startswith(PREFIX) else None
    if not record:
        raise ReconciliationRequired(f'No existe la entrega {key}.')
    if record.get('state') != 'reconcile_required':
        raise ReconciliationRequired(f'{key} está {record.get("state")}: --reject solo cierra una entrega pendiente de '
                                     'reconciliación.')
    if writer.status(record['op_id']) == 'done' or writer.delivered(record['op_id']):
        raise ReconciliationRequired(f'{key}: su bloque ya está en el tracker ({record["op_id"]}); no se puede declarar '
                                     'no entregado. Inspecciona el tracker y el journal antes de decidir.')
    now = time.time()
    record = {**record, 'state': 'rejected', 'acknowledged': now, 'updated': now,
              'resolution': {'kind': 'rejected_by_operator', 'at': now, 'previous_reason': record.get('reason')},
              'history': _history(record, {'at': now, 'from': 'reconcile_required', 'to': 'rejected',
                                           'event': 'rejected_by_operator'})}
    store.put(key, record)
    return record


def report(store):
    """Read-only operator view: every delivery with its category, orphans and open incidents."""
    def row(key, record):
        return {'key': key, 'state': record.get('state'), 'category': describe(record), 'reason': record.get('reason'),
                'agent': record.get('agent'), 'path': record.get('path') or record.get('name'),
                'acknowledged': bool(record.get('acknowledged')), 'escalated': bool(record.get('escalated')),
                'notice': (record.get('notice') or {}).get('state')}
    return {'deliveries': [row(key, record) for key, record in records(store)],
            'orphans': [row(key, record) for key, record in orphans(store)],
            'incidents': [key for key, _ in incidents(store)]}


# ------------------------------------------------------------------------------------------------- inspection (E5.1)
def publication_compatibility(config):
    """Outbox agents whose current permissions cannot publish the response file. Reported, never relaxed."""
    policy = config.data.get('outbox') or {}
    problems = []
    for agent in sorted(TRACKER_AUTHORS):
        if channel_for(policy, agent) != 'outbox':
            continue
        selection = config.resolve(agent=agent)
        options = selection.options or {}
        if selection.provider == 'codex' and options.get('sandbox') == 'read-only':
            issue = 'codex_read_only_sandbox'
        elif selection.provider == 'claude' and options.get('permission_mode') in ('plan', 'manual'):
            issue = 'claude_permission_' + options['permission_mode']
        elif selection.provider not in ('claude', 'codex'):
            issue = 'provider_not_verified_for_outbox'
        else:
            continue
        problems.append({'agent': agent, 'provider': selection.provider, 'issue': issue})
    return problems


def procedure(record, scope=''):
    """Human recovery procedure for one delivery. There is no authorized re-ingestion: see the E5.1 report."""
    key, state, reason = record.get('key'), record.get('state'), str(record.get('reason') or '')
    cli = f'python -m bmad_runtime.outbox{scope}'
    if state == 'expected':
        if record.get('escalated'):
            return ('Sin respuesta tras los recordatorios. Una publicación tardía queda en reconcile_required y no se '
                    'incorpora; para repetir la etapa, registra una nueva decisión humana en el tracker.')
        return f'Esperando la publicación del agente en {record.get("path")}.'
    if state == 'writing':
        return 'Archivo incompleto (sin marca final): nada se lee hasta que el agente lo termine.'
    if state in ('ready', 'validating', 'ingesting'):
        return 'En curso: el watcher lo completa de forma idempotente al reanudar.'
    if state == 'confirmed':
        return 'Incorporado al tracker y handoff confirmado.'
    if state == 'rejected':
        if record.get('acknowledged') or record.get('reason') in SILENT_REASONS:
            return 'Cerrada sin entrega. Para continuar la etapa, registra una nueva decisión humana en el tracker.'
        return (f'Revisa el archivo y, con el watcher detenido: {cli} --acknowledge {key} --confirm (registra la '
                'revisión; nunca entrega el bloque).')
    if reason.startswith('tracker_append') or reason == 'tracker_block_missing':
        op = 'tracker_append:' + str(record.get('op_id'))
        return (f'Resuelve primero el append (E1.1) con el watcher detenido: python -m bmad_runtime.state{scope} '
                f'--acknowledge {op} --confirm y --reconcile {op} --confirm (si reaparece completo queda done); si sigue '
                f'ausente, --accept-loss o --authorize-reissue. Si el bloque no quedó en el tracker: {cli} --reject '
                f'{key} --confirm.')
    if reason == 'direct_and_outbox':
        return ('El bloque directo del tracker es la respuesta registrada y una violación de protocolo: reconócela con '
                f'python -m bmad_runtime.state{scope} --acknowledge protocol_violation:<bloque> --confirm y cierra esta '
                f'entrega con {cli} --reject {key} --confirm.')
    return (f'Entrega no correlacionable con certeza ({reason}): inspecciona el panel y el archivo; si no debe '
            f'incorporarse, {cli} --reject {key} --confirm. Para repetir la etapa, una nueva decisión humana.')


def _blocks(text):
    """[(author, text)] of the tracker blocks in workflow.autores_en_tracker order."""
    found = list(_AUTHORS.finditer(text))
    return [(match.group(1).strip(), text[match.start():found[index + 1].start() if index + 1 < len(found)
                                          else len(text)]) for index, match in enumerate(found)]


def handoff_view(queued, blocks):
    """The five milestones of a handoff, from evidence: produced, incorporated, confirmed, human pending/decided."""
    index = queued.get('confirmed_block') if queued else None
    view = {'stage': (queued or {}).get('stage'), 'confirmed': (queued or {}).get('stage') == 'confirmado',
            'block_index': index, 'human': None}
    if isinstance(index, int) and 0 <= index < len(blocks):
        author, text = blocks[index]
        body = text.split('\n', 1)[1] if '\n' in text else ''
        if author.upper() != 'HUMANO' and '@HUMANO:' in body:
            decided = any(other.upper() == 'HUMANO' for other, _ in blocks[index + 1:])
            view['human'] = 'decision_received' if decided else 'pending'
        else:
            view['human'] = 'not_requested'
    return view


def blockers(context, store, text, scope=''):
    """Why the watcher holds dispatches now (read-only): every open incident with its recovery command."""
    from .tracker_io import is_open_incident
    from .watcher_service import maintenance_blocks, paused_for_human, protocol_violations
    found = [{'kind': 'outbox', 'key': key, 'reason': record.get('reason'), 'procedure': procedure(record, scope)}
             for key, record in incidents(store)]
    found += [{'kind': 'protocol_violation', 'key': key, 'reason': record.get('reason'),
               'procedure': f'python -m bmad_runtime.state{scope} --acknowledge {key} --confirm'}
              for key, record in protocol_violations(store)]
    for key, raw in store.db.execute("SELECT id,data FROM records WHERE id LIKE 'tracker_append:%'"):
        record = json.loads(raw)
        if is_open_incident(record):
            found.append({'kind': 'tracker_append', 'key': key, 'reason': record.get('state'),
                          'procedure': f'python -m bmad_runtime.state{scope} --reconcile {key} --confirm (E1.1)'})
    integrity = store.get('tracker_integrity')
    if integrity and integrity.get('state') != 'done':
        found.append({'kind': 'tracker_integrity', 'key': 'tracker_integrity', 'reason': integrity.get('reason'),
                      'procedure': f'python -m bmad_runtime.state{scope} --rebaseline-tracker --confirm (tras revisar)'})
    for agent, op in maintenance_blocks(store).items():
        found.append({'kind': 'maintenance', 'key': op, 'reason': agent,
                      'procedure': f'python -m bmad_runtime.maintenance{scope} --reconcile {agent} --confirm'})
    authority = store.get('hu_authority') or {}
    if authority.get('state') == 'reconcile_required':
        found.append({'kind': 'hu_lifecycle', 'key': 'hu_authority', 'reason': authority.get('reason'),
                      'procedure': f'python -m bmad_runtime.hu_enforcement{scope} --inspect'})
    for key, raw in store.db.execute("SELECT id,data FROM records WHERE id LIKE 'blocked_write:%'"):
        record = json.loads(raw)
        if record.get('state') == 'requiere_intervencion':
            found.append({'kind': 'blocked_write', 'key': key, 'reason': record.get('reason'),
                          'procedure': 'Revisa el bloque y responde como HUMANO; ninguna de sus líneas se ejecutó.'})
    if paused_for_human(text):
        found.append({'kind': 'human_pause', 'key': None, 'reason': 'awaiting_human_decision',
                      'procedure': 'Registra la decisión humana (Control Center o utils/approve_step.py).'})
    return found


def inspect(context, store, config=None):
    """Read-only evidence of every delivery: file, journal, tracker bytes, handoff milestones and procedure."""
    from .tracker_io import JOURNAL, _legacy_ack, locate, resolution_kind
    scope = scope_arguments(context)
    try:
        data = context.tracker_path.read_bytes()
    except FileNotFoundError:
        data = b''
    text = data.decode('utf-8', errors='replace')
    blocks = _blocks(text)
    policy = (config.data.get('outbox') or {}) if config else None
    rows = []
    for key, record in records(store):
        try:
            path = context.output(record['path'])
        except ConfigurationError:
            path = None
        status, problem, raw = (read_delivery(path, record.get('max_bytes', DEFAULT_MAX_BYTES)) if path is not None
                                else ('invalid', 'path_outside_workspace', None))
        digest = _sha(raw) if raw is not None else None
        journal = store.get(JOURNAL + record['op_id']) if record.get('op_id') else None
        in_tracker = locate(data, journal, start=0)[0] if journal else None
        findings = []
        if record.get('sha256') and status == 'absent':
            findings.append('evidence_missing')
        elif record.get('sha256') and digest and digest != record['sha256'] and record['state'] not in OBSERVING:
            findings.append('evidence_changed_after_receipt')
        if record['state'] == 'confirmed' and in_tracker != 'present':
            findings.append('delivered_then_lost')
        if journal and journal.get('acknowledged') and journal.get('state') != 'done':
            findings.append('acknowledged_not_delivered')
        if policy is not None and channel_for(policy, record['agent']) != 'outbox':
            findings.append('current_policy_is_direct_channel_kept')
        rows.append({
            'key': key, 'agent': record.get('agent'), 'state': record['state'], 'category': describe(record),
            'reason': record.get('reason'), 'path': record.get('path'),
            'file': {'status': 'present' if status == 'data' else status, 'problem': problem, 'sha256': digest,
                     'matches_received': digest == record.get('sha256') if digest and record.get('sha256') else None},
            'tracker': {'journal_state': ('unverified' if journal and _legacy_ack(journal)
                                          else (journal or {}).get('state')),
                        'resolution': resolution_kind(journal) if journal else None, 'bytes': in_tracker},
            'dispatch': {key_: (store.get(record['dispatch']) or {}).get(key_) for key_ in ('state', 'channel', 'attempt')},
            'handoff': handoff_view(store.get(record['queued']), blocks),
            'findings': findings, 'procedure': procedure(record, scope)})
    return {'deliveries': rows, 'orphans': report(store)['orphans'], 'blockers': blockers(context, store, text, scope),
            'compatibility': publication_compatibility(config) if config else None}


def main(argv=None):
    from .context import add_project_arguments, resolve_context
    from .state import project_lock
    parser = argparse.ArgumentParser(description='Outbox de respuestas de agentes (Fase 4F-E5): inspección y '
                                                 'reconciliación explícita; nunca ingiere, borra ni reintenta.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    add_project_arguments(parser)
    parser.add_argument('--config', type=Path, help='Configuración a comparar con la del watcher en ejecución.')
    parser.add_argument('--status', action='store_true', help='Entregas, categorías, incidencias y diferencias de '
                                                              'configuración (solo lectura).')
    parser.add_argument('--inspect', action='store_true', help='Evidencia completa por entrega (archivo, journal, bytes '
                                                               'en el tracker, hitos del handoff, procedimiento) y '
                                                               'motivos de bloqueo (solo lectura).')
    parser.add_argument('--acknowledge', metavar='KEY', help='Registrar la revisión de una entrega rechazada.')
    parser.add_argument('--reject', metavar='KEY', help='Cerrar sin ingerir una entrega pendiente de reconciliación.')
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    context = resolve_context(args.root, workspace=args.workspace, project=args.project, config_path=args.config)
    if args.acknowledge or args.reject:
        if not args.confirm:
            parser.error('--acknowledge/--reject require --confirm.')
        from .tracker_io import TrackerWriter
        # The watcher must be stopped: it is the only ingestor.
        with project_lock(context, 'watcher'), project_lock(context, LOCK):
            store = StateStore(context)
            try:
                try:
                    if args.acknowledge:
                        result = acknowledge(store, args.acknowledge)
                    else:
                        result = reject(store, TrackerWriter.for_context(context), args.reject)
                except ReconciliationRequired as exc:
                    parser.error(str(exc))
                print(json.dumps({'key': result['key'], 'state': result['state'], 'reason': result.get('reason'),
                                  'acknowledged': bool(result.get('acknowledged'))}, ensure_ascii=False))
            finally:
                store.close()
        return 0
    store = StateStore.open_readonly(context)
    if store is None:
        print(json.dumps({'deliveries': [], 'orphans': [], 'incidents': []}, ensure_ascii=False))
        return 0
    try:
        from .config import RuntimeConfig
        from .policy_audit import divergence
        try:
            config = RuntimeConfig.load(context.workspace_root, args.config, context)
        except Exception as exc:              # reported: an unreadable config never reads as "no difference"
            config, config_error = None, type(exc).__name__
        else:
            config_error = None
        if args.inspect:
            result = inspect(context, store, config)
        else:
            text = context.tracker_path.read_text(encoding='utf-8', errors='replace') \
                if context.tracker_path.exists() else ''
            result = {**report(store), 'blockers': blockers(context, store, text, scope_arguments(context)),
                      'compatibility': publication_compatibility(config) if config else None}
        result['config'] = divergence(context, store, config_path=args.config)
        if config_error:
            result['config']['local_error'] = config_error
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        store.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
