import io
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import maintenance, workflow
from bmad_runtime.commands import Command
from bmad_runtime.errors import CommandError
from bmad_runtime.providers import Capabilities, default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.state import StateStore
from bmad_runtime.watcher_service import WatcherService, read_tracker
from tests.pane_doubles import ready_pane

ARTIFACT = 'docs/business-analyst/001-demo.md'


class FakeProvider:
    identifier = 'fake'
    herdr_kind = 'fake'
    capabilities = Capabilities(True, True, True, True)
    screen_profile = 'claude'   # pane_state: the fake pane renders an idle Claude-like composer

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

    def clear_instruction(self):
        raise AssertionError('planning must never request a clear instruction')


def registry():
    value = default_registry()
    value.register('fake', FakeProvider)
    return value


def block(author='Business Analyst', artifact=ARTIFACT, estado='HU redactada y validada.',
          handoff='@HUMANO: revisar la HU.'):
    lines = [f'### [09-10-2026] {author}', '- **Hora:** 10:05:00', f'- **Artefacto generado:** `{artifact}`']
    if estado:
        lines.append(f'- **Estado:** {estado}')
    lines += ['- **⚠️ Puntos Abiertos:** Ninguno.', f'- **Handoff:** {handoff}']
    return '\n'.join(lines) + '\n'


