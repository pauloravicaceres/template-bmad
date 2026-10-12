"""Fase 4F-E5: outbox durable de respuestas de agentes (unidad, watcher con dobles, multiproceso y Git real)."""
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import textwrap
import time
from unittest.mock import Mock, patch

import pytest

from bmad_runtime import outbox, policy_audit, workflow
from bmad_runtime.commands import Result
from bmad_runtime.config import RuntimeConfig, TRACKER_AUTHORS
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ConfigurationError, DeliveryRejected, ReconciliationRequired
from bmad_runtime.outbox import OutboxIngestor
from bmad_runtime.providers import default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import TRACKER_RULE
from bmad_runtime.state import ProjectLock, StateStore, project_lock
from bmad_runtime.tracker_io import TrackerWriter
from bmad_runtime.watcher_service import read_tracker
from tests.test_hu_enforcement import ba_handoffs, branches, checkout_root, head, rejected_ops
from tests.test_hu_lifecycle import HU_A, HU_B, ROOT, git
from tests.test_tracker_integrity import FakeProvider
from tests.test_tracker_io import run_watcher
from tests.pane_doubles import ready_pane

POLICY = {'mode': 'outbox', 'agents': [], 'max_bytes': 4096, 'settle_seconds': 0}


class Crash(BaseException):
    """The process dies: no handler of the ingestor runs."""


class Clock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


# ------------------------------------------------------------------------------------------------ unit helpers
class Space:
    """Isolated multiworkspace project: tracker, SQLite and outbox under its own workspace."""

    def __init__(self, base, project_id='alpha', **policy):
        self.root = (base / project_id).resolve()
        self.root.mkdir(parents=True)
        self.context = ProjectContext(ROOT, self.root, project_id)
        self.context.tracker_path.parent.mkdir(parents=True)
        self.context.tracker_path.write_text('', encoding='utf-8')
        self.store = StateStore.in_directory(self.context.state_dir)
        self.policy = {**POLICY, **policy}
        self.clock = Clock()
        self.ingestor = OutboxIngestor(self.context, self.store, self.writer, clock=self.clock)

    def writer(self):
        return TrackerWriter.for_context(self.context)

    def dispatch(self, agent='business-analyst', event=None, attempt=1, state='done'):
        """What the dispatcher persists before sending an outbox task."""
        event = event or secrets.token_hex(32)
        self.store.put('queued:' + event, {'state': 'done', 'agent_id': agent, 'line_number': 0,
                                           'stage': 'despachado', 'stages': {'despachado': 1.0}})
        record = outbox.expect(self.store, self.context, event_id=event, attempt=attempt, agent=agent,
                               policy=self.policy)
        self.store.put('dispatch:' + event, {'state': state, 'agent_id': agent, 'attempt': attempt,
                                             'channel': 'outbox', 'outbox': record['key']})
        return record

    def path(self, record):
        return self.root / record['path']

    def text(self, record, *lines, author=None, begin=None, end=None, handoff='- **Handoff:** @SA: diseña.'):
        body = f'### [11-10-2026] {author or record["authors"][0]}\n- **Hora:** 10:00:00\n- **Estado:** listo\n'
        body += ''.join(f'{line}\n' for line in lines) + (f'{handoff}\n' if handoff else '')
        return f'{begin or outbox.begin_marker(record)}\n{body}{end or outbox.end_marker(record)}\n'

    def publish(self, record, *lines, data=None, **options):
        path = self.path(record)
        path.write_bytes(data if data is not None else self.text(record, *lines, **options).encode('utf-8'))
        return path

    def tick(self):
        return self.ingestor.tick()

    def get(self, record):
        return self.store.get(record['key'])

    def tracker(self):
        return self.context.tracker_path.read_text(encoding='utf-8')

    def close(self):
        self.store.close()


@pytest.fixture
def space(tmp_path):
    item = Space(tmp_path)
    yield item
    item.close()


def blocks_by(text, author):
    return len(re.findall(rf'^### \[[^\]]+\] {re.escape(author)}', text, re.MULTILINE))


# ------------------------------------------------------------------------------------------------ configuration
def test_direct_is_the_default_and_policy_is_validated():
    assert outbox.policy_from_config(None) == {'mode': 'direct', 'agents': [], 'max_bytes': 65536, 'settle_seconds': 2}
    for bad in ({'mode': 'agents'}, {'agents': ['business-analyst']}, {'mode': 'both', 'agents': ['dev-backend']},
                {'mode': 'both', 'agents': ['qa-tech', 'qa-tech']}, {'max_bytes': 10}, {'settle_seconds': 61},
                {'mode': 'outbox', 'extra': 1}, {'max_bytes': True}):
        with pytest.raises(ConfigurationError):
            outbox.policy_from_config(bad)
    both = {'mode': 'both', 'agents': ['business-analyst']}
    assert outbox.channel_for(both, 'business-analyst') == 'outbox'
    assert outbox.channel_for(both, 'solutions-architect') == 'direct'
    assert outbox.channel_for({'mode': 'outbox'}, 'dev-backend') == 'direct'      # headless: no block author
    assert outbox.channel_for({'mode': 'outbox'}, 'qa-tech') == 'outbox'
    assert outbox.channel_for(None, 'qa-tech') == 'direct'


def test_project_json_opts_in_without_touching_the_engine_config(tmp_path):
    engine, workspace = tmp_path / 'engine', tmp_path / 'ws'
    engine.mkdir()
    workspace.mkdir()
    engine_config = json.dumps({'ai': {'defaults': {'provider': 'claude'}}})
    (engine / 'config_bmad.json').write_text(engine_config, encoding='utf-8')
    (workspace / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'iso', 'config': {
        'ai': {'outbox': {'mode': 'both', 'agents': ['business-analyst']}}}}), encoding='utf-8')
    context = ProjectContext(engine, workspace, 'iso')
    assert RuntimeConfig.load(workspace, context=context).data['outbox']['mode'] == 'both'
    assert RuntimeConfig.load(engine, context=ProjectContext(engine, engine, 'legacy', True)).data['outbox']['mode'] \
        == 'direct'
    assert (engine / 'config_bmad.json').read_text(encoding='utf-8') == engine_config


