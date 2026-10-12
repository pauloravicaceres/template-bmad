"""Phase 4C: context budget, loop guard and progress ledger. Herdr and CLIs are fakes; nothing real is launched."""
import io
import json
import time
import types
from unittest.mock import Mock, patch

from bmad_runtime import guard as guard_module, runtime as runtime_module, state as state_module, workflow
from bmad_runtime.errors import ConfigurationError, DeliveryUncertain, ReconciliationRequired
from bmad_runtime.guard import availability, describe, load_events, metric
from bmad_runtime.providers import ClaudeProvider, CodexProvider
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import EXECUTION_RULE, TRACKER_RULE, agent_contract, source_digests
from bmad_runtime.technical_context import assemble
from tests.test_session_lifecycle import ARTIFACT, FakeProvider, SessionCase, block, registry
from tests.test_session_maintenance import MaintenanceCase
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)
from tests.pane_doubles import ready_pane

BA, SA = 'business-analyst', 'solutions-architect'


class Steps:
    """Deterministic clock a few minutes in the past: events stay inside the real-time window after a restart."""

    def __init__(self):
        self.value = time.time() - 600

    def __call__(self):
        self.value += 1.0
        return self.value


def levels(findings):
    return {(f['rule'], f['agent']): f['level'] for f in findings}


def kinds(store, agent=None):
    return [e['kind'] for e in load_events(store) if agent is None or e['agent'] == agent]


class GuardCase(SessionCase):
    def setUp(self):
        super().setUp()
        self.steps = Steps()
        self.rt.guard.clock = self.steps

    def start(self):
        super().start()
        if getattr(self, 'steps', None):
            self.rt.guard.clock = self.steps

    @property
    def guard(self):
        return self.rt.guard

    def write_guard(self, settings):
        data = json.loads((self.root / 'config_bmad.json').read_text(encoding='utf-8'))
        data['ai']['guard'] = settings
        (self.root / 'config_bmad.json').write_text(json.dumps(data), encoding='utf-8')

    def dispatch(self, agent, message, times=1):
        for _ in range(times):
            self.guard.on_dispatch(agent, message, f'ev{self.steps.value:.0f}')

    def run_watcher(self, actions, expect=KeyboardInterrupt):
        steps = iter(actions)

        def sleep(_seconds):
            action = next(steps, None)
            if action is None:
                raise KeyboardInterrupt
            action()

        fake_time = types.SimpleNamespace(time=time.time, monotonic=time.monotonic, sleep=sleep)
        output = io.StringIO()
        with patch.multiple(workflow, _runtime=self.rt, DIRECTORIO_RAIZ=self.root, TRACKER_PATH=str(self.tracker),
                            RETRABAJO_STATE_PATH=self.root / 'rework.json',
                            RETRABAJO_CLASIFICACION_PATH=self.root / 'rework.md',
                            _ultimo_chequeo_vigilante=0, INTERVALO_VIGILANTE_S=0, time=fake_time), \
                patch.dict(workflow.seguimiento_agentes, clear=True), \
                patch.dict(workflow.contexto_bloque, {'autor': None, 'hora': None}), \
                patch('sys.stdout', output), self.assertRaises(expect):
            workflow.iniciar_watcher()
        return output.getvalue()


# 1. Normal execution ---------------------------------------------------------------------------------------------
class NormalExecutionTests(GuardCase):
    def test_normal_run_records_verified_progress_and_no_alert(self):
        self.rt.guard.clock = time.time   # the watcher compares artifact mtimes with real time

        def deliver():
            (self.root / ARTIFACT).write_text('# HU demo v2\n', encoding='utf-8')
            self.append(block(handoff='product-manager revisará la HU.'))
        output = self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU 001.\n'), deliver])
        self.assertEqual(self.gateway.prompt.call_count, 1)
        self.assertEqual(kinds(self.rt.state), ['dispatched', 'handoff_confirmed', 'artifacts_changed', 'task_completed'])
        dispatched, confirmed = load_events(self.rt.state)[:2]
        # Accepted delivery and completion are different facts.
        self.assertEqual(confirmed['progress'], 'verified')
        self.assertEqual(confirmed['artifacts']['changed'], [ARTIFACT])
        self.assertEqual(confirmed['metrics']['duration_s']['quality'], 'measured')
        self.assertEqual(dispatched['metrics']['task_prompt_tokens']['quality'], 'estimated')
        self.assertGreater(dispatched['metrics']['task_prompt_tokens']['value'], 0)
        self.assertEqual(self.guard.evaluate(), [])
        self.assertNotIn('[Guard', output)
        self.assertFalse(self.rt.context.output('logs/guard.log').exists())
        # The tracker only holds the handoff and the agent block; the guard never writes there.
        self.assertNotIn('Guard', self.tracker.read_text(encoding='utf-8'))


