"""Phase 4B: operator-confirmed CLEAR/ROTATE. Herdr, Claude and Codex are stateful fakes; nothing real is launched."""
import io
import json
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import maintenance, workflow
from bmad_runtime.commands import Command
from bmad_runtime.context import resolve_context
from bmad_runtime.errors import (CommandError, DeliveryRejected, DeliveryUncertain, ReconciliationRequired,
                                 UnsupportedCapability)
from bmad_runtime.maintenance import Coordination, SessionMaintenance
from bmad_runtime.providers import Capabilities, ClaudeProvider, CodexProvider
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import interactive_command, probe_verdict, source_digests
from bmad_runtime.state import ProjectLock, StateStore
from bmad_runtime.watcher_service import (SESSION_PROTOCOL, WatcherService, maintenance_blocks, read_tracker,
                                          watcher_heartbeat)
from bmad_runtime.workspace import bootstrap
from tests.test_session_lifecycle import FakeProvider, SessionCase, block, registry as base_registry

BA, SA = 'business-analyst', 'solutions-architect'


class FakeClaude(FakeProvider):
    identifier = 'claude'
    herdr_kind = 'claude'
    capabilities = Capabilities(True, True, True, True, True)

    def interactive(self, selection, root, profile):
        return Command((self.executable, '--append-system-prompt-file', str(profile)), profile.parent)

    def clear_instruction(self):
        return '/clear'

    interaction_blocker = ClaudeProvider.interaction_blocker


class FakeCodex(FakeProvider):
    identifier = 'codex'
    herdr_kind = 'codex'
    requires_native_pwsh = True

    def interactive(self, selection, root, profile):
        return Command((self.executable, 'initial prompt'), profile.parent)

    def clear_instruction(self):
        raise UnsupportedCapability('Codex loses its role on /clear.')

    interaction_blocker = CodexProvider.interaction_blocker


def registry():
    value = base_registry()
    value.register('fake-claude', FakeClaude)
    value.register('fake-codex', FakeCodex)
    return value


