"""H1-H5: real Herdr 0.8.2 integration contract on Windows, verified with doubles (no processes)."""
import hashlib
import json
import re
from unittest.mock import Mock

import pytest

from bmad_runtime.commands import Command, Result
from bmad_runtime.config import AGENT_PHASES, Selection
from bmad_runtime.context import ProjectContext, ROLE_ALIASES
from bmad_runtime.errors import ConfigurationError, DeliveryRejected, DeliveryUncertain, ReconciliationRequired
from bmad_runtime.fleet import FleetOrchestrator
from bmad_runtime.herdr import HerdrGateway
from bmad_runtime.providers import default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import agent_contract, contract_path, interactive_command, write_contract
from bmad_runtime.watcher_service import WatcherService
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)

HERDR_NAME = re.compile(r'[a-z][a-z0-9_-]{0,31}')
CLI_HELP = ('--model --effort --permission-mode --append-system-prompt --sandbox --cd --add-dir --config '
            '--ask-for-approval')


def configure(ctx, ai):
    identity = json.loads(ctx.output('project.json').read_text(encoding='utf-8'))
    identity['config'] = {'ai': ai}
    ctx.output('project.json').write_text(json.dumps(identity), encoding='utf-8')


def owned_runtime(engine, project='alpha'):
    ctx = new_project(engine, project)
    gateway = Mock()
    rt = Runtime(engine, context=ctx, gateway=gateway, runner=Mock())
    selection, _ = rt.factory.resolve(agent='business-analyst')
    name = ctx.session_name('business-analyst')
    rt.state.put('agent:business-analyst', {'provider': selection.provider, 'model': selection.model,
                                            'pane_id': 'p1', 'state': 'ready', 'session_name': name})
    gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p1', 'agent_status': 'idle'}]
    return ctx, rt, gateway


def herdr_error(code):
    return Result(1, '', json.dumps({'error': {'code': code, 'message': code}, 'id': 'cli:agent:prompt'}) + '\n')


# H1 ---------------------------------------------------------------------------------------------

def test_prompt_uses_wait_until_acceptance_and_timeout(tmp_path):
    runner = Mock()
    runner.run.return_value = Result(0, '{"id":"cli:agent:prompt","result":{"type":"agent_prompted"}}')
    HerdrGateway(runner, tmp_path).prompt('p1', 'hola')
    argv = runner.run.call_args.args[0].argv
    assert argv[:5] == ('herdr', 'agent', 'prompt', 'p1', 'hola')
    assert argv.index('--wait') < argv.index('--timeout')
    assert [argv[i + 1] for i, arg in enumerate(argv) if arg == '--until'] == ['working', 'idle', 'done', 'blocked']
    assert argv[argv.index('--timeout') + 1] == '30000'


@pytest.mark.parametrize('result', [herdr_error('agent_blocked'), herdr_error('agent_not_found'),
                                    herdr_error('agent_not_ready'), Result(127, error='cli_missing'),
                                    Result(2, '', 'error: --timeout requires --wait\n')])
def test_prompt_rejected_before_sending(tmp_path, result):
    runner = Mock()
    runner.run.return_value = result
    with pytest.raises(DeliveryRejected):
        HerdrGateway(runner, tmp_path).prompt('p1', 'hola')


@pytest.mark.parametrize('result', [herdr_error('agent_prompt_stalled'), herdr_error('timeout'),
                                    herdr_error('something_new'), Result(124, error='timeout'), Result(1, 'garbage')])
def test_prompt_uncertain_delivery(tmp_path, result):
    runner = Mock()
    runner.run.return_value = result
    with pytest.raises(DeliveryUncertain):
        HerdrGateway(runner, tmp_path).prompt('p1', 'hola')


# H2 ---------------------------------------------------------------------------------------------

def test_session_names_fit_herdr_and_never_collide(tmp_path):
    projects = ['alpha', 'a' * 64, '9-numerico', 'MAYUS_Y-guion', 'x']
    names = {}
    for index in range(400):
        project = projects[index % len(projects)]
        ctx = ProjectContext(tmp_path, tmp_path / f'Proyecto {index} ñ', project)
        for role in AGENT_PHASES:
            name = ctx.session_name(role)
            assert HERDR_NAME.fullmatch(name), name
            assert name == ctx.session_name(role)
            assert names.setdefault(name, (index, role)) == (index, role), f'collision: {name}'
    assert ProjectContext(tmp_path, tmp_path / 'w', 'alpha').session_name('business-analyst').startswith('alpha-')
    assert len(set(ROLE_ALIASES.values())) == len(AGENT_PHASES) == len(ROLE_ALIASES)


def test_legacy_names_and_unknown_roles(tmp_path):
    legacy = ProjectContext(tmp_path, tmp_path, 'legacy', True)
    assert legacy.session_name('business-storyteller') == 'business-storyteller'
    with pytest.raises(ConfigurationError):
        ProjectContext(tmp_path, tmp_path / 'w', 'alpha').session_name('Negocio y Producto')
    assert ProjectContext(tmp_path, tmp_path / 'w', 'alpha').tab_label('Negocio y Producto').endswith('Negocio y Producto')


