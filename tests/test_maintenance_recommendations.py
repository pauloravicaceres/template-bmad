"""Phase 4D.2: supervised maintenance recommendations. The runtime recommends CLEAR/ROTATE with evidence and the exact
command; it never runs it. Herdr and CLIs are fakes; nothing real is launched."""
import io
import json
from pathlib import Path
from unittest.mock import Mock, patch

from bmad_runtime import guard as guard_module, maintenance as maintenance_module, runtime as runtime_module
from bmad_runtime import state as state_module
from bmad_runtime.guard import load_events, maintenance_command, metric, recommendations, status
from bmad_runtime.runtime import Runtime
from bmad_runtime.watcher_service import WatcherService
from tests.test_context_guard import BA, SA, GuardCase, Steps
from tests.test_session_maintenance import MaintenanceCase, registry
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)


class RecommendationCase(MaintenanceCase):
    def setUp(self):
        super().setUp()
        self.prepare()

    def prepare(self):
        self.rt.guard.clock = Steps()
        self.rt.guard.settings['budget']['max_operations_per_session'] = 2

    def work(self, name=BA, times=2, token='@BA:'):
        """Confirmed tasks dispatched to the current session of `name`, like the watcher records them."""
        for _ in range(times):
            task = self.handoff(name, token)
            self.rt.state.put('dispatch:' + task['event_id'], {'state': 'done', 'provider': self.provider, 'attempt': 1})
            self.rt.guard.on_dispatch(name, f'{token} tarea', task['event_id'])
            self.rt.guard.event('handoff_confirmed', name, event_id=task['event_id'], progress='verified',
                                metrics={'duration_s': metric(20.0, 'measured', 'runtime_clock')})

    def advice(self, name=BA):
        return recommendations(self.rt.guard, self.rt.sessions, self.rt.state)[name]

    def announce(self):
        return self.rt.guard.announce_recommendations(self.rt.sessions, force=True)


# 1-2. Correct recommendation per provider ----------------------------------------------------------------------
class ProviderRecommendationTests(RecommendationCase):
    def test_claude_gets_clear_with_evidence_and_exact_command(self):
        self.work()
        entry = self.advice()
        self.assertEqual((entry['status'], entry['operation'], entry['provider'], entry['generation']),
                         ('recommended', 'CLEAR', 'fake-claude', 1))
        self.assertEqual((entry['operations'], entry['threshold'], entry['cause']), (2, 2, 'operations_per_session'))
        self.assertTrue(all(value == 'ok' for value in entry['checks'].values()), entry['checks'])
        self.assertEqual(entry['evidence']['tasks_confirmed'], 2)
        self.assertEqual(entry['evidence']['duration_s']['value'], 40.0)
        # Token usage is never invented for interactive sessions, so it is never a trigger.
        self.assertEqual(entry['evidence']['input_tokens'], metric(source='provider'))
        self.assertIn('-m bmad_runtime.maintenance --clear business-analyst --confirm', entry['commands']['apply'])
        self.assertIn('--plan-clear', entry['commands']['review'])
        self.assertEqual(entry['commands']['cwd'], str(self.rt.context.engine_root))
        # Recommending changes nothing: no prompt, no /clear, agent still ready in generation 1.
        self.announce()
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.rt.state.get('agent:' + BA).get('generation', 1), 1)
        self.assertEqual(self.rt.state.get('agent:' + BA)['state'], 'ready')
        self.assertEqual(self.ops(), [])

    def test_codex_gets_rotate(self):
        self.configure('fake-codex')
        self.prepare()
        self.provider = 'fake-codex'
        self.work(SA, token='@SA:')
        entry = self.advice(SA)
        self.assertEqual((entry['status'], entry['operation'], entry['provider']), ('recommended', 'ROTATE', 'fake-codex'))
        self.assertIn('--rotate solutions-architect --confirm', entry['commands']['apply'])
        self.assertEqual(self.advice(BA)['status'], 'below_threshold')


