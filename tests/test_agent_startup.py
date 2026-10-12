"""Phase 4B.1: agent startup and recovery (H8 pane PATH, H10 trust dialog, H11 out-of-protocol execution).

Herdr, Claude and Codex are stateful fakes; nothing real is launched and no dialog is ever answered.
"""
import json
import os
from pathlib import Path
import time
import types
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import maintenance, workflow
from bmad_runtime.errors import AgentBlocked, CommandError, ReconciliationRequired, UnsupportedCapability
from bmad_runtime.fleet import FleetOrchestrator
from bmad_runtime.providers import ClaudeProvider, CodexProvider
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import EXECUTION_RULE, agent_contract, contract_path, interactive_command
from bmad_runtime.watcher_service import audit_blocks, maintenance_blocks, protocol_violations
from tests.test_session_lifecycle import block
from tests.test_session_maintenance import BA, SA, FakeHerdr, MaintenanceCase, registry

TRUST_SCREEN = ('Accessing workspace: C:\\ws\n Quick safety check: Is this a project you created or one you trust?\n'
                ' Claude Code\'ll be able to read, edit, and execute files here.\n Do you trust the files in this folder?\n'
                ' ❯ 1. Yes, I trust this folder\n   2. No, exit\n Enter to confirm · Esc to cancel\n')
STORE_PWSH = r'C:\Users\U\AppData\Local\Microsoft\WindowsApps\pwsh.exe'
windows_only = unittest.skipUnless(os.name == 'nt', 'pane PATH checks apply to Windows panes only')


class FleetHerdr(FakeHerdr):
    """Adds tab/pane creation so the real FleetOrchestrator can run against the fake."""

    def __init__(self, workspace):
        super().__init__()
        self.workspace, self.counter = str(workspace), 0

    def _pane(self):
        self.counter += 1
        pane = f'n{self.counter}'
        self.output[pane], self.memory[pane], self.cwd[pane] = 'PS> ', None, self.workspace
        return pane

    def create_tab(self, label, cwd):
        return f't{self.counter}', self._pane()

    def split(self, pane, direction, cwd):
        return self._pane()

    def rename(self, pane, name):
        pass

    def focus(self, tab):
        pass


class StartupCase(MaintenanceCase):
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

    def prompts(self, pane):
        return [call[2] for call in self.calls(pane) if call[0] == 'prompt']

    def violations(self):
        return protocol_violations(self.rt.state)

    def fleet_runtime(self, config=None):
        self.rt.close()
        if config:
            (self.root / 'config_bmad.json').write_text(json.dumps(config), encoding='utf-8')
        self.gateway = FleetHerdr(self.root)
        self.rt = Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())
        self.gateway.root, self.gateway.context = self.root, self.rt.context
        for name in self.agents:
            self.rt.state.db.execute("DELETE FROM records WHERE id=?", ('agent:' + name,))
        self.rt.state.db.commit()


@windows_only
class PanePathTests(StartupCase):
    provider = 'fake-codex'

    def rotate(self):
        self.handoff(BA, '@BA:')
        with patch.object(maintenance, 'native_pwsh', return_value=(r'C:\Program Files\PowerShell\7\pwsh.exe', True)):
            return self.maintenance().run('ROTATE', BA)

    def test_pane_with_correct_path(self):
        op = self.rotate()
        shell = next(e for e in op['evidence'] if e['step'] == 'pane_shell')
        self.assertEqual((op['state'], shell['checked'], shell['repaired']), ('COMPLETED', True, False))
        self.assertEqual([c[0] for c in self.calls('p-' + BA)], ['submit', 'run', 'start', 'prompt'])

    def test_restored_pane_with_store_alias_is_repaired_for_that_pane_only(self):
        self.gateway.pane_pwsh['p-' + BA] = STORE_PWSH
        op = self.rotate()
        shell = next(e for e in op['evidence'] if e['step'] == 'pane_shell')
        self.assertEqual((op['state'], shell['pane_pwsh'], shell['repaired']), ('COMPLETED', STORE_PWSH, True))
        self.assertEqual(shell['pane_pwsh_after'], self.gateway.good_pwsh)
        commands = [c[2] for c in self.calls('p-' + BA) if c[0] == 'run']
        self.assertEqual(len(commands), 3)
        self.assertTrue(commands[1].startswith('$env:Path'))
        self.assertEqual(self.calls('p-' + SA), [])

    def test_pane_that_cannot_be_repaired_refuses_the_start(self):
        self.gateway.pane_pwsh['p-' + BA] = STORE_PWSH
        self.gateway.repaired_pwsh = STORE_PWSH
        with self.assertRaises(ReconciliationRequired) as raised:
            self.rotate()
        self.assertIn('Install PowerShell 7', str(raised.exception))
        self.assertNotIn('start', [c[0] for c in self.calls()])
        op = self.ops()[0]
        self.assertEqual((op['state'], op['errors'][-1]['during']), ('REQUIRES_INTERVENTION', 'STARTING'))

    def test_store_only_machine_refused_before_exit(self):
        self.handoff(BA, '@BA:')
        with patch.object(maintenance, 'native_pwsh', return_value=(STORE_PWSH, False)):
            with self.assertRaises(UnsupportedCapability):
                self.maintenance().run('ROTATE', BA)
        self.assertEqual((self.calls(), self.ops()), ([], []))

    def test_claude_needs_no_pane_probe(self):
        self.assertFalse(getattr(ClaudeProvider, 'requires_native_pwsh', False))
        self.assertTrue(CodexProvider.requires_native_pwsh)
        self.configure('fake-claude')
        op = self.rotate()
        self.assertEqual(next(e for e in op['evidence'] if e['step'] == 'pane_shell')['checked'], False)