class SessionCase(unittest.TestCase):
    agents = ('business-analyst', 'solutions-architect')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD sesiones ñ ')
        self.root = Path(self.temp.name)
        (self.root / 'config_bmad.json').write_text(json.dumps({'ai': {
            'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}}}}), encoding='utf-8')
        self.herdr = {name: 'idle' for name in self.agents}
        self.gateway = Mock()
        # Legacy context: the Herdr session name is the role itself.
        self.gateway.list_agents.side_effect = lambda: [
            {'name': name, 'pane_id': 'p-' + name, 'agent_status': status} for name, status in self.herdr.items()]
        self.screens = ready_pane(self.gateway)
        self.rt = None
        self.start()
        artifact = self.root / ARTIFACT
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text('# HU demo\n', encoding='utf-8')
        self.tracker = self.rt.context.tracker_path
        self.tracker.parent.mkdir(parents=True, exist_ok=True)
        self.tracker.write_text('', encoding='utf-8')

    def start(self):
        if self.rt:
            self.rt.close()
        self.rt = Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())
        self.service = WatcherService(self.rt)
        for name in self.agents:
            if not self.rt.state.get('agent:' + name):
                self.rt.state.put('agent:' + name, {'agent_id': name, 'provider': 'fake', 'model': None,
                                                    'pane_id': 'p-' + name, 'state': 'ready', 'run_id': 'run-1',
                                                    'attempt': 1})

    def tearDown(self):
        self.rt.close()
        self.temp.cleanup()

    def append(self, text):
        with self.tracker.open('a', encoding='utf-8', newline='') as handle:
            handle.write(text)

    def sync_cursor(self):
        lines = read_tracker(self.tracker).lines
        self.service.save_cursor(lines, len(lines))

    def handoff(self, name, token, *, dispatch=True, confirm=True, report=None):
        line = f'- **Handoff:** {token} Tarea para {name}.\n'
        self.append(line)
        index = len(read_tracker(self.tracker).lines) - 1
        task = self.service.enqueue(index, line, {'agente': name, 'mensaje': line.split('**Handoff:** ')[1].strip()})
        if dispatch:
            self.service.mark(task, 'reservado')
            self.service.dispatched(task)
        if confirm:
            report = block() if report is None else report
            self.append(report)
            self.service.mark(task, 'confirmado')
            self.rt.sessions.record_summary(name, task['event_id'], report)
        self.sync_cursor()
        return task

    def plan(self):
        return {row['agent']: row for row in self.rt.sessions.plan(self.rt.state)}


class EligibilityTests(SessionCase):
    def test_confirmed_idle_agent_is_eligible_for_rotation(self):
        task = self.handoff('business-analyst', '@BA:')
        rows = self.plan()
        ba = rows['business-analyst']
        self.assertEqual((ba['eligibility'], ba['proposed_action'], ba['reasons']), ('ELIGIBLE', 'ROTATE', ['all_checks_passed']))
        self.assertEqual((ba['herdr_status'], ba['summary'], ba['clear_context_verified']), ('idle', 'complete', False))
        self.assertEqual(ba['last_confirmed_task']['task_id'], task['event_id'])
        self.assertEqual(ba['last_confirmed_task']['handoff'], '@BA: Tarea para business-analyst.')
        self.assertEqual((rows['solutions-architect']['proposed_action'], rows['solutions-architect']['reasons']),
                         ('SKIP', ['no_handoff']))
        self.gateway.prompt.assert_not_called()

    def test_verified_clear_capability_proposes_clear(self):
        self.handoff('business-analyst', '@BA:')
        with patch.object(FakeProvider, 'capabilities', Capabilities(True, True, True, True, True)):
            # The capability alone is not enough: /clear keeps the role only for Claude Code.
            self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'ROTATE')
            with patch.object(FakeProvider, 'identifier', 'claude'):
                self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'CLEAR')

    def test_summary_contents_are_bounded_and_evidence_only(self):
        task = self.handoff('business-analyst', '@BA:', report=block(estado='x' * 2000))
        summary = self.rt.state.get('session:business-analyst')
        self.assertEqual((summary['agent_id'], summary['task_id'], summary['phase'], summary['project_id']),
                         ('business-analyst', task['event_id'], 'M', 'legacy'))
        self.assertEqual(summary['workspace'], str(self.rt.context.workspace_root))
        self.assertEqual(summary['artifacts'], [{'path': ARTIFACT, 'exists': True}])
        self.assertEqual((summary['decisions'], summary['decisions_source'], summary['open_issues']), ([], 'no_registrado', []))
        self.assertEqual(summary['session_generation'], {'run_id': 'run-1', 'attempt': 1})
        self.assertLessEqual(len(summary['result']), 500)
        self.assertEqual(summary['state'], 'confirmado')

    def test_busy_agent(self):
        self.handoff('business-analyst', '@BA:')
        for status in ('working', 'blocked'):
            with self.subTest(status=status):
                self.herdr['business-analyst'] = status
                row = self.plan()['business-analyst']
                self.assertEqual((row['eligibility'], row['proposed_action'], row['reasons']),
                                 ('NOT_ELIGIBLE', 'SKIP', ['herdr_busy:' + status]))

    def test_idle_agent_with_pending_tasks(self):
        self.handoff('business-analyst', '@BA:')
        self.handoff('solutions-architect', '@SA:', dispatch=False, confirm=False)
        row = self.plan()['business-analyst']
        self.assertEqual((row['eligibility'], row['proposed_action']), ('NOT_ELIGIBLE', 'SKIP'))
        self.assertIn('pending_tasks', row['reasons'])

    def test_unconfirmed_handoff(self):
        self.handoff('business-analyst', '@BA:')
        self.handoff('business-analyst', '@BA:', confirm=False)
        row = self.plan()['business-analyst']
        self.assertEqual((row['eligibility'], row['proposed_action'], row['summary']), ('NOT_ELIGIBLE', 'SKIP', 'pending_confirmation'))
        self.assertEqual(set(row['reasons']), {'unconfirmed_tasks', 'last_handoff_unconfirmed:despachado'})

    def test_failed_or_escalated_handoff_needs_review_until_acknowledged(self):
        self.handoff('business-analyst', '@BA:')
        task = self.handoff('solutions-architect', '@SA:', confirm=False)
        self.service.mark(task, 'requiere_intervencion')
        self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'MANUAL_REVIEW')
        key = 'queued:' + task['event_id']
        self.rt.state.put(key, {**self.rt.state.get(key), 'acknowledged': time.time()})
        self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'ROTATE')
        self.assertEqual(self.plan()['solutions-architect']['reasons'], ['last_handoff_requiere_intervencion'])

    def test_followup_active(self):
        self.handoff('business-analyst', '@BA:')
        self.rt.state.put('followup', {'business-analyst': {'pane_id': 'p-business-analyst'}})
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['followup_active'])