class FakeHerdr:
    """Herdr session with agents that answer the maintenance verification like a real CLI would."""

    def __init__(self):
        self.agents, self.output, self.memory, self.calls = {}, {}, {}, []
        self.cwd = {}
        self.exit_works = self.clear_works = True
        self.submit_error = self.start_error = self.prompt_error = None
        self.responder = None   # optional override: (pane, nonce, fields) -> reply text
        self.status_after_start = 'idle'
        self.argv, self.screen, self.pane_pwsh = {}, {}, {}
        self.good_pwsh = r'C:\Program Files\PowerShell\7\pwsh.exe'
        self.repaired_pwsh = self.good_pwsh
        self.screen_after_start = ''

    def add(self, name, pane, kind, cwd=None):
        self.agents[pane] = {'name': name, 'pane_id': pane, 'agent_status': 'idle', 'agent': kind}
        self.output[pane], self.memory[pane] = 'PS> ', '[BMAD 0a1b2c3d4e5f]'
        self.cwd[pane] = cwd

    def list_agents(self):
        return [dict(agent) for agent in self.agents.values()]

    def list_panes(self):
        return [{'pane_id': pane, 'tab_id': 't', 'cwd': cwd} for pane, cwd in self.cwd.items()]

    def verify_provider(self, provider):
        pass

    def start_command(self, name, pane, provider, native):
        return Command(('herdr', 'agent', 'start', name, '--pane', pane, *native.argv[1:]), native.cwd)

    def submit(self, pane, text):
        self.calls.append(('submit', pane, text))
        if self.submit_error:
            raise self.submit_error
        if text == '/exit' and self.exit_works:
            self.agents.pop(pane, None)
            self.output[pane] += '\nPS> '
        if text == '/clear' and self.clear_works:
            self.memory[pane] = None

    def start(self, name, pane, provider, native):
        self.calls.append(('start', pane, name, native.argv))
        if self.start_error:
            raise self.start_error
        self.agents[pane] = {'name': name, 'pane_id': pane, 'agent_status': self.status_after_start,
                             'agent': provider.herdr_kind}
        self.argv[pane] = (provider.herdr_kind, *native.argv[1:])
        self.screen[pane] = self.screen_after_start
        self.memory[pane] = None

    def prompt(self, pane, text, timeout_ms=None):
        self.calls.append(('prompt', pane, text))
        if self.prompt_error:
            raise self.prompt_error
        match = re.match(r'\[BMAD-MANT (\w+)\] Lee y ejecuta íntegramente (\S+)', text)
        if not match:
            self.memory[pane] = text.split(']')[0] + ']'
            return
        nonce, relative = match.groups()
        header = (self.root / relative).read_text(encoding='utf-8').splitlines()[0]
        role = re.search(r'agent=(\S+)', header).group(1)
        fields = {'rol': role, 'proyecto': self.context.project_id, 'workspace': str(self.context.workspace_root),
                  'fuentes': ','.join(f'{k}:{v}' for k, v in source_digests(self.context, role).items()),
                  'memoria': self.memory[pane] or 'NINGUNA'}
        reply = self.responder(pane, nonce, fields) if self.responder else (
            f'BMAD-VERIFICACION op={nonce} ' + ' '.join(f'{k}={v}' for k, v in fields.items()))
        self.output[pane] += '\n● ' + reply + '\n'

    def process_info(self, pane):
        agent = self.agents.get(pane)
        if agent:
            foreground = [{'pid': 2, 'name': agent['agent'] + '.exe', 'argv': list(self.argv.get(pane, ()))}]
        else:
            foreground = [{'pid': 1, 'name': 'powershell.exe'}]
        return {'shell_pid': 1, 'foreground_processes': foreground}

    def read(self, pane, lines=40, source='recent'):
        if source == 'visible':
            return self.screen.get(pane, '')
        return self.output.get(pane, '')

    def run_in_pane(self, pane, command):
        self.calls.append(('run', pane, command[:20]))
        if pane in self.agents:
            raise AssertionError('commands are only typed at a shell prompt')
        if command.startswith('$env:Path'):
            self.pane_pwsh[pane] = self.repaired_pwsh
            return
        nonce = re.search(r"-PWSH (\w+) ", command).group(1)
        self.output[pane] += f'\nPS> {command}\nBMAD-PWSH {nonce} {self.pane_pwsh.get(pane, self.good_pwsh)}\nPS> '


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class MaintenanceCase(SessionCase):
    provider = 'fake-claude'

    def setUp(self):
        super().setUp()
        for name in self.agents:
            folder = self.root / name
            folder.mkdir(exist_ok=True)
            (folder / 'AGENTS.md').write_text(f'Perfil {name} v1\n', encoding='utf-8')
        self.configure(self.provider)

    def configure(self, provider):
        (self.root / 'config_bmad.json').write_text(json.dumps({'ai': {'defaults': {'provider': provider}, 'providers': {
            'fake': {'executable': 'fake-cli'}, 'fake-claude': {'executable': 'claude-cli'},
            'fake-codex': {'executable': 'codex-cli'}}}}), encoding='utf-8')
        self.gateway = FakeHerdr()
        self.rt.close()
        self.rt = Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())
        self.service = WatcherService(self.rt)
        self.gateway.root, self.gateway.context = self.root, self.rt.context
        kind = {'fake-claude': 'claude', 'fake-codex': 'codex'}.get(provider, 'fake')
        for name in self.agents:
            self.rt.state.put('agent:' + name, {'agent_id': name, 'provider': provider, 'model': None,
                                                'pane_id': 'p-' + name, 'state': 'ready', 'run_id': 'run-1',
                                                'attempt': 1, 'session_name': name})
            self.gateway.add(name, 'p-' + name, kind)

    def start(self):
        if self.rt:
            self.rt.close()
        self.rt = Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())
        self.service = WatcherService(self.rt)
        if isinstance(self.gateway, FakeHerdr):
            self.gateway.context = self.rt.context
        for name in self.agents:
            if not self.rt.state.get('agent:' + name):
                self.rt.state.put('agent:' + name, {'agent_id': name, 'provider': 'fake', 'model': None,
                                                    'pane_id': 'p-' + name, 'state': 'ready', 'run_id': 'run-1',
                                                    'attempt': 1})

    def maintenance(self):
        self.clock = Clock()
        return SessionMaintenance(self.rt, clock=self.clock, sleep=self.clock.sleep)

    def ops(self):
        rows = self.rt.state.db.execute("SELECT data FROM records WHERE id LIKE 'maintenance:%'")
        return [json.loads(data) for (data,) in rows]

    def calls(self, pane=None):
        return [call for call in self.gateway.calls if pane is None or call[1] == pane]

    def assert_untouched(self, name):
        self.assertEqual(self.calls('p-' + name), [])
        self.assertEqual(self.rt.state.get('agent:' + name)['state'], 'ready')

    def reset_operations(self):
        self.rt.state.db.execute("DELETE FROM records WHERE id LIKE 'maintenance:%'")
        self.rt.state.db.commit()