def test_the_three_protected_files_and_the_engine_default_stay_direct():
    data = json.loads((ROOT / 'config_bmad.json').read_text(encoding='utf-8'))
    assert 'outbox' not in data.get('ai', {})
    assert outbox.policy_from_config(data.get('ai', {}).get('outbox'))['mode'] == 'direct'


# ------------------------------------------------------------------------------------------------ happy path
def test_published_response_is_validated_ingested_once_and_its_handoff_confirmed(space):
    record = space.dispatch()
    assert record['state'] == 'expected' and record['path'].startswith('handoffs/outbox/')
    assert space.tick() == [] and space.get(record)['state'] == 'expected'          # nothing published yet
    space.publish(record)
    [done] = space.tick()
    assert done['state'] == 'confirmed' and done['block_index'] == 0
    text = space.tracker()
    assert blocks_by(text, 'Business Analyst') == 1 and 'BMAD-OUTBOX' not in text
    queued = space.store.get(record['queued'])
    assert (queued['stage'], queued['confirmed_block'], queued['channel']) == ('confirmado', 0, 'outbox')
    writer = space.writer()
    assert writer.status(record['op_id']) == 'done' and writer.delivered(record['op_id'])
    stamp = queued['stages']['confirmado']
    for _ in range(3):                                                              # idempotent
        assert space.tick() == []
    assert blocks_by(space.tracker(), 'Business Analyst') == 1
    assert space.store.get(record['queued'])['stages']['confirmado'] == stamp
    assert space.path(record).exists()                                              # evidence is never deleted
    history = [entry['to'] for entry in space.get(record)['history']]
    assert history == ['expected', 'ready', 'validating', 'ingesting', 'confirmed']


def test_received_validated_ingested_and_confirmed_are_separate_milestones(space):
    space.policy['settle_seconds'] = 5
    record = space.dispatch()
    space.publish(record)
    space.tick()
    assert space.get(record)['state'] == 'ready' and not space.tracker()           # received, not validated
    space.clock.now += 5
    with patch.object(OutboxIngestor, '_ingest', lambda self, item: item):
        space.tick()
    assert space.get(record)['state'] == 'ingesting' and not space.tracker()       # validated, not appended
    space.tick()
    assert space.get(record)['state'] == 'confirmed'


def test_two_responses_with_identical_text_and_different_events_are_two_deliveries(space):
    first, second = space.dispatch(), space.dispatch()
    body = space.text(first)
    space.publish(first, data=body.encode('utf-8'))
    space.publish(second, data=body.replace(first['nonce'], second['nonce'])
                  .replace(first['event_id'], second['event_id']).encode('utf-8'))
    assert sorted(item['state'] for item in space.tick()) == ['confirmed', 'confirmed']
    assert blocks_by(space.tracker(), 'Business Analyst') == 2
    assert space.get(first)['op_id'] != space.get(second)['op_id']


# ------------------------------------------------------------------------------------------------ publication
def test_incomplete_publication_is_never_read_as_a_response(space):
    record = space.dispatch()
    full = space.text(record)
    space.publish(record, data=full[:full.index('<!-- BMAD-OUTBOX-END')].encode('utf-8'))
    space.tick()
    assert space.get(record)['state'] == 'writing' and space.tracker() == ''
    partial_end = full[:-12]                                                        # half-written end marker
    space.publish(record, data=partial_end.encode('utf-8'))
    space.tick()
    assert space.get(record)['state'] == 'writing' and outbox.describe(space.get(record)) == 'incomplete_file'
    space.publish(record, data=full.encode('utf-8'))
    space.tick()
    assert space.get(record)['state'] == 'confirmed'


def test_empty_file_is_incomplete_not_ingested(space):
    record = space.dispatch()
    space.publish(record, data=b'')
    space.tick()
    assert space.get(record)['state'] == 'writing' and space.tracker() == ''


def test_atomic_publication_ignores_the_temporary_file(space):
    record = space.dispatch()
    temporary = space.path(record).with_name(space.path(record).name + '.tmp')
    temporary.write_text(space.text(record), encoding='utf-8')
    space.tick()
    assert space.get(record)['state'] == 'expected' and outbox.orphans(space.store) == []
    os.replace(temporary, space.path(record))
    space.tick()
    assert space.get(record)['state'] == 'confirmed'


def test_content_must_repeat_after_settle_before_validation(space):
    space.policy['settle_seconds'] = 3
    record = space.dispatch()
    space.publish(record, handoff='- **Handoff:** @SA: primera versión.')
    space.tick()
    space.clock.now += 2
    space.publish(record, handoff='- **Handoff:** @SA: versión final.')
    space.tick()
    space.clock.now += 2
    space.tick()
    assert space.get(record)['state'] == 'ready'                                  # changed: the timer restarted
    space.clock.now += 1
    space.tick()
    assert space.get(record)['state'] == 'confirmed' and 'versión final' in space.tracker()
    assert 'primera versión' not in space.tracker()