class TrackerAndHeadlessTests(SessionCase):
    def setUp(self):
        super().setUp()
        self.handoff('business-analyst', '@BA:')

    def test_rewritten_tracker_needs_review(self):
        self.tracker.write_text('### [09-10-2026] Otro\n', encoding='utf-8')
        row = self.plan()['business-analyst']
        self.assertEqual((row['proposed_action'], row['reasons']), ('MANUAL_REVIEW', ['tracker_rewritten']))

    def test_suspended_tracker_needs_review(self):
        self.rt.state.put('tracker_integrity', {'state': 'requiere_intervencion', 'reason': 'shorter'})
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['tracker_integrity_shorter'])

    def test_unprocessed_lines_wait(self):
        for text in ('- **Handoff:** @SA: nueva\n', '@QT: parcial'):
            with self.subTest(text=text):
                self.append(text)
                row = self.plan()['business-analyst']
                self.assertEqual((row['proposed_action'], row['reasons']), ('SKIP', ['tracker_unprocessed_lines']))

    def test_missing_cursor_needs_review(self):
        self.rt.state.db.execute("DELETE FROM records WHERE id='tracker_cursor'")
        self.rt.state.db.commit()
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['tracker_cursor_missing'])

    def test_headless_execution(self):
        self.rt.state.claim('run:1', {'agent_id': 'speckit.implement'})
        row = self.plan()['business-analyst']
        self.assertEqual((row['proposed_action'], row['reasons']), ('SKIP', ['headless_active']))
        self.rt.state.finish('run:1', 'uncertain')
        self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'MANUAL_REVIEW')


class IdentityAndSummaryTests(SessionCase):
    def setUp(self):
        super().setUp()
        self.handoff('business-analyst', '@BA:')

    def test_agent_from_another_workspace(self):
        self.gateway.list_agents.side_effect = lambda: [
            {'name': 'otro-0123456789ab-business-analyst', 'pane_id': 'p-business-analyst', 'agent_status': 'idle'}]
        row = self.plan()['business-analyst']
        self.assertEqual((row['proposed_action'], row['reasons']), ('MANUAL_REVIEW', ['herdr_agent_absent']))

    def test_pane_mismatch(self):
        self.gateway.list_agents.side_effect = lambda: [
            {'name': 'business-analyst', 'pane_id': 'p-ajeno', 'agent_status': 'idle'}]
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['herdr_identity_mismatch'])

    def test_summary_from_another_workspace(self):
        summary = self.rt.state.get('session:business-analyst')
        self.rt.state.put('session:business-analyst', {**summary, 'workspace': str(self.root / 'otro')})
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['summary_workspace_mismatch'])

    def test_unknown_status_and_herdr_unavailable(self):
        self.herdr['business-analyst'] = 'unknown'
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['herdr_status_unknown'])
        self.gateway.list_agents.side_effect = CommandError('Herdr down')
        row = self.plan()['business-analyst']
        self.assertEqual((row['proposed_action'], row['reasons']), ('MANUAL_REVIEW', ['herdr_unavailable']))

    def test_not_owned_agent(self):
        row = self.rt.sessions.plan(self.rt.state, names=['qa-tech'])[0]
        self.assertEqual((row['eligibility'], row['proposed_action']), ('NOT_ELIGIBLE', 'MANUAL_REVIEW'))
        self.assertIn('not_owned_or_not_ready', row['reasons'])

    def test_incomplete_or_missing_summary(self):
        (self.root / ARTIFACT).unlink()
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['summary_incomplete:artifacts_exist'])
        self.handoff('business-analyst', '@BA:', report=block(estado=None, artifact='docs/business-analyst/x.md'))
        row = self.plan()['business-analyst']
        self.assertEqual((row['proposed_action'], row['reasons']), ('MANUAL_REVIEW', ['summary_incomplete:result,artifacts_exist']))
        self.rt.state.db.execute("DELETE FROM records WHERE id='session:business-analyst'")
        self.rt.state.db.commit()
        self.assertEqual(self.plan()['business-analyst']['reasons'], ['summary_missing'])

    def test_untracked_legacy_handoff(self):
        line = '- **Handoff:** @SA: legado\n'
        self.append(line)
        index = len(read_tracker(self.tracker).lines) - 1
        event_id = StateStore.fingerprint(index, 'solutions-architect', '@SA: legado')
        start = line.find('@SA: legado')
        self.rt.state.put('queued:' + event_id, {'state': 'done', 'agent_id': 'solutions-architect', 'line_number': index,
                                                 'line_hash': StateStore.fingerprint(line), 'start': start,
                                                 'end': start + len('@SA: legado')})
        self.sync_cursor()
        self.assertEqual(self.plan()['solutions-architect']['reasons'], ['last_handoff_untracked'])
        self.assertEqual(self.plan()['business-analyst']['proposed_action'], 'ROTATE')