# 3-7. Blocking conditions ---------------------------------------------------------------------------------------
class BlockedRecommendationTests(RecommendationCase):
    def blocked(self, group):
        entry = self.advice()
        self.assertEqual(entry['status'], 'blocked')
        self.assertNotEqual(entry['checks'][group], 'ok', entry['checks'])
        self.assertEqual(self.announce(), [])
        return entry

    def test_agent_not_eligible_while_busy(self):
        self.work()
        self.gateway.agents['p-' + BA]['agent_status'] = 'working'
        self.assertIn('herdr_busy:working', self.blocked('owned_idle_agent')['checks']['owned_idle_agent'])

    def test_pending_handoff(self):
        self.work()
        self.handoff(BA, '@BA:', dispatch=False, confirm=False)
        self.blocked('no_pending_or_uncertain_handoffs')

    def test_uncertain_delivery(self):
        self.work()
        self.rt.state.put('dispatch:incierto', {'state': 'uncertain', 'agent_id': BA, 'attempt': 1})
        self.assertIn('uncertain_dispatch', self.blocked('no_pending_or_uncertain_handoffs')['reasons'])

    def test_inconsistent_tracker(self):
        self.work()
        self.tracker.write_text('historia reescrita\n', encoding='utf-8')
        self.assertTrue(any(r.startswith('tracker_') for r in self.blocked('tracker_integrity')['reasons']))

    def test_maintenance_in_progress(self):
        self.work()
        self.rt.state.put('maintenance:enCurso', {'op_id': 'enCurso' + '0' * 25, 'agent': SA, 'kind': 'ROTATE',
                                                  'state': 'STOPPING', 'states': {'REQUESTED': 1.0}})
        self.assertIn('maintenance_pending:' + SA, self.blocked('no_maintenance_in_progress')['reasons'])


# 8. Duplicates and new evidence --------------------------------------------------------------------------------
class DuplicateRecommendationTests(RecommendationCase):
    def test_once_per_session_cause_and_evidence(self):
        self.work()
        first = self.announce()
        self.assertEqual([(r['agent'], r['operation'], r['step']) for r in first], [(BA, 'CLEAR', 1)])
        self.assertEqual(self.announce(), [], 'same generation and cause, no new evidence')
        log = self.rt.context.output('logs/guard.log').read_text(encoding='utf-8').splitlines()
        self.assertEqual([json.loads(line)['type'] for line in log if '"recommendation"' in line], ['recommendation'])
        self.assertIsNotNone(status(self.rt, self.rt.state, names=[BA])['agents'][0]['recommendation']['announced_at'])
        self.work(times=1)
        self.assertEqual(self.announce(), [], 'one more task is not a new full budget')
        self.work(times=1)
        self.assertEqual([r['step'] for r in self.announce()], [2], 'another full budget is new evidence')
        # The operator applies it: a new generation starts below the threshold.
        op = self.maintenance().run('CLEAR', BA)
        self.assertEqual(op['generation_after'], 2)
        self.assertEqual((self.advice()['status'], self.announce()), ('below_threshold', []))
        self.work()
        self.assertEqual([(r['generation'], r['step']) for r in self.announce()], [(2, 1)])

    def test_throttled_without_force_and_off_mode_silent(self):
        self.work()
        guard = self.rt.guard
        self.assertEqual(len(guard.announce_recommendations(self.rt.sessions)), 1)
        self.rt.state.db.execute("DELETE FROM records WHERE id LIKE 'guard_recommendation:%'")
        self.rt.state.db.commit()
        self.assertEqual(guard.announce_recommendations(self.rt.sessions), [], 'evaluated at most every 30 s')
        guard.settings['mode'] = 'off'
        self.assertEqual(self.announce(), [])


# 9. Watcher restart --------------------------------------------------------------------------------------------
class WatcherRecommendationTests(GuardCase):
    def test_watcher_prints_once_and_never_runs_it_across_restarts(self):
        self.guard.settings['budget']['max_operations_per_session'] = 2
        for number in range(2):
            self.append(f'- **Handoff:** @BA: Tarea {number}.\n')
            index = len(self.tracker.read_text(encoding='utf-8').splitlines()) - 1
            line = f'- **Handoff:** @BA: Tarea {number}.\n'
            task = self.service.enqueue(index, line, {'agente': BA, 'mensaje': f'@BA: Tarea {number}.'})
            self.service.mark(task, 'reservado')
            self.service.dispatched(task)
            self.rt.state.put('dispatch:' + task['event_id'], {'state': 'done', 'provider': 'fake', 'attempt': 1})
            self.guard.on_dispatch(BA, line, task['event_id'])
            report = (f'### [10-10-2026] Business Analyst\n- **Hora:** 10:0{number}:00\n'
                      '- **Artefacto generado:** `docs/business-analyst/001-demo.md`\n- **Estado:** hecho\n'
                      '- **⚠️ Puntos Abiertos:** Ninguno.\n- **Handoff:** @HUMANO: revisar.\n')
            self.append(report)
            self.service.mark(task, 'confirmado')
            self.rt.sessions.record_summary(BA, task['event_id'], report)
        self.sync_cursor()
        output = self.run_watcher([lambda: None])
        self.assertEqual(output.count('[Guard RECOMENDACIÓN] ROTATE business-analyst'), 1, output)
        self.assertIn('No se ejecuta automáticamente', output)
        self.gateway.prompt.assert_not_called()
        self.gateway.submit.assert_not_called()
        self.start()
        self.guard.settings['budget']['max_operations_per_session'] = 2
        self.assertNotIn('RECOMENDACIÓN', self.run_watcher([lambda: None]), 'persisted: a restart does not repeat it')


