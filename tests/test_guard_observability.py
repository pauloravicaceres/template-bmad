"""Phase 4D.1: usage metrics, calibration and read-only diagnosis of the guard. Herdr and CLIs are fakes; the JSON
payloads mirror results observed live (Claude Code 2.1.296, Codex 0.162.0) with identifiers removed."""
import io
import json
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch

from bmad_runtime import guard as guard_module, runtime as runtime_module
from bmad_runtime.commands import Command, Result
from bmad_runtime.config import AGENT_PHASES
from bmad_runtime.errors import ConfigurationError
from bmad_runtime.guard import availability, calibrate, describe, load_events, metric, status
from bmad_runtime.providers import ClaudeProvider, CodexProvider, GeminiProvider
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import EXECUTION_RULE, TRACKER_RULE, agent_contract
from tests.test_context_guard import BA, SA, GuardCase, Steps
from tests.test_session_lifecycle import registry
from tests.test_session_maintenance import MaintenanceCase
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)
from tests.pane_doubles import ready_pane

REPO = Path(__file__).resolve().parents[1]

CLAUDE_OK = {'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 3, 'duration_ms': 5000,
             'result': 'Plan generado.\n¿Hay alguna ambigüedad?', 'total_cost_usd': 0.25,
             'usage': {'input_tokens': 12, 'cache_creation_input_tokens': 1000, 'cache_read_input_tokens': 5000,
                       'output_tokens': 300},
             'modelUsage': {'claude-x': {'inputTokens': 12, 'outputTokens': 300, 'cacheReadInputTokens': 5000,
                                         'cacheCreationInputTokens': 1000, 'costUSD': 0.25, 'contextWindow': 200000,
                                         'costBasis': 'list'}}}
# Observed live: stopped by --max-budget-usd, `usage` is all zero and only modelUsage holds the counts.
CLAUDE_BUDGET = {'type': 'result', 'subtype': 'error_max_budget_usd', 'is_error': True, 'result': None, 'num_turns': 1,
                 'total_cost_usd': 0.188428, 'terminal_reason': 'budget_exhausted',
                 'usage': {'input_tokens': 0, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0,
                           'output_tokens': 0},
                 'modelUsage': {'claude-y': {'inputTokens': 2, 'outputTokens': 4, 'cacheReadInputTokens': 0,
                                             'cacheCreationInputTokens': 47096, 'contextWindow': 1000000,
                                             'costBasis': 'list'}}}
CLAUDE_AUTH = {'type': 'result', 'subtype': 'success', 'is_error': True, 'result': 'Invalid API key',
               'num_turns': 1, 'total_cost_usd': 0, 'api_error_status': 401, 'modelUsage': {},
               'usage': {'input_tokens': 0, 'output_tokens': 0}}
CODEX_OK = '\n'.join(json.dumps(event) for event in (
    {'type': 'thread.started', 'thread_id': 't'}, {'type': 'turn.started'},
    {'type': 'item.completed', 'item': {'id': 'item_0', 'type': 'reasoning', 'text': 'pensando'}},
    {'type': 'item.completed', 'item': {'id': 'item_1', 'type': 'agent_message', 'text': 'ok'}},
    {'type': 'turn.completed', 'usage': {'input_tokens': 15266, 'cached_input_tokens': 11008,
                                         'cache_write_input_tokens': 0, 'output_tokens': 5,
                                         'reasoning_output_tokens': 0}})) + '\n'
CODEX_LIMIT = '\n'.join(json.dumps(event) for event in (
    {'type': 'thread.started', 'thread_id': 't'}, {'type': 'turn.started'},
    {'type': 'turn.failed', 'error': {'message': "You've hit your usage limit."}})) + '\n'


def values(metrics):
    return {name: (item['value'], item['quality']) for name, item in metrics.items()}


# 1. Structured headless usage -------------------------------------------------------------------------------------
def test_claude_json_result_is_measured_and_keeps_the_text_answer():
    provider = ClaudeProvider('claude')
    command = provider.structured_headless(Command(('claude', '-p', '--model', 'm'), Path('.'), stdin='x'))
    assert command.argv == ('claude', '-p', '--output-format', 'json', '--model', 'm') and command.stdin == 'x'
    result, usage = provider.read_headless_usage(Result(0, json.dumps(CLAUDE_OK), '', None, 5100))
    assert result.stdout == CLAUDE_OK['result'] and result.duration_ms == 5100
    assert values(usage) == {'input_tokens': (6012, 'measured'), 'cached_input_tokens': (5000, 'measured'),
                             'cache_write_tokens': (1000, 'measured'), 'output_tokens': (300, 'measured'),
                             'turns': (3, 'measured'), 'cost_usd': (0.25, 'estimated'),
                             'context_window': (200000, 'measured')}
    assert 'costBasis=list' in usage['cost_usd']['source'] and 'not billing' in usage['cost_usd']['source']
    assert provider.classify(result) == 'success'