# H3 ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize('provider_id', ['claude', 'codex'])
def test_contract_file_preserves_multiline_unicode_and_args_are_single_line(engine, provider_id):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, persist=False)
    provider = default_registry().create(provider_id, provider_id)
    command = interactive_command(rt.config, provider, Selection(provider_id), 'business-analyst')
    assert not contract_path(ctx, 'business-analyst').exists(), 'building a command must not write'
    path = write_contract(ctx, 'business-analyst')
    text = path.read_text(encoding='utf-8')
    assert text == agent_contract(ctx, 'business-analyst')
    assert '\n' in text and 'CONTRATO MULTIWORKSPACE' in text and 'ñ' in str(ctx.workspace_root)
    assert all('\n' not in arg and '\r' not in arg for arg in command.argv)
    assert path.as_posix() in ' '.join(arg.replace('\\', '/') for arg in command.argv)
    if provider_id == 'claude':
        assert command.argv[command.argv.index('--append-system-prompt-file') + 1] == str(path)
    herdr = HerdrGateway(Mock(), ctx.workspace_root).start_command(ctx.session_name('business-analyst'), 'p', provider, command)
    assert HERDR_NAME.fullmatch(herdr.argv[3])


def test_start_command_rejects_multiline_arguments(tmp_path):
    provider = default_registry().create('claude', 'claude')
    with pytest.raises(ConfigurationError):
        HerdrGateway(Mock(), tmp_path).start_command('alpha-ba', 'p', provider,
                                                     Command(('claude', '--append-system-prompt', 'a\nb'), tmp_path))


def test_fleet_launch_writes_contracts_before_start_for_both_providers(engine):
    ctx = new_project(engine)
    configure(ctx, {'agents': {'business-analyst': {'provider': 'claude'}}})
    gateway = Mock()
    gateway.list_agents.return_value = []
    gateway.create_tab.side_effect = [('t1', 'p1'), ('t2', 'p2'), ('t3', 'p3')]
    gateway.split.side_effect = [f's{i}' for i in range(10)]
    started = {}

    def start(name, pane, provider, native):
        role = next(role for role in AGENT_PHASES if ctx.session_name(role) == name)
        assert contract_path(ctx, role).is_file()
        HerdrGateway(Mock(), ctx.workspace_root).start_command(name, pane, provider, native)
        started[role] = provider.identifier

    gateway.start.side_effect = start
    runner = Mock()
    runner.run.return_value = Result(0, CLI_HELP)
    rt = Runtime(engine, context=ctx, gateway=gateway, runner=runner)
    try:
        assert FleetOrchestrator(rt).launch(verify=False) == 13
        assert started['business-analyst'] == 'claude' and started['solutions-architect'] == 'codex'
        record = rt.state.get('agent:business-analyst')
        assert record['session_name'] == ctx.session_name('business-analyst') and record['state'] == 'ready'
        labels = [call.args[0] for call in gateway.create_tab.call_args_list]
        assert labels[0] == ctx.tab_label('Negocio y Producto')
    finally:
        rt.close()


# H4 ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize('sandbox, add_dir', [('read-only', False), ('workspace-write', True)])
def test_codex_add_dir_only_with_writable_sandbox(engine, sandbox, add_dir):
    ctx = new_project(engine)
    configure(ctx, {'agents': {'business-analyst': {'provider': 'codex', 'model': 'gpt-6-astra',
                                                    'options': {'sandbox': sandbox, 'approval': 'on-request'}}}})
    rt = Runtime(engine, context=ctx, persist=False)
    selection, provider = rt.factory.resolve(agent='business-analyst')
    command = interactive_command(rt.config, provider, selection, 'business-analyst')
    assert ('--add-dir' in command.argv) is add_dir
    assert command.argv[command.argv.index('--sandbox') + 1] == sandbox
    assert command.argv[command.argv.index('--cd') + 1] == str(ctx.workspace_root)
    assert command.argv[command.argv.index('--ask-for-approval') + 1] == 'on-request'


# H5 ---------------------------------------------------------------------------------------------

def task_text(ctx, rt, event_id):
    record = rt.state.get('dispatch:' + event_id)
    content = ctx.output(record['task_file']).read_text(encoding='utf-8')
    assert hashlib.sha256(content.encode('utf-8')).hexdigest() == record['task_sha256']
    return content


@pytest.mark.parametrize('message', ['@BA: Redacta la HU 001.', '@BA: ' + ('línea larga ñ\n' * 1500)])
def test_short_and_long_handoffs_travel_as_task_files(engine, message):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        assert rt.dispatcher.dispatch('business-analyst', 'p1', message, 'e' * 64)
        prompt = gateway.prompt.call_args.args[1]
        content = task_text(ctx, rt, 'e' * 64)
        # Minimal terminal message: token, event and workspace-relative path only.
        assert '\n' not in prompt and len(prompt) < 120
        assert prompt == f'[BMAD {"e" * 12}] @BA: Lee y ejecuta íntegramente handoffs/tasks/{"e" * 24}-1.md'
        assert content.endswith(message + '\n') and 'CONTRATO MULTIWORKSPACE' in content
        assert 'event_id=' + 'e' * 64 in content.splitlines()[0]
        record = rt.state.get('dispatch:' + 'e' * 64)
        assert (record['state'], record['delivery']) == ('done', 'accepted')
    finally:
        rt.close()