# 2. High consumption ---------------------------------------------------------------------------------------------
class HighConsumptionTests(GuardCase):
    def test_budget_warnings_recommend_manual_maintenance_and_never_interrupt(self):
        budget = self.guard.settings['budget']
        budget.update(max_operations_per_session=3, max_consecutive_operations=3, max_operation_seconds=600)
        self.guard.settings['mode'] = 'enforce'
        for number in range(3):
            self.dispatch(BA, f'@BA: HU {number}')
        self.rt.state.put('followup', {BA: {'pane_id': 'p-' + BA, 'inicio': self.steps.value - 4000,
                                            'despachado': self.steps.value - 10}})
        findings = self.guard.evaluate()
        self.assertEqual(levels(findings), {('operations_per_session', BA): 'WARNING',
                                            ('consecutive_operations', BA): 'WARNING',
                                            ('operation_duration', BA): 'WARNING'})
        session = next(f for f in findings if f['rule'] == 'operations_per_session')
        self.assertIn('--plan-clear', session['recommendation'])
        self.assertIn('ROTATE', session['recommendation'])   # fake provider: no verified /clear
        duration = next(f for f in findings if f['rule'] == 'operation_duration')
        self.assertEqual(duration['evidence']['duration_s']['quality'], 'measured')
        self.guard.tick(force=True)
        # Warnings never hold a dispatch, even in enforce mode, and nothing is sent to any agent.
        self.assertIsNone(self.guard.hold(BA))
        self.gateway.prompt.assert_not_called()
        self.gateway.submit.assert_not_called()


# 3. Unavailable metrics ------------------------------------------------------------------------------------------
class MetricAvailabilityTests(GuardCase):
    def test_usage_is_unavailable_never_zero_or_invented(self):
        self.dispatch(BA, '@BA: HU')
        event = load_events(self.rt.state)[-1]
        for name in ('input_tokens', 'output_tokens', 'cost_usd'):
            self.assertEqual(event['metrics'][name], {'value': None, 'quality': 'unavailable', 'source': 'provider'})
        for provider in (ClaudeProvider('claude'), CodexProvider('codex')):
            table = availability(provider)
            self.assertEqual({table[name] for name in ('input_tokens', 'output_tokens', 'cost_usd')}, {'unavailable'})
            self.assertTrue(table['task_prompt_tokens'].startswith('estimated'))

    def test_token_or_cost_limits_need_a_provider_that_reports_them(self):
        for limit in ({'max_input_tokens': 1000}, {'max_cost_usd': 1}):
            with self.subTest(limit=limit):
                self.write_guard({'agents': {BA: limit}})
                with self.assertRaisesRegex(ConfigurationError, 'does not report'):
                    Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())
        self.write_guard({'agents': {BA: {'max_cost_usd': 0.5}}})
        with patch.object(FakeProvider, 'measured_usage', frozenset({'cost_usd'}), create=True):
            self.start()
            self.guard.event('headless_run', BA, metrics={'cost_usd': metric(9.0, 'estimated', 'guess')})
            self.assertEqual(self.guard.evaluate(), [], 'estimates never trigger usage rules')
            self.guard.event('handoff_confirmed', BA, metrics={'cost_usd': metric(0.9, 'measured', 'provider')})
            self.assertEqual(levels(self.guard.evaluate()), {('usage_limit', BA): 'WARNING'})