def test_claude_error_results_never_report_invented_usage():
    provider = ClaudeProvider('claude')
    result, usage = provider.read_headless_usage(Result(1, json.dumps(CLAUDE_BUDGET), 'warn', None, 2500))
    assert values(usage)['input_tokens'] == (47098, 'measured') and values(usage)['output_tokens'] == (4, 'measured')
    assert usage['cost_usd']['quality'] == 'estimated'
    assert result.stdout == '' and 'error_max_budget_usd' in result.stderr and provider.classify(result) == 'cli_error'
    result, usage = provider.read_headless_usage(Result(1, json.dumps(CLAUDE_AUTH)))
    assert {name for name, (_, quality) in values(usage).items() if quality == 'unavailable'} == {
        'input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens', 'cost_usd', 'context_window'}
    assert usage['input_tokens']['value'] is None and result.stdout == 'Invalid API key'
    # Text output (capture disabled or an older CLI) is left untouched.
    raw = Result(0, 'texto libre', '')
    assert provider.read_headless_usage(raw) == (raw, None)
    assert provider.read_headless_usage(Result(0, '{"type": "other"}')) == (Result(0, '{"type": "other"}'), None)


def test_codex_jsonl_usage_and_errors():
    provider = CodexProvider('codex')
    command = provider.structured_headless(Command(('codex', 'exec', '--sandbox', 'read-only', '-'), Path('.')))
    assert command.argv == ('codex', 'exec', '--json', '--sandbox', 'read-only', '-')
    result, usage = provider.read_headless_usage(Result(0, 'aviso no JSON\n' + CODEX_OK, ''))
    assert result.stdout == 'ok'
    assert values(usage) == {'input_tokens': (15266, 'measured'), 'cached_input_tokens': (11008, 'measured'),
                             'cache_write_tokens': (0, 'measured'), 'output_tokens': (5, 'measured'),
                             'turns': (1, 'measured'), 'cost_usd': (None, 'unavailable'),
                             'context_window': (None, 'unavailable')}
    result, usage = provider.read_headless_usage(Result(1, CODEX_LIMIT, ''))
    assert values(usage)['turns'] == (0, 'measured') and usage['input_tokens']['quality'] == 'unavailable'
    assert provider.classify(result) == 'quota'
    assert provider.read_headless_usage(Result(0, 'ok\n')) == (Result(0, 'ok\n'), None)


def test_availability_distinguishes_interactive_and_headless():
    for provider, cost in ((ClaudeProvider('claude'), 'estimated'), (CodexProvider('codex'), 'unavailable')):
        table = availability(provider, headless_usage=True)
        assert {table[name] for name in ('input_tokens', 'output_tokens', 'cost_usd')} == {'unavailable'}
        assert table['headless']['input_tokens'] == 'measured' and table['headless']['cost_usd'].startswith(cost)
        assert availability(provider)['headless']['input_tokens'].startswith('unavailable (activable')
    assert set(availability(GeminiProvider('gemini'), True)['headless'].values()) == {'unavailable', 'measured (runtime_clock)'}


def _speckit(engine, provider, stdout, *, capture):
    config = json.loads((engine / 'config_bmad.json').read_text(encoding='utf-8'))
    config['ai']['defaults'] = {'provider': provider, 'options': {'effort': 'low'}}
    config['ai']['phases'] = {}
    config['ai']['guard'] = {'headless_usage': capture}
    (engine / 'config_bmad.json').write_text(json.dumps(config), encoding='utf-8')
    ctx = new_project(engine)
    help_text = ('--model --effort --permission-mode --append-system-prompt --print --permission-prompts '
                 '--max-budget-usd --sandbox --cd --add-dir --config --ephemeral')
    runner = Mock()
    runner.run.side_effect = lambda command, timeout=None: (
        Result(0, help_text) if '--help' in command.argv else Result(0, stdout, '', None, 4200))
    return Runtime(engine, context=ctx, gateway=Mock(), runner=runner), runner