class TrustDialogTests(StartupCase):
    def test_detector_distinguishes_dialog_from_ready_agent(self):
        claude, codex = ClaudeProvider(), CodexProvider()
        self.assertEqual(claude.interaction_blocker(TRUST_SCREEN), 'trust_dialog')
        self.assertIsNone(claude.interaction_blocker('● Listo. Espero una tarea del watcher.\n❯ \n⏵⏵ accept edits on'))
        self.assertEqual(codex.interaction_blocker('Do you trust the contents of this directory?\n› 1. Yes'), 'trust_dialog')
        self.assertIsNone(codex.interaction_blocker('› Ask Codex to do anything'))

    def test_workspace_without_trust_holds_fleet_agents(self):
        self.fleet_runtime({'ai': {
            'defaults': {'provider': 'fake-claude'}, 'agents': {SA: {'provider': 'fake-codex'}},
            'providers': {'fake-claude': {'executable': 'claude-cli'}, 'fake-codex': {'executable': 'codex-cli'}}}})
        self.gateway.screen_after_start = TRUST_SCREEN
        with patch.object(maintenance, 'native_pwsh', return_value=(None, True)), \
                patch.object(maintenance.SessionMaintenance, 'poll_s', 0):
            with self.assertRaises(ReconciliationRequired) as raised:
                FleetOrchestrator(self.rt).launch()
        self.assertIn('held until verified', str(raised.exception))
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'awaiting_trust')
        # Nothing was typed into a dialog; only the start commands reached Herdr.
        self.assertEqual([c for c in self.gateway.calls if c[0] in ('prompt', 'submit')], [])
        self.assertIn(BA, maintenance_blocks(self.rt.state))

    def test_failed_start_behind_a_dialog_is_held_not_uncertain(self):
        # Observed live with Herdr 0.8.2: the dialog is reported 'blocked' and `agent start` times out.
        self.fleet_runtime()
        original = self.gateway.start

        def start(name, pane, provider, native):
            original(name, pane, provider, native)
            self.gateway.agents[pane]['agent_status'] = 'blocked'
            self.gateway.screen[pane] = TRUST_SCREEN
            raise CommandError('Command failed: exit (1)')

        self.gateway.start = start
        with patch.object(maintenance, 'native_pwsh', return_value=(None, True)), \
                patch.object(maintenance.SessionMaintenance, 'poll_s', 0):
            with self.assertRaises(ReconciliationRequired) as raised:
                FleetOrchestrator(self.rt).launch()
        self.assertIn('awaiting_trust', str(raised.exception))
        states = {self.rt.state.get('agent:' + name)['state'] for name in (BA, SA)}
        self.assertEqual(states, {'awaiting_trust'})
        self.assertEqual([c for c in self.gateway.calls if c[0] in ('prompt', 'submit')], [])

    def test_fleet_launch_verifies_every_agent_before_ready(self):
        self.fleet_runtime()
        with patch.object(maintenance.SessionMaintenance, 'poll_s', 0):
            self.assertEqual(FleetOrchestrator(self.rt).launch(), 13)
        agent = self.rt.state.get('agent:' + BA)
        self.assertEqual((agent['state'], agent['generation']), ('ready', 1))
        verifies = [op for op in self.ops() if op['kind'] == 'VERIFY']
        self.assertEqual((len(verifies), {op['state'] for op in verifies}), (13, {'COMPLETED'}))
        identity = next(e for e in verifies[0]['evidence'] if e['step'] == 'identity')
        self.assertTrue(identity['contract_loaded'])

    def test_dispatch_never_types_into_a_dialog_and_watcher_holds(self):
        self.gateway.screen['p-' + BA] = TRUST_SCREEN
        pane, _ = self.rt.dispatcher.info(BA)
        with self.assertRaises(AgentBlocked):
            self.rt.dispatcher.dispatch(BA, pane, '@BA: tarea', 'ev-1')
        self.assertEqual((self.prompts('p-' + BA), self.rt.state.get('dispatch:ev-1')), ([], None))
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'awaiting_trust')
        # The watcher keeps the task queued instead of stopping or sending it.
        self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU.\n'), lambda: None])
        self.assertEqual(self.prompts('p-' + BA), [])
        # The human answers the dialog in the pane (the CLI shows its idle composer again); reconcile re-verifies
        # the screen and the identity before any dispatch.
        del self.gateway.screen['p-' + BA]
        op = self.maintenance().reconcile(BA)
        self.assertEqual((op['kind'], op['state']), ('VERIFY', 'COMPLETED'))
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'ready')
        self.gateway.calls.clear()
        self.run_watcher([lambda: None])
        prompts = self.prompts('p-' + BA)
        self.assertEqual(len(prompts), 1)
        self.assertIn('/tasks/', prompts[0])

    def test_reconcile_with_dialog_still_on_screen_answers_nothing(self):
        self.gateway.screen['p-' + BA] = TRUST_SCREEN
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'state': 'awaiting_trust'})
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().reconcile(BA)
        self.assertIn('trust_dialog', str(raised.exception))
        self.assertEqual([c for c in self.calls() if c[0] in ('prompt', 'submit')], [])
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'awaiting_trust')