# 4. Legitimate repetition ----------------------------------------------------------------------------------------
class LegitimateRepetitionTests(GuardCase):
    def test_iterations_with_verified_progress_raise_nothing(self):
        for _ in range(4):
            self.dispatch(BA, '@BA: Corrige la HU según la revisión.')
            self.guard.event('artifacts_changed', BA, paths=[ARTIFACT])
            self.dispatch(SA, '@SA: Revisa la HU.')
            self.guard.event('artifacts_changed', SA, paths=['docs/sa/review.md'])
        self.assertEqual(self.guard.evaluate(), [])

    def test_confirmation_without_declared_artifacts_is_neutral(self):
        progress = self.guard.on_confirmed(BA, 'e1', {'artifacts': []},
                                           {'handoff': '@HUMANO: aprueba', 'puntos abiertos': 'Ninguno.'}, None)
        self.assertEqual(progress, 'unverifiable')
        self.assertEqual(kinds(self.rt.state), ['handoff_confirmed'])

    def test_existing_file_is_not_proof_of_progress(self):
        summary = {'artifacts': [{'path': ARTIFACT, 'exists': True}]}
        self.assertEqual(self.guard.on_confirmed(BA, 'e1', summary, {}, None), 'verified')
        # Same content confirmed again: the file exists, but nothing changed.
        self.assertEqual(self.guard.on_confirmed(BA, 'e2', summary, {}, None), 'none')
        self.assertEqual(kinds(self.rt.state)[-1], 'no_progress')
        # A missing declared artifact is never a completed task.
        missing = {'artifacts': [{'path': 'docs/business-analyst/nope.md', 'exists': False}]}
        self.assertEqual(self.guard.on_confirmed(BA, 'e3', missing, {}, None), 'none')
        self.assertEqual(kinds(self.rt.state).count('task_completed'), 1)


# 5. Loop without progress ----------------------------------------------------------------------------------------
class NoProgressLoopTests(GuardCase):
    def test_levels_escalate_with_combined_signals(self):
        self.dispatch(BA, '@BA: Redacta la HU 001 a las 10:05:00.')
        self.dispatch(BA, '@BA: redacta la HU 001 a las 11:17:42.')   # same instruction, other time
        self.assertEqual(levels(self.guard.evaluate()), {('repeated_instruction', BA): 'WARNING'})
        self.dispatch(BA, '@BA: Redacta la HU 001 a las 12:00:00.')
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        self.assertEqual(levels(self.guard.evaluate()), {('repeated_instruction', BA): 'PAUSE',
                                                         ('no_progress', BA): 'PAUSE'})
        self.guard.event('no_progress', BA, reason='escalated_without_block')
        self.assertEqual(levels(self.guard.evaluate())[('no_progress', BA)], 'REQUIRES_INTERVENTION')

    def test_observe_mode_only_alerts_and_enforce_holds_new_dispatches(self):
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        raised = self.guard.tick(force=True)
        self.assertEqual([(a['rule'], a['level'], a['mode']) for a in raised], [('no_progress', 'PAUSE', 'observe')])
        self.assertIn('modo observación', describe(raised[0]))
        self.assertIn('--acknowledge no_progress:business-analyst --confirm', describe(raised[0]))
        self.assertIsNone(self.guard.hold(BA))
        self.guard.settings['mode'] = 'enforce'
        self.assertEqual(self.guard.tick(force=True), [], 'same level: no new announcement')
        self.assertEqual(self.guard.hold(BA)['rule'], 'no_progress')
        # Seen live: an alert raised in observe mode and held after a restart in enforce must say so.
        self.assertNotIn('modo observación', describe(self.guard.hold(BA)))
        self.assertIsNone(self.guard.hold(SA))
        output = self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU 001.\n'), lambda: None])
        self.gateway.prompt.assert_not_called()
        self.assertIn("[Guard] 'business-analyst' retenido", output)
        rows = self.rt.state.db.execute("SELECT data FROM records WHERE id LIKE 'queued:%'").fetchall()
        self.assertEqual([(json.loads(d)['state'], json.loads(d)['stage']) for (d,) in rows], [('queued', 'detectado')])


# 6. Cyclic handoffs ----------------------------------------------------------------------------------------------
class CycleTests(GuardCase):
    def test_ping_pong_without_artifact_changes(self):
        for round_ in range(3):
            self.dispatch(BA, f'@BA: revisa ronda {round_}')
            self.dispatch(SA, f'@SA: revisa ronda {round_}')
        self.assertEqual(levels(self.guard.evaluate()), {('handoff_cycle', '*'): 'WARNING'})
        self.dispatch(BA, '@BA: revisa ronda 3')
        self.dispatch(SA, '@SA: revisa ronda 3')
        finding = next(f for f in self.guard.evaluate() if f['rule'] == 'handoff_cycle')
        self.assertEqual((finding['level'], finding['evidence']['agents']), ('PAUSE', [BA, SA]))
        self.guard.settings['mode'] = 'enforce'
        self.guard.tick(force=True)
        self.assertEqual((self.guard.hold(BA)['rule'], self.guard.hold(SA)['rule']), ('handoff_cycle', 'handoff_cycle'))
        self.guard.acknowledge('handoff_cycle', '*')
        self.assertIsNone(self.guard.hold(BA))
        self.assertEqual(self.guard.evaluate(), [])


