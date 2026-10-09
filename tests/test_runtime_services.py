import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from bmad_runtime.commands import Command, Result
from bmad_runtime.config import Selection
from bmad_runtime.errors import ReconciliationRequired, UnsupportedCapability
from bmad_runtime.fleet import FleetOrchestrator, TABS_CONFIG
from bmad_runtime.providers import Capabilities, default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.state import StateStore, project_lock
from bmad_runtime.watcher_service import WatcherService


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

    def classify(self, result):
        return 'success' if result.returncode == 0 else 'cli_error'


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD pruebas ñ ')
        self.root = Path(self.temp.name)
        (self.root / 'config_bmad.json').write_text(json.dumps({'ai': {
            'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}}}}))
        registry = default_registry()
        registry.register('fake', FakeProvider)
        self.gateway = Mock()
        self.gateway.list_agents.return_value = []
        self.gateway.create_tab.side_effect = [('t1', 'p1'), ('t2', 'p2'), ('t3', 'p3')]
        self.gateway.split.side_effect = [f'split{i}' for i in range(10)]
        self.runner = Mock()
        self.runner.run.return_value = Result(0, 'done')
        self.rt = Runtime(self.root, registry=registry, gateway=self.gateway, runner=self.runner)

    def tearDown(self):
        self.rt.close()
        self.temp.cleanup()

    def test_external_provider_launches_without_orchestrator_edits(self):
        self.assertEqual(FleetOrchestrator(self.rt).launch(), 13)
        self.assertEqual(self.gateway.start.call_count, 13)
        self.assertEqual(self.rt.state.get('agent:business-analyst')['provider'], 'fake')

    def test_speckit_provider_independent_of_trigger_agent(self):
        result = self.rt.spec.execute('implement')
        self.assertEqual(result.returncode, 0)
        prompt = self.runner.run.call_args.args[0].stdin
        self.assertTrue(prompt.endswith('fake-skill:implement'))
        self.assertIn('CONTEXTO BMAD:', prompt)

    def test_partial_launch_never_succeeds_or_closes_tabs(self):
        self.gateway.start.side_effect = RuntimeError('partial')
        with self.assertRaises(RuntimeError):
            FleetOrchestrator(self.rt).launch()
        self.assertEqual(self.rt.state.get('agent:business-storyteller')['state'], 'uncertain')
        self.gateway.focus.assert_not_called()
        self.gateway.close.assert_not_called()

    def test_existing_session_prevents_duplicate_launch(self):
        self.gateway.list_agents.return_value = [{'name': 'business-analyst'}]
        with self.assertRaises(ReconciliationRequired):
            FleetOrchestrator(self.rt).launch()
        self.gateway.create_tab.assert_not_called()

    def test_persistent_dedupe_and_ambiguous_restart(self):
        store = self.rt.state
        self.assertTrue(store.claim('completed'))
        store.finish('completed', 'done')
        other = StateStore(self.root)
        try:
            self.assertFalse(other.claim('completed'))
            store.claim('interrupted')
            with self.assertRaises(ReconciliationRequired):
                other.claim('interrupted')
        finally:
            other.close()

    def test_dispatch_duplicate_and_ownership(self):
        self.rt.state.put('agent:business-analyst', {'provider': 'fake', 'model': None, 'pane_id': 'p', 'state': 'ready'})
        self.gateway.list_agents.return_value = [{'name': 'business-analyst', 'pane_id': 'p', 'agent_status': 'idle'}]
        dispatcher = self.rt.dispatcher
        self.assertTrue(dispatcher.dispatch('business-analyst', 'p', 'write', 'one'))
        self.assertFalse(dispatcher.dispatch('business-analyst', 'p', 'write', 'one'))
        self.gateway.prompt.assert_called_once()
        with self.assertRaises(ReconciliationRequired):
            dispatcher.dispatch('business-analyst', 'other-project', 'write', 'two')

    def test_safe_context_cleanup(self):
        self.rt.state.put('agent:business-analyst', {'provider': 'fake', 'model': None, 'pane_id': 'p', 'state': 'ready'})
        with self.assertRaises(UnsupportedCapability):
            self.rt.sessions.clear('business-analyst')
        self.gateway.prompt.assert_not_called()

    def test_queue_restart_preserves_reference_without_prompt(self):
        service = WatcherService(self.rt)
        lines = ['- **Handoff:** @BA: texto secreto\n']
        task = {'agente': 'business-analyst', 'mensaje': '@BA: texto secreto'}
        queued = service.enqueue(0, lines[0], task)
        service.save_cursor(lines, 1)
        self.assertEqual(service.pending_tasks(lines), [queued])
        self.assertEqual(service.restore_cursor(lines, 0), 1)
        raw = str(list(self.rt.state.db.execute('SELECT data FROM records')))
        self.assertNotIn('texto secreto', raw)
        with self.assertRaises(ReconciliationRequired):
            service.restore_cursor(['changed'], 0)

    def test_instance_lock(self):
        with project_lock(self.root, 'watcher'):
            with self.assertRaises(ReconciliationRequired):
                with project_lock(self.root, 'watcher'):
                    pass


if __name__ == '__main__':
    unittest.main()