class ClearTests(MaintenanceCase):
    def test_clear_claude_success_reloads_profile_and_bumps_generation(self):
        self.handoff(BA, '@BA:')
        (self.root / BA / 'AGENTS.md').write_text('Perfil BA v2\n', encoding='utf-8')
        op = self.maintenance().run('CLEAR', BA)
        self.assertEqual((op['state'], op['result'], op['generation_before'], op['generation_after']),
                         ('COMPLETED', 'success', 1, 2))
        self.assertEqual(list(op['states']), ['REQUESTED', 'QUIESCED', 'CLEARING', 'VERIFYING', 'COMPLETED'])
        self.assertEqual([c[0] + ':' + c[2][:10] for c in self.calls()], ['submit:/clear', 'prompt:[BMAD-MANT'])
        agent = self.rt.state.get('agent:' + BA)
        self.assertEqual((agent['state'], agent['generation'], agent['last_maintenance']), ('ready', 2, op['op_id']))
        self.assertNotIn('maintenance_op', agent)
        # Summary snapshot is verifiable and the contract was regenerated from the current profile.
        self.assertEqual(op['summary'], self.rt.state.get('session:' + BA))
        self.assertEqual(len(op['summary_sha256']), 64)
        self.assertEqual(op['contract']['sources'], source_digests(self.rt.context, BA))
        self.assertIn('Perfil BA v2', (self.root / op['contract']['path']).read_text(encoding='utf-8'))
        verification = [e for e in op['evidence'] if e['step'] == 'verification'][0]
        self.assertEqual((verification['verdict'], verification['problems']), ('verified', []))
        self.assert_untouched(SA)

    def test_clear_is_never_available_for_codex(self):
        self.assertFalse(CodexProvider.capabilities.clear_context)
        with self.assertRaises(UnsupportedCapability):
            CodexProvider().clear_instruction()
        self.assertEqual(ClaudeProvider().clear_instruction(), '/clear')
        self.configure('fake-codex')
        self.handoff(BA, '@BA:')
        with self.assertRaises(UnsupportedCapability):
            self.maintenance().run('CLEAR', BA)
        self.assertEqual((self.calls(), self.ops()), ([], []))

    def test_clear_failures_never_fall_back_to_rotation(self):
        cases = [(DeliveryRejected('agent_blocked'), 'FAILED', 'ready'),
                 (DeliveryUncertain('agent_prompt_stalled'), 'REQUIRES_INTERVENTION', 'maintenance')]
        for error, state, agent_state in cases:
            with self.subTest(error=type(error).__name__):
                self.configure('fake-claude')
                self.reset_operations()
                self.handoff(BA, '@BA:')
                self.gateway.submit_error = error
                with self.assertRaises(ReconciliationRequired):
                    self.maintenance().run('CLEAR', BA)
                op = self.ops()[-1]
                self.assertEqual((op['state'], op['generation_after'], op['uncertain']), (state, None, state != 'FAILED'))
                self.assertEqual(self.rt.state.get('agent:' + BA)['state'], agent_state)
                self.assertNotIn('/exit', [c[2] for c in self.calls()])
                self.assertNotIn('start', [c[0] for c in self.calls()])
                self.assertEqual(self.rt.state.get('agent:' + BA).get('generation', 1), 1)

    def test_clear_that_keeps_context_requires_intervention(self):
        self.handoff(BA, '@BA:')
        self.gateway.clear_works = False
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('CLEAR', BA)
        op = self.ops()[0]
        self.assertEqual(op['state'], 'REQUIRES_INTERVENTION')
        self.assertIn('context_not_reset', op['errors'][-1]['error'])
        self.assertEqual(maintenance_blocks(self.rt.state), {BA: op['op_id']})
        self.assertNotIn('start', [c[0] for c in self.calls()])