# 10. Two workspaces --------------------------------------------------------------------------------------------
def test_recommendations_and_commands_stay_in_their_workspace(engine):
    alpha, beta = new_project(engine, 'alpha'), new_project(engine, 'beta')
    gateway = Mock()
    gateway.list_agents.return_value = []
    runtimes = [Runtime(engine, context=context, gateway=gateway, runner=Mock()) for context in (alpha, beta)]
    try:
        for rt in runtimes:
            rt.guard.settings['budget']['max_operations_per_session'] = 2
            selection, _ = rt.factory.resolve(agent=BA)
            rt.state.put('agent:' + BA, {'provider': selection.provider, 'model': selection.model, 'pane_id': 'p1',
                                         'state': 'ready', 'run_id': 'r1', 'session_name': rt.context.session_name(BA)})
        for event in ('e1', 'e2'):
            runtimes[0].guard.on_dispatch(BA, '@BA: tarea', event)
        a, b = (recommendations(rt.guard, rt.sessions, rt.state)[BA] for rt in runtimes)
        # Herdr shows no agent: alpha reached its budget but is not eligible; beta has no work at all.
        assert (a['status'], a['operations'], b['status'], b['operations']) == ('blocked', 2, 'below_threshold', 0)
        assert 'herdr_agent_absent' in a['checks']['owned_idle_agent']
        for rt, ctx in zip(runtimes, (alpha, beta)):
            command = maintenance_command(rt.context, '--plan-clear')
            assert f'--workspace "{ctx.workspace_root}" --project {ctx.project_id}' in command
        assert load_events(runtimes[1].state) == []
    finally:
        for rt in runtimes:
            rt.close()


# 11. Earlier SQLite states -------------------------------------------------------------------------------------
class CompatibilityTests(RecommendationCase):
    def test_records_without_run_id_ledger_or_recommendation_fields(self):
        self.rt.state.put('agent:' + BA, {k: v for k, v in self.rt.state.get('agent:' + BA).items() if k != 'run_id'})
        self.assertEqual(self.advice()['status'], 'below_threshold')
        self.assertEqual(self.announce(), [])
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'run_id': 'run-1'})
        self.rt.state.put('guard_recommendation:' + BA, {'state': 'done'})   # earlier or hand-edited record
        self.work()
        self.assertEqual(len(self.announce()), 1)
        # Recommendations are facts already handled, never pending work in the state listing.
        self.rt.close()
        self.rt = None
        output = io.StringIO()
        try:
            with patch('sys.stdout', output), patch('warnings.warn'):
                state_module.main(['--root', str(self.root)])
        finally:
            self.start()
        self.assertNotIn('guard_recommendation', output.getvalue())

    def test_legacy_command_has_no_workspace_arguments(self):
        self.assertTrue(self.rt.context.legacy)
        self.assertNotIn('--workspace', maintenance_command(self.rt.context, '--plan-clear'))