class ReadOnlyCliTests(SessionCase):
    def snapshot(self):
        return {str(path): (path.stat().st_size, path.stat().st_mtime_ns) for path in self.root.rglob('*') if path.is_file()}

    def run_cli(self, *argv):
        def runtime(root, **kwargs):
            return Runtime(root, registry=registry(), gateway=self.gateway, runner=Mock(), **kwargs)

        output = io.StringIO()
        with patch.object(maintenance, 'Runtime', runtime), patch('sys.stdout', output):
            code = maintenance.plan_main(self.root, ['--plan-clear', *argv])
        return code, output.getvalue()

    def test_plan_clear_changes_nothing(self):
        self.handoff('business-analyst', '@BA:')
        self.rt.close()
        self.rt = None
        try:
            before = self.snapshot()
            code, output = self.run_cli()
            self.assertEqual(self.snapshot(), before)
        finally:
            self.start()
        self.assertEqual(code, 0)
        report = json.loads(output)
        self.assertEqual((report['mode'], report['project_id']), ('dry_run', 'legacy'))
        self.assertEqual({row['agent']: row['proposed_action'] for row in report['agents']},
                         {'business-analyst': 'ROTATE', 'solutions-architect': 'SKIP'})
        self.gateway.prompt.assert_not_called()

    def test_plan_requires_flag_and_reports_missing_state(self):
        with patch('sys.stderr'), self.assertRaises(SystemExit):
            maintenance.plan_main(self.root, [])
        state_db = self.rt.context.state_dir / 'state.sqlite3'
        self.rt.close()
        self.rt = None
        state_db.rename(state_db.with_suffix('.bak'))
        try:
            code, output = self.run_cli()
            self.assertEqual((code, json.loads(output)['reason']), (0, 'state_missing'))
            self.assertFalse(state_db.exists())
        finally:
            state_db.with_suffix('.bak').rename(state_db)
            self.start()

    def test_readonly_store_rejects_writes(self):
        store = StateStore.open_readonly(self.rt.context)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                store.put('x', {})
        finally:
            store.close()


class RestartRecoveryTests(SessionCase):
    def run_watcher(self, actions):
        steps = iter(actions)

        def sleep(_seconds):
            action = next(steps, None)
            if action is None:
                raise KeyboardInterrupt
            action()

        fake_time = types.SimpleNamespace(time=time.time, monotonic=time.monotonic, sleep=sleep)
        with patch.multiple(workflow, _runtime=self.rt, DIRECTORIO_RAIZ=self.root, TRACKER_PATH=str(self.tracker),
                            RETRABAJO_STATE_PATH=self.root / 'rework.json',
                            RETRABAJO_CLASIFICACION_PATH=self.root / 'rework.md',
                            _ultimo_chequeo_vigilante=0, INTERVALO_VIGILANTE_S=0, time=fake_time), \
                patch.dict(workflow.seguimiento_agentes, clear=True), \
                patch.dict(workflow.contexto_bloque, {'autor': None, 'hora': None}), \
                patch('builtins.print'), self.assertRaises(KeyboardInterrupt):
            workflow.iniciar_watcher()

    def test_watcher_confirmation_persists_summary_across_restart(self):
        # A @HUMANO handoff pauses the vigilante by design; use a block without dispatch tokens.
        self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU 001.\n'),
                          lambda: self.append(block(handoff='product-manager revisará la HU.'))])
        self.start()
        row = self.plan()['business-analyst']
        self.assertEqual((row['eligibility'], row['proposed_action'], row['summary']), ('ELIGIBLE', 'ROTATE', 'complete'))
        summary = self.rt.state.get('session:business-analyst')
        self.assertEqual((summary['last_handoff'], summary['result']), ('@BA: Redacta la HU 001.', 'HU redactada y validada.'))
        self.assertEqual(self.gateway.prompt.call_count, 1)


if __name__ == '__main__':
    unittest.main()