# 7. Repeated errors ----------------------------------------------------------------------------------------------
class RepeatedErrorTests(GuardCase):
    def test_equivalent_errors_escalate_and_distinct_ones_do_not_aggregate(self):
        for stamp in ('10:00:01', '10:05:09', '10:09:30'):
            self.guard.error(BA, f'reminder_failed: CommandError at {stamp}')
        self.guard.error(BA, 'provider_limit:quota')
        self.assertEqual(kinds(self.rt.state), ['recoverable_error', 'repeated_error', 'repeated_error',
                                                'recoverable_error'])
        finding = next(f for f in self.guard.evaluate() if f['rule'] == 'repeated_error')
        self.assertEqual((finding['level'], finding['evidence']['count']), ('PAUSE', 3))
        self.guard.acknowledge('repeated_error', BA)
        self.assertEqual(self.guard.evaluate(), [])
        self.assertEqual(self.guard.error(BA, 'reminder_failed: CommandError')['kind'], 'recoverable_error')


# 8. Uncertain delivery -------------------------------------------------------------------------------------------
class UncertainDeliveryTests(GuardCase):
    def test_uncertain_delivery_requires_intervention_and_is_never_retried(self):
        self.gateway.prompt.side_effect = DeliveryUncertain('herdr timeout after send')
        self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU 001.\n')], expect=DeliveryUncertain)
        self.assertEqual(kinds(self.rt.state), ['delivery_uncertain'])
        self.assertEqual(levels(self.guard.evaluate()), {('delivery_uncertain', BA): 'REQUIRES_INTERVENTION'})
        self.assertIn('nunca se reintenta', self.guard.evaluate()[0]['recommendation'])
        # Restart: the pending task meets its uncertain dispatch claim and stops again, without sending.
        self.start()
        self.run_watcher([], expect=ReconciliationRequired)
        self.assertEqual(self.gateway.prompt.call_count, 1)


# 9-10. Restart and recovery from SQLite --------------------------------------------------------------------------
class RestartRecoveryTests(GuardCase):
    def alert(self):
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        return self.guard.tick(force=True)

    def test_metrics_and_alerts_survive_a_watcher_restart_without_new_announcements(self):
        self.dispatch(BA, '@BA: HU')
        self.assertEqual(len(self.alert()), 1)
        log = self.rt.context.output('logs/guard.log')
        self.assertEqual(len(log.read_text(encoding='utf-8').splitlines()), 1)
        before = self.guard.evaluate()
        self.start()
        self.rt.guard.clock = time.time
        self.assertEqual(self.guard.evaluate(), before)
        self.assertEqual(self.guard.tick(force=True), [])
        output = self.run_watcher([lambda: None])
        self.assertNotIn('[Guard', output)
        self.assertEqual(len(log.read_text(encoding='utf-8').splitlines()), 1)
        self.assertEqual(self.rt.state.get('guard_alert:no_progress:' + BA)['state'], 'open')
        self.assertEqual(kinds(self.rt.state, BA)[0], 'dispatched')

    def cli(self, *argv):
        def build(root, **kwargs):
            return Runtime(root, registry=registry(), gateway=self.gateway, runner=Mock(), **kwargs)
        output = io.StringIO()
        with patch.object(runtime_module, 'Runtime', build), patch('sys.stdout', output):
            code = guard_module.main(self.root, list(argv))
        return code, output.getvalue()

    def snapshot(self):
        return {str(p): p.stat().st_mtime_ns for p in self.root.rglob('*') if p.is_file()}

    def test_report_is_read_only_and_acknowledge_recovers(self):
        self.alert()
        before = self.snapshot()
        code, output = self.cli()
        self.assertEqual(self.snapshot(), before)
        report = json.loads(output)
        self.assertEqual((code, report['mode']), (0, 'observe'))
        self.assertEqual([(a['rule'], a['level']) for a in report['open_alerts']], [('no_progress', 'PAUSE')])
        self.assertEqual(report['metrics_by_provider']['fake']['cost_usd'], 'unavailable')
        with patch('sys.stderr'), self.assertRaises(SystemExit):
            self.cli('--acknowledge', 'no_progress:' + BA)   # needs --confirm
        code, output = self.cli('--acknowledge', 'no_progress:' + BA, '--confirm')
        self.assertEqual((code, json.loads(output)['alert_level']), (0, 'PAUSE'))
        self.assertEqual(self.rt.state.get('guard_alert:no_progress:' + BA)['resolution'], 'acknowledged')
        self.rt.guard.clock = time.time
        self.guard.event('no_progress', BA, reason='turn_without_block')
        self.assertEqual(self.guard.evaluate(), [], 'events reviewed by the operator stop counting')
        self.assertEqual(self.cli('--acknowledge', 'bogus:' + BA, '--confirm')[0], 1)