class RotateTests(MaintenanceCase):
    def test_rotate_claude_and_codex_success(self):
        for provider in ('fake-claude', 'fake-codex'):
            with self.subTest(provider=provider):
                self.configure(provider)
                self.reset_operations()
                self.handoff(BA, '@BA:')
                op = self.maintenance().run('ROTATE', BA)
                self.assertEqual(list(op['states']), ['REQUESTED', 'QUIESCED', 'STOPPING', 'STARTING', 'VERIFYING', 'COMPLETED'])
                self.assertEqual((op['state'], op['generation_after'], op['provider']), ('COMPLETED', 2, provider))
                # 'run' = the pane shell pwsh probe (4B.1, Codex on Windows only), typed before the relaunch.
                calls = [c for c in self.calls('p-' + BA) if c[0] != 'run']
                self.assertEqual([c[0] for c in calls], ['submit', 'start', 'prompt'])
                self.assertEqual((calls[0][2], calls[1][2]), ('/exit', BA))
                self.assertIn('exited_to_shell', [e['step'] for e in op['evidence']])
                self.assert_untouched(SA)

    def test_exit_failure(self):
        self.handoff(BA, '@BA:')
        self.gateway.exit_works = False
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        op = self.ops()[0]
        self.assertEqual((op['state'], op['uncertain']), ('REQUIRES_INTERVENTION', True))
        self.assertNotIn('start', [c[0] for c in self.calls()])
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'maintenance')
        row = self.plan()[BA]
        self.assertEqual(row['proposed_action'], 'MANUAL_REVIEW')
        self.assertIn('maintenance_pending:' + BA, row['reasons'])

    def test_exit_rejected_before_sending_changes_nothing(self):
        self.handoff(BA, '@BA:')
        self.gateway.submit_error = DeliveryRejected('agent_not_found')
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        self.assertEqual(self.ops()[0]['state'], 'FAILED')
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'ready')
        self.assertEqual(maintenance_blocks(self.rt.state), {})

    def test_relaunch_failure(self):
        self.handoff(BA, '@BA:')
        self.gateway.start_error = CommandError('herdr agent start timed out')
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        op = self.ops()[0]
        self.assertEqual((op['state'], op['errors'][-1]['during']), ('REQUIRES_INTERVENTION', 'STARTING'))

    def test_profile_recovery_failure(self):
        self.handoff(BA, '@BA:')
        self.gateway.responder = lambda pane, nonce, f: (
            f"BMAD-VERIFICACION op={nonce} rol={f['rol']} proyecto={f['proyecto']} workspace={f['workspace']} "
            'fuentes=PERFIL DEL ROL:0123456789abcdef memoria=NINGUNA')
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        op = self.ops()[0]
        self.assertEqual((op['state'], op['generation_after']), ('REQUIRES_INTERVENTION', None))
        self.assertIn('profile_sources', op['errors'][-1]['error'])
        self.assertEqual(self.rt.state.get('agent:' + BA).get('generation', 1), 1)

    def test_wrong_identity_after_relaunch(self):
        self.handoff(BA, '@BA:')
        self.gateway.responder = lambda pane, nonce, f: (
            f"BMAD-VERIFICACION op={nonce} rol=solutions-architect proyecto={f['proyecto']} "
            f"workspace={f['workspace']} fuentes={f['fuentes']} memoria=NINGUNA")
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        self.assertIn('role', self.ops()[0]['errors'][-1]['error'])

    def test_blocked_after_relaunch_approves_nothing(self):
        self.handoff(BA, '@BA:')
        self.gateway.status_after_start = 'blocked'
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        self.assertIn('nothing was approved', self.ops()[0]['errors'][-1]['error'])
        self.assertNotIn('prompt', [c[0] for c in self.calls()])

    def test_interrupted_operation_is_recorded_as_uncertain(self):
        self.handoff(BA, '@BA:')
        self.gateway.start_error = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.maintenance().run('ROTATE', BA)
        op = self.ops()[0]
        self.assertEqual((op['state'], op['uncertain']), ('REQUIRES_INTERVENTION', True))


