"""Fase 4F-E1.1: reconocer una incidencia del journal no confirma la entrega; la reconciliación es explícita."""
import json
import subprocess
import sys
import textwrap
import time
from unittest.mock import patch

import pytest

from bmad_runtime import state as state_module
from bmad_runtime import workflow
from bmad_runtime.errors import ReconciliationRequired
from bmad_runtime.state import ProjectLock, StateStore
from bmad_runtime.tracker_io import INDEX, JOURNAL, TrackerBusy, TrackerIntegrityError, TrackerWriter
from tests.test_tracker_io import ROOT, bloque, crash, journal, legacy_root, rt, run_watcher  # noqa: F401  (fixture)


def lost(tmp_path, op='gate:abc', grace=0.1):
    """A decision appended, then erased by an agent's whole-file rewrite and detected by the next write."""
    tracker = legacy_root(tmp_path)
    writer = TrackerWriter(tracker, grace=grace)
    writer.append(bloque('base-0001'))
    writer.append(bloque('decision-0001', 'HUMANO'), op_id=op)
    original = tracker.read_bytes()
    tracker.write_bytes(original.split(b'\n### [11-10-2026] HUMANO')[0] + b'\n')
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('otro-0001'))
    return writer, original


def uncertain(tmp_path):
    tracker = legacy_root(tmp_path)
    writer = TrackerWriter(tracker)
    writer.append(bloque('base-0001'))
    with crash(writer, 'partial'):
        writer.append(bloque('op-0001'), op_id='op')
    with pytest.raises(TrackerIntegrityError):
        TrackerWriter(tracker).recover()
    return TrackerWriter(tracker)


def cli(root, capsys, *args):
    """state CLI with --confirm; returns the JSON lines of the journal actions it printed."""
    capsys.readouterr()
    assert state_module.main(['--root', str(root), *args, '--confirm']) == 0
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith('{"action"')]


# ----------------------------------------------------------------------------- acknowledge
def test_lost_and_acknowledged_is_neither_done_nor_replayed(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    before = writer.path.read_bytes()
    [ack] = cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    assert (ack['state'], ack['acknowledged'], ack['resolution']) == ('lost', True, None)
    record = journal(writer)['gate:abc']
    assert (record['state'], record['acknowledged_state']) == ('lost', 'lost') and record['acknowledged']
    assert writer.status('gate:abc') == 'lost' and not writer.delivered('gate:abc')
    with pytest.raises(TrackerIntegrityError, match='gate:abc') as raised:
        writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:abc')
    assert raised.value.operations == [JOURNAL + 'gate:abc']
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('otro-0001'))       # acknowledging does not unblock unrelated writes either
    assert writer.path.read_bytes() == before
    assert [h['event'] for h in record['history']] == ['done->lost', 'acknowledged']


def test_uncertain_and_acknowledged_stays_fail_closed(tmp_path):
    writer = uncertain(tmp_path)
    before = writer.path.read_bytes()
    writer.acknowledge('op')
    assert writer.status('op') == 'uncertain'
    for op in ('op', None):
        with pytest.raises(TrackerIntegrityError):
            writer.append(bloque('op-0001'), op_id=op)
    assert writer.path.read_bytes() == before
    assert writer.reconcile('op')['outcome'] == 'partial'
    for action in (writer.authorize_reissue, writer.accept_loss):
        with pytest.raises(ReconciliationRequired, match='uncertain'):
            action('op')
    assert journal(writer)['op']['state'] == 'uncertain' and writer.path.read_bytes() == before


def test_acknowledge_and_reconcile_require_an_incident_and_confirmation(tmp_path, capsys):
    tracker = legacy_root(tmp_path)
    TrackerWriter(tracker).append(bloque('a-0001'), op_id='ok')
    with pytest.raises(SystemExit):
        state_module.main(['--root', str(tmp_path), '--acknowledge', 'tracker_append:ok', '--confirm'])
    assert 'no hay incidencia' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        state_module.main(['--root', str(tmp_path), '--reconcile', 'tracker_append:ok'])     # no --confirm
    assert journal(TrackerWriter(tracker))['ok']['state'] == 'done'


