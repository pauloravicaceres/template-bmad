"""Fase 4F-E1: TrackerWriter (lock interproceso, journal SQLite, recuperación, verificación) y su uso en el motor."""
from contextlib import contextmanager
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap
import threading
import time
import types
from unittest.mock import patch

import pytest

from bmad_runtime import state as state_module
from bmad_runtime import workflow
from bmad_runtime.config import AGENT_PHASES, RuntimeConfig
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired
from bmad_runtime.state import ProjectLock, StateStore
from bmad_runtime.tracker_io import (JOURNAL, TrackerBusy, TrackerConflict, TrackerIntegrityError, TrackerWriter,
                                     no_human_block_since, state_dir_for)
from tests.test_tracker_integrity import make_runtime
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'- \*\*Mensaje:\*\* (\w+-\d{4}) x{120}\n')


def bloque(tag, autor='WATCHER'):
    return f'\n### [11-10-2026] {autor}\n- **Hora:** 12:00:00\n- **Mensaje:** {tag} ' + 'x' * 120 + '\n'


def journal(writer):
    store = StateStore.in_directory(writer.state_dir)
    try:
        return {key[len(JOURNAL):]: json.loads(raw) for key, raw in
                store.db.execute("SELECT id,data FROM records WHERE id LIKE 'tracker_append:%'")}
    finally:
        store.close()