# 13. Watcher started with --config: the recommended command keeps that file --------------------------------------
class AlternateConfigTests(RecommendationCase):
    def prepare(self):
        self.rt.guard.clock = Steps()     # the threshold comes from the configuration file, not from the test

    def alternate(self):
        """Copy of the engine config with a 2-task budget, under a path with a space (the command must quote it)."""
        raw = json.loads((self.root / 'config_bmad.json').read_text(encoding='utf-8'))
        raw['ai']['guard'] = {'mode': 'observe', 'budget': {'max_operations_per_session': 2}}
        path = self.root / 'alterna' / 'config umbral.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(raw), encoding='utf-8')
        return path.resolve()

    def build(self, root, **kwargs):
        # The CLI must forward --config itself: the fake only replaces Herdr and the CLIs.
        return Runtime(root, registry=registry(), gateway=self.gateway, runner=Mock(), **kwargs)

    def restart(self, config=None):
        """Same as starting the watcher with (or without) --config; a relative path is anchored to ENGINE_ROOT."""
        self.rt.close()
        self.rt = self.build(self.root, config_path=config)
        self.service = WatcherService(self.rt)
        self.gateway.context = self.rt.context
        self.prepare()

    def cli(self, module, *argv):
        output = io.StringIO()
        target = maintenance_module if module is maintenance_module else runtime_module
        with patch.object(target, 'Runtime', self.build), patch('sys.stdout', output), patch('warnings.warn'):
            code = module.main(self.root, list(argv))
        return code, output.getvalue()

    def test_default_configuration_command_is_unchanged(self):
        self.rt.guard.settings['budget']['max_operations_per_session'] = 2
        self.work()
        entry = self.advice()
        self.assertEqual(entry['status'], 'recommended')
        self.assertIsNone(entry['commands']['config'])
        self.assertNotIn('--config', entry['commands']['review'] + entry['commands']['apply'])
        self.assertTrue(entry['commands']['apply'].endswith('--clear business-analyst --confirm'))

    def test_alternate_configuration_is_kept_absolute_in_both_commands(self):
        path = self.alternate()
        self.restart(Path('alterna') / 'config umbral.json')
        self.assertEqual(self.advice()['threshold'], 2, 'threshold read from the alternate file')
        self.work()
        entry = self.advice()
        self.assertEqual(entry['status'], 'recommended')
        self.assertEqual(entry['commands']['config'], str(path))
        self.assertTrue(path.is_file(), 'explicit and verifiable')
        for command in (entry['commands']['review'], entry['commands']['apply']):
            self.assertTrue(command.endswith(f'--config "{path}"'), command)
        record = self.announce()[0]
        self.assertIn(f'--config "{path}"', guard_module.describe_recommendation(record))
        self.assertEqual(self.rt.state.get('guard_recommendation:' + BA)['commands']['config'], str(path))

    def test_recommended_commands_run_with_the_same_file(self):
        path = self.alternate()
        self.restart(path)
        self.work()
        self.announce()
        self.rt.close()
        self.rt = None
        try:
            code, output = self.cli(maintenance_module, '--plan-clear', '--config', str(path))
            report = json.loads(output)
            self.assertEqual((code, report['config']), (0, str(path)))
            self.assertEqual({row['agent']: row['eligibility'] for row in report['agents']}[BA], 'ELIGIBLE')
            self.assertEqual(json.loads(self.cli(maintenance_module, '--plan-clear')[1])['config'], 'default')
            # guard --status with the watcher's file: same threshold, no warning.
            code, output = self.cli(guard_module, '--status', '--agent', BA, '--config', str(path))
            advice = json.loads(output)['agents'][0]['recommendation']
            self.assertEqual((code, advice['status'], advice['threshold']), (0, 'recommended', 2))
            self.assertNotIn('config_warning', advice)
            self.assertIsNotNone(advice['announced_at'])
        finally:
            self.start()
        self.assertEqual(self.gateway.calls, [], 'reviewing and planning never touch the agent')

    def test_report_from_another_configuration_warns(self):
        path = self.alternate()
        self.restart(path)
        self.work()
        self.announce()
        self.restart()                                         # operator forgot --config
        # Seen live: with the default budget the report said below_threshold and nothing else.
        advice = status(self.rt, self.rt.state, names=[BA])['agents'][0]['recommendation']
        self.assertEqual(advice['status'], 'below_threshold')
        self.assertIn(str(path), advice['config_warning'])
        self.assertIn('Usa el mismo --config que el watcher', advice['config_warning'])
        self.rt.guard.settings['budget']['max_operations_per_session'] = 2
        advice = status(self.rt, self.rt.state, names=[BA])['agents'][0]['recommendation']
        self.assertIsNone(advice['commands']['config'])
        self.assertIn(str(path), advice['config_warning'])

    def test_budget_alert_text_names_the_watcher_configuration(self):
        path = self.alternate()
        self.restart(path)
        self.work()
        alert = next(a for a in self.rt.guard.tick(force=True) if a['rule'] == 'operations_per_session')
        self.assertIn(f'--plan-clear --config "{path}"', alert['recommendation'])
        self.restart()
        self.rt.guard.settings['budget']['max_operations_per_session'] = 2
        self.assertNotIn('--config', self.rt.guard._recommend({'rule': 'operations_per_session', 'agent': BA}))

    def test_records_from_earlier_versions_do_not_invent_a_warning(self):
        self.rt.guard.settings['budget']['max_operations_per_session'] = 2
        self.work()
        record = self.announce()[0]
        record['commands'].pop('config')
        self.rt.state.put('guard_recommendation:' + BA, record)
        self.assertNotIn('config_warning', status(self.rt, self.rt.state, names=[BA])['agents'][0]['recommendation'])