class EligibilityTests(MaintenanceCase):
    def refused(self, kind='ROTATE'):
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().run(kind, BA)
        self.assertEqual((self.calls(), self.ops()), ([], []))
        return str(raised.exception)

    def test_busy_or_blocked_agent(self):
        self.handoff(BA, '@BA:')
        for status in ('working', 'blocked'):
            with self.subTest(status=status):
                self.gateway.agents['p-' + BA]['agent_status'] = status
                self.assertIn('herdr_busy:' + status, self.refused())

    def test_pending_or_uncertain_handoff(self):
        self.handoff(BA, '@BA:')
        task = self.handoff(SA, '@SA:', dispatch=False, confirm=False)
        self.assertIn('pending_tasks', self.refused())
        key = 'queued:' + task['event_id']
        self.rt.state.put(key, {**self.rt.state.get(key), 'state': 'done'})
        self.rt.state.claim('dispatch:' + task['event_id'])
        self.assertIn('uncertain_dispatch', self.refused('CLEAR'))

    def test_followup_active(self):
        self.handoff(BA, '@BA:')
        self.rt.state.put('followup', {BA: {'pane_id': 'p-' + BA}})
        self.assertIn('followup_active', self.refused())

    def test_inconsistent_tracker(self):
        self.handoff(BA, '@BA:')
        self.tracker.write_text('### [09-10-2026] Otro\n', encoding='utf-8')
        self.assertIn('tracker_rewritten', self.refused())

    def test_identity_inconsistent(self):
        self.handoff(BA, '@BA:')
        self.gateway.agents['p-' + BA]['pane_id'] = 'p-ajeno'
        self.assertIn('herdr_identity_mismatch', self.refused())
        self.gateway.agents['p-' + BA].update(pane_id='p-' + BA, agent='codex')
        self.assertIn('identity changed', self.refused())