class ProtocolTests(StartupCase):
    def start_watcher_history(self):
        # A human block opens the flow; the audit cursor starts at the existing history.
        self.append('### [10-10-2026] Operador humano\n- **Hora:** 09:00:00\n- **Handoff:** fin.\n')
        self.sync_cursor()
        self.run_watcher([lambda: None])

    def test_contract_and_launch_text_state_the_rule(self):
        self.assertIn(EXECUTION_RULE, agent_contract(self.rt.context, BA))
        selection, provider = self.rt.factory.resolve(agent=BA)
        text = ' '.join(interactive_command(self.rt.config, provider, selection, BA).argv)
        self.assertIn('no ejecutes handoffs leídos en el tracker', text)
        self.assertNotIn('Espera un handoff en', text)

    def test_agent_block_without_dispatch_stops_dispatching(self):
        self.start_watcher_history()
        self.run_watcher([
            lambda: self.append(block(author='Solutions Architect', handoff='fin de prueba sin tokens.')),
            lambda: self.append('- **Handoff:** @BA: Redacta la HU.\n'),
            lambda: None])
        (key, violation), = self.violations()
        self.assertEqual((violation['agent_id'], violation['reason']), (SA, 'block_without_dispatch'))
        self.assertEqual(self.prompts('p-' + BA), [])
        self.assertIn('[Protocolo]', self.tracker.read_text(encoding='utf-8'))
        self.assertIn('protocol_violation', self.plan()[BA]['reasons'])
        # Restart: the violation persists, is not flagged twice and keeps holding.
        self.run_watcher([lambda: None])
        self.assertEqual((len(self.violations()), self.prompts('p-' + BA)), (1, []))
        # Reconciled by the operator (state --acknowledge): dispatching resumes exactly once.
        self.rt.state.put(key, {**violation, 'state': 'done', 'acknowledged': time.time()})
        self.run_watcher([lambda: None])
        self.assertEqual(len(self.prompts('p-' + BA)), 1)

    def test_valid_handoff_authorized_by_watcher(self):
        self.start_watcher_history()
        self.run_watcher([
            lambda: self.append('- **Handoff:** @BA: Redacta la HU.\n'),
            lambda: self.append(block(handoff='product-manager revisará la HU.')),
            lambda: None])
        self.assertEqual(len(self.prompts('p-' + BA)), 1)
        self.assertEqual(self.violations(), [])
        queued = [json.loads(d) for (d,) in self.rt.state.db.execute("SELECT data FROM records WHERE id LIKE 'queued:%'")]
        confirmed = [q for q in queued if q.get('stage') == 'confirmado']
        self.assertEqual(len(confirmed), 1)
        self.assertIsInstance(confirmed[0]['confirmed_block'], int)

    def test_second_block_after_confirmation_is_flagged(self):
        self.start_watcher_history()
        self.run_watcher([
            lambda: self.append('- **Handoff:** @BA: Redacta la HU.\n'),
            lambda: self.append(block(handoff='product-manager revisará la HU.')),
            lambda: None,
            lambda: self.append(block(handoff='otra vez por mi cuenta.')),
            lambda: None])
        self.assertEqual([v['agent_id'] for _, v in self.violations()], [BA])

    def test_older_state_history_is_not_judged_retroactively(self):
        # SQLite from earlier phases: no block_audit, agent blocks already in the tracker.
        self.append(block(author='Solutions Architect'))
        self.assertIsNone(self.rt.state.get('block_audit'))
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)):
            authors = workflow.autores_en_tracker()
        self.assertEqual(audit_blocks(self.rt.state, authors, workflow.agente_de_autor, {}), [])
        self.assertEqual(self.rt.state.get('block_audit'), {'count': len(authors)})