def test_workspace_command_keeps_scope_and_alternate_config(engine, tmp_path):
    alpha = new_project(engine, 'alpha')
    config = (tmp_path / 'otra config.json').resolve()
    config.write_text((engine / 'config_bmad.json').read_text(encoding='utf-8'), encoding='utf-8')
    assert maintenance_command(alpha, '--plan-clear').endswith(f'--project {alpha.project_id}')
    command = maintenance_command(alpha, '--plan-clear', config=config)
    assert command.endswith(f'--workspace "{alpha.workspace_root}" --project {alpha.project_id} --config "{config}"')


# 12. Headless metrics never drive interactive recommendations ---------------------------------------------------
class HeadlessMetricTests(RecommendationCase):
    def test_measured_and_unavailable_headless_usage(self):
        self.rt.guard.settings['headless_usage'] = True
        huge = {name: metric(10 ** 7, 'measured', 'claude --output-format json') for name in ('input_tokens', 'output_tokens')}
        self.rt.guard.event('headless_run', 'speckit.plan', status='success', metrics=huge)
        self.rt.guard.event('headless_run', 'speckit.clarify', status='success',
                            metrics={'input_tokens': metric(source='provider')})
        self.work(times=1)
        report = status(self.rt, self.rt.state)
        self.assertEqual([(r['operation'], r['metrics']['input_tokens']['quality']) for r in report['headless_runs']],
                         [('speckit.plan', 'measured'), ('speckit.clarify', 'unavailable')])
        self.assertEqual({row['agent']: row['recommendation']['status'] for row in report['agents']},
                         {BA: 'below_threshold', SA: 'below_threshold'})
        self.assertNotIn('speckit.plan', recommendations(self.rt.guard, self.rt.sessions, self.rt.state))


# Recovery tool: releasing a followup only after the operator acknowledged its task ------------------------------
class ReleaseFollowupTests(GuardCase):
    def cli(self, *argv):
        self.rt.close()
        self.rt = None
        output = io.StringIO()
        try:
            with patch('sys.stdout', output), patch('sys.stderr'), patch('warnings.warn'):
                code = state_module.main(['--root', str(self.root), *argv])
        finally:
            self.start()
        return code, output.getvalue()

    def test_requires_acknowledged_event_and_never_confirms(self):
        line = '- **Handoff:** @BA: Tarea huérfana.\n'
        self.append(line)
        task = self.service.enqueue(0, line, {'agente': BA, 'mensaje': '@BA: Tarea huérfana.'})
        self.service.mark(task, 'reservado')
        self.service.dispatched(task)
        self.rt.state.put('followup', {BA: {'pane_id': 'p-gone', 'event_id': task['event_id'], 'inicio': 1.0}})
        with self.assertRaises(SystemExit):
            self.cli('--release-followup', BA, '--confirm')    # not acknowledged yet
        self.assertIn(BA, self.rt.state.get('followup'))
        self.cli('--acknowledge', 'queued:' + task['event_id'], '--confirm')
        with self.assertRaises(SystemExit):
            self.cli('--release-followup', BA)                  # needs --confirm
        self.cli('--release-followup', BA, '--confirm')
        self.assertEqual(self.rt.state.get('followup'), {})
        queued = self.rt.state.get('queued:' + task['event_id'])
        self.assertEqual(queued['stage'], 'despachado', 'released, never confirmed')
        self.assertTrue(queued['acknowledged'])

    def test_listing_survives_a_cp1252_console(self):
        # Seen live: the changes were applied, then the listing of agent text ('✻') failed with exit code 1.
        self.rt.state.put('protocol_violation:x', {'state': 'open', 'block': 'texto ✻ del agente'})
        self.rt.close()
        self.rt = None
        console = io.TextIOWrapper(io.BytesIO(), encoding='cp1252')
        try:
            with patch('sys.stdout', console), patch('warnings.warn'):
                self.assertEqual(state_module.main(['--root', str(self.root)]), 0)
                console.flush()
                self.assertIn('✻', console.buffer.getvalue().decode('utf-8'))
        finally:
            self.start()