class CoordinationTests(MaintenanceCase):
    def hold_running_watcher(self):
        self.watcher = ProjectLock(self.rt.context, 'watcher')
        self.assertTrue(self.watcher.acquire())

    def test_two_concurrent_maintenances(self):
        self.handoff(BA, '@BA:')
        other = ProjectLock(self.rt.context, 'maintenance')
        self.assertTrue(other.acquire())
        try:
            with self.assertRaises(ReconciliationRequired) as raised:
                self.maintenance().run('ROTATE', BA)
            self.assertIn('Another session maintenance', str(raised.exception))
        finally:
            other.release()
        self.assertEqual((self.calls(), self.ops()), ([], []))

    def test_maintenance_waits_bounded_for_watcher_tick(self):
        self.handoff(BA, '@BA:')
        self.hold_running_watcher()
        watcher_heartbeat(self.rt.state, time.time())
        tick = ProjectLock(self.rt.context, 'sessions')
        self.assertTrue(tick.acquire())
        try:
            with self.assertRaises(ReconciliationRequired) as raised:
                self.maintenance().run('ROTATE', BA)
            self.assertIn('sessions lock', str(raised.exception))
        finally:
            tick.release()
            self.watcher.release()
        self.assertEqual(self.calls(), [])

    def test_running_watcher_must_take_part(self):
        self.handoff(BA, '@BA:')
        self.hold_running_watcher()
        try:
            with self.assertRaises(ReconciliationRequired) as raised:
                self.maintenance().run('ROTATE', BA)
            self.assertIn('watcher_without_coordination', str(raised.exception))
            self.rt.state.put('watcher', {'protocol': SESSION_PROTOCOL, 'heartbeat': time.time() - 120})
            with self.assertRaises(ReconciliationRequired) as raised:
                self.maintenance().run('ROTATE', BA)
            self.assertIn('watcher_heartbeat_stale', str(raised.exception))
            self.assertEqual(self.calls(), [])
            watcher_heartbeat(self.rt.state, time.time())
            op = self.maintenance().run('ROTATE', BA)
        finally:
            self.watcher.release()
        self.assertEqual((op['state'], op['evidence'][0]['watcher']), ('COMPLETED', 'coordinated'))

    def test_maintenance_without_watcher_holds_watcher_lock(self):
        with Coordination(self.rt.context, self.rt.state) as coordination:
            self.assertEqual(coordination.watcher, 'stopped')
            starting_watcher = ProjectLock(self.rt.context, 'watcher')
            self.assertFalse(starting_watcher.acquire())
        # Released on exit (and by the OS on a crash): a later watcher or maintenance can proceed.
        self.assertTrue(starting_watcher.acquire())
        starting_watcher.release()

    def test_two_independent_workspaces(self):
        engine = Path(tempfile.mkdtemp(prefix='BMAD motor 4B '))
        for name in (BA, SA):
            (engine / name).mkdir()
            (engine / name / 'AGENTS.md').write_text(f'Perfil {name}\n', encoding='utf-8')
        (engine / 'constitution.md').write_text('Política\n', encoding='utf-8')
        (engine / 'config_bmad.json').write_text(json.dumps({'ai': {
            'defaults': {'provider': 'fake-claude'}, 'providers': {'fake-claude': {'executable': 'claude-cli'}}}}),
            encoding='utf-8')
        herdr = FakeHerdr()
        runtimes = []
        for project in ('alfa', 'beta'):
            context = bootstrap(resolve_context(engine, workspace=engine.parent / f'{engine.name} {project} ñ',
                                                project=project, initialize=True, environ={}))
            rt = Runtime(engine, context=context, registry=registry(), gateway=herdr, runner=Mock())
            runtimes.append(rt)
            session = context.session_name(BA)
            rt.state.put('agent:' + BA, {'agent_id': BA, 'provider': 'fake-claude', 'model': None, 'session_name': session,
                                         'pane_id': f'{project}-p1', 'state': 'ready', 'run_id': 'r', 'attempt': 1})
            herdr.add(session, f'{project}-p1', 'claude', cwd=str(context.workspace_root))
            line = f'- **Handoff:** @BA: tarea {project}\n'
            context.tracker_path.write_text(line, encoding='utf-8')
            service = WatcherService(rt)
            task = service.enqueue(0, line, {'agente': BA, 'mensaje': f'@BA: tarea {project}'})
            service.mark(task, 'reservado')
            service.dispatched(task)
            artifact = context.output('docs/ba/hu.md')
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('# HU\n', encoding='utf-8')
            report = block(artifact='docs/ba/hu.md')
            with context.tracker_path.open('a', encoding='utf-8') as handle:
                handle.write(report)
            service.mark(task, 'confirmado')
            rt.sessions.record_summary(BA, task['event_id'], report)
            lines = read_tracker(context.tracker_path).lines
            service.save_cursor(lines, len(lines))
        alfa, beta = runtimes
        try:
            # Alfa's maintenance in progress does not block beta's coordination.
            with Coordination(alfa.context, alfa.state):
                with Coordination(beta.context, beta.state) as coordination:
                    self.assertEqual(coordination.watcher, 'stopped')
            herdr.root, herdr.context = alfa.context.workspace_root, alfa.context
            clock = Clock()
            op = SessionMaintenance(alfa, clock=clock, sleep=clock.sleep).run('CLEAR', BA)
            self.assertEqual((op['state'], op['project_id'], op['workspace']),
                             ('COMPLETED', 'alfa', str(alfa.context.workspace_root)))
            self.assertEqual({call[1] for call in herdr.calls}, {'alfa-p1'})
            self.assertEqual(beta.state.get('agent:' + BA).get('generation', 1), 1)
            self.assertEqual(maintenance_blocks(beta.state), {})
            self.assertEqual(beta.state.db.execute(
                "SELECT COUNT(*) FROM records WHERE id LIKE 'maintenance:%'").fetchone()[0], 0)
            # A pane whose cwd belongs to the other workspace is an identity problem.
            herdr.cwd['beta-p1'] = str(alfa.context.workspace_root)
            herdr.root, herdr.context = beta.context.workspace_root, beta.context
            with self.assertRaises(ReconciliationRequired):
                SessionMaintenance(beta, clock=clock, sleep=clock.sleep).run('ROTATE', BA)
            self.assertEqual({call[1] for call in herdr.calls}, {'alfa-p1'})
        finally:
            for rt in runtimes:
                rt.close()