# 11. Two independent workspaces ----------------------------------------------------------------------------------
def test_two_workspaces_keep_independent_ledgers_and_alerts(engine):
    alpha, beta = new_project(engine, 'alpha'), new_project(engine, 'beta')
    runtimes = [Runtime(engine, context=context, gateway=Mock(), runner=Mock()) for context in (alpha, beta)]
    a, b = runtimes
    try:
        for _ in range(3):
            a.guard.event('no_progress', BA, reason='turn_without_block')
        assert [(x['rule'], x['level']) for x in a.guard.tick(force=True)] == [('no_progress', 'PAUSE')]
        assert b.guard.tick(force=True) == [] and load_events(b.state) == []
        assert alpha.output('logs/guard.log').is_file() and not beta.output('logs/guard.log').exists()
        b.guard.acknowledge('no_progress', BA)
        assert a.state.get('guard_alert:no_progress:' + BA)['state'] == 'open'
        assert a.state.get('guard_ack:no_progress:' + BA) is None
    finally:
        for rt in runtimes:
            rt.close()


# 12. Manual CLEAR and ROTATE after an alert ----------------------------------------------------------------------
class ManualMaintenanceAfterAlertTests(MaintenanceCase):
    def test_clear_and_rotate_work_and_only_reset_the_context_budget(self):
        guard = self.rt.guard
        guard.clock = Steps()
        guard.settings['mode'] = 'enforce'
        guard.settings['budget']['max_operations_per_session'] = 1
        self.handoff(BA, '@BA:')
        guard.on_dispatch(BA, '@BA: HU', 'e1')
        for _ in range(3):
            guard.event('no_progress', BA, reason='turn_without_block')
        guard.tick(force=True)
        self.assertEqual(levels(guard.evaluate()), {('operations_per_session', BA): 'WARNING', ('no_progress', BA): 'PAUSE'})
        self.assertIn('CLEAR', next(f for f in guard.evaluate() if f['rule'] == 'operations_per_session')['recommendation'])
        op = self.maintenance().run('CLEAR', BA)
        self.assertEqual((op['state'], op['generation_after']), ('COMPLETED', 2))
        self.assertEqual([c[0] for c in self.calls('p-' + BA)], ['submit', 'prompt'])   # nothing from the guard
        guard.tick(force=True)
        self.assertEqual(self.rt.state.get('guard_alert:operations_per_session:' + BA)['resolution'], 'condition_cleared')
        # A loop is not erased by refreshing the context: the operator reviews it explicitly.
        self.assertEqual(guard.hold(BA)['rule'], 'no_progress')
        guard.acknowledge('no_progress', BA)
        self.assertIsNone(guard.hold(BA))

        self.handoff(SA, '@SA:')
        for _ in range(3):
            guard.event('no_progress', SA, reason='turn_without_block')
        guard.tick(force=True)
        op = self.maintenance().run('ROTATE', SA)
        self.assertEqual((op['state'], op['generation_after']), ('COMPLETED', 2))
        self.assertEqual(guard.hold(SA)['rule'], 'no_progress')