def test_speckit_records_measured_usage_only_when_enabled(engine):
    rt, _ = _speckit(engine, 'claude', json.dumps(CLAUDE_OK), capture=True)
    try:
        _, _, command = rt.spec.prepare('clarify')
        assert command.argv[1:4] == ('-p', '--output-format', 'json')
        result = rt.spec.execute('clarify')
        # Callers (clarify, analyze, converge) keep reading the text answer.
        assert result.stdout == CLAUDE_OK['result'] and '?' in result.stdout
        run = next(e for e in load_events(rt.state) if e['kind'] == 'headless_run')
        assert run['metrics']['input_tokens'] == metric(6012, 'measured', 'claude --output-format json modelUsage')
        assert run['metrics']['duration_s'] == metric(4.2, 'measured', 'runtime_clock')
        assert run['metrics']['cost_usd']['quality'] == 'estimated'
        record = rt.state.get(run['run'])
        assert (record['turns'], record['cost_usd']) == (3, 0.25)
    finally:
        rt.close()


def test_speckit_text_output_is_unchanged_by_default(engine):
    rt, _ = _speckit(engine, 'codex', 'texto final', capture=False)
    try:
        _, _, command = rt.spec.prepare('plan')
        assert '--json' not in command.argv
        assert rt.spec.execute('plan').stdout == 'texto final'
        run = next(e for e in load_events(rt.state) if e['kind'] == 'headless_run')
        assert {run['metrics'][name]['quality'] for name in ('input_tokens', 'output_tokens', 'cost_usd')} == {'unavailable'}
        assert (rt.state.get(run['run'])['cost_usd'], rt.state.get(run['run'])['turns']) == ('no_disponible', 'no_disponible')
    finally:
        rt.close()


def test_codex_speckit_usage_and_unparseable_output(engine):
    rt, runner = _speckit(engine, 'codex', CODEX_OK, capture=True)
    try:
        assert rt.spec.execute('plan').stdout == 'ok'
        runner.run.side_effect = lambda command, timeout=None: (
            Result(0, '--model --sandbox --cd --add-dir --config --ephemeral') if '--help' in command.argv
            else Result(0, 'salida inesperada', ''))
        assert rt.spec.execute('plan').stdout == 'salida inesperada'
        runs = [e for e in load_events(rt.state) if e['kind'] == 'headless_run']
        assert runs[0]['metrics']['output_tokens']['value'] == 5
        assert runs[1]['metrics']['output_tokens'] == metric(source='provider')
    finally:
        rt.close()


def test_headless_usage_flag_is_validated(engine):
    config = json.loads((engine / 'config_bmad.json').read_text(encoding='utf-8'))
    config['ai']['guard'] = {'headless_usage': 'yes'}
    (engine / 'config_bmad.json').write_text(json.dumps(config), encoding='utf-8')
    ctx = new_project(engine)
    try:
        Runtime(engine, context=ctx, gateway=Mock(), runner=Mock())
    except ConfigurationError as exc:
        assert 'headless_usage' in str(exc)
    else:
        raise AssertionError('invalid headless_usage accepted')