class RecoveryTests(MaintenanceCase):
    def crashed_operation(self, state='STOPPING'):
        """State left by a maintenance process killed mid-operation (its OS locks are already released)."""
        # A @HUMANO handoff pauses the watcher by design; use a block without dispatch tokens.
        self.handoff(BA, '@BA:', report=block(handoff='product-manager revisará la HU.'))
        op = {'op_id': 'f' * 32, 'kind': 'ROTATE', 'agent': BA, 'provider': 'fake-claude', 'project_id': 'legacy',
              'workspace': str(self.root), 'session_name': BA, 'pane_id': 'p-' + BA, 'generation_before': 1,
              'generation_after': None, 'state': state, 'states': {'REQUESTED': 1.0, state: 2.0}, 'errors': [],
              'evidence': [], 'uncertain': False, 'resolution': None, 'result': None}
        self.rt.state.put('maintenance:' + op['op_id'], op)
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'state': 'maintenance',
                                          'maintenance_op': op['op_id']})
        return op

    def test_unexpected_termination_blocks_until_reconciled(self):
        op = self.crashed_operation()
        self.gateway.agents.pop('p-' + BA)            # the old CLI had already exited
        self.start()                                   # maintenance command restarted: SQLite is the source
        self.assertEqual(maintenance_blocks(self.rt.state), {BA: op['op_id']})
        row = self.plan()[SA]
        self.assertEqual(row['proposed_action'], 'MANUAL_REVIEW')
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().reconcile(BA)
        self.assertIn('relaunch it manually', str(raised.exception))
        stored = self.rt.state.get('maintenance:' + op['op_id'])
        self.assertEqual((stored['state'], stored['errors'][-1]['error']),
                         ('REQUIRES_INTERVENTION', 'interrupted during STOPPING'))
        self.assertEqual([c for c in self.calls() if c[0] in ('submit', 'start')], [])
        # The operator relaunches by hand; reconcile verifies and releases the block without retrying anything.
        selection, provider = self.rt.factory.resolve(agent=BA)
        self.gateway.start(BA, 'p-' + BA, provider, interactive_command(self.rt.config, provider, selection, BA))
        self.gateway.calls.clear()
        resolved = self.maintenance().reconcile(BA)
        self.assertEqual((resolved['state'], resolved['resolution']['outcome'], resolved['generation_after']),
                         ('REQUIRES_INTERVENTION', 'fresh_context_verified', 2))
        self.assertEqual([c[0] for c in self.calls()], ['prompt'])
        self.assertEqual(maintenance_blocks(self.rt.state), {})
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'ready')
        self.assertIsNone(self.maintenance().reconcile(BA))

    def test_reconcile_previous_context_keeps_generation(self):
        self.crashed_operation('REQUIRES_INTERVENTION')
        resolved = self.maintenance().reconcile(BA)
        self.assertEqual((resolved['resolution']['outcome'], resolved['generation_after']),
                         ('previous_context_verified', 1))
        self.assertEqual(self.rt.state.get('agent:' + BA).get('generation', 1), 1)
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'ready')

    def test_idempotence_and_recovery_from_sqlite(self):
        self.handoff(BA, '@BA:')
        op = self.maintenance().run('ROTATE', BA)
        self.start()
        stored = self.rt.state.get('maintenance:' + op['op_id'])
        self.assertEqual((stored['state'], stored['generation_after']), ('COMPLETED', 2))
        row = self.plan()[BA]
        self.assertEqual((row['generation'], row['proposed_action'], row['reasons']), (2, 'SKIP', ['session_already_fresh']))
        calls = len(self.gateway.calls)
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().run('ROTATE', BA)
        self.assertEqual(len(self.gateway.calls), calls)
        # A new confirmed handoff makes the session eligible again; its summary carries the generation.
        self.handoff(BA, '@BA:')
        self.assertEqual(self.plan()[BA]['proposed_action'], 'CLEAR')
        self.assertEqual(self.rt.state.get('session:' + BA)['session_generation']['generation'], 2)
        with self.assertRaises(ReconciliationRequired):
            self.maintenance()._advance(stored, 'STARTING')

    def test_watcher_restart_during_maintenance(self):
        op = self.crashed_operation('STARTING')
        held = ProjectLock(self.rt.context, 'sessions')
        self.assertTrue(held.acquire())                 # maintenance still running in another process
        try:
            self.run_watcher([lambda: self.append('- **Handoff:** @BA: Nueva tarea.\n')])
        finally:
            held.release()
        self.assertEqual(self.calls(), [])
        # After the maintenance process died: the watcher reads the tracker, keeps BA's task and dispatches nothing.
        self.run_watcher([lambda: None, lambda: None])
        self.assertEqual(self.calls(), [])
        queued = [json.loads(d) for (d,) in self.rt.state.db.execute("SELECT data FROM records WHERE id LIKE 'queued:%'")]
        self.assertIn('detectado', [q.get('stage') for q in queued if q['agent_id'] == BA])
        self.assertEqual(self.rt.state.get('watcher')['protocol'], SESSION_PROTOCOL)
        self.assertEqual(maintenance_blocks(self.rt.state), {BA: op['op_id']})
        # Control: once reconciled, the same restart dispatches the held task exactly once.
        resolved = self.maintenance().reconcile(BA)
        self.assertEqual(resolved['resolution']['outcome'], 'previous_context_verified')
        self.gateway.calls.clear()
        self.run_watcher([lambda: None])
        self.assertEqual([c[0] for c in self.calls('p-' + BA)], ['prompt'])
        (dispatch,) = [json.loads(d) for (d,) in self.rt.state.db.execute("SELECT data FROM records WHERE id LIKE 'dispatch:%'")]
        self.assertIn('Nueva tarea', (self.root / dispatch['task_file']).read_text(encoding='utf-8'))

    def run_watcher(self, actions):
        import types
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