# ------------------------------------------------------------------------------------------------ invalid files
@pytest.mark.parametrize('mutate, reason', [
    (lambda text, r: text.replace(outbox.begin_marker(r), 'basura'), 'missing_begin_marker'),
    (lambda text, r: text.replace(outbox.end_marker(r), outbox.end_marker({**r, 'nonce': 'f' * 32})), 'nonce_mismatch'),
    (lambda text, r: text.replace(f'nonce={r["nonce"]} -->\n###', f'nonce={"e" * 32} -->\n###'), 'nonce_mismatch'),
    (lambda text, r: text.replace(f'agent={r["agent"]}', 'agent=product-manager'), 'role_mismatch'),
    (lambda text, r: text.replace(f'project={r["project_id"]}', 'project=beta'), 'other_project'),
    (lambda text, r: text.replace(f'event_id={r["event_id"]}', 'event_id=' + 'a' * 64), 'identity_mismatch'),
    (lambda text, r: text.replace('Business Analyst', 'Product Manager'), 'role_mismatch'),
    (lambda text, r: text.replace('Business Analyst', 'HUMANO'), 'forged_author'),
    (lambda text, r: text.replace('Business Analyst', 'Business Analyst WATCHER'), 'forged_author'),
    (lambda text, r: text.replace('- **Estado:**', '### [11-10-2026] Business Analyst\n- **Estado:**'), 'multiple_blocks'),
    (lambda text, r: text.replace('- **Estado:**', 'nota ### [x] y\n- **Estado:**'), 'multiple_blocks'),
    (lambda text, r: text.replace('- **Hora:** 10:00:00\n', ''), 'missing_field_hora'),
    (lambda text, r: text.replace('[11-10-2026]', '[31-02-2026]'), 'invalid_header_date'),
    (lambda text, r: text.replace('- **Estado:**', '<!-- BMAD-TAREA x -->\n- **Estado:**'), 'embedded_marker'),
    (lambda text, r: text.replace('- **Estado:**', '- **Estado:** \x07'), 'control_characters'),
])
def test_malformed_or_forged_deliveries_are_rejected_and_audited(space, mutate, reason):
    record = space.dispatch()
    space.publish(record, data=mutate(space.text(record), record).encode('utf-8'))
    [rejected] = space.tick()
    assert (rejected['state'], rejected['reason']) == ('rejected', reason)
    text = space.tracker()
    assert 'Business Analyst' not in text.split('] WATCHER')[0] and blocks_by(text, 'WATCHER') == 1
    assert '- **Handoff:** @HUMANO:' in text and 'GITOPS' not in text
    queued = space.store.get(record['queued'])
    assert queued['stage'] == 'requiere_intervencion' and queued['failure'] == 'outbox:' + reason
    assert [key for key, _ in outbox.incidents(space.store)] == [record['key']]
    space.tick()
    assert blocks_by(space.tracker(), 'WATCHER') == 1                              # notice emitted once


def test_invalid_utf8_is_rejected(space):
    record = space.dispatch()
    data = space.text(record).encode('utf-8').replace(b'listo', b'list\xff\xfe')
    space.publish(record, data=data)
    [rejected] = space.tick()
    assert rejected['reason'] == 'invalid_utf8' and outbox.describe(rejected) == 'invalid_file'


def test_oversized_file_is_rejected_without_reading_it(space):
    record = space.dispatch()
    space.publish(record, data=b'x' * 5000)
    [rejected] = space.tick()
    assert rejected['reason'] == 'too_large'


def test_assigned_path_cannot_escape_the_outbox(space):
    record = space.dispatch()
    space.store.put(record['key'], {**record, 'path': '../outside.md'})
    with pytest.raises((ConfigurationError, ReconciliationRequired)):
        space.tick()
    space.store.put(record['key'], {**record, 'path': 'handoffs/tracker_bmad.md'})
    with pytest.raises(ReconciliationRequired):
        space.tick()
    assert space.tracker() == ''


def _symlink(target, link, directory=False):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip('symlinks are not available to this user')


def test_symlinked_response_is_rejected_and_never_followed(space, tmp_path):
    record = space.dispatch()
    outside = tmp_path / 'secret.md'
    outside.write_text(space.text(record), encoding='utf-8')
    _symlink(outside, space.path(record))
    [rejected] = space.tick()
    assert rejected['reason'] == 'symlink' and space.tracker().count('Business Analyst') == 0


def test_outbox_directory_through_a_junction_is_refused(tmp_path):
    space = Space(tmp_path)
    try:
        record = space.dispatch()
        directory = space.context.handoffs_dir / 'outbox'
        moved = tmp_path / 'elsewhere'
        directory.rename(moved)
        if os.name == 'nt':
            import _winapi
            _winapi.CreateJunction(str(moved), str(directory))
        else:
            _symlink(moved, directory, directory=True)
        (moved / Path(record['path']).name).write_text(space.text(record), encoding='utf-8')
        with pytest.raises(ReconciliationRequired):
            space.tick()
        assert space.tracker() == ''
    finally:
        space.close()


# ------------------------------------------------------------------------------------------------ roles and macros
@pytest.mark.parametrize('agent, macro, allowed', [
    ('product-manager', f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}', True),
    ('business-analyst', f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}', False),
    ('code-review', f'@WATCHER: GITOPS-MERGE-CLOSE feat/{HU_A}', True),
    ('qa-tech', f'@WATCHER: GITOPS-MERGE-CLOSE feat/{HU_A}', False),
    ('product-manager', f'@WATCHER: GITOPS-MERGE-CLOSE feat/{HU_A}', False),
    ('business-analyst', f'Nota: emitiría `@WATCHER: GITOPS-MERGE-CLOSE feat/{HU_A}`', False),
    ('solutions-architect', f'@WATCHER: SDD-FREEZE {HU_A}.md', True),
    ('business-analyst', f'@WATCHER: SDD-FREEZE {HU_A}.md', False),
    ('qa-documental', '@WATCHER: /speckit.clarify sí', False),
])
def test_macros_are_accepted_only_from_their_contract_role(space, agent, macro, allowed):
    record = space.dispatch(agent)
    space.publish(record, macro)
    [result] = space.tick()
    if allowed:
        assert result['state'] == 'confirmed' and macro in space.tracker()
    else:
        assert result['reason'].startswith('unauthorized_macro') and macro not in space.tracker()
        assert outbox.describe(result) == 'wrong_role'


def test_role_comes_from_the_persisted_dispatch_not_from_the_file(space):
    record = space.dispatch('business-analyst')
    forged = space.text(record, f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}', author='Product Manager')
    space.publish(record, data=forged.replace('agent=business-analyst', 'agent=product-manager').encode('utf-8'))
    [rejected] = space.tick()
    assert rejected['reason'] == 'role_mismatch' and 'GITOPS' not in space.tracker()


# ------------------------------------------------------------------------------------------------ identity
def test_file_without_expected_delivery_is_an_audited_orphan(space):
    stranger = secrets.token_hex(32)
    space.dispatch()                                    # creates the directory; it is scanned from now on
    (space.context.handoffs_dir / 'outbox' / outbox.file_name(stranger, 1)).write_text('hola', encoding='utf-8')
    [orphan] = space.tick()
    assert (orphan['state'], orphan['reason']) == ('rejected', 'unknown_identity')
    assert space.tick() == []                           # same evidence: audited once
    assert 'WATCHER' in space.tracker() and [k for k, _ in outbox.incidents(space.store)] == [orphan['key']]
    outbox.acknowledge(space.store, orphan['key'])
    assert outbox.incidents(space.store) == []
    (space.context.handoffs_dir / 'outbox' / outbox.file_name(stranger, 1)).write_text('otra', encoding='utf-8')
    [again] = space.tick()                              # new content: a new incident
    assert again['key'] == orphan['key'] and not again.get('acknowledged')