# 2. Read-only diagnosis -------------------------------------------------------------------------------------------
class StatusTests(GuardCase):
    def send(self, agent, message, event_id, *, task=None):
        record = {'provider': 'fake', 'attempt': 1}
        if task:
            self.rt.context.output(task).parent.mkdir(parents=True, exist_ok=True)
            self.rt.context.output(task).write_text('x' * 400, encoding='utf-8')
            record['task_file'] = task
        self.rt.state.put('dispatch:' + event_id, record)
        self.guard.on_dispatch(agent, message, event_id)

    def confirm(self, agent, event_id, seconds):
        self.guard.event('handoff_confirmed', agent, event_id=event_id, progress='verified',
                         metrics={'duration_s': metric(seconds, 'measured', 'runtime_clock')})
        self.guard.event('artifacts_changed', agent, event_id=event_id, paths=['a.md'])

    def report(self, *names):
        return {row['agent']: row for row in status(self.rt, self.rt.state, names=list(names) or None)['agents']}

    def test_session_work_metrics_holds_and_eligibility(self):
        self.send(BA, '@BA: HU 1', 'e1', task='handoffs/tasks/e1.md')
        self.confirm(BA, 'e1', 30)
        # Operator CLEAR/ROTATE: a new generation of the same launch.
        self.rt.state.put('agent:' + BA, {**self.rt.state.get('agent:' + BA), 'generation': 2,
                                          'session_refreshed_at': '2026-10-10T10:30:19-05:00'})
        self.send(BA, '@BA: HU 2', 'e2', task='handoffs/tasks/e2.md')
        self.confirm(BA, 'e2', 12.5)
        ba = self.report()[BA]
        self.assertEqual(ba['session']['generation'], 2)
        self.assertEqual({k: ba['since_last_maintenance'][k] for k in ('tasks_dispatched', 'tasks_confirmed',
                                                                         'verified_progress')}, {
            'tasks_dispatched': 1, 'tasks_confirmed': 1, 'verified_progress': 1})
        self.assertEqual((ba['duration']['accumulated_s']['value'], ba['duration']['accumulated_s']['quality']),
                         (12.5, 'measured'))
        self.assertEqual((ba['metrics']['task_prompt_tokens']['value'], ba['metrics']['task_prompt_tokens']['quality']),
                         (100, 'estimated'))
        self.assertEqual(ba['metrics']['input_tokens'], metric(source='provider'))
        self.assertEqual(ba['eligibility']['eligibility'], 'NOT_ELIGIBLE')
        self.assertEqual((ba['holds'], ba['alerts']), ([], []))

        for _ in range(3):
            self.guard.event('no_progress', SA, reason='turn_without_block')
        self.guard.tick(force=True)
        sa = self.report(SA)[SA]
        self.assertEqual([(h['source'], h['level'], h['holds_dispatch']) for h in sa['holds']],
                         [('guard', 'PAUSE', False)])
        self.assertIn('modo observación', sa['holds'][0]['effect'])
        # Mode changed (restart in enforce) before the watcher re-persisted the alert: the effect is the current one.
        self.guard.settings['mode'] = 'enforce'
        sa = self.report(SA)[SA]
        self.assertEqual((sa['holds'][0]['holds_dispatch'], sa['alerts'][0]['stored_mode']), (True, 'observe'))
        self.assertEqual(sa['holds'][0]['effect'], 'modo enforce: nuevos despachos retenidos para ' + SA)

        self.rt.state.put('maintenance:op1', {'op_id': 'op1' * 8, 'agent': BA, 'kind': 'ROTATE',
                                              'state': 'REQUIRES_INTERVENTION', 'states': {'REQUESTED': 1.0},
                                              'errors': [{'error': '/exit not confirmed'}]})
        self.rt.state.put('agent:' + SA, {**self.rt.state.get('agent:' + SA), 'state': 'awaiting_trust',
                                          'blocker': 'trust_dialog'})
        rows = self.report()
        self.assertEqual([(h['source'], h['reason']) for h in rows[BA]['holds']],
                         [('maintenance', '/exit not confirmed')])
        self.assertIn('maintenance_pending:' + BA, rows[BA]['eligibility']['reasons'])
        self.assertEqual(rows[BA]['last_maintenance']['state'], 'REQUIRES_INTERVENTION')
        self.assertEqual([h['source'] for h in rows[SA]['holds']], ['guard', 'agent_state'])
        self.assertEqual(rows[SA]['holds'][1]['reason'], 'trust_dialog')

    def test_running_watcher_with_another_config_decides_the_effect(self):
        # Seen live: the watcher ran with --config (enforce) while the workspace config says observe.
        from bmad_runtime.watcher_service import SESSION_PROTOCOL
        self.guard.settings['mode'] = 'enforce'
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        self.guard.tick(force=True)
        self.guard.settings['mode'] = 'observe'
        self.rt.state.put('watcher', {'protocol': SESSION_PROTOCOL, 'heartbeat': time.time()})
        report = status(self.rt, self.rt.state, names=[BA])
        hold = report['agents'][0]['holds'][0]
        self.assertEqual((report['mode'], report['watcher'], report['watcher_modes']), ('observe', 'active', ['enforce']))
        self.assertEqual((hold['holds_dispatch'], hold['effect']),
                         (True, 'modo enforce: nuevos despachos retenidos para ' + BA))
        # Without a live watcher nothing enforces the stored mode: the configured one applies.
        self.rt.state.put('watcher', {'protocol': SESSION_PROTOCOL, 'heartbeat': time.time() - 3600})
        self.assertFalse(status(self.rt, self.rt.state, names=[BA])['agents'][0]['holds'][0]['holds_dispatch'])

    def cli(self, *argv):
        def build(root, **kwargs):
            return Runtime(root, registry=registry(), gateway=self.gateway, runner=Mock(), **kwargs)
        output = io.StringIO()
        with patch.object(runtime_module, 'Runtime', build), patch('sys.stdout', output):
            code = guard_module.main(self.root, list(argv))
        return code, output.getvalue()

    def snapshot(self):
        return {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}

    def test_status_and_calibrate_cli_are_read_only(self):
        self.send(BA, '@BA: HU', 'e1')
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        self.guard.tick(force=True)
        before = self.snapshot()
        code, output = self.cli('--status', '--agent', BA)
        report = json.loads(output)
        self.assertEqual((code, report['read_only'], [row['agent'] for row in report['agents']]), (0, True, [BA]))
        code, output = self.cli('--calibrate')
        self.assertEqual((code, json.loads(output)['alerts_by_rule']['no_progress']['episodes']), (0, 1))
        self.assertEqual(self.snapshot(), before)
        self.gateway.prompt.assert_not_called()
        self.gateway.submit.assert_not_called()
        for argv in (('--status', '--confirm'), ('--agent', BA), ('--status', '--agent', 'nadie'),
                     ('--status', '--calibrate')):
            with self.subTest(argv=argv), patch('sys.stderr'), self.assertRaises(SystemExit):
                self.cli(*argv)

    def test_old_records_and_states_without_guard_data(self):
        # A pre-4C state: no ledger, no alerts. Reports work and propose nothing.
        self.assertEqual([row['alerts'] for row in self.report().values()], [[], []])
        result = calibrate(self.rt, self.rt.state)
        self.assertEqual((result['sample']['events'], result['alerts_by_rule'], result['proposals']), (0, {}, []))
        # An alert record missing fields (older version or edited by hand) is reported and then rewritten.
        self.rt.state.put('guard_alert:no_progress:' + BA, {'state': 'open'})
        self.assertEqual(self.report(BA)[BA]['alerts'][0]['rule'], 'no_progress')
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        self.assertEqual([(a['rule'], a['level']) for a in self.guard.tick(force=True)], [('no_progress', 'PAUSE')])
        stored = self.rt.state.get('guard_alert:no_progress:' + BA)
        self.assertEqual((stored['level'], stored['mode'], stored['agents']), ('PAUSE', 'observe', [BA]))