# 13. Compatibility with earlier states ---------------------------------------------------------------------------
class CompatibilityTests(GuardCase):
    def test_defaults_old_followups_and_state_listing(self):
        self.assertEqual(self.rt.config.data['guard']['mode'], 'observe')
        self.assertEqual(self.guard.evaluate(), [])
        # Followups saved before 4C have no 'inicio' (or nothing at all).
        self.rt.state.put('followup', {BA: {'pane_id': 'p-' + BA, 'despachado': self.steps.value - 5000},
                                       SA: {'pane_id': 'p-' + SA}})
        self.dispatch(SA, '@SA: plan')
        self.dispatch(BA, '@BA: HU')
        self.assertEqual(levels(self.guard.evaluate()), {('operation_duration', BA): 'WARNING'})
        for _ in range(3):
            self.guard.event('no_progress', BA)
        self.guard.tick(force=True)
        self.rt.close()
        self.rt = None
        output = io.StringIO()
        try:
            with patch('sys.stdout', output), patch('warnings.warn'):
                state_module.main(['--root', str(self.root)])
        finally:
            self.start()
        listed = [json.loads(line)['id'] for line in output.getvalue().splitlines()]
        self.assertFalse([key for key in listed if key.startswith('progress:')], 'facts are never pending work')
        self.assertIn('guard_alert:no_progress:' + BA, listed)

    def test_off_mode_records_nothing(self):
        self.guard.settings['mode'] = 'off'
        self.assertIsNone(self.guard.event('no_progress', BA))
        self.assertIsNone(self.guard.error(BA, 'x'))
        self.assertEqual((self.guard.tick(force=True), self.guard.hold(BA)), ([], None))
        self.assertEqual(load_events(self.rt.state), [])

    def test_invalid_guard_configuration(self):
        for settings in ({'mode': 'auto'}, {'loop': {'no_progress': {'warning': 5, 'pause': 2}}},
                         {'providers': {'nadie': {}}}, {'budget': {'max_attempts': 0}}, {'unknown': 1}):
            with self.subTest(settings=settings):
                self.write_guard(settings)
                with self.assertRaises(ConfigurationError):
                    Runtime(self.root, registry=registry(), gateway=self.gateway, runner=Mock())

    def test_observer_failures_never_stop_the_flow(self):
        with patch.object(self.rt.state, 'put', side_effect=OSError('disk full')), patch('sys.stdout'):
            self.assertIsNone(self.guard.event('no_progress', BA))
            self.assertIsNone(self.guard.on_dispatch(BA, '@BA: HU', 'e1'))


# 14. Optimized contracts without lost instructions ---------------------------------------------------------------
POLICY = ('# Política global\n## Aislamiento\nNunca escribas fuera de WORKSPACE_ROOT.\n'
          '## Seguridad\nNo leas secretos ni credenciales.\n## Tracker\nSolo anexa bloques; no reescribas historia.\n')


def test_task_references_policy_in_contract_without_losing_instructions(engine):
    (engine / 'constitution.md').write_text(POLICY, encoding='utf-8')
    ctx = new_project(engine)
    gateway = Mock()
    rt = Runtime(engine, context=ctx, gateway=gateway, runner=Mock())
    try:
        selection, _ = rt.factory.resolve(agent=BA)
        name = ctx.session_name(BA)
        rt.state.put('agent:' + BA, {'provider': selection.provider, 'model': selection.model, 'pane_id': 'p1',
                                     'state': 'ready', 'session_name': name})
        gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p1', 'agent_status': 'idle'}]
        ready_pane(gateway, rt.factory.resolve(agent=BA)[1])
        before = ctx.instructions() + assemble(ctx, role=BA) + TRACKER_RULE
        assert rt.dispatcher.dispatch(BA, 'p1', '@BA: Redacta la HU 001.', 'ev-4c')
        task = ctx.output(rt.state.get('dispatch:ev-4c')['task_file']).read_text(encoding='utf-8')
        contract = agent_contract(ctx, BA)
        # Every line the task carried before is still delivered: in the task or, once, in the contract.
        assert all(line in task or line in contract for line in before.splitlines() if line.strip())
        assert all(line in contract and line not in task for line in POLICY.splitlines()[1:] if line.strip())
        for rule in (ctx.instructions(), TRACKER_RULE, '@BA: Redacta la HU 001.', 'CONTRATO VIGENTE'):
            assert rule in task
        assert 'POLÍTICA GLOBAL: ' + (engine / 'constitution.md').as_posix() in task
        assert 'POLÍTICA GLOBAL de tu contrato state/contracts/business-analyst.md' in task
        for rule in (EXECUTION_RULE, TRACKER_RULE, 'Shared role: write legacy ../docs here.'):
            assert rule in contract
        assert source_digests(ctx, BA)['POLÍTICA GLOBAL'] in contract.splitlines()[0]
        assert len(assemble(ctx, role=BA, policy_in_contract='c.md')) < len(assemble(ctx, role=BA))
        # Headless runs have no contract: they keep the complete policy.
        assert 'Nunca escribas fuera de WORKSPACE_ROOT.' in assemble(ctx, operation='plan')
    finally:
        rt.close()