def test_two_independent_projects_never_accept_each_others_responses(tmp_path):
    alpha, beta = Space(tmp_path, 'alpha'), Space(tmp_path, 'beta')
    try:
        record_a, record_b = alpha.dispatch(), beta.dispatch()
        text_a = alpha.text(record_a)
        (beta.context.handoffs_dir / 'outbox' / Path(record_a['path']).name).write_text(text_a, encoding='utf-8')
        beta.publish(record_b, data=text_a.encode('utf-8'))             # alpha's response at beta's path
        results = {item['key']: item for item in beta.tick()}
        assert results[record_b['key']]['reason'] == 'other_project'
        assert any(item['reason'] == 'unknown_identity' for item in results.values())
        alpha.publish(record_a)
        assert [item['state'] for item in alpha.tick()] == ['confirmed']
        assert 'Business Analyst' in alpha.tracker() and blocks_by(beta.tracker(), 'Business Analyst') == 0
        assert alpha.context.state_dir != beta.context.state_dir
    finally:
        alpha.close()
        beta.close()


def test_retry_after_not_delivered_uses_a_new_attempt_and_audits_a_stale_file(space):
    event = secrets.token_hex(32)
    first = space.dispatch(event=event, attempt=1, state='not_delivered')
    outbox.abandon(space.store, first['key'])
    assert outbox.incidents(space.store) == []                          # silent: nothing reached the agent
    second = space.dispatch(event=event, attempt=2)
    assert second['path'] != first['path']
    space.publish(first)                                                # a file for the undelivered attempt
    space.publish(second)
    results = {item['key']: item for item in space.tick()}
    assert results[second['key']]['state'] == 'confirmed'
    [orphan] = [item for key, item in results.items() if key.startswith(outbox.ORPHAN_PREFIX)]
    assert orphan['reason'] == 'stale_attempt' and blocks_by(space.tracker(), 'Business Analyst') == 1


def test_expect_never_overwrites_existing_evidence(space):
    event = secrets.token_hex(32)
    directory = space.context.handoffs_dir / 'outbox'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / outbox.file_name(event, 1)).write_text('previo', encoding='utf-8')
    with pytest.raises(ReconciliationRequired):
        outbox.expect(space.store, space.context, event_id=event, attempt=1, agent='business-analyst', policy=POLICY)
    assert (directory / outbox.file_name(event, 1)).read_text(encoding='utf-8') == 'previo'


@pytest.mark.parametrize('dispatch_state, queued_change, state, reason', [
    ('uncertain', {}, 'reconcile_required', 'dispatch_uncertain'),
    ('in_flight', {}, 'reconcile_required', 'dispatch_uncertain'),
    ('not_delivered', {}, 'rejected', 'response_without_delivery'),
    ('done', {'acknowledged': 1.0}, 'reconcile_required', 'handoff_acknowledged'),
    ('done', {'stage': 'confirmado'}, 'reconcile_required', 'already_confirmed'),
])
def test_delivery_is_authorized_only_by_a_completed_dispatch(space, dispatch_state, queued_change, state, reason):
    record = space.dispatch(state=dispatch_state)
    space.store.put(record['queued'], {**space.store.get(record['queued']), **queued_change})
    space.publish(record)
    [result] = space.tick()
    assert (result['state'], result['reason']) == (state, reason)
    assert 'Business Analyst' not in space.tracker()


def test_acknowledging_an_incident_never_delivers_it(space):
    record = space.dispatch()
    space.publish(record, f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}')
    [rejected] = space.tick()
    outbox.acknowledge(space.store, record['key'])
    after = space.get(record)
    assert after['state'] == 'rejected' and after['acknowledged'] and outbox.incidents(space.store) == []
    assert space.store.get(record['queued'])['stage'] == 'requiere_intervencion'
    assert space.writer().status(record['op_id']) is None and 'Business Analyst' not in space.tracker()
    space.tick()
    assert space.get(record)['state'] == 'rejected'                                 # never retried


def test_uncertain_delivery_is_closed_only_when_absent_from_the_tracker(space):
    record = space.dispatch(state='uncertain')
    space.publish(record)
    space.tick()
    with pytest.raises(ReconciliationRequired):
        outbox.acknowledge(space.store, record['key'])                              # not a rejection
    closed = outbox.reject(space.store, space.writer(), record['key'])
    assert closed['state'] == 'rejected' and closed['resolution']['kind'] == 'rejected_by_operator'
    assert outbox.incidents(space.store) == []


# ------------------------------------------------------------------------------------------------ crash recovery
def test_crash_before_the_tracker_write_resumes_and_appends_once(space):
    record = space.dispatch()
    space.publish(record)
    with patch.object(TrackerWriter, 'append', side_effect=Crash), pytest.raises(Crash):
        space.tick()
    assert space.get(record)['state'] == 'ingesting' and space.tracker() == ''
    space.ingestor = OutboxIngestor(space.context, space.store, space.writer, clock=space.clock)     # restart
    space.tick()
    assert space.get(record)['state'] == 'confirmed' and blocks_by(space.tracker(), 'Business Analyst') == 1


def test_crash_after_the_tracker_write_and_before_confirmation_never_duplicates(space):
    record = space.dispatch()
    space.publish(record)
    with patch.object(OutboxIngestor, '_confirm', side_effect=Crash), pytest.raises(Crash):
        space.tick()
    assert space.get(record)['state'] == 'ingesting' and blocks_by(space.tracker(), 'Business Analyst') == 1
    assert space.store.get(record['queued'])['stage'] == 'despachado'             # delivered, not yet confirmed
    space.ingestor = OutboxIngestor(space.context, space.store, space.writer, clock=space.clock)
    [done] = space.tick()
    assert done['state'] == 'confirmed' and blocks_by(space.tracker(), 'Business Analyst') == 1
    assert space.store.get(record['queued'])['stage'] == 'confirmado'


