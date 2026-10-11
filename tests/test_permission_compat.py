"""Phase 3.6: least-privilege startup (H7), Codex sandbox shell on Windows (H8), tracker writes (H9)."""
import os
from unittest.mock import Mock

import pytest

from bmad_runtime.commands import Result
from bmad_runtime.config import Selection
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ReconciliationRequired
from bmad_runtime.herdr import HerdrGateway, pane_env_args, store_alias_last
from bmad_runtime.providers import default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import (TRACKER_RULE, agent_contract, contract_path, interactive_command,
                                   source_digests, write_contract)
from bmad_runtime.watcher_service import WatcherService
from test_multiworkspace import engine, new_project  # noqa: F401  (pytest fixture)

PROFILE_TEXT = 'Shared role: write legacy ../docs here.'


def policy(engine, text='# Política global\nAislamiento ante todo.\n'):
    (engine / 'constitution.md').write_text(text, encoding='utf-8')


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


# H7 ---------------------------------------------------------------------------------------------

def test_profiles_load_from_contract_in_separate_workspaces(engine):
    policy(engine)
    alpha, beta = new_project(engine, 'alpha'), new_project(engine, 'beta')
    for ctx, other in ((alpha, beta), (beta, alpha)):
        text = write_contract(ctx, 'business-analyst').read_text(encoding='utf-8')
        assert PROFILE_TEXT in text and 'Aislamiento ante todo.' in text
        assert f'WORKSPACE_ROOT={ctx.workspace_root}' in text
        assert str(other.workspace_root) not in text
        assert contract_path(ctx, 'business-analyst').is_relative_to(ctx.workspace_root)


@pytest.mark.parametrize('provider_id, phrase', [('claude', 'no releas'), ('codex', 'no leas')])
def test_startup_message_never_asks_to_read_engine_files(engine, provider_id, phrase):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, persist=False)
    provider = default_registry().create(provider_id, provider_id)
    command = interactive_command(rt.config, provider, Selection(provider_id), 'business-analyst')
    assert phrase in command.argv[-1]
    assert 'Lee el perfil compartido' not in ' '.join(command.argv)


def test_contract_regenerates_only_when_sources_change(engine):
    policy(engine)
    ctx = new_project(engine)
    path = write_contract(ctx, 'business-analyst')
    stamp = path.stat().st_mtime_ns
    before = source_digests(ctx, 'business-analyst')
    assert write_contract(ctx, 'business-analyst').stat().st_mtime_ns == stamp, 'unchanged sources: no rewrite'
    (engine / 'business-analyst' / 'AGENTS.md').write_text('Perfil enmendado v2', encoding='utf-8')
    policy(engine, '# Política global v2\n')
    text = write_contract(ctx, 'business-analyst').read_text(encoding='utf-8')
    after = source_digests(ctx, 'business-analyst')
    assert 'Perfil enmendado v2' in text and 'Política global v2' in text and PROFILE_TEXT not in text
    assert all(before[key] != after[key] for key in before)
    assert text.splitlines()[0].count(after['PERFIL DEL ROL']) == 1


def test_dispatch_refreshes_contract_and_references_current_sources(engine):
    policy(engine)
    ctx, rt, gateway = owned_runtime(engine)
    try:
        write_contract(ctx, 'business-analyst')
        (engine / 'business-analyst' / 'AGENTS.md').write_text('Perfil enmendado v3', encoding='utf-8')
        assert rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: tarea', 'ev1')
        assert 'Perfil enmendado v3' in contract_path(ctx, 'business-analyst').read_text(encoding='utf-8')
        task = ctx.output(rt.state.get('dispatch:ev1')['task_file']).read_text(encoding='utf-8')
        digest = source_digests(ctx, 'business-analyst')['PERFIL DEL ROL']
        assert 'CONTRATO VIGENTE: state/contracts/business-analyst.md' in task and digest in task
        assert task.endswith('@BA: tarea\n')
    finally:
        rt.close()


def test_global_and_local_constitutions_are_reachable(engine):
    ctx = new_project(engine)
    missing = agent_contract(ctx, 'business-analyst')
    assert 'POLÍTICA GLOBAL: no disponible' in missing, 'absent policy is explicit, never silent'
    policy(engine)
    text = agent_contract(ctx, 'business-analyst')
    assert 'Aislamiento ante todo.' in text
    assert '.specify/memory/constitution.md' in text   # local constitution stays inside the workspace


def test_legacy_contract_stays_in_legacy_state_dir(tmp_path):
    (tmp_path / 'business-analyst').mkdir()
    (tmp_path / 'business-analyst' / 'AGENTS.md').write_text(PROFILE_TEXT, encoding='utf-8')
    legacy = ProjectContext(tmp_path, tmp_path, 'legacy', True)
    path = write_contract(legacy, 'business-analyst')
    assert path == tmp_path / '.bmad-runtime' / 'contracts' / 'business-analyst.md'
    assert PROFILE_TEXT in path.read_text(encoding='utf-8')
    assert legacy.session_name('business-analyst') == 'business-analyst'


# H8 ---------------------------------------------------------------------------------------------