# 3. Restart with active alerts ------------------------------------------------------------------------------------
class RestartModeTextTests(GuardCase):
    def test_first_hold_after_restart_in_enforce_tells_the_current_mode(self):
        for _ in range(3):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        raised = self.guard.tick(force=True)
        self.assertIn('modo observación', describe(raised[0]))
        self.write_guard({'mode': 'enforce'})
        self.start()
        # The watcher checks holds before its first tick: the stored alert still says observe.
        self.assertEqual(self.rt.state.get('guard_alert:no_progress:' + BA)['mode'], 'observe')
        output = self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU 001.\n'), lambda: None])
        self.assertIn('modo enforce: nuevos despachos retenidos para business-analyst', output)
        self.assertNotIn('modo observación', output)
        self.gateway.prompt.assert_not_called()
        self.assertEqual(self.rt.state.get('guard_alert:no_progress:' + BA)['mode'], 'enforce')
        # Back to observe: nothing held, and the text says so.
        self.write_guard({'mode': 'observe'})
        self.start()
        self.assertIsNone(self.guard.hold(BA))
        self.guard.tick(force=True)
        self.assertIn('modo observación', describe(self.rt.state.get('guard_alert:no_progress:' + BA)))

    def test_enforce_warning_text_never_claims_a_hold(self):
        self.guard.settings['mode'] = 'enforce'
        for _ in range(2):
            self.guard.event('no_progress', BA, reason='turn_without_block')
        alert = self.guard.tick(force=True)[0]
        self.assertEqual(alert['level'], 'WARNING')
        self.assertIn('modo enforce: aviso, no retiene despachos', describe(alert))
        self.assertIsNone(self.guard.hold(BA))