def test_crash_inside_the_append_leaves_an_uncertain_write_for_a_human(space):
    record = space.dispatch()
    space.publish(record)
    real_open = Path.open

    def torn(self, mode='r', *args, **kwargs):
        handle = real_open(self, mode, *args, **kwargs)
        if mode == 'ab':
            write = handle.write
            handle.write = lambda data: (write(data[:80]), handle.flush(), (_ for _ in ()).throw(Crash()))
        return handle
    with patch.object(Path, 'open', torn), pytest.raises(Crash):
        space.tick()
    space.ingestor = OutboxIngestor(space.context, space.store, space.writer, clock=space.clock)
    from bmad_runtime.tracker_io import TrackerIntegrityError
    with pytest.raises(TrackerIntegrityError):                                     # never repaired automatically
        space.tick()
    after = space.get(record)
    assert (after['state'], after['reason']) == ('reconcile_required', 'tracker_append_uncertain')
    assert space.writer().status(record['op_id']) == 'uncertain'
    assert blocks_by(space.tracker(), 'Business Analyst') == 1                    # only the torn fragment


def test_lost_ingested_block_is_never_reported_as_delivered(space):
    record = space.dispatch()
    space.publish(record)
    space.tick()
    space.context.tracker_path.write_text('', encoding='utf-8')                   # external rewrite
    assert not space.writer().delivered(record['op_id'])
    with pytest.raises(ReconciliationRequired):
        outbox.reject(space.store, space.writer(), record['key'])                 # it was delivered once


# ------------------------------------------------------------------------------------------------ concurrency
WORKER = textwrap.dedent('''
    import sys, time
    from pathlib import Path
    sys.path.insert(0, sys.argv[1])
    from bmad_runtime.context import ProjectContext
    from bmad_runtime.outbox import OutboxIngestor
    from bmad_runtime.state import StateStore
    from bmad_runtime.tracker_io import TrackerWriter
    context = ProjectContext(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    store = StateStore.in_directory(context.state_dir)
    ingestor = OutboxIngestor(context, store, lambda: TrackerWriter.for_context(context, timeout=60))
    start = float(sys.argv[4])
    while time.time() < start:
        time.sleep(0.001)
    for _ in range(30):
        ingestor.tick()
        time.sleep(0.005)
''')


def test_concurrent_ingestors_in_separate_processes_deliver_each_response_once(space):
    records = [space.dispatch() for _ in range(6)]
    for record in records:
        space.publish(record)
    start = time.time() + 2
    procs = [subprocess.Popen([sys.executable, '-c', WORKER, str(ROOT), str(space.root), 'alpha', str(start)])
             for _ in range(3)]
    assert [proc.wait(timeout=300) for proc in procs] == [0, 0, 0]
    assert blocks_by(space.tracker(), 'Business Analyst') == 6
    assert all(space.get(record)['state'] == 'confirmed' for record in records)
    assert len({space.store.get(r['queued'])['confirmed_block'] for r in records}) == 6


def test_second_watcher_and_busy_outbox_lock_never_ingest(space):
    record = space.dispatch()
    space.publish(record)
    with project_lock(space.context, 'watcher'):
        with pytest.raises(ReconciliationRequired):
            with project_lock(space.context, 'watcher'):
                pass
    lock = ProjectLock(space.context, outbox.LOCK)
    assert lock.acquire()
    try:
        assert space.tick() == [] and space.get(record)['state'] == 'expected'
    finally:
        lock.release()
    assert space.tick()[0]['state'] == 'confirmed'


# ------------------------------------------------------------------------------------------------ dispatcher
def make_runtime(root, policy=None, hu='observe', config_name='config_bmad.json'):
    ai = {'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}},
          'tracker': {'settle_seconds': 3600, 'rewrite_grace_seconds': 0}, 'hu_lifecycle': {'mode': hu}}
    if policy is not None:
        ai['outbox'] = policy
    (root / config_name).write_text(json.dumps({'ai': ai}), encoding='utf-8')
    registry = default_registry()
    registry.register('fake', FakeProvider)
    runner = Mock()
    runner.run.return_value = Result(0, '')
    rt = Runtime(root, registry=registry, gateway=Mock(), runner=runner,
                 config_path=None if config_name == 'config_bmad.json' else root / config_name)
    ready_pane(rt.gateway)
    rt.context.tracker_path.parent.mkdir(parents=True, exist_ok=True)
    if not rt.context.tracker_path.exists():
        rt.context.tracker_path.write_text('', encoding='utf-8')
    return rt


def ready(rt, name='business-analyst'):
    rt.state.put('agent:' + name, {'agent_id': name, 'provider': 'fake', 'model': None, 'pane_id': 'p-' + name,
                                   'state': 'ready'})
    rt.gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p-' + name, 'agent_status': 'idle'}]


@pytest.mark.parametrize('mode', ['direct', 'both', 'outbox'])
def test_dispatcher_assigns_and_persists_one_channel_per_dispatch(tmp_path, mode):
    policy = {'mode': mode, **({'agents': ['business-analyst']} if mode == 'both' else {})}
    rt = make_runtime(tmp_path, policy)
    try:
        ready(rt)
        event = secrets.token_hex(32)
        assert rt.dispatcher.dispatch('business-analyst', 'p-business-analyst', '@BA: analiza', event)
        dispatch = rt.state.get('dispatch:' + event)
        task = (tmp_path / dispatch['task_file']).read_text(encoding='utf-8')
        if mode == 'direct':
            assert 'channel' not in dispatch and TRACKER_RULE in task and 'BMAD-OUTBOX' not in task
            assert outbox.records(rt.state) == []
        else:
            record = rt.state.get(dispatch['outbox'])
            assert (dispatch['channel'], record['state'], record['agent']) == ('outbox', 'expected', 'business-analyst')
            assert outbox.begin_marker(record) in task and outbox.end_marker(record) in task
            assert TRACKER_RULE not in task and record['path'] in task
        terminal = rt.gateway.prompt.call_args[0][1]
        assert 'BMAD-OUTBOX' not in terminal and len(terminal) < 120                 # Herdr line stays short
    finally:
        rt.close()