# ----------------------------------------------------------------------------- replay
def test_done_is_replayed_only_while_its_bytes_are_in_the_tracker(tmp_path):
    tracker = legacy_root(tmp_path)
    writer = TrackerWriter(tracker, grace=0)
    writer.append(bloque('a-0001'), op_id='a')
    assert writer.append(bloque('a-0001'), op_id='a').replayed and writer.delivered('a')
    # Older than the verification window: the per-write check no longer covers it.
    store = StateStore.in_directory(writer.state_dir)
    try:
        key = next(k for (k,) in store.db.execute('SELECT id FROM records WHERE id LIKE ?', (INDEX + '%',)))
        store.put(key, {**store.get(key), 'recent': []})
    finally:
        store.close()
    tracker.write_text('', encoding='utf-8')
    assert not writer.delivered('a')
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('a-0001'), op_id='a')
    assert (journal(writer)['a']['state'], journal(writer)['a']['reason']) == ('lost', 'missing_on_replay')
    assert tracker.read_text(encoding='utf-8') == ''


def test_a_pre_e11_acknowledgement_is_not_a_delivery(tmp_path, capsys):
    """Journals written by the E1 preview hold lost/uncertain ops rewritten as done+acknowledged."""
    tracker = legacy_root(tmp_path)
    writer = TrackerWriter(tracker, grace=0)
    writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:old')
    store = StateStore.in_directory(writer.state_dir)
    try:
        store.put(JOURNAL + 'gate:old', {**store.get(JOURNAL + 'gate:old'), 'acknowledged': time.time()})
    finally:
        store.close()
    tracker.write_text('', encoding='utf-8')
    assert writer.status('gate:old') == 'unverified' and not writer.delivered('gate:old')
    [result] = cli(tmp_path, capsys, '--reconcile', 'tracker_append:gate:old')
    assert (result['outcome'], result['state'], result['acknowledged']) == ('absent', 'lost', False)
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:old')


# ----------------------------------------------------------------------------- reconciliation
def test_reconcile_finds_a_restored_copy_and_closes_the_incident(tmp_path, capsys):
    writer, original = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    writer.path.write_bytes(original)             # the agent restores the decision
    [result] = cli(tmp_path, capsys, '--reconcile', 'tracker_append:gate:abc')
    assert (result['outcome'], result['state'], result['copies']) == ('present', 'done', 1)
    record = journal(writer)['gate:abc']
    assert record['resolution']['kind'] == 'verified_present'
    assert [h['event'] for h in record['history']] == ['done->lost', 'acknowledged', 'reconciled_present']
    assert writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:abc').replayed   # idempotent after recovery
    writer.append(bloque('otro-0001'))
    assert writer.read().count('decision-0001') == 1


def test_reconcile_of_an_absent_append_keeps_it_lost_and_blocking(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    [result] = cli(tmp_path, capsys, '--reconcile', 'tracker_append:gate:abc')
    assert (result['outcome'], result['state']) == ('absent', 'lost')
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('otro-0001'))
    with pytest.raises(SystemExit):
        state_module.main(['--root', str(tmp_path), '--authorize-reissue', 'tracker_append:gate:abc', '--confirm'])
    assert 'no está reconocida' in capsys.readouterr().err