# 4. Calibration ---------------------------------------------------------------------------------------------------
class CalibrationTests(GuardCase):
    def send(self, agent, message, event_id):
        self.rt.state.put('dispatch:' + event_id, {'provider': 'fake', 'attempt': 1})
        self.guard.on_dispatch(agent, message, event_id)

    def test_replay_classifies_episodes_repetitions_and_recovery(self):
        self.send(BA, '@BA: corrige la HU', 'a1')
        self.guard.event('artifacts_changed', BA, paths=['a.md'])
        self.send(BA, '@BA: corrige la HU', 'a2')            # legitimate: progress in between
        self.guard.event('artifacts_changed', BA, paths=['a.md'])
        for number in range(3):                               # induced loop, reviewed by the operator
            self.send(BA, '@BA: redacta la HU 9', f'b{number}')
        self.guard.acknowledge('repeated_instruction', BA)
        self.send(SA, '@SA: plan', 's1')
        for _ in range(3):                                    # PAUSE that progress resolved by itself
            self.guard.event('no_progress', SA, reason='turn_without_block')
        self.guard.event('artifacts_changed', SA, paths=['p.md'])
        for _ in range(2):
            self.guard.error(BA, 'reminder_failed: CommandError')
        finished = self.steps()
        self.rt.state.put('maintenance:c1', {'op_id': 'c1' * 16, 'agent': BA, 'kind': 'CLEAR', 'provider': 'fake',
                                             'state': 'COMPLETED', 'states': {'REQUESTED': finished - 0.5,
                                                                              'COMPLETED': finished}})
        self.send(BA, '@BA: HU 10', 'c2')
        self.guard.event('handoff_confirmed', BA, event_id='c2', progress='verified')
        self.guard.event('artifacts_changed', BA, event_id='c2', paths=['a.md'])
        before = self.rt.state.db.execute('SELECT COUNT(*), MAX(id) FROM records').fetchone()
        result = calibrate(self.rt, self.rt.state)
        self.assertEqual(self.rt.state.db.execute('SELECT COUNT(*), MAX(id) FROM records').fetchone(), before)
        rules = result['alerts_by_rule']
        self.assertEqual(rules['repeated_instruction']['ended_by'], {'acknowledged': 1})
        self.assertEqual(rules['repeated_instruction']['peak'], {'PAUSE': 1})
        self.assertEqual((rules['no_progress']['ended_by'], rules['no_progress']['holding_self_resolved']),
                         ({'progress': 1}, 1))
        self.assertEqual(rules['repeated_error']['ended_by'], {'open': 1})
        self.assertEqual(result['repeated_instructions'], {'legitimate': 1, 'without_progress': 2})
        self.assertEqual([(r['kind'], r['outcome']) for r in result['recovery_after_maintenance']], [('CLEAR', 'verified')])
        fake = result['by_provider']['fake']
        self.assertEqual((fake['dispatches'], fake['no_progress_by_reason']), (7, {'turn_without_block': 3}))
        self.assertEqual(result['verdicts'], [{'scope': 'fake', 'verdict': 'insufficient_evidence',
                                               'detail': '7 despachos < 30: se mantienen los umbrales globales'}])
        self.assertEqual((result['proposals'], result['mode']), ([], 'observe'))

    def test_recovery_only_counts_tasks_of_that_session(self):
        # Seen on a real ledger: operations older than the ledger and a later CLEAR took the same "next task".
        old = self.steps.value - 5000
        self.rt.state.put('maintenance:old', {'op_id': 'o' * 32, 'agent': BA, 'kind': 'ROTATE', 'state': 'COMPLETED',
                                              'states': {'REQUESTED': old, 'COMPLETED': old + 1}})
        self.send(BA, '@BA: HU 1', 'x1')
        first = self.steps()
        self.rt.state.put('maintenance:c1', {'op_id': 'a' * 32, 'agent': BA, 'kind': 'CLEAR', 'state': 'COMPLETED',
                                             'states': {'REQUESTED': first, 'COMPLETED': first + 0.1}})
        second = self.steps()
        self.rt.state.put('maintenance:c2', {'op_id': 'b' * 32, 'agent': BA, 'kind': 'CLEAR', 'state': 'COMPLETED',
                                             'states': {'REQUESTED': second, 'COMPLETED': second + 0.1}})
        self.send(BA, '@BA: HU 2', 'x2')
        self.guard.event('handoff_confirmed', BA, event_id='x2', progress='none')
        rows = calibrate(self.rt, self.rt.state)['recovery_after_maintenance']
        self.assertEqual([(r['op_id'][:1], r['outcome']) for r in rows],
                         [('o', 'before_ledger'), ('a', 'no_task'), ('b', 'none')])

    def test_threshold_proposal_needs_enough_evidence(self):
        for number in range(30):
            self.send(SA, f'@SA: tarea {number}', f's{number}')
            if number < 6:
                for _ in range(3):
                    self.guard.event('no_progress', SA, reason='turn_without_block')
            self.guard.event('artifacts_changed', SA, paths=['p.md'])
        result = calibrate(self.rt, self.rt.state)
        self.assertEqual(result['by_provider']['fake']['turn_without_block_per_dispatch'], 0.6)
        self.assertEqual([(p['scope'], p['rule']) for p in result['proposals']], [('fake', 'no_progress')])
        self.assertIn('6/6', result['proposals'][0]['evidence'])
        # Only a proposal: the configuration and the mode are untouched.
        self.assertEqual((self.guard.mode, self.guard.settings['loop']['no_progress']['pause']), ('observe', 3))