def test_rejected_delivery_attempt_closes_its_expectation_silently(tmp_path):
    rt = make_runtime(tmp_path, {'mode': 'outbox'})
    try:
        ready(rt)
        rt.gateway.prompt.side_effect = DeliveryRejected('pane closed')
        event = secrets.token_hex(32)
        with pytest.raises(DeliveryRejected):
            rt.dispatcher.dispatch('business-analyst', 'p-business-analyst', '@BA: analiza', event)
        [(key, record)] = outbox.records(rt.state)
        assert (record['state'], record['reason']) == ('rejected', 'dispatch_not_delivered')
        assert outbox.incidents(rt.state) == []
        rt.gateway.prompt.side_effect = None
        assert rt.dispatcher.dispatch('business-analyst', 'p-business-analyst', '@BA: analiza', event)
        assert rt.state.get('dispatch:' + event)['outbox'].endswith(':2')
    finally:
        rt.close()


def test_reminder_keeps_the_channel_and_opens_no_new_expectation(tmp_path):
    rt = make_runtime(tmp_path, {'mode': 'outbox'})
    try:
        ready(rt)
        event = secrets.token_hex(32)
        rt.dispatcher.dispatch('business-analyst', 'p-business-analyst', '@BA: analiza', event)
        [(_, record)] = outbox.records(rt.state)
        reminder = secrets.token_hex(32)
        rt.dispatcher.dispatch('business-analyst', 'p-business-analyst', 'recuerda', reminder, reminder=True,
                               outbox_record=record)
        assert len(outbox.records(rt.state)) == 1
        task = (tmp_path / rt.state.get('dispatch:' + reminder)['task_file']).read_text(encoding='utf-8')
        assert outbox.begin_marker(record) in task and 'channel' not in rt.state.get('dispatch:' + reminder)
    finally:
        rt.close()


# ------------------------------------------------------------------------------------------------ watcher
def human(rt, *lines):
    def action():
        with rt.context.tracker_path.open('a', encoding='utf-8') as handle:
            handle.write('\n### [11-10-2026] HUMANO\n- **Hora:** 10:00:00\n' + ''.join(f'{line}\n' for line in lines))
    return action


def direct_block(rt, author, *lines):
    def action():
        with rt.context.tracker_path.open('a', encoding='utf-8') as handle:
            handle.write(f'\n### [11-10-2026] {author}\n- **Hora:** 10:00:00\n' + ''.join(f'{line}\n' for line in lines))
    return action


def reply(rt, agent, *lines, atomic=False, author=None):
    """Simulated agent CLI (Claude/Codex double): follows only what its task file says."""
    def action():
        candidates = [record for _, record in outbox.records(rt.state)
                      if record['agent'] == agent and record['state'] == 'expected']
        record = max(candidates, key=lambda item: item['created'])
        task = (rt.context.workspace_root / rt.state.get(record['dispatch'])['task_file']).read_text(encoding='utf-8')
        begin = re.search(r'^<!-- BMAD-OUTBOX v1 .* -->$', task, re.MULTILINE).group(0)
        end = re.search(r'^<!-- BMAD-OUTBOX-END .* -->$', task, re.MULTILINE).group(0)
        relative = re.search(r'en el archivo nuevo (\S+) \(relativo', task).group(1)
        name = author or re.search(r'^### \[DD-MM-YYYY\] (.+)$', task, re.MULTILINE).group(1)
        text = (f'{begin}\n### [11-10-2026] {name}\n- **Hora:** 10:00:00\n- **Estado:** listo\n'
                + ''.join(f'{line}\n' for line in lines) + f'{end}\n')
        target = rt.context.workspace_root / relative
        if atomic:
            temporary = target.with_name(target.name + '.tmp')
            temporary.write_text(text, encoding='utf-8')
            os.replace(temporary, target)
        else:
            target.write_text(text, encoding='utf-8')
    return action


def run(rt, root, actions, expect=KeyboardInterrupt, create=None, **patches):
    with patch.multiple(workflow, _runtime=rt, DIRECTORIO_RAIZ=root, TRACKER_PATH=str(rt.context.tracker_path),
                        **patches), \
            patch.object(workflow, 'gitops_branch_create', create or Mock(side_effect=checkout_root(root))):
        run_watcher(rt, root, actions, expect=expect)


def queued_for(rt, agent):
    return [data for _, raw in rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'")
            for data in [json.loads(raw)] if data.get('agent_id') == agent]


def prompts_to(rt, agent):
    return [c for c in rt.gateway.prompt.call_args_list if c[0][0] == 'p-' + agent]


def outbox_policy(mode='outbox', **extra):
    return {'mode': mode, 'settle_seconds': 0, **extra}


def test_pilot_claude_ba_to_codex_sa_through_outbox_watcher_and_tracker(tmp_path):
    """Piloto con dobles: BA (Claude) -> outbox -> watcher -> TrackerWriter -> tracker -> SA (Codex)."""
    rt = make_runtime(tmp_path, outbox_policy())
    try:
        run(rt, tmp_path, [human(rt, f'- **Handoff:** @BA: Analiza la HU {HU_A}.'), lambda: None,
                           reply(rt, 'business-analyst', '- **Artefacto generado:** `docs/business-analyst/x.md`',
                                 '- **Handoff:** @SA: Diseña la solución.'), lambda: None,
                           reply(rt, 'solutions-architect', '- **Handoff:** @HUMANO: Revisa el diseño.', atomic=True),
                           lambda: None, lambda: None])
        text = rt.context.tracker_path.read_text(encoding='utf-8')
        assert blocks_by(text, 'Business Analyst') == 1 and blocks_by(text, 'Solutions Architect') == 1
        assert 'BMAD-OUTBOX' not in text
        deliveries = {record['agent']: record for _, record in outbox.records(rt.state)}
        assert {agent: record['state'] for agent, record in deliveries.items()} == \
            {'business-analyst': 'confirmed', 'solutions-architect': 'confirmed'}
        for agent in ('business-analyst', 'solutions-architect'):
            [queued] = queued_for(rt, agent)
            assert queued['stage'] == 'confirmado' and queued['outbox'] == deliveries[agent]['key']
            dispatch = rt.state.get(deliveries[agent]['dispatch'])
            assert (dispatch['channel'], dispatch['agent_id'], dispatch['attempt']) == ('outbox', agent, 1)
            assert len(prompts_to(rt, agent)) == 1
            journal = TrackerWriter.for_context(rt.context).describe(deliveries[agent]['op_id'])
            assert journal['source'] == 'outbox:' + agent and journal['state'] == 'done'
        assert rt.state.get('followup') == {} and workflow.protocol_violations(rt.state) == []
        assert rt.state.get('session:business-analyst')['task_id'] == deliveries['business-analyst']['event_id']
    finally:
        rt.close()