def test_lost_retry_needs_an_explicit_reissue_and_writes_one_copy(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    with pytest.raises(TrackerIntegrityError):
        writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:abc')
    [auth] = cli(tmp_path, capsys, '--authorize-reissue', 'tracker_append:gate:abc')
    assert (auth['state'], auth['resolution']) == ('lost', 'reissue_authorized')
    # The producer rebuilds the event (a new timestamp changes its bytes) and writes it exactly once.
    reissue = bloque('decision-0001', 'HUMANO').replace('12:00:00', '12:05:00')
    result = writer.append(reissue, op_id='gate:abc')
    assert result.reissued and not result.replayed
    again = writer.append(reissue, op_id='gate:abc')
    assert again.replayed and not again.reissued
    assert writer.read().count('decision-0001') == 1
    record = journal(writer)['gate:abc']
    assert (record['state'], record['resolution']['kind'], record['attempt']) == ('done', 'reissued', 2)
    previous = next(h for h in record['history'] if h['event'] == 'reissue')['previous']
    assert previous['state'] == 'lost' and previous['sha256'] == record['lost_evidence']['sha256'] != record['sha256']


def test_accept_loss_closes_the_incident_but_never_writes_the_op_again(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    [accepted] = cli(tmp_path, capsys, '--accept-loss', 'tracker_append:gate:abc')
    assert (accepted['state'], accepted['resolution']) == ('lost', 'loss_accepted')
    writer.append(bloque('otro-0001'))
    with pytest.raises(TrackerIntegrityError, match='pérdida se cerró'):
        writer.append(bloque('decision-0001', 'HUMANO'), op_id='gate:abc')
    assert 'decision-0001' not in writer.read()
    capsys.readouterr()
    state_module.main(['--root', str(tmp_path)])
    listed = [json.loads(line)['id'] for line in capsys.readouterr().out.splitlines() if line.startswith('{')]
    assert JOURNAL + 'gate:abc' in listed, 'an accepted loss stays visible'


def test_the_original_reappearing_before_the_reissue_is_the_delivery(tmp_path, capsys):
    writer, original = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    cli(tmp_path, capsys, '--authorize-reissue', 'tracker_append:gate:abc')
    writer.path.write_bytes(original)
    result = writer.append(bloque('decision-0001', 'HUMANO').replace('12:00:00', '12:05:00'), op_id='gate:abc')
    assert result.replayed and not result.reissued
    assert writer.read().count('decision-0001') == 1
    assert journal(writer)['gate:abc']['resolution']['kind'] == 'verified_present'


def test_crash_during_a_reissue_is_recovered_without_a_second_copy(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    cli(tmp_path, capsys, '--authorize-reissue', 'tracker_append:gate:abc')
    reissue = bloque('decision-0001', 'HUMANO').replace('12:00:00', '12:05:00')
    with crash(writer, 'before_write'):
        writer.append(reissue, op_id='gate:abc')
    fresh = TrackerWriter(writer.path)
    assert fresh.append(reissue.replace('12:05:00', '12:06:00'), op_id='gate:abc').reissued
    with crash(fresh, 'after_write'):
        fresh.append(bloque('alerta-0001'), op_id='alerta')
    assert TrackerWriter(writer.path).append(bloque('alerta-0001'), op_id='alerta').replayed
    assert fresh.read().count('decision-0001') == 1 and fresh.read().count('alerta-0001') == 1
    assert journal(fresh)['gate:abc']['resolution']['kind'] == 'reissued'


# ----------------------------------------------------------------------------- concurrency
REISSUER = textwrap.dedent('''
    import sys, time
    sys.path.insert(0, sys.argv[1])
    from bmad_runtime.tracker_io import TrackerWriter
    start = float(sys.argv[3])
    while time.time() < start:
        time.sleep(0.001)
    result = TrackerWriter(sys.argv[2], timeout=60).append(
        "\\n### [11-10-2026] HUMANO\\n- **Hora:** 12:05:00\\n- **Mensaje:** decision-0001 " + "x" * 120 + "\\n",
        op_id="gate:abc")
    print("reissued" if result.reissued else "replayed" if result.replayed else "written")
''')


def test_concurrent_producers_reissue_an_authorized_op_once(tmp_path, capsys):
    writer, _ = lost(tmp_path)
    cli(tmp_path, capsys, '--acknowledge', 'tracker_append:gate:abc')
    cli(tmp_path, capsys, '--authorize-reissue', 'tracker_append:gate:abc')
    start = time.time() + 2
    procs = [subprocess.Popen([sys.executable, '-c', REISSUER, str(ROOT), str(writer.path), str(start)],
                              stdout=subprocess.PIPE, text=True) for _ in range(4)]
    outcomes = sorted(p.communicate(timeout=120)[0].strip() for p in procs)
    assert outcomes == ['reissued', 'replayed', 'replayed', 'replayed']
    assert writer.read().count('decision-0001') == 1


def test_writes_wait_while_a_reconciliation_holds_the_tracker_lock(tmp_path):
    writer, _ = lost(tmp_path)
    busy = TrackerWriter(writer.path, timeout=0.2)
    holder = ProjectLock.at(writer.state_dir / 'tracker.lock')      # what `python -m bmad_runtime.state` holds
    assert holder.acquire()
    try:
        with pytest.raises(TrackerBusy):
            busy.append(bloque('otro-0001'))
        with pytest.raises(TrackerBusy):
            busy.reconcile('gate:abc')
    finally:
        holder.release()
    assert journal(writer)['gate:abc']['history'][-1]['event'] == 'done->lost'


# ----------------------------------------------------------------------------- watcher and MERGE-CLOSE
def lose_engine_block(rt, op_id, text):
    writer = TrackerWriter.for_context(rt.context, grace=0)
    before = rt.context.tracker_path.read_bytes()
    writer.append(text, op_id=op_id)
    rt.context.tracker_path.write_bytes(before)
    with pytest.raises(TrackerIntegrityError):
        writer.recover()
    return writer


def test_watcher_restart_with_an_acknowledged_but_open_incident_stays_stopped(rt, tmp_path):
    writer = lose_engine_block(rt, 'alerta', bloque('alerta-0001'))
    writer.acknowledge('alerta')
    run_watcher(rt, tmp_path, [], expect=TrackerIntegrityError)
    assert rt.gateway.prompt.call_count == 0
    writer.accept_loss('alerta')
    run_watcher(rt, tmp_path, [])            # resolved explicitly: the watcher runs again
    assert journal(writer)['alerta']['state'] == 'lost'


def test_lost_merge_conflict_alert_is_not_emitted_by_acknowledging_it(rt):
    tracker = rt.context.tracker_path
    tracker.write_text('### [11-10-2026] Code Review\n- **Hora:** 12:00:00\n- **Estado:** APROBADO\n'
                       '@WATCHER: GITOPS-MERGE-CLOSE feat/004-gestion-pagos\n- **Handoff:** @PM: HU cerrada.\n',
                       encoding='utf-8')
    gate = tracker.read_bytes()
    event = 'event:' + 'ab' * 32
    op_id = 'gitops-conflict:' + 'ab' * 32

    def fake_git(argv, **kwargs):
        if argv[1] == 'merge' and '--abort' not in argv:
            raise subprocess.CalledProcessError(1, ['git', 'merge'])
        return subprocess.CompletedProcess(argv, 0, '', '')

    def merge_close():
        with patch.object(workflow, 'run_git', fake_git), patch.object(workflow, 'auto_commit_security'), \
                patch.object(workflow, 'get_base_branch', return_value='main'), \
                patch('builtins.input', return_value='feat/004-gestion-pagos'), patch('builtins.print'), \
                pytest.raises(SystemExit):           # the pause holds: the watcher exits every time
            workflow.gitops_merge_close('feat/004-gestion-pagos', event)

    merge_close()
    assert tracker.read_text(encoding='utf-8').count('ALERTA GITOPS') == 1
    tracker.write_bytes(gate)                    # an agent rewrite drops the alert
    writer = TrackerWriter.for_context(rt.context, grace=0)
    with pytest.raises(TrackerIntegrityError):
        writer.recover()
    writer.acknowledge(op_id)
    assert writer.status(op_id) == 'lost' and not writer.delivered(op_id)
    merge_close()                                # retried: no automatic re-emission
    assert tracker.read_bytes() == gate
    writer.authorize_reissue(op_id)
    merge_close()
    merge_close()
    assert tracker.read_text(encoding='utf-8').count('ALERTA GITOPS') == 1
    assert journal(writer)[op_id]['resolution']['kind'] == 'reissued'