# 5. Manual maintenance after an alert -----------------------------------------------------------------------------
class StatusAfterMaintenanceTests(MaintenanceCase):
    def test_clear_resets_session_work_but_not_the_alert(self):
        guard = self.rt.guard
        guard.clock = Steps()
        self.handoff(BA, '@BA:')
        self.rt.state.put('dispatch:e1', {'state': 'done', 'provider': 'fake-claude', 'attempt': 1})
        guard.on_dispatch(BA, '@BA: HU', 'e1')
        for _ in range(3):
            guard.event('no_progress', BA, reason='turn_without_block')
        guard.tick(force=True)
        before = {row['agent']: row for row in status(self.rt, self.rt.state)['agents']}[BA]
        self.assertEqual((before['since_last_maintenance']['tasks_dispatched'], before['eligibility']['proposed_action']),
                         (1, 'CLEAR'))
        op = self.maintenance().run('CLEAR', BA)
        self.assertEqual(op['state'], 'COMPLETED')
        after = {row['agent']: row for row in status(self.rt, self.rt.state)['agents']}[BA]
        self.assertEqual((after['session']['generation'], after['since_last_maintenance']['tasks_dispatched']), (2, 0))
        self.assertEqual(after['last_maintenance']['kind'], 'CLEAR')
        self.assertEqual([a['rule'] for a in after['alerts']], ['no_progress'])
        self.assertEqual(after['eligibility']['reasons'], ['session_already_fresh'])
        # Maintenance prompts once (/clear + verification); the diagnosis sends nothing.
        self.assertEqual([c[0] for c in self.calls('p-' + BA)], ['submit', 'prompt'])


# 6. Two workspaces ------------------------------------------------------------------------------------------------
def test_status_of_one_workspace_never_shows_another(engine):
    alpha, beta = new_project(engine, 'alpha'), new_project(engine, 'beta')
    gateway = Mock()
    gateway.list_agents.return_value = []
    runtimes = [Runtime(engine, context=context, gateway=gateway, runner=Mock()) for context in (alpha, beta)]
    try:
        for rt in runtimes:
            selection, _ = rt.factory.resolve(agent=BA)
            rt.state.put('agent:' + BA, {'provider': selection.provider, 'model': selection.model, 'pane_id': 'p1',
                                         'state': 'ready', 'run_id': 'r'})
        for _ in range(3):
            runtimes[0].guard.event('no_progress', BA, reason='turn_without_block')
        runtimes[0].guard.tick(force=True)
        a, b = (status(rt, rt.state) for rt in runtimes)
        assert [x['rule'] for x in a['agents'][0]['alerts']] == ['no_progress']
        assert b['agents'][0]['alerts'] == [] and b['project_id'] == 'beta'
        assert calibrate(runtimes[1], runtimes[1].state)['sample']['events'] == 0
    finally:
        for rt in runtimes:
            rt.close()


# 7. Context after the Phase 4C reduction -------------------------------------------------------------------------
# Characters of a task without its absolute roots. The task repeats the workspace root about 15 times, so the raw
# length depends on where the workspace lives; the budget applies to the rest. 4300 is slightly below what the former
# raw limit (6000) allowed at the harness location (about 6000 - 1660 path characters) and well below a task that
# embedded the global policy again (policy of about 5000 characters).
FUNCTIONAL_TASK_LIMIT = 4300