def test_watcher_restart_between_tracker_write_and_confirmation(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy())
    try:
        with patch.object(OutboxIngestor, '_confirm', side_effect=Crash):
            run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None,
                               reply(rt, 'business-analyst', '- **Handoff:** @HUMANO: listo.')], expect=Crash)
        assert blocks_by(rt.context.tracker_path.read_text(encoding='utf-8'), 'Business Analyst') == 1
        [record] = [record for _, record in outbox.records(rt.state)]
        assert record['state'] == 'ingesting' and queued_for(rt, 'business-analyst')[0]['stage'] == 'despachado'
        rt.close()
        rt = make_runtime(tmp_path, outbox_policy())
        run(rt, tmp_path, [lambda: None])
        text = rt.context.tracker_path.read_text(encoding='utf-8')
        assert blocks_by(text, 'Business Analyst') == 1
        [record] = [record for _, record in outbox.records(rt.state)]
        assert record['state'] == 'confirmed' and queued_for(rt, 'business-analyst')[0]['stage'] == 'confirmado'
        assert rt.state.get('followup') == {} and workflow.protocol_violations(rt.state) == []
    finally:
        rt.close()


def test_both_mode_routes_each_agent_through_its_own_channel(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy('both', agents=['business-analyst']))
    try:
        run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None,
                           reply(rt, 'business-analyst', '- **Handoff:** @SA: Diseña.'), lambda: None,
                           direct_block(rt, 'Solutions Architect', '- **Handoff:** @DA: Diseña los datos.'),
                           lambda: None, lambda: None])
        sa = rt.state.get('dispatch:' + next(k for k, raw in rt.state.db.execute(
            "SELECT id,data FROM records WHERE id LIKE 'dispatch:%'") if json.loads(raw)['agent_id'] ==
            'solutions-architect')[len('dispatch:'):])
        assert sa['channel'] == 'direct'
        assert [q['stage'] for q in queued_for(rt, 'business-analyst')] == ['confirmado']
        assert [q['stage'] for q in queued_for(rt, 'solutions-architect')] == ['confirmado']
        assert workflow.protocol_violations(rt.state) == [] and outbox.incidents(rt.state) == []
    finally:
        rt.close()


def test_response_through_both_channels_stops_for_reconciliation(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy())
    try:
        run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None,
                           direct_block(rt, 'Business Analyst', '- **Handoff:** @SA: Diseña.'),
                           reply(rt, 'business-analyst', '- **Handoff:** @SA: Diseña.'), lambda: None, lambda: None])
        [record] = [record for _, record in outbox.records(rt.state)]
        assert (record['state'], record['reason']) == ('reconcile_required', 'direct_and_outbox')
        assert [violation[1]['agent_id'] for violation in workflow.protocol_violations(rt.state)] == ['business-analyst']
        text = rt.context.tracker_path.read_text(encoding='utf-8')
        assert blocks_by(text, 'Business Analyst') == 1                         # only the direct one, never both
        assert prompts_to(rt, 'solutions-architect') == []                      # nothing dispatched from it
        assert queued_for(rt, 'business-analyst')[0]['stage'] == 'requiere_intervencion'
    finally:
        rt.close()


def test_file_for_a_direct_dispatch_is_a_wrong_channel_incident(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy('both', agents=['solutions-architect']))
    try:
        def stray():
            [event] = [k[len('dispatch:'):] for k, _ in rt.state.db.execute(
                "SELECT id,data FROM records WHERE id LIKE 'dispatch:%'")]
            directory = rt.context.handoffs_dir / 'outbox'
            directory.mkdir(parents=True, exist_ok=True)
            (directory / outbox.file_name(event, 1)).write_text('respuesta', encoding='utf-8')
        run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None, stray, lambda: None])
        [(_, orphan)] = outbox.orphans(rt.state)
        assert orphan['reason'] == 'wrong_channel' and outbox.describe(orphan) == 'duplicate_delivery'
        assert outbox.incidents(rt.state)
    finally:
        rt.close()


def test_mode_change_after_restart_never_reinterprets_a_dispatch(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy())
    run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None])
    rt.close()
    rt = make_runtime(tmp_path, {'mode': 'direct'})            # outbox -> direct while BA works
    try:
        run(rt, tmp_path, [reply(rt, 'business-analyst', '- **Handoff:** @SA: Diseña.'), lambda: None,
                           direct_block(rt, 'Solutions Architect', '- **Handoff:** @DA: Diseña los datos.'),
                           lambda: None, lambda: None])
        assert [record['state'] for _, record in outbox.records(rt.state)] == ['confirmed']
        sa = [q for q in queued_for(rt, 'solutions-architect')]
        assert [q['stage'] for q in sa] == ['confirmado']                         # SA was dispatched direct
        assert len(outbox.records(rt.state)) == 1
    finally:
        rt.close()
    rt = make_runtime(tmp_path, outbox_policy())               # direct -> outbox: the SA dispatch stays direct
    try:
        run(rt, tmp_path, [lambda: None])
        assert workflow.protocol_violations(rt.state) == [] and outbox.incidents(rt.state) == []
    finally:
        rt.close()


