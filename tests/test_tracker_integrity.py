import json
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import state as state_module
from bmad_runtime import workflow
from bmad_runtime.commands import Command, Result
from bmad_runtime.config import AGENT_PHASES, RuntimeConfig
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired
from bmad_runtime.providers import Capabilities, default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.state import StateStore
from bmad_runtime.watcher_service import WatcherService, read_tracker


class FakeProvider:
    identifier = 'fake'
    herdr_kind = 'fake'
    capabilities = Capabilities(True, True, True, True)

    def __init__(self, executable):
        self.executable = executable

    def validate(self, selection):
        pass

    def verify(self, *args, **kwargs):
        pass

    def interactive(self, selection, root, profile):
        return Command((self.executable, '--fake-native'), profile.parent)

    def headless(self, selection, root, prompt, directive, env):
        return Command((self.executable, 'headless'), root, stdin=prompt, env=env)

    def skill(self, root, operation):
        return 'fake-skill:' + operation

    def limit_state(self, text):
        return None

    def classify(self, result):
        return 'success' if result.returncode == 0 else 'cli_error'


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make_runtime(root, tracker=None):
    ai = {'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}}}
    if tracker is not None:
        ai['tracker'] = tracker
    (root / 'config_bmad.json').write_text(json.dumps({'ai': ai}), encoding='utf-8')
    registry = default_registry()
    registry.register('fake', FakeProvider)
    runner = Mock()
    runner.run.return_value = Result(0, '')
    rt = Runtime(root, registry=registry, gateway=Mock(), runner=runner)
    rt.context.tracker_path.parent.mkdir(parents=True, exist_ok=True)
    return rt


class TrackerCase(unittest.TestCase):
    tracker_settings = {'settle_seconds': 5, 'rewrite_grace_seconds': 10}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD tracker ñ ')
        self.root = Path(self.temp.name)
        self.rt = make_runtime(self.root, self.tracker_settings)
        self.path = self.rt.context.tracker_path
        self.clock = Clock()
        self.service = WatcherService(self.rt, clock=self.clock)

    def tearDown(self):
        self.rt.close()
        self.temp.cleanup()

    def write(self, text):
        self.path.write_bytes(text.encode('utf-8') if isinstance(text, str) else text)

    def append(self, text):
        with self.path.open('ab') as handle:
            handle.write(text.encode('utf-8') if isinstance(text, str) else text)

    def restart(self):
        self.rt.close()
        self.rt = make_runtime(self.root, self.tracker_settings)
        self.service = WatcherService(self.rt, clock=self.clock)
        return self.service

    def consume(self, service=None):
        """Mirror the watcher loop: process new verified lines once and advance the cursor."""
        service = service or self.service
        saved = self.rt.state.get('tracker_cursor')
        cursor = saved['count'] if saved else 0
        lines = service.poll(cursor)
        if lines is None:
            return None
        processed = []
        for number in range(cursor, len(lines)):
            key, claimed = service.begin_line(number, lines[number])
            if claimed:
                processed.append(lines[number])
                service.complete_line(key)
        service.save_cursor(lines, len(lines))
        return processed


class SafeReadingTests(TrackerCase):
    def test_line_written_in_two_parts(self):
        self.write('### [09-10-2026] Product Manager\n- **Handoff:** @SA: Dise')
        self.assertEqual(self.consume(), ['### [09-10-2026] Product Manager\n'])
        self.append('ña la arquitectura.\n')
        self.assertEqual(self.consume(), ['- **Handoff:** @SA: Diseña la arquitectura.\n'])

    def test_split_multibyte_character_waits(self):
        self.write(b'@SA: Dise\xc3')
        self.assertIsNone(self.service.poll(0))
        self.append(b'\xb1a\n')
        self.assertEqual(self.consume(), ['@SA: Diseña\n'])

    def test_unterminated_line_waits_for_settle_time(self):
        self.write('- **Handoff:** @BA: Redacta la HU')
        self.assertEqual(self.consume(), [])
        self.clock.now = 4.9
        self.assertEqual(self.consume(), [])
        self.clock.now = 5
        self.assertEqual(self.consume(), ['- **Handoff:** @BA: Redacta la HU\n'])
        # The writer adds the newline later: same line, nothing replayed.
        self.append('\n- **Handoff:** @SA: Siguiente\n')
        self.assertEqual(self.consume(), ['- **Handoff:** @SA: Siguiente\n'])
        self.assertIsNone(self.rt.state.get('tracker_integrity'))

    def test_settle_restarts_when_line_keeps_growing(self):
        self.write('@BA: uno')
        self.consume()
        self.clock.now = 4
        self.append(' dos')
        self.assertEqual(self.consume(), [])
        self.clock.now = 8.9
        self.assertEqual(self.consume(), [])
        self.clock.now = 9
        self.assertEqual(self.consume(), ['@BA: uno dos\n'])

    def test_crlf_and_blank_lines_match_legacy_reader(self):
        self.write('uno\r\n\r\n  \ndos\r\n')
        self.assertEqual(read_tracker(self.path).lines, self.service.read_lines())

    def test_modification_during_read_is_retried(self):
        self.write('@BA: uno\n')
        original = Path.read_bytes

        def growing(path):
            data = original(path)
            with path.open('ab') as handle:
                handle.write(b'@SA: dos\n')
            return data

        with patch.object(Path, 'read_bytes', growing):
            self.assertIsNone(self.service.poll(0))
        self.assertEqual(self.consume(), ['@BA: uno\n', '@SA: dos\n'])


class RewriteAndTruncationTests(TrackerCase):
    def setUp(self):
        super().setUp()
        self.write('### [09-10-2026] PM\n- **Handoff:** @BA: Redacta\n')
        self.consume()

    def test_transient_truncation_recovers_without_replay(self):
        self.write('')
        self.assertIsNone(self.consume())
        self.clock.now = 9.9
        self.write('### [09-10-2026] PM\n')
        self.assertIsNone(self.consume())
        self.write('### [09-10-2026] PM\n- **Handoff:** @BA: Redacta\n- **Handoff:** @SA: Nuevo\n')
        self.assertEqual(self.consume(), ['- **Handoff:** @SA: Nuevo\n'])
        self.clock.now = 30
        self.assertEqual(self.consume(), [])
        self.assertIsNone(self.rt.state.get('tracker_integrity'))

    def test_identical_rewrite_does_not_replay(self):
        self.write(self.path.read_bytes())
        self.assertEqual(self.consume(), [])

    def test_persistent_truncation_suspends_after_grace(self):
        self.write('### [09-10-2026] PM\n')
        self.assertIsNone(self.consume())
        self.clock.now = 9.9
        self.assertIsNone(self.consume())
        self.clock.now = 10
        with self.assertRaises(ReconciliationRequired):
            self.consume()
        record = self.rt.state.get('tracker_integrity')
        self.assertEqual((record['state'], record['reason'], record['cursor'], record['observed_lines']),
                         ('requiere_intervencion', 'shorter', 2, 1))
        self.assertEqual(self.path.read_text(encoding='utf-8'), '### [09-10-2026] PM\n', 'tracker must not be written')

    def test_persistent_rewrite_and_missing_file_suspend(self):
        for change, reason in [(lambda: self.write('### [09-10-2026] XX\n- **Handoff:** @BA: Redacta\n'), 'rewritten'),
                               (lambda: self.path.unlink(), 'missing')]:
            with self.subTest(reason=reason):
                change()
                service = WatcherService(self.rt, clock=self.clock)
                self.clock.now = 100
                self.assertIsNone(service.poll(2))
                self.clock.now = 110
                with self.assertRaises(ReconciliationRequired):
                    service.poll(2)
                self.assertEqual(self.rt.state.get('tracker_integrity')['reason'], reason)

    def test_zero_grace_keeps_immediate_suspension(self):
        self.rt.config.data['tracker']['rewrite_grace_seconds'] = 0
        service = WatcherService(self.rt, clock=self.clock)
        self.write('')
        with self.assertRaises(ReconciliationRequired):
            service.poll(2)


class RestartAndStateTests(TrackerCase):
    def test_restart_during_partial_write(self):
        self.write('@BA: uno\n@SA: Dise')
        self.assertEqual(self.consume(), ['@BA: uno\n'])
        service = self.restart()
        lines = service.startup_lines(sleep=Mock(side_effect=AssertionError('no wait expected')))
        self.assertEqual(service.restore_cursor(lines, 0), 1)
        self.append('ña\n')
        self.assertEqual(self.consume(), ['@SA: Diseña\n'])

    def test_restart_after_settled_unterminated_line(self):
        self.write('@BA: uno')
        self.assertEqual(self.consume(), [])
        self.clock.now = 5
        self.assertEqual(self.consume(), ['@BA: uno\n'])
        service = self.restart()
        self.clock.now = 6
        lines = service.startup_lines(sleep=Mock(side_effect=AssertionError('no wait expected')))
        self.assertEqual(service.restore_cursor(lines, 0), 1)
        self.assertEqual(self.consume(), [])

    def test_duplicate_events_are_claimed_once(self):
        line = '- **Handoff:** @BA: Redacta\n'
        key, claimed = self.service.begin_line(0, line)
        self.assertTrue(claimed)
        self.service.complete_line(key)
        self.assertEqual(self.service.begin_line(0, line), (key, False))
        task = {'agente': 'business-analyst', 'mensaje': '@BA: Redacta'}
        self.assertEqual(self.service.enqueue(0, line, task), self.service.enqueue(0, line, task))
        rows = list(self.rt.state.db.execute("SELECT id FROM records WHERE id LIKE 'queued:%'"))
        self.assertEqual(len(rows), 1)

    def test_in_flight_event_requires_reconciliation(self):
        self.service.begin_line(0, '@BA: uno\n')
        with self.assertRaises(ReconciliationRequired):
            self.service.begin_line(0, '@BA: uno\n')

    def test_sqlite_recovery_of_queue_cursor_and_stages(self):
        line = '- **Handoff:** @BA: Redacta\n'
        self.write(line)
        task = self.service.enqueue(0, line, {'agente': 'business-analyst', 'mensaje': '@BA: Redacta'})
        self.service.mark(task, 'reservado')
        self.service.save_cursor([line], 1)
        service = self.restart()
        lines = service.startup_lines()
        self.assertEqual(service.restore_cursor(lines, 0), 1)
        self.assertEqual(service.pending_tasks(lines), [task])
        record = self.rt.state.get('queued:' + task['event_id'])
        self.assertEqual((record['state'], record['stage'], set(record['stages'])),
                         ('queued', 'reservado', {'detectado', 'reservado'}))
        service.dispatched(task)
        self.assertEqual(service.pending_tasks(lines), [])
        record = self.rt.state.get('queued:' + task['event_id'])
        self.assertEqual((record['state'], record['stage']), ('done', 'despachado'))

    def test_legacy_cursor_and_queue_without_final_newline(self):
        # State written by the previous reader for an unterminated last line.
        self.write('@BA: uno\n@SA: dos\n')
        self.rt.state.put('tracker_cursor', {'count': 2, 'prefix_hash': StateStore.fingerprint('@BA: uno\n', '@SA: dos')})
        event_id = StateStore.fingerprint(1, 'solutions-architect', '@SA: dos')
        self.rt.state.put('queued:' + event_id, {'state': 'queued', 'agent_id': 'solutions-architect', 'line_number': 1,
                                                 'line_hash': StateStore.fingerprint('@SA: dos'), 'start': 0, 'end': 8})
        lines = self.service.startup_lines()
        self.assertEqual(self.service.restore_cursor(lines, 0), 2)
        self.assertEqual(self.service.pending_tasks(lines)[0]['mensaje'], '@SA: dos')

    def test_failure_stages(self):
        task = self.service.enqueue(0, '@BA: uno\n', {'agente': 'business-analyst', 'mensaje': '@BA: uno'})
        self.service.failed(task, 'ReconciliationRequired')
        self.assertEqual(self.rt.state.get('queued:' + task['event_id'])['stage'], 'fallido')
        self.rt.state.claim('dispatch:' + task['event_id'])
        self.service.failed(task, 'CommandError')
        record = self.rt.state.get('queued:' + task['event_id'])
        self.assertEqual((record['state'], record['stage'], record['failure']),
                         ('queued', 'requiere_intervencion', 'CommandError'))

    def test_rebaseline_requires_confirmation_and_never_replays(self):
        self.write('@BA: uno\n')
        self.consume()
        self.write('@BA: corregido\n@SA: dos\n@QT: parcial')
        self.rt.state.put('tracker_integrity', {'state': 'requiere_intervencion', 'reason': 'rewritten'})
        with patch('builtins.print'), patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                state_module.main(['--root', str(self.root), '--rebaseline-tracker'])
            self.assertEqual(state_module.main(['--root', str(self.root), '--rebaseline-tracker', '--confirm']), 0)
        self.assertEqual(self.rt.state.get('tracker_integrity')['state'], 'done')
        self.assertEqual(self.consume(), [])
        self.append('\n')
        self.assertEqual(self.consume(), ['@QT: parcial\n'])


class TrackerConfigTests(unittest.TestCase):
    def test_defaults_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config_bmad.json').write_text(json.dumps({'ai': {}}), encoding='utf-8')
            self.assertEqual(RuntimeConfig.load(root).data['tracker'], {'settle_seconds': 4, 'rewrite_grace_seconds': 10})
            for value in [{'settle_seconds': -1}, {'rewrite_grace_seconds': 3601}, {'settle_seconds': True},
                          {'unknown': 1}, []]:
                (root / 'config_bmad.json').write_text(json.dumps({'ai': {'tracker': value}}), encoding='utf-8')
                with self.subTest(value=value), self.assertRaises(ConfigurationError):
                    RuntimeConfig.load(root)


class WatcherLoopTests(unittest.TestCase):
    """Simulated integration of iniciar_watcher: real loop, SQLite and tracker; Herdr is a double."""
    settings = {'settle_seconds': 3600, 'rewrite_grace_seconds': 3600}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD watcher ñ ')
        self.root = Path(self.temp.name)
        self.prompts = []
        self.rt = None

    def tearDown(self):
        if self.rt:
            self.rt.close()
        self.temp.cleanup()

    def start(self):
        if self.rt:
            self.rt.close()
        self.rt = make_runtime(self.root, self.settings)
        for name in AGENT_PHASES:
            self.rt.state.put('agent:' + name, {'agent_id': name, 'provider': 'fake', 'model': None,
                                                'pane_id': 'p-' + name, 'state': 'ready'})
        self.rt.gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p-' + name, 'agent_status': 'idle'}
                                                    for name in AGENT_PHASES]
        self.rt.gateway.prompt.side_effect = lambda pane, text: self.prompts.append((pane, text))
        return self.rt.context.tracker_path

    def run_watcher(self, actions, expect=KeyboardInterrupt):
        tracker = self.rt.context.tracker_path
        steps = iter(actions)

        def sleep(_seconds):
            action = next(steps, None)
            if action is None:
                raise KeyboardInterrupt
            action()

        fake_time = types.SimpleNamespace(time=time.time, monotonic=time.monotonic, sleep=sleep)
        with patch.multiple(workflow, _runtime=self.rt, DIRECTORIO_RAIZ=self.root, TRACKER_PATH=str(tracker),
                            RETRABAJO_STATE_PATH=self.root / 'rework.json',
                            RETRABAJO_CLASIFICACION_PATH=self.root / 'rework.md',
                            _ultimo_chequeo_vigilante=0, INTERVALO_VIGILANTE_S=0, time=fake_time), \
                patch.dict(workflow.seguimiento_agentes, clear=True), \
                patch.dict(workflow.contexto_bloque, {'autor': None, 'hora': None}), \
                patch('builtins.print'), self.assertRaises(expect):
            workflow.iniciar_watcher()

    def append(self, text):
        def action():
            with self.rt.context.tracker_path.open('ab') as handle:
                handle.write(text.encode('utf-8'))
        return action

    def queued(self):
        return {json.loads(data)['agent_id']: json.loads(data)
                for _, data in self.rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'")}

    def test_consecutive_handoffs_partial_write_and_rewrite(self):
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        # The opening handoff comes from a human: an agent-authored block without dispatch stops the flow (H11).
        pm = '### [09-10-2026] Operador humano\n- **Hora:** 10:00:00\n- **Handoff:** @BA: Redacta la HU 001.\n'
        ba = '### [09-10-2026] Business Analyst\n- **Hora:** 10:05:00\n- **Handoff:** @SA: Dise'
        self.run_watcher([
            self.append(pm),
            self.append(ba),
            self.append('ña la arquitectura.\n'),
            lambda: tracker.write_bytes(tracker.read_bytes()),   # whole-file rewrite by an agent tool
        ])
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst', 'p-solutions-architect'])
        self.assertIn('@BA:', self.prompts[0][1])
        self.assertIn('@SA:', self.prompts[1][1])
        queued = self.queued()
        task = self.rt.context.output(queued['solutions-architect']['task_file']).read_text(encoding='utf-8')
        self.assertTrue(task.endswith('@SA: Diseña la arquitectura.\n'))
        self.assertEqual(queued['business-analyst']['state'], 'done')
        self.assertEqual(set(queued['business-analyst']['stages']), {'detectado', 'reservado', 'despachado', 'confirmado'})
        self.assertEqual((queued['solutions-architect']['state'], queued['solutions-architect']['stage']), ('done', 'despachado'))
        self.assertEqual(tracker.read_text(encoding='utf-8'), pm + ba + 'ña la arquitectura.\n', 'watcher wrote to tracker')

    def test_restart_during_partial_write_dispatches_each_handoff_once(self):
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        self.run_watcher([
            self.append('- **Handoff:** @BA: Redacta la HU 001.\n'),
            self.append('- **Handoff:** @SA: Dise'),
        ])
        self.start()
        self.run_watcher([self.append('ña la arquitectura.\n')])
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst', 'p-solutions-architect'])
        task = self.rt.context.output(self.queued()['solutions-architect']['task_file']).read_text(encoding='utf-8')
        self.assertTrue(task.endswith('@SA: Diseña la arquitectura.\n'))

    def test_persistent_truncation_stops_without_dispatch(self):
        self.settings = {'settle_seconds': 0, 'rewrite_grace_seconds': 0}
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        with self.assertRaises(ReconciliationRequired):
            self.run_watcher([self.append('- **Handoff:** @BA: uno\n'),
                              lambda: tracker.write_text('', encoding='utf-8'),
                              self.append('- **Handoff:** @SA: dos\n')])
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst'])
        self.assertEqual(self.rt.state.get('tracker_integrity')['reason'], 'shorter')

    def queued_by_text(self, text):
        lines = read_tracker(self.rt.context.tracker_path).lines
        for key, raw in self.rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'"):
            data = json.loads(raw)
            if text in lines[data['line_number']]:
                event_id = key[len('queued:'):]
                return {**data, 'event_id': event_id, 'dispatch': self.rt.state.get('dispatch:' + event_id)}
        raise AssertionError(f'No queued handoff for {text}')

    def test_active_followup_holds_next_handoff_to_same_agent(self):
        # Herdr reports the agent idle while its previous handoff has no block yet: dispatching again would
        # replace the followup and leave the first handoff unconfirmed forever.
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        self.run_watcher([
            self.append('- **Handoff:** @BA: Redacta la HU 001.\n'),
            self.append('- **Handoff:** @BA: Redacta la HU 002.\n'),
            lambda: None,
        ])
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst'])
        first, second = self.queued_by_text('HU 001'), self.queued_by_text('HU 002')
        self.assertEqual((first['state'], first['stage']), ('done', 'despachado'))
        self.assertEqual((second['state'], second['stage'], second['dispatch']), ('queued', 'detectado', None))
        self.assertEqual(self.rt.state.get('followup')['business-analyst']['event_id'], first['event_id'])

        # The held handoff survives a restart; the agent's block confirms the first one and releases the second.
        self.start()
        block = '### [09-10-2026] Business Analyst\n- **Hora:** 10:05:00\n- **Estado:** HU redactada\n'
        self.run_watcher([self.append(block), lambda: None, lambda: None])
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst'] * 2)
        first, second = self.queued_by_text('HU 001'), self.queued_by_text('HU 002')
        self.assertEqual(first['stage'], 'confirmado')
        self.assertEqual((second['state'], second['stage']), ('done', 'despachado'))
        self.assertEqual(self.rt.state.get('followup')['business-analyst']['event_id'], second['event_id'])
        self.assertEqual(workflow.protocol_violations(self.rt.state), [])

    def test_escalated_followup_releases_the_held_handoff(self):
        # Escalation without a block ends the followup (same release as before the hold existed).
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        self.run_watcher([self.append('- **Handoff:** @BA: Redacta la HU 001.\n'),
                          self.append('- **Handoff:** @BA: Redacta la HU 002.\n')])
        self.assertEqual(len(self.prompts), 1)
        followup = self.rt.state.get('followup')
        followup['business-analyst'].update(recordatorios=workflow.MAX_RECORDATORIOS, vio_trabajando=True,
                                            idle_desde=0)
        self.rt.state.put('followup', followup)
        self.start()
        self.run_watcher([lambda: None, lambda: None])
        self.assertEqual(self.queued_by_text('HU 001')['stage'], 'requiere_intervencion')
        self.assertEqual(self.queued_by_text('HU 002')['stage'], 'despachado')
        self.assertEqual([pane for pane, _ in self.prompts], ['p-business-analyst'] * 2)

    def test_merge_conflict_explains_manual_reconciliation_and_never_repeats_the_merge(self):
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        merges = []

        def git(argv, **kwargs):
            if argv[:2] == ['git', 'merge'] and '--abort' not in argv:
                merges.append(argv)
                raise workflow.subprocess.CalledProcessError(1, argv)
            return types.SimpleNamespace(stdout='main\n' if 'branch' in argv else '', returncode=0)

        with patch.object(workflow, 'run_git', git), patch('builtins.input', return_value='feat/001-a'):
            self.run_watcher([self.append('@WATCHER: GITOPS-MERGE-CLOSE feat/001-a\n')], expect=SystemExit)
            events = [(key, json.loads(raw)) for key, raw in
                      self.rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'event:%'")]
            self.assertEqual([data['state'] for _, data in events], ['in_flight'])
            key = events[0][0]
            text = tracker.read_text(encoding='utf-8')
            self.assertIn('reiniciar el Watcher NO la resuelve', text)
            self.assertIn(f'python -m bmad_runtime.state --acknowledge {key} --confirm', text)
            self.assertNotIn('asumirá el cierre', text)

            # Fail-closed: a restart alone stops again on the in_flight macro, without merging.
            self.start()
            with self.assertRaises(ReconciliationRequired):
                self.run_watcher([lambda: None])
            with patch('sys.stdout'):
                self.assertEqual(state_module.main(['--root', str(self.root), '--acknowledge', key, '--confirm']), 0)
            self.start()
            self.run_watcher([lambda: None])
        self.assertEqual(len(merges), 1)
        self.assertEqual(self.prompts, [])

    def test_reconcile_command_keeps_the_project_selection(self):
        context = types.SimpleNamespace(legacy=False, workspace_root=Path('D:/Proyectos/Agenda'),
                                        project_id='agenda-citas')
        with patch.object(workflow, '_runtime', types.SimpleNamespace(context=context)):
            command = workflow.comando_reconciliar_evento('event:abc')
        self.assertEqual(command, f'python -m bmad_runtime.state --workspace "{Path("D:/Proyectos/Agenda")}" '
                                  '--project agenda-citas --acknowledge event:abc --confirm')

    def test_human_and_watcher_tokens_are_not_dispatched(self):
        tracker = self.start()
        tracker.write_text('', encoding='utf-8')
        self.run_watcher([self.append('- **Handoff:** @HUMANO: decide.\n@WATCHER: nota\n')])
        self.assertEqual(self.prompts, [])


if __name__ == '__main__':
    unittest.main()