def functional_text(text, ctx):
    """Text with the variable absolute roots replaced by fixed markers; the rest is the functional content."""
    for root, marker in ((ctx.workspace_root, '<WORKSPACE_ROOT>'), (ctx.engine_root, '<ENGINE_ROOT>')):
        for form in (str(root), root.as_posix()):
            text = text.replace(form, marker)
    return text


def dispatched_task(engine):
    """(context, task file text) of a real-profile dispatch to BA in a new project of `engine`."""
    shutil.copyfile(REPO / 'constitution.md', engine / 'constitution.md')
    for name in AGENT_PHASES:
        shutil.copyfile(REPO / name / 'AGENTS.md', engine / name / 'AGENTS.md')
    ctx = new_project(engine)
    gateway = Mock()
    rt = Runtime(engine, context=ctx, gateway=gateway, runner=Mock())
    try:
        selection, _ = rt.factory.resolve(agent=BA)
        session = ctx.session_name(BA)
        rt.state.put('agent:' + BA, {'provider': selection.provider, 'model': selection.model, 'pane_id': 'p1',
                                     'state': 'ready', 'session_name': session})
        gateway.list_agents.return_value = [{'name': session, 'pane_id': 'p1', 'agent_status': 'idle'}]
        ready_pane(gateway, rt.factory.resolve(agent=BA)[1])
        assert rt.dispatcher.dispatch(BA, 'p1', '@BA: Redacta la HU 001.', 'ev-4d1')
        return ctx, ctx.output(rt.state.get('dispatch:ev-4d1')['task_file']).read_text(encoding='utf-8')
    finally:
        rt.close()


def test_real_profiles_keep_every_mandatory_instruction(engine):
    """Contracts built from the real role profiles and policy keep them verbatim; tasks keep their own rules."""
    ctx, task = dispatched_task(engine)
    policy = (REPO / 'constitution.md').read_text(encoding='utf-8-sig')
    for name in AGENT_PHASES:
        contract = agent_contract(ctx, name)
        profile = (REPO / name / 'AGENTS.md').read_text(encoding='utf-8-sig')
        for required in (profile, policy, TRACKER_RULE, EXECUTION_RULE, ctx.instructions()):
            assert required in contract, name
    for required in (ctx.instructions(), TRACKER_RULE, '@BA: Redacta la HU 001.', 'CONTRATO VIGENTE',
                     'POLÍTICA GLOBAL de tu contrato state/contracts/business-analyst.md'):
        assert required in task
    # The policy travels once, in the contract; the task stays small apart from its absolute roots.
    functional = functional_text(task, ctx)
    assert str(engine.parent) not in functional and engine.parent.as_posix() not in functional
    assert policy.splitlines()[0] not in task and len(functional) < FUNCTIONAL_TASK_LIMIT


def test_task_budget_ignores_workspace_path_length(engine, tmp_path):
    """Short and long workspace locations yield the same functional task; only the absolute roots differ."""
    # About 70 extra characters: enough to move the raw size by ~1000 while staying under Windows MAX_PATH, since the
    # isolated harness keeps its temporary directories.
    deep = tmp_path / ('ruta-larga-' * 6) / 'nivel'
    deep.mkdir(parents=True)
    long_engine = deep / engine.name
    shutil.copytree(engine, long_engine)
    short_ctx, short_task = dispatched_task(engine)
    long_ctx, long_task = dispatched_task(long_engine)
    extra = len(str(long_ctx.workspace_root)) - len(str(short_ctx.workspace_root))
    assert extra > 60
    # The raw size grows with the path (the reason a raw limit was fragile)...
    assert len(long_task) - len(short_task) > 10 * extra
    # ...while the functional content is identical and within budget.
    assert functional_text(long_task, long_ctx) == functional_text(short_task, short_ctx)
    assert len(functional_text(long_task, long_ctx)) < FUNCTIONAL_TASK_LIMIT


def test_functional_budget_still_catches_an_embedded_policy(engine):
    """The budget detects real growth: a task that carried the global policy again would exceed it."""
    ctx, task = dispatched_task(engine)
    policy = (REPO / 'constitution.md').read_text(encoding='utf-8-sig')
    assert len(functional_text(task + policy, ctx)) >= FUNCTIONAL_TASK_LIMIT