def test_rejected_delivery_allows_explicit_new_attempt_without_overwrite(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        gateway.prompt.side_effect = DeliveryRejected('agent_blocked')
        with pytest.raises(DeliveryRejected):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: uno', 'ev1')
        first = ctx.handoffs_dir / 'tasks' / 'ev1-1.md'
        before = first.read_bytes()
        assert rt.state.get('dispatch:ev1')['state'] == 'not_delivered'
        gateway.prompt.side_effect = None
        assert rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: uno', 'ev1')
        record = rt.state.get('dispatch:ev1')
        assert (record['state'], record['attempt'], record['task_file']) == ('done', 2, 'handoffs/tasks/ev1-2.md')
        assert first.read_bytes() == before
    finally:
        rt.close()


def test_existing_task_file_is_never_overwritten(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        path = ctx.handoffs_dir / 'tasks' / 'ev2-1.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('otro contenido', encoding='utf-8')
        with pytest.raises(ReconciliationRequired):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: dos', 'ev2')
        assert path.read_text(encoding='utf-8') == 'otro contenido'
        assert rt.state.get('dispatch:ev2')['state'] == 'not_delivered'
        gateway.prompt.assert_not_called()
    finally:
        rt.close()


@pytest.mark.parametrize('failure', [DeliveryUncertain('agent_prompt_stalled'), KeyboardInterrupt()])
def test_uncertain_or_interrupted_delivery_is_never_retried(engine, failure):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        gateway.prompt.side_effect = failure
        with pytest.raises(type(failure)):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: tres', 'ev3')
        assert rt.state.get('dispatch:ev3')['state'] == 'uncertain'
    finally:
        rt.close()
    # Watcher restart: same event, new process; the uncertain delivery requires reconciliation.
    rt = Runtime(engine, context=ctx, gateway=gateway, runner=Mock())
    try:
        gateway.prompt.side_effect = None
        with pytest.raises(ReconciliationRequired):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: tres', 'ev3')
        gateway.prompt.assert_called_once()
        assert (ctx.handoffs_dir / 'tasks' / 'ev3-1.md').is_file()
    finally:
        rt.close()


def test_watcher_stages_for_rejected_and_uncertain_delivery(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        service = WatcherService(rt)
        line = '- **Handoff:** @BA: cuatro\n'
        task = service.enqueue(0, line, {'agente': 'business-analyst', 'mensaje': '@BA: cuatro'})
        gateway.prompt.side_effect = DeliveryRejected('agent_blocked')
        with pytest.raises(DeliveryRejected):
            rt.dispatcher.dispatch('business-analyst', 'p1', task['mensaje'], task['event_id'])
        service.failed(task, 'DeliveryRejected')
        assert rt.state.get('queued:' + task['event_id'])['stage'] == 'fallido'
        assert service.pending_tasks([line]) == [task]
        gateway.prompt.side_effect = DeliveryUncertain('stalled')
        with pytest.raises(DeliveryUncertain):
            rt.dispatcher.dispatch('business-analyst', 'p1', task['mensaje'], task['event_id'])
        service.failed(task, 'DeliveryUncertain')
        assert rt.state.get('queued:' + task['event_id'])['stage'] == 'requiere_intervencion'
        gateway.prompt.side_effect = None
        task2 = service.enqueue(1, line, {'agente': 'business-analyst', 'mensaje': '@BA: cuatro'})
        assert rt.dispatcher.dispatch('business-analyst', 'p1', task2['mensaje'], task2['event_id'])
        service.dispatched(task2)
        record = rt.state.get('queued:' + task2['event_id'])
        assert (record['stage'], record['delivery']) == ('despachado', 'accepted')
        assert record['task_file'].startswith('handoffs/tasks/')
    finally:
        rt.close()


def test_existing_sqlite_records_keep_their_meaning(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        # Records written before Phase 3.5: no task_file, no session_name.
        rt.state.put('dispatch:old-done', {'state': 'done', 'agent_id': 'business-analyst'})
        rt.state.put('dispatch:old-uncertain', {'state': 'uncertain', 'agent_id': 'business-analyst'})
        assert rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: x', 'old-done') is False
        with pytest.raises(ReconciliationRequired):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: x', 'old-uncertain')
        record = rt.state.get('agent:business-analyst')
        rt.state.put('agent:business-analyst', {key: value for key, value in record.items() if key != 'session_name'})
        assert rt.dispatcher.info('business-analyst') == ('p1', 'idle')
        gateway.prompt.assert_not_called()
    finally:
        rt.close()