def test_store_aliases_resolve_after_real_executables():
    path = os.pathsep.join([r'C:\WINDOWS\system32', r'C:\Users\U\AppData\Local\Microsoft\WindowsApps',
                            r'C:\Program Files\PowerShell\7', 'C:\\Users\\U\\AppData\\Local\\Microsoft\\WindowsApps\\'])
    ordered = store_alias_last(path).split(os.pathsep)
    assert ordered[:2] == [r'C:\WINDOWS\system32', r'C:\Program Files\PowerShell\7']
    assert all('WindowsApps' in entry for entry in ordered[2:])
    assert sorted(ordered) == sorted(path.split(os.pathsep)), 'nothing added or removed'


def test_pane_env_only_on_windows_and_only_when_needed():
    environ = {'PATH': os.pathsep.join([r'C:\Users\U\AppData\Local\Microsoft\WindowsApps', r'C:\Program Files\PowerShell\7'])}
    assert pane_env_args(environ, platform='posix') == ()
    assert pane_env_args({'PATH': r'C:\Program Files\PowerShell\7'}, platform='nt') == ()
    flag, value = pane_env_args(environ, platform='nt')
    assert flag == '--env' and value.startswith('PATH=C:\\Program Files\\PowerShell\\7')


@pytest.mark.skipif(os.name != 'nt', reason='pane PATH ordering only applies to Windows hosts')
def test_tabs_and_splits_carry_pane_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('PATH', os.pathsep.join([r'C:\Users\U\AppData\Local\Microsoft\WindowsApps', r'C:\Tools']))
    runner = Mock()
    runner.run.return_value = Result(0, '{"result":{"tab":{"tab_id":"t"},"root_pane":{"pane_id":"p"},"pane":{"pane_id":"s"}}}')
    gateway = HerdrGateway(runner, tmp_path)
    gateway.create_tab('label', tmp_path)
    gateway.split('p', 'right', tmp_path)
    for call in runner.run.call_args_list:
        argv = call.args[0].argv
        assert argv[argv.index('--env') + 1] == 'PATH=' + os.pathsep.join([r'C:\Tools', r'C:\Users\U\AppData\Local\Microsoft\WindowsApps'])


@pytest.mark.parametrize('sandbox', ['workspace-write', 'read-only'])
def test_codex_sandbox_is_never_widened(engine, sandbox):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, persist=False)
    provider = default_registry().create('codex', 'codex')
    command = interactive_command(rt.config, provider, Selection('codex', 'gpt-6-astra', {'sandbox': sandbox}), 'business-analyst')
    assert command.argv[command.argv.index('--sandbox') + 1] == sandbox
    assert not any('danger' in arg or 'bypass' in arg for arg in command.argv)


# H9 ---------------------------------------------------------------------------------------------

def test_tracker_rule_in_contract_and_every_task(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        assert TRACKER_RULE in agent_contract(ctx, 'business-analyst')
        assert rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: registra', 'ev2')
        task = ctx.output(rt.state.get('dispatch:ev2')['task_file']).read_text(encoding='utf-8')
        assert TRACKER_RULE in task and 'nunca con comandos de shell' in task
    finally:
        rt.close()


def test_lost_update_by_whole_file_edit_is_detected_and_escalated(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        rt.config.data['tracker']['rewrite_grace_seconds'] = 0
        service = WatcherService(rt)
        tracker = ctx.tracker_path
        tracker.write_text('### [09-10-2026] PM\n- **Handoff:** @BA: uno\n', encoding='utf-8')
        lines = service.poll(0)
        service.save_cursor(lines, len(lines))
        # The agent read the tracker, then the watcher appended, then the agent's edit wrote its stale copy.
        with tracker.open('a', encoding='utf-8') as handle:
            handle.write('### [09-10-2026] WATCHER\n- **Mensaje:** aviso\n')
        lines = service.poll(len(lines))
        service.save_cursor(lines, len(lines))
        tracker.write_text('### [09-10-2026] PM\n- **Handoff:** @BA: uno\n### [09-10-2026] Business Analyst\n'
                           '- **Estado:** listo\n', encoding='utf-8')
        with pytest.raises(ReconciliationRequired):
            service.poll(len(lines))
        assert rt.state.get('tracker_integrity')['reason'] == 'rewritten'
    finally:
        rt.close()


# Recovery after permission dialogs ---------------------------------------------------------------

def test_blocked_agent_is_not_dispatched_and_recovers_when_idle(engine):
    ctx, rt, gateway = owned_runtime(engine)
    try:
        name = ctx.session_name('business-analyst')
        gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p1', 'agent_status': 'blocked'}]
        with pytest.raises(ReconciliationRequired):
            rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: tres', 'ev3')
        assert rt.state.get('dispatch:ev3') is None and not (ctx.handoffs_dir / 'tasks' / 'ev3-1.md').exists()
        gateway.list_agents.return_value = [{'name': name, 'pane_id': 'p1', 'agent_status': 'idle'}]
        assert rt.dispatcher.dispatch('business-analyst', 'p1', '@BA: tres', 'ev3')
        assert rt.state.get('dispatch:ev3')['state'] == 'done'
    finally:
        rt.close()
