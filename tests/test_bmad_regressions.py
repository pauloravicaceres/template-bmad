import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import watcher_bmad as workflow
from bmad_runtime.cli import launcher_main, spec_plan
from bmad_runtime.commands import Command, Result
from bmad_runtime.config import RuntimeConfig, Selection
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired, UnsupportedCapability
from bmad_runtime.gitops import GitService
from bmad_runtime.herdr import HerdrGateway
from bmad_runtime.maintenance import close_owned_tabs
from bmad_runtime.providers import ClaudeProvider, CodexProvider
from bmad_runtime.runtime import Runtime


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tracker = self.root / 'tracker.md'
        self.tracker.write_text('', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_human_gate_survives_informational_log(self):
        self.tracker.write_text('### [08-10-2026] QA Documental\n- **Handoff:** @HUMANO: decide\n\n### [08-10-2026] WATCHER\n- **Mensaje:** esperando\n', encoding='utf-8')
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)):
            self.assertTrue(workflow.is_tracker_paused_for_human())

    def test_human_gate_blocks_sdd_trigger(self):
        with patch.object(workflow, 'is_tracker_paused_for_human', return_value=True), patch.object(workflow, 'ejecutar_sdd_fase_implementacion') as implement:
            self.assertEqual(workflow.extraer_instrucciones('@DEV-BACK: arquitectura aprobada'), [])
            implement.assert_not_called()

    def test_human_approval_releases_gate_and_keeps_macro_before_handoff(self):
        from utils import approve_step
        self.tracker.write_text('### [08-10-2026] QA Documental\n- **Handoff:** @HUMANO: decide\n', encoding='utf-8')
        with patch.object(approve_step, 'TRACKER_PATH', self.tracker), patch.object(workflow, 'TRACKER_PATH', str(self.tracker)):
            approve_step.registrar_aprobacion('@WATCHER: GITOPS-BRANCH-CREATE feat/test\n@BA: empieza', 'spec.md')
            self.assertFalse(workflow.is_tracker_paused_for_human())
        text = self.tracker.read_text(encoding='utf-8')
        self.assertLess(text.index('@WATCHER:'), text.index('@BA:'))

    def test_clarify_failure_does_not_handoff(self):
        with patch.object(workflow, 'is_tracker_paused_for_human', return_value=True), patch.object(workflow, 'write_watcher_log'), patch.object(workflow, 'ejecutar_speckit', return_value=Result(1)), patch.object(workflow, 'registrar_traspaso_fase_a') as handoff:
            with self.assertRaises(ReconciliationRequired):
                workflow.extraer_instrucciones('@WATCHER: /speckit.clarify respuesta')
            handoff.assert_not_called()

    def test_rework_analyze_failure_stops_converge(self):
        with patch.object(workflow, 'get_current_branch', return_value='feat/test'), patch.object(workflow, '_leer_estado_retrabajo', return_value={}), patch.object(workflow, '_guardar_estado_retrabajo'), patch.object(workflow, 'write_watcher_log'), patch.object(workflow, 'ejecutar_speckit', return_value=Result(1)) as execute:
            self.assertFalse(workflow.ejecutar_sdd_retrabajo('Code Review', '**Handoff:** @DEV-BACK: rejected'))
            execute.assert_called_once_with('analyze')

    def test_rework_iteration_limit_escalates_without_process(self):
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)), patch.object(workflow, 'get_current_branch', return_value='feat/test'), patch.object(workflow, '_leer_estado_retrabajo', return_value={'feat/test': 2}), patch.object(workflow, 'ejecutar_speckit') as execute:
            self.assertFalse(workflow.ejecutar_sdd_retrabajo('Code Review', '**Handoff:** @DEV-BACK: rejected'))
            execute.assert_not_called()
            self.assertIn('@HUMANO:', self.tracker.read_text(encoding='utf-8'))

    def test_sdd_order_and_freeze_gate(self):
        rt = Mock()
        with patch.object(workflow, 'runtime', return_value=rt), patch.object(workflow, 'TRACKER_PATH', str(self.tracker)), patch.object(workflow, 'write_watcher_log'), patch.object(workflow, 'ejecutar_speckit', side_effect=[Result(0), Result(0), Result(1)]) as execute, patch.object(workflow, 'GitService') as git:
            self.assertFalse(workflow.ejecutar_sdd_fase_arquitectura())
            self.assertEqual([call.args[0] for call in execute.call_args_list], ['plan', 'tasks', 'analyze'])
            git.assert_not_called()
            self.assertNotIn('@DA:', self.tracker.read_text())

    def test_git_preserves_staged_work(self):
        rt = Mock()
        rt.config.root = self.root
        rt.runner.run.return_value = Result(0, 'user-file.txt')
        with self.assertRaises(ReconciliationRequired):
            GitService(rt).freeze()
        self.assertEqual(rt.runner.run.call_count, 1)

    def test_herdr_prompt_is_literal_and_redacted(self):
        runner = Mock()
        runner.run.return_value = Result(0)
        gateway = HerdrGateway(runner, self.root)
        payload = '"; & del * | $secret\ná'
        gateway.prompt('pane123', payload)
        command = runner.run.call_args.args[0]
        self.assertEqual(command.argv[:4], ('herdr', 'agent', 'prompt', 'pane123'))
        self.assertEqual(command.argv[4], payload)
        self.assertNotIn(payload, str(command.sanitized()))

    def test_herdr_rejects_error_envelope(self):
        runner = Mock()
        runner.run.return_value = Result(0, '{"ok":false,"error":"denied"}')
        with self.assertRaises(Exception):
            HerdrGateway(runner, self.root).list_agents()

    def test_skill_must_exist_and_match_resources(self):
        for provider, folder in [(ClaudeProvider(), '.claude'), (CodexProvider(), '.agents')]:
            with self.assertRaises(UnsupportedCapability):
                provider.skill(self.root, 'implement')
            source = self.root / '.github/skills/speckit-implement'
            destination = self.root / folder / 'skills/speckit-implement'
            source.mkdir(parents=True, exist_ok=True)
            destination.mkdir(parents=True, exist_ok=True)
            text = '---\nname: speckit-implement\n---\nDo the work.'
            (source / 'SKILL.md').write_text(text)
            (destination / 'SKILL.md').write_text(text)
            self.assertTrue(provider.skill(self.root, 'implement').endswith('speckit-implement'))
            (destination / 'SKILL.md').write_text(text + ' Different semantics.')
            with self.assertRaises(UnsupportedCapability):
                provider.skill(self.root, 'implement')

    def test_flags_missing_from_installed_help_are_rejected(self):
        runner = Mock()
        runner.run.return_value = Result(0, 'old CLI help')
        for provider in [ClaudeProvider(), CodexProvider()]:
            with self.assertRaises(UnsupportedCapability):
                provider.verify(runner, self.root, headless=True)

    def test_config_invalid_inputs(self):
        for ai in [{'schema_version': 2}, {'limits': {'max_processes': 0}}, {'defaults': {'model': '--injected'}}, {'speckit': {'unknown': {}}}, {'providers': {'claude': {'token': 'no'}}}]:
            (self.root / 'config_bmad.json').write_text(json.dumps({'ai': ai}))
            with self.assertRaises(ConfigurationError):
                RuntimeConfig.load(self.root)

    def test_dry_run_starts_no_process_and_writes_no_state(self):
        from bmad_runtime.fleet import TABS_CONFIG
        for agents in TABS_CONFIG.values():
            for agent in agents:
                folder = self.root / agent['name']
                folder.mkdir()
                (folder / 'AGENTS.md').write_text('profile')
        (self.root / 'config_bmad.json').write_text('{"ai":{"agents":{"business-analyst":{"provider":"gemini"}}}}')
        with patch('subprocess.Popen', side_effect=AssertionError('dry-run spawned process')), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(launcher_main(self.root, ['--dry-run']), 0)
        rows = json.loads(output.getvalue())
        self.assertEqual(next(r for r in rows if r['name'] == 'business-analyst')['status'], 'pending')
        self.assertFalse((self.root / '.bmad-runtime').exists())

    def test_no_direct_provider_or_herdr_calls_outside_adapters(self):
        repo = Path(__file__).resolve().parents[1]
        for path in [repo / 'watcher_bmad.py', repo / 'utils/start_agents.py', repo / 'utils/stop_agents.py', repo / 'bmad_runtime/workflow.py']:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotEqual(ast.unparse(node.func), 'subprocess.run', str(path))

    def test_close_tabs_rejects_unowned_pane(self):
        rt = Mock()
        rt.config.root = self.root
        rt.gateway.list_agents.return_value = []
        rt.gateway.list_panes.return_value = [{'pane_id': 'unowned', 'tab_id': 't'}]
        rt.gateway.list_tabs.return_value = [{'tab_id': 't'}]
        rt.state.get.return_value = {'project': str(self.root)}
        with self.assertRaises(ReconciliationRequired):
            close_owned_tabs(rt)
        rt.gateway.close_tab.assert_not_called()


if __name__ == '__main__':
    unittest.main()