def test_agent_without_response_is_escalated_and_never_confirmed(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy())
    try:
        steps = [human(rt, '- **Handoff:** @BA: Analiza.')] + [lambda: None] * 6
        run(rt, tmp_path, steps, GRACIA_SIN_TRABAJO_S=0, IDLE_MINIMO_S=0)
        [record] = [record for _, record in outbox.records(rt.state)]
        assert record['state'] == 'expected' and record['escalated']['reason'] == 'no_response'
        assert outbox.describe(record) == 'no_response'
        reminders = [c[0][1] for c in prompts_to(rt, 'business-analyst')][1:]
        assert len(reminders) == workflow.MAX_RECORDATORIOS
        assert len(outbox.records(rt.state)) == 1                                 # reminders open nothing new
        text = rt.context.tracker_path.read_text(encoding='utf-8')
        assert blocks_by(text, 'Business Analyst') == 0 and record['path'] in text
        assert queued_for(rt, 'business-analyst')[0]['stage'] == 'requiere_intervencion'
        rt.close()
        rt = make_runtime(tmp_path, outbox_policy())
        run(rt, tmp_path, [reply(rt, 'business-analyst', '- **Handoff:** @SA: Diseña.'), lambda: None])
        [record] = [record for _, record in outbox.records(rt.state)]
        assert (record['state'], record['reason']) == ('reconcile_required', 'late_after_escalation')
        assert blocks_by(rt.context.tracker_path.read_text(encoding='utf-8'), 'Business Analyst') == 0
        assert prompts_to(rt, 'solutions-architect') == []
    finally:
        rt.close()


def test_rejected_delivery_holds_dispatches_until_acknowledged(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy())
    try:
        run(rt, tmp_path, [human(rt, '- **Handoff:** @BA: Analiza.'), lambda: None,
                           reply(rt, 'business-analyst', f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_B}',
                                 '- **Handoff:** @SA: Diseña.'), lambda: None,
                           human(rt, '- **Handoff:** @SA: continúa igualmente.'), lambda: None, lambda: None])
        [record] = [record for _, record in outbox.records(rt.state)]
        assert record['reason'] == 'unauthorized_macro:GITOPS-BRANCH-CREATE'
        assert prompts_to(rt, 'solutions-architect') == []                          # held by the incident
        assert 'GITOPS-BRANCH-CREATE' not in rt.context.tracker_path.read_text(encoding='utf-8').replace(
            'unauthorized_macro:GITOPS-BRANCH-CREATE', '')
        outbox.acknowledge(rt.state, record['key'])
        run(rt, tmp_path, [lambda: None, lambda: None])
        assert len(prompts_to(rt, 'solutions-architect')) == 1                      # released, never delivered
        assert rt.state.get(record['key'])['state'] == 'rejected'
    finally:
        rt.close()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    (tmp_path / 'README.md').write_text('base\n', encoding='utf-8')
    git(tmp_path, 'add', 'README.md')
    git(tmp_path, 'commit', '-q', '-m', 'init')
    return tmp_path


def test_d5_pm_outbox_branch_create_rejected_by_enforce_dispatches_nothing(repo):
    rt = make_runtime(repo, outbox_policy(), hu='enforce')
    try:
        create = Mock(side_effect=checkout_root(repo))
        run(rt, repo, [human(rt, '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}'),
                       lambda: None, human(rt, '- **Handoff:** @PM: Elige la siguiente HU.'), lambda: None,
                       reply(rt, 'product-manager', f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_B}',
                             f'- **Handoff:** @BA: Inicia el análisis de {HU_B}.'),
                       lambda: None, lambda: None], create=create)
        create.assert_called_once_with(f'feat/{HU_A}')
        assert f'feat/{HU_B}' not in branches(repo) and head(repo) == f'feat/{HU_A}'
        [pm] = [record for _, record in outbox.records(rt.state)]
        assert pm['state'] == 'confirmed'                                          # authorized role: ingested
        [op] = rejected_ops(rt)
        assert op['hu'] == HU_B and ba_handoffs(rt) == [] and prompts_to(rt, 'business-analyst') == []
        with patch.object(workflow, 'TRACKER_PATH', str(rt.context.tracker_path)):
            assert workflow.is_tracker_paused_for_human()
    finally:
        rt.close()


# ------------------------------------------------------------------------------------------------ config §11
def test_watcher_records_its_policies_and_divergence_is_reported(tmp_path):
    rt = make_runtime(tmp_path, outbox_policy(), hu='enforce', config_name='scratch.json')
    (tmp_path / 'config_bmad.json').write_text(json.dumps({'ai': {
        'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}}}}), encoding='utf-8')
    try:
        assert [d['setting'] for d in policy_audit.startup_report(rt)] == ['hu_lifecycle', 'outbox']
        policy_audit.record(rt)
        workflow.watcher_heartbeat(rt.state, time.time())
        report = policy_audit.divergence(rt.context, rt.state)
        assert report['watcher_running'] and {d['setting'] for d in report['differences']} == {'hu_lifecycle', 'outbox'}
        assert policy_audit.running_policies(rt.state)['hu_lifecycle'] == 'enforce'
        assert policy_audit.running_policies(rt.state, now=time.time() + 3600) is None     # stale heartbeat
    finally:
        rt.close()


def test_status_cli_is_read_only_and_reconciliation_needs_a_stopped_watcher(space, capsys):
    record = space.dispatch()
    space.publish(record, f'@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}')
    space.tick()
    space.store.close()
    scope = ['--root', str(ROOT), '--workspace', str(space.root), '--project', 'alpha']
    (space.root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alpha'}), encoding='utf-8')
    before = (space.context.state_dir / 'state.sqlite3').read_bytes()
    assert outbox.main(scope + ['--status']) == 0
    status = json.loads(capsys.readouterr().out)
    assert status['incidents'] == [record['key']] and status['deliveries'][0]['category'] == 'wrong_role'
    assert (space.context.state_dir / 'state.sqlite3').read_bytes() == before
    with project_lock(space.context, 'watcher'), pytest.raises(ReconciliationRequired):
        outbox.main(scope + ['--acknowledge', record['key'], '--confirm'])
    with pytest.raises(SystemExit):
        outbox.main(scope + ['--acknowledge', record['key']])                    # --confirm is mandatory
    assert outbox.main(scope + ['--acknowledge', record['key'], '--confirm']) == 0
    space.store = StateStore.in_directory(space.context.state_dir)
    assert outbox.incidents(space.store) == [] and space.get(record)['state'] == 'rejected'