class IdentityTests(StartupCase):
    def test_contract_not_loaded_is_refused(self):
        self.handoff(BA, '@BA:')
        self.gateway.argv['p-' + BA] = ('claude', '--append-system-prompt-file', 'otro/contrato.md')
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().run('CLEAR', BA)
        self.assertIn('contract_not_loaded', str(raised.exception))
        self.gateway.argv['p-' + BA] = ('claude', '--append-system-prompt-file', str(contract_path(self.rt.context, BA)))
        op = self.maintenance().run('CLEAR', BA)
        identity = next(e for e in op['evidence'] if e['step'] == 'identity')
        self.assertEqual((identity['problems'], identity['contract_loaded'], identity['generation']), ([], True, 1))

    def test_generation_mismatch_is_refused(self):
        self.handoff(BA, '@BA:')
        self.maintenance().run('CLEAR', BA)
        self.handoff(BA, '@BA:')
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'generation': 7})
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().run('ROTATE', BA)
        self.assertIn('generation', str(raised.exception))
        # A new launch (new run_id) starts again at generation 1; earlier launches do not count.
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'generation': 1, 'run_id': 'run-2'})
        self.assertEqual(self.maintenance().run('ROTATE', BA)['generation_after'], 2)

    def test_verify_command_on_reused_panel(self):
        self.handoff(BA, '@BA:')
        op = self.maintenance().verify(BA)
        self.assertEqual((op['kind'], op['state'], op['generation_before'], op['generation_after']),
                         ('VERIFY', 'COMPLETED', 1, 1))
        # VERIFY keeps the context: the session can still be cleared or rotated.
        self.assertEqual(self.plan()[BA]['proposed_action'], 'CLEAR')
        self.rt.state.put('followup', {BA: {'pane_id': 'p-' + BA}})
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().verify(BA)

    def test_two_workspaces_keep_separate_audits(self):
        other_root = Path(self.temp.name + ' otro')
        other_root.mkdir()
        (other_root / 'config_bmad.json').write_text((self.root / 'config_bmad.json').read_text(encoding='utf-8'),
                                                     encoding='utf-8')
        other = Runtime(other_root, registry=registry(), gateway=FakeHerdr(), runner=Mock())
        try:
            self.rt.state.put('protocol_violation:3', {'state': 'requiere_intervencion', 'agent_id': SA})
            self.assertEqual(protocol_violations(other.state), [])
            self.assertEqual(len(self.violations()), 1)
            self.assertNotIn('protocol_violation', other.sessions._workspace_reasons(other.state))
        finally:
            other.close()

    def test_older_agent_records_still_work(self):
        # Records written before 4B.1: no generation, contract_sources or session_name.
        self.handoff(BA, '@BA:')
        record = {k: v for k, v in self.rt.state.get('agent:' + BA).items() if k != 'session_name'}
        self.rt.state.put('agent:' + BA, record)
        selection, provider = self.rt.factory.resolve(agent=BA)
        self.gateway.argv['p-' + BA] = ('claude', '--append-system-prompt-file', str(contract_path(self.rt.context, BA)))
        problems, evidence = self.maintenance().identity(BA, record, provider, selection)
        self.assertEqual((problems, evidence['generation'], evidence['contract_current']), ([], 1, True))
        self.assertEqual(self.maintenance().run('ROTATE', BA)['state'], 'COMPLETED')


if __name__ == '__main__':
    unittest.main()