@contextmanager
def crash(writer, point):
    """Kill the append at `point` without running its own cleanup, as a dead process would."""
    real_open = Path.open

    class Dying:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.handle.close()

        def write(self, data):
            if point == 'partial':
                self.handle.write(data[:len(data) // 2])
            elif point == 'after_write':
                self.handle.write(data)
            self.handle.flush()
            raise SystemExit(f'crash {point}')

    def dying_open(path, mode='r', *args, **kwargs):
        handle = real_open(path, mode, *args, **kwargs)
        return Dying(handle) if mode == 'ab' and path == writer.path else handle

    with patch.object(Path, 'open', dying_open), patch.object(TrackerWriter, '_recover_one', lambda *a: None), \
            pytest.raises(SystemExit):
        yield


def legacy_root(tmp_path):
    (tmp_path / 'config_bmad.json').write_text('{}', encoding='utf-8')
    (tmp_path / 'docs').mkdir()
    return tmp_path / 'docs' / 'tracker_bmad.md'


# ----------------------------------------------------------------------------- unit
def test_state_dir_is_the_project_state_directory(engine):
    ctx = new_project(engine)
    assert state_dir_for(ctx.tracker_path) == ctx.state_dir
    legacy = ProjectContext(engine, engine, 'legacy', True)
    assert state_dir_for(legacy.tracker_path) == legacy.state_dir
    assert TrackerWriter.for_context(ctx).state_dir == ctx.state_dir


def test_append_writes_complete_lines_and_journals_the_operation(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    tracker.write_bytes('previo sin salto'.encode('utf-8'))
    writer = TrackerWriter(tracker)
    result = writer.append('### [11-10-2026] WATCHER\n- **Mensaje:** ñ', op_id='uno')
    assert tracker.read_text(encoding='utf-8') == 'previo sin salto\n### [11-10-2026] WATCHER\n- **Mensaje:** ñ\n'
    record = journal(writer)['uno']
    assert (record['state'], record['offset'], record['source']) == ('done', len('previo sin salto'), 'python')
    assert result.offset == record['offset'] and not result.replayed
    assert 'Mensaje' not in json.dumps(record), 'the journal keeps digests, never tracker text'


def test_same_op_id_is_idempotent_and_cannot_change_content(tmp_path):
    writer = TrackerWriter(tmp_path / 'tracker_bmad.md')
    writer.append(bloque('a-0001'), op_id='gate:1')
    assert writer.append(bloque('a-0001'), op_id='gate:1').replayed
    assert writer.read().count('a-0001') == 1
    with pytest.raises(ReconciliationRequired):
        writer.append(bloque('otro-0001'), op_id='gate:1')
    with pytest.raises(ValueError):
        writer.append('x', op_id='con espacios')


def test_threads_sharing_and_not_sharing_a_writer_lose_nothing(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    shared = TrackerWriter(tracker, timeout=30)

    def worker(tag, own):
        writer = TrackerWriter(tracker, timeout=30) if own else shared
        for i in range(25):
            writer.append(bloque(f'{tag}-{i:04d}'))

    threads = [threading.Thread(target=worker, args=(f't{n}', n % 2 == 0)) for n in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    found = PATTERN.findall(tracker.read_text(encoding='utf-8'))
    assert len(found) == len(set(found)) == 100
    assert sum(r['state'] == 'done' for r in journal(shared).values()) == 100


WORKER = textwrap.dedent('''
    import sys, time
    sys.path.insert(0, sys.argv[1])
    from bmad_runtime.tracker_io import TrackerWriter
    writer = TrackerWriter(sys.argv[2], timeout=120)
    start = float(sys.argv[5])
    while time.time() < start:
        time.sleep(0.001)
    for i in range(int(sys.argv[4])):
        writer.append("\\n### [11-10-2026] WATCHER\\n- **Hora:** 12:00:00\\n- **Mensaje:** %s-%04d " % (sys.argv[3], i)
                      + "x" * 120 + "\\n", source=sys.argv[3])
''')


def test_concurrent_processes_append_without_loss_or_interleaving(tmp_path):
    """R1 regression: four OS processes (Windows: msvcrt locking) append 240 blocks; none is lost or mixed."""
    tracker = tmp_path / 'tracker_bmad.md'
    start = time.time() + 2
    procs = [subprocess.Popen([sys.executable, '-c', WORKER, str(ROOT), str(tracker), f'p{n}', '60', str(start)])
             for n in range(4)]
    assert [p.wait(timeout=300) for p in procs] == [0, 0, 0, 0]
    text = tracker.read_text(encoding='utf-8')
    found = PATTERN.findall(text)
    assert len(found) == len(set(found)) == 240
    assert text.count('### [') == 240
    states = [r['state'] for r in journal(TrackerWriter(tracker)).values()]
    assert states.count('done') == 240 and len(states) == 240


HOLDER = textwrap.dedent('''
    import sys, time
    sys.path.insert(0, sys.argv[1])
    from bmad_runtime.state import ProjectLock
    lock = ProjectLock.at(sys.argv[2])
    assert lock.acquire()
    print("ready", flush=True)
    time.sleep(float(sys.argv[3]))
''')


@contextmanager
def lock_held_by_other_process(lock_path, seconds=20):
    proc = subprocess.Popen([sys.executable, '-c', HOLDER, str(ROOT), str(lock_path), str(seconds)],
                            stdout=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == 'ready'
        yield
    finally:
        proc.kill()
        proc.wait()


def test_lock_timeout_fails_safe_without_writing(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    tracker.write_text('historia\n', encoding='utf-8')
    writer = TrackerWriter(tracker, timeout=0.3)
    with lock_held_by_other_process(writer.state_dir / 'tracker.lock'):
        began = time.monotonic()
        with pytest.raises(TrackerBusy):
            writer.append(bloque('nunca-0001'), op_id='nunca')
        assert time.monotonic() - began < 5
    assert tracker.read_text(encoding='utf-8') == 'historia\n'
    assert 'nunca' not in journal(writer)
    writer.append(bloque('luego-0001'), op_id='nunca')   # released by the OS when the holder dies
    assert 'luego-0001' in writer.read()


def test_lock_timeout_is_configurable(tmp_path):
    (tmp_path / 'config_bmad.json').write_text(json.dumps({'ai': {'tracker': {'lock_timeout_seconds': 12}}}),
                                               encoding='utf-8')
    assert RuntimeConfig.load(tmp_path).data['tracker']['lock_timeout_seconds'] == 12
    for value in (-1, 3601, True):
        (tmp_path / 'config_bmad.json').write_text(json.dumps({'ai': {'tracker': {'lock_timeout_seconds': value}}}),
                                                   encoding='utf-8')
        with pytest.raises(ConfigurationError):
            RuntimeConfig.load(tmp_path)
    rt = make_runtime(tmp_path, {'settle_seconds': 1, 'rewrite_grace_seconds': 1, 'lock_timeout_seconds': 7})
    try:
        assert TrackerWriter.for_runtime(rt).timeout == 7
    finally:
        rt.close()


# ----------------------------------------------------------------------------- interruptions
def test_crash_before_write_is_not_written_and_the_retry_writes_once(tmp_path):
    writer = TrackerWriter(tmp_path / 'tracker_bmad.md')
    writer.append(bloque('base-0001'))
    with crash(writer, 'before_write'):
        writer.append(bloque('op-0001'), op_id='op')
    assert journal(writer)['op']['state'] == 'in_flight'
    fresh = TrackerWriter(writer.path)      # restarted process
    fresh.recover()
    assert journal(fresh)['op']['state'] == 'not_written'
    fresh.append(bloque('op-0001'), op_id='op')
    assert fresh.read().count('op-0001') == 1
    assert journal(fresh)['op']['attempt'] == 2


def test_crash_after_write_before_confirmation_is_completed(tmp_path):
    writer = TrackerWriter(tmp_path / 'tracker_bmad.md')
    with crash(writer, 'after_write'):
        writer.append(bloque('op-0001'), op_id='op')
    assert journal(writer)['op']['state'] == 'in_flight'
    # An agent appended after the crash: the journaled bytes are still found from their offset.
    with writer.path.open('ab') as handle:
        handle.write(bloque('agente-0001', 'Business Analyst').encode('utf-8'))
    fresh = TrackerWriter(writer.path)
    assert fresh.append(bloque('op-0001'), op_id='op').replayed
    assert fresh.read().count('op-0001') == 1
    record = journal(fresh)['op']
    assert (record['state'], record['recovered']) == ('done', True)


def test_partial_write_is_uncertain_until_reconciled_from_evidence(tmp_path):
    """E1.1: acknowledging records the review only; the fragment keeps the incident open until it is gone."""
    tracker = legacy_root(tmp_path)
    writer = TrackerWriter(tracker)
    writer.append(bloque('base-0001'))
    base = tracker.read_bytes()
    with crash(writer, 'partial'):
        writer.append(bloque('op-0001'), op_id='op')
    before = tracker.read_bytes()
    fresh = TrackerWriter(tracker)
    with pytest.raises(TrackerIntegrityError, match='tracker_append:op'):
        fresh.recover()
    with pytest.raises(TrackerIntegrityError):
        fresh.append(bloque('otro-0001'))
    assert tracker.read_bytes() == before, 'nothing is appended or repaired while uncertain'
    assert journal(fresh)['op']['state'] == 'uncertain'
    with patch('sys.stdout'):
        assert state_module.main(['--root', str(tmp_path), '--acknowledge', 'tracker_append:op', '--confirm']) == 0
    assert journal(fresh)['op']['state'] == 'uncertain'
    with pytest.raises(TrackerIntegrityError):
        fresh.append(bloque('otro-0001'))
    assert tracker.read_bytes() == before
    tracker.write_bytes(base)       # the operator removes the fragment by hand: now the absence is verifiable
    assert fresh.reconcile('tracker_append:op')['outcome'] == 'absent'
    fresh.accept_loss('op')
    fresh.append(bloque('otro-0001'))
    assert 'otro-0001' in fresh.read() and journal(fresh)['op']['state'] == 'lost'


# ----------------------------------------------------------------------------- integrity
def test_external_rewrite_that_drops_an_engine_block_stops_writes(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    writer = TrackerWriter(tracker, grace=0.2)
    writer.append(bloque('humano-0001', 'HUMANO'), op_id='decision')
    # An agent's whole-file edit based on an older read loses the decision.
    tracker.write_text(bloque('agente-0001', 'Business Analyst'), encoding='utf-8')
    assert writer.missing() == [JOURNAL + 'decision']
    before = tracker.read_bytes()
    with pytest.raises(TrackerIntegrityError, match='decision'):
        writer.append(bloque('nuevo-0001'))
    assert tracker.read_bytes() == before
    assert journal(writer)['decision']['state'] == 'lost'
    assert writer.audit() == ([], [JOURNAL + 'decision'])


def test_transient_rewrite_within_grace_is_tolerated(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    writer = TrackerWriter(tracker, grace=3)
    writer.append(bloque('humano-0001', 'HUMANO'))
    original = tracker.read_bytes()
    tracker.write_bytes(b'')        # an editor truncates before writing the new content
    threading.Timer(0.4, lambda: tracker.write_bytes(original + bloque('agente-0001').encode())).start()
    writer.append(bloque('nuevo-0001'))
    assert 'humano-0001' in writer.read() and 'nuevo-0001' in writer.read()


def test_line_ending_normalization_is_not_a_loss(tmp_path):
    tracker = tmp_path / 'tracker_bmad.md'
    writer = TrackerWriter(tracker, grace=0)
    writer.append(bloque('a-0001'))
    tracker.write_bytes(b'cabecera\r\n' + tracker.read_bytes().replace(b'\n', b'\r\n'))
    assert writer.missing() == []
    writer.append(bloque('b-0001'))


def test_precondition_rejects_a_human_decision_recorded_meanwhile(tmp_path):
    writer = TrackerWriter(tmp_path / 'tracker_bmad.md')
    writer.append(bloque('gate-0001', 'Product Manager'))
    reviewed = writer.path.stat().st_size
    writer.append(bloque('cc-0001', 'HUMANO'))          # Control Center decided first
    with pytest.raises(TrackerConflict):
        writer.append(bloque('cli-0001', 'HUMANO'), precondition=no_human_block_since(reviewed))
    assert 'cli-0001' not in writer.read()
    writer.append(bloque('log-0001'), precondition=no_human_block_since(writer.path.stat().st_size))


def test_projects_have_independent_locks_and_journals(engine):
    alpha, beta = new_project(engine, 'alpha'), new_project(engine, 'beta')
    writer_a, writer_b = TrackerWriter.for_context(alpha, timeout=0.2), TrackerWriter.for_context(beta, timeout=0.2)
    with lock_held_by_other_process(alpha.state_dir / 'tracker.lock'):
        with pytest.raises(TrackerBusy):
            writer_a.append('### [11-10-2026] WATCHER\n- **Mensaje:** alfa')
        writer_b.append('### [11-10-2026] WATCHER\n- **Mensaje:** beta', op_id='solo-beta')
    assert 'beta' in beta.tracker_path.read_text(encoding='utf-8')
    assert 'beta' not in alpha.tracker_path.read_text(encoding='utf-8')
    assert 'solo-beta' in journal(writer_b) and 'solo-beta' not in journal(writer_a)


def test_state_cli_lock_is_the_tracker_writer_lock(engine):
    ctx = new_project(engine)
    holder = ProjectLock(ctx, 'tracker')
    assert holder.acquire()
    try:
        with pytest.raises(TrackerBusy):
            TrackerWriter.for_context(ctx, timeout=0.2).append('x')
    finally:
        holder.release()


# ----------------------------------------------------------------------------- engine writers
@pytest.fixture
def rt(tmp_path):
    runtime = make_runtime(tmp_path, {'settle_seconds': 3600, 'rewrite_grace_seconds': 0})
    runtime.context.tracker_path.write_text('', encoding='utf-8')
    with patch.multiple(workflow, _runtime=runtime, DIRECTORIO_RAIZ=tmp_path,
                        TRACKER_PATH=str(runtime.context.tracker_path)):
        yield runtime
    runtime.close()


def test_watcher_writes_go_through_the_journal_and_release_the_lock(rt):
    workflow.write_watcher_log('⚙️ mensaje')
    records = journal(TrackerWriter.for_context(rt.context))
    assert [r['source'] for r in records.values()] == ['watcher']
    lock = ProjectLock(rt.context, 'tracker')
    assert lock.acquire(), 'no provider call may run while the watcher holds the tracker lock'
    lock.release()


def test_no_python_writer_appends_to_the_tracker_directly():
    """Every engine-side write goes through tracker_io (agent CLIs are migrated in a later stage)."""
    offenders = []
    for path in [*ROOT.glob('bmad_runtime/*.py'), *ROOT.glob('utils/*.py'),
                 *ROOT.glob('bmad-control-center/backend/services/*.py'), *ROOT.glob('bmad-control-center/backend/api/*.py')]:
        if path.name == 'tracker_io.py':
            continue
        text = path.read_text(encoding='utf-8')
        if re.search(r"open\((?:TRACKER_PATH|self\.file_path)[^)]*['\"][aw]", text):
            offenders.append(path.name)
    assert offenders == []


def run_watcher(rt, root, actions, expect=KeyboardInterrupt):
    for name in AGENT_PHASES:
        rt.state.put('agent:' + name, {'agent_id': name, 'provider': 'fake', 'model': None,
                                       'pane_id': 'p-' + name, 'state': 'ready'})
    rt.gateway.list_agents.return_value = [{'name': n, 'pane_id': 'p-' + n, 'agent_status': 'idle'} for n in AGENT_PHASES]
    steps = iter(actions)

    def sleep(_seconds):
        action = next(steps, None)
        if action is None:
            raise KeyboardInterrupt
        action()

    fake_time = types.SimpleNamespace(time=time.time, monotonic=time.monotonic, sleep=sleep)
    with patch.multiple(workflow, RETRABAJO_STATE_PATH=root / 'rework.json',
                        RETRABAJO_CLASIFICACION_PATH=root / 'rework.md', _ultimo_chequeo_vigilante=0,
                        INTERVALO_VIGILANTE_S=0, time=fake_time), \
            patch.dict(workflow.seguimiento_agentes, clear=True), \
            patch.dict(workflow.contexto_bloque, {'autor': None, 'hora': None}), \
            patch('builtins.input', return_value='n'), patch('builtins.print'), pytest.raises(expect):
        workflow.iniciar_watcher()


def test_watcher_restart_completes_an_interrupted_engine_append(rt, tmp_path):
    writer = TrackerWriter.for_context(rt.context)
    with crash(writer, 'after_write'):
        writer.append(bloque('alerta-0001'), op_id='alerta')
    run_watcher(rt, tmp_path, [])
    assert journal(writer)['alerta']['state'] == 'done'


def test_watcher_restart_stops_on_an_uncertain_engine_append(rt, tmp_path):
    writer = TrackerWriter.for_context(rt.context)
    writer.append(bloque('base-0001'))
    with crash(writer, 'partial'):
        writer.append(bloque('alerta-0001'), op_id='alerta')
    run_watcher(rt, tmp_path, [], expect=TrackerIntegrityError)
    assert rt.gateway.prompt.call_count == 0


def test_watcher_stops_when_an_unprocessed_engine_block_is_lost(rt, tmp_path):
    """The silent loss of the 4F diagnosis: a decision appended and erased before the watcher read it."""
    tracker = rt.context.tracker_path
    writer = TrackerWriter.for_context(rt.context)

    def decision_then_agent_rewrite():
        before = tracker.read_text(encoding='utf-8')
        writer.append('### [11-10-2026] HUMANO\n- **Handoff:** @BA: empieza\n', op_id='decision')
        tracker.write_text(before, encoding='utf-8')

    run_watcher(rt, tmp_path, [decision_then_agent_rewrite], expect=TrackerIntegrityError)
    assert journal(writer)['decision']['state'] == 'lost'
    assert rt.gateway.prompt.call_count == 0


# ----------------------------------------------------------------------------- D4
def test_merge_conflict_alert_is_a_human_gate_and_not_a_completed_close(rt):
    tracker = rt.context.tracker_path
    tracker.write_text('### [11-10-2026] Code Review\n- **Hora:** 12:00:00\n- **Estado:** APROBADO\n'
                       '@WATCHER: GITOPS-MERGE-CLOSE feat/004-gestion-pagos\n- **Handoff:** @PM: HU cerrada.\n',
                       encoding='utf-8')

    def fake_git(argv, **kwargs):
        if argv[1] == 'merge' and '--abort' not in argv:
            raise subprocess.CalledProcessError(1, ['git', 'merge'])
        return subprocess.CompletedProcess(argv, 0, '', '')

    with patch.object(workflow, 'run_git', fake_git), patch.object(workflow, 'auto_commit_security'), \
            patch.object(workflow, 'get_base_branch', return_value='main'), \
            patch('builtins.input', return_value='feat/004-gestion-pagos'), patch('builtins.print'):
        for _ in range(2):      # a restarted watcher re-running the same event writes one alert only
            with pytest.raises(SystemExit):
                workflow.gitops_merge_close('feat/004-gestion-pagos', 'event:' + 'ab' * 32)
        assert workflow.is_tracker_paused_for_human()

    text = tracker.read_text(encoding='utf-8')
    alert = text.split('### [')[-1]
    assert re.match(r'\d{2}-\d{2}-\d{4}\] WATCHER\n', alert)
    assert text.count('ALERTA GITOPS') == 1
    assert not [line for line in alert.splitlines() if workflow.macro_gitops(line, 'MERGE-CLOSE')]
    assert '- **Handoff:** @HUMANO:' in alert and 'hacia main' in alert
    assert 'python -m bmad_runtime.state --acknowledge event:' in alert