class ProbeTests(unittest.TestCase):
    expected = {'nonce': 'abc123def456', 'role': BA, 'project_id': 'alfa', 'workspace': r'C:\Work Space\Proyecto ñ',
                'digests': ['0123456789abcdef', 'fedcba9876543210']}

    def test_wrapped_terminal_reply_with_forward_slashes(self):
        output = ('Read(state/maintenance/abc123def456.md)\n● BMAD-VERIFICACION op=abc123def456 rol=business-analyst\n'
                  '  proyecto=alfa workspace=C:/Work Space/Proyec\n  to ñ fuentes=PERFIL DEL ROL:0123456789abcdef,'
                  'POLÍTICA GLOBAL:fedcba9876543210 memoria=NINGUNA\n› ')
        self.assertEqual(probe_verdict(output, **self.expected)[0], 'verified')

    def test_template_echo_partial_and_wrong_memory(self):
        template = 'BMAD-VERIFICACION op=abc123def456 rol=<valor rol= de la primera línea> proyecto=<PROJECT_ID>'
        self.assertEqual(probe_verdict(template, **self.expected)[0], 'incomplete')
        self.assertEqual(probe_verdict('nothing yet', **self.expected)[0], 'absent')
        wrong = (f'BMAD-VERIFICACION op=abc123def456 rol={BA} proyecto=alfa workspace=C:\\Work Space\\Proyecto ñ '
                 'fuentes=0123456789abcdef,fedcba9876543210 memoria=[BMAD 0a1b2c3d4e5f]')
        verdict, details = probe_verdict(wrong, **self.expected)
        self.assertEqual((verdict, details['problems']), ('mismatch', ['context_not_reset']))


class CliTests(MaintenanceCase):
    def run_cli(self, *argv):
        def runtime(root, **kwargs):
            return Runtime(root, registry=registry(), gateway=self.gateway, runner=Mock(), **kwargs)

        output = io.StringIO()
        with patch.object(maintenance, 'Runtime', runtime), patch('sys.stdout', output):
            code = maintenance.main(self.root, list(argv))
        return code, output.getvalue()

    def test_operation_without_confirm_is_read_only(self):
        self.handoff(BA, '@BA:')
        self.rt.close()
        self.rt = None
        try:
            before = {str(p): p.stat().st_mtime_ns for p in self.root.rglob('*') if p.is_file()}
            code, output = self.run_cli('--rotate', 'ba')
            self.assertEqual({str(p): p.stat().st_mtime_ns for p in self.root.rglob('*') if p.is_file()}, before)
        finally:
            self.start()
        report = json.loads(output)
        self.assertEqual((code, report['agents'][0]['agent'], report['agents'][0]['proposed_action']), (0, BA, 'CLEAR'))
        self.assertIn('--confirm', report['note'])
        self.assertEqual(self.gateway.calls, [])

    def test_confirmed_rotate_and_errors(self):
        self.handoff(BA, '@BA:')
        self.rt.close()
        self.rt = None
        try:
            with patch.object(SessionMaintenance, 'poll_s', 0):
                code, output = self.run_cli('--rotate', BA, '--confirm')
            self.assertEqual((code, json.loads(output)['state']), (0, 'COMPLETED'))
            code, output = self.run_cli('--clear', 'nadie', '--confirm')
            self.assertEqual(code, 1)
            self.assertIn('Unknown agent role', output)
            with patch('sys.stderr'), self.assertRaises(SystemExit):
                self.run_cli('--plan-clear', '--confirm')
            code, output = self.run_cli('--reconcile', BA, '--confirm')
            self.assertEqual((code, json.loads(output)['result']), (0, 'nothing_to_reconcile'))
        finally:
            self.start()


if __name__ == '__main__':
    unittest.main()
