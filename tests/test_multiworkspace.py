"""Multiworkspace contract tests. All AI/Herdr operations are fakes or mocks."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import shutil
from unittest.mock import Mock, patch

import pytest

from bmad_runtime.cli import launcher_main, spec_plan
from bmad_runtime.commands import Command, Result
from bmad_runtime.config import AGENT_PHASES, RuntimeConfig
from bmad_runtime.context import resolve_context
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired
from bmad_runtime.fleet import FleetOrchestrator
from bmad_runtime.gitops import GitService
from bmad_runtime.herdr import HerdrGateway
from bmad_runtime.maintenance import close_owned_tabs
from bmad_runtime.providers import default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import interactive_command
from bmad_runtime.state import project_lock
from bmad_runtime.watcher_service import WatcherService
from bmad_runtime.workspace import bootstrap, migrate


@pytest.fixture
def engine(tmp_path):
    root = tmp_path / 'Motor compartido ñ'
    root.mkdir()
    (root / 'config_bmad.json').write_text(json.dumps({'project_type': 'fullstack', 'ai': {
        'defaults': {'provider': 'codex', 'model': 'gpt-6-astra', 'options': {'effort': 'low'}},
        'phases': {'D': {'options': {'effort': 'medium'}}}}}), encoding='utf-8')
    for name in AGENT_PHASES:
        folder = root / name
        folder.mkdir()
        (folder / 'AGENTS.md').write_text('Shared role: write legacy ../documents here.', encoding='utf-8')
    for folder in ('.github', '.agents', '.claude'):
        for operation in ('specify', 'clarify', 'plan', 'tasks', 'analyze', 'converge', 'implement'):
            skill = root / folder / 'skills' / f'speckit-{operation}'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text(f'---\nname: speckit-{operation}\n---\nInstructions', encoding='utf-8')
    return root


def new_project(engine, project='alpha'):
    return bootstrap(resolve_context(engine, workspace=engine.parent / f'Proyecto {project} ñ',
                                     project=project, initialize=True, environ={}))


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_bootstrap_idempotent_and_engine_unchanged(engine):
    original = snapshot(engine)
    ctx = new_project(engine)
    ctx.tracker_path.write_text('keep history', encoding='utf-8')
    ctx.output('app/main.py').write_text('user code', encoding='utf-8')
    before = snapshot(ctx.workspace_root)
    bootstrap(ctx)
    assert snapshot(ctx.workspace_root) == before
    assert snapshot(engine) == original
    assert not (ctx.workspace_root / '.git').exists()
    for folder in ('.agents', '.claude', 'business-analyst', 'utils', 'bmad_runtime'):
        assert not (ctx.workspace_root / folder).exists()


def test_selection_precedence_and_cwd_independence(engine, monkeypatch, tmp_path):
    ctx = new_project(engine)
    cfg = json.loads((engine / 'config_bmad.json').read_text())
    cfg['projects'] = {'alpha': '../Proyecto alpha ñ'}
    (engine / 'config_bmad.json').write_text(json.dumps(cfg), encoding='utf-8')
    monkeypatch.chdir(tmp_path.parent)
    assert resolve_context(engine, project='alpha', environ={}) == ctx
    assert resolve_context(engine, workspace='../Proyecto alpha ñ', environ={}) == ctx
    assert resolve_context(engine, workspace=ctx.workspace_root, project='alpha',
                           environ={'BMAD_WORKSPACE': '/absent', 'BMAD_PROJECT': 'other'}) == ctx
    with pytest.raises(ConfigurationError):
        resolve_context(engine, project='missing', environ={})
    with pytest.raises(ConfigurationError):
        resolve_context(engine, workspace=ctx.workspace_root, project='wrong', environ={})
    with pytest.raises(ConfigurationError):
        resolve_context(engine, workspace=tmp_path / 'absent', project='x', environ={})


def test_project_config_merges_without_mutating_global(engine):
    ctx = new_project(engine)
    before = (engine / 'config_bmad.json').read_bytes()
    ctx.output('project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alpha', 'config': {
        'project_type': 'headless', 'ai': {'defaults': {'options': {'effort': 'high'}},
        'agents': {'business-analyst': {'provider': 'claude', 'options': {'effort': 'medium'}}},
        'speckit': {'implement': {'options': {'effort': 'xhigh'}}}}}}), encoding='utf-8')
    rt = Runtime(engine, context=ctx, persist=False)
    assert rt.config.resolve(operation='implement').options == {'effort': 'xhigh'}
    assert rt.config.resolve(agent='business-storyteller').options == {'effort': 'high'}
    assert rt.config.resolve(agent='business-analyst').model is None
    assert not any(r['name'] == 'designer-ux' for r in FleetOrchestrator(rt).plan())
    assert (engine / 'config_bmad.json').read_bytes() == before


@pytest.mark.parametrize('value', ['../escape', 'app/../../engine', 'C:\\escape', 'C:escape', '\\\\host\\share\\x'])
def test_traversal_rejected(engine, value):
    ctx = new_project(engine)
    with pytest.raises(ConfigurationError):
        ctx.output(value)


@pytest.mark.parametrize('identity', ['../bad', 'bad name', 'NUL', '', 'a' * 65])
def test_invalid_identity(engine, identity):
    with pytest.raises(ConfigurationError):
        resolve_context(engine, workspace=engine.parent / 'new', project=identity, initialize=True, environ={})


def test_engine_overlap_rejected(engine):
    for path in (engine, engine.parent, engine / 'documents/new', engine / 'business-analyst/new'):
        with pytest.raises(ConfigurationError):
            resolve_context(engine, workspace=path, project='alpha', initialize=True, environ={})


@pytest.mark.parametrize('config', [{'tracker': '../other'}, {'ai': {'providers': {}}},
                                   {'code_dirs': {'backend': '../escape'}}, {'code_dirs': {'frontend': 'documents/code'}}])
def test_disallowed_overrides(engine, config):
    ctx = new_project(engine)
    ctx.output('project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alpha', 'config': config}))
    with pytest.raises(ConfigurationError):
        Runtime(engine, context=ctx, persist=False)


def test_dry_run_no_process_no_writes(engine, capsys):
    ctx = new_project(engine)
    before = snapshot(ctx.workspace_root)
    with patch('subprocess.Popen', side_effect=AssertionError('No processes allowed')):
        assert launcher_main(engine, ['--workspace', str(ctx.workspace_root), '--dry-run']) == 0
        spec_rows = spec_plan(engine, context=ctx)
    rows = json.loads(capsys.readouterr().out)
    assert all(row['cwd'] == str(ctx.workspace_root) for row in rows + spec_rows)
    assert all(row['session_name'].startswith('alpha-') for row in rows)
    assert snapshot(ctx.workspace_root) == before


@pytest.mark.parametrize('provider_id', ['claude', 'codex'])
def test_shared_profiles_workspace_cwd_and_explicit_context(engine, provider_id):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, persist=False)
    from bmad_runtime.config import Selection
    provider = default_registry().create(provider_id, provider_id)
    cmd = interactive_command(rt.config, provider, Selection(provider_id), 'business-analyst')
    assert cmd.cwd == ctx.workspace_root
    assert str(ctx.engine_root / 'business-analyst/AGENTS.md').replace('\\', '/') in ' '.join(cmd.argv)
    assert str(ctx.tracker_path) in ' '.join(cmd.argv)
    assert cmd.env['PROJECT_ID'] == 'alpha'
    herdr = HerdrGateway(Mock(), ctx.workspace_root).start_command(ctx.session_name('business-analyst'), 'pane', provider, cmd)
    assert herdr.cwd == ctx.workspace_root and herdr.env == cmd.env
    assert 'CONTRATO MULTIWORKSPACE' not in ' '.join(herdr.sanitized())
    _, _, spec = rt.spec.prepare('implement', 'work')
    assert spec.env['SPECIFY_INIT_DIR'] == str(ctx.workspace_root)
    assert str(ctx.tracker_path) in spec.stdin
    assert 'speckit-implement/SKILL.md' in spec.stdin


def test_persisted_feature_and_env_traversal_rejected(engine):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, persist=False)
    with pytest.raises(ConfigurationError):
        rt.spec.prepare('implement', env={'SPECIFY_FEATURE_DIRECTORY': '../escape'})
    with pytest.raises(ConfigurationError):
        rt.spec.prepare('implement', env={'WORKSPACE_ROOT': 'wrong'})
    ctx.output('.specify/feature.json').write_text('{"feature_directory":"../escape"}')
    with pytest.raises(ConfigurationError):
        rt.spec.prepare('implement')


def test_parallel_ab_artifacts_watchers_locks_and_dedupe(engine):
    a, b = new_project(engine, 'alpha'), new_project(engine, 'beta')
    before = snapshot(engine)
    def simulate(ctx):
        rt = Runtime(engine, context=ctx)
        try:
            with project_lock(ctx, 'watcher'):
                with pytest.raises(ReconciliationRequired):
                    with project_lock(ctx, 'watcher'):
                        pass
                service = WatcherService(rt)
                if ctx.project_id == 'alpha':
                    ctx.tracker_path.write_text('- **Handoff:** @BA: alpha only\n', encoding='utf-8')
                    ctx.output('documents/result.md').write_text('alpha', encoding='utf-8')
                    ctx.output('app/main.py').write_text('alpha', encoding='utf-8')
                lines = service.read_lines()
                for n, line in enumerate(lines):
                    key, claimed = service.begin_line(n, line)
                    assert claimed
                    service.complete_line(key)
                    assert not service.begin_line(n, line)[1]
                service.save_cursor(lines, len(lines))
                return len(lines)
        finally:
            rt.close()
    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(simulate, (a, b))) == [1, 0]
    assert not b.output('documents/result.md').exists()
    assert not b.output('app/main.py').exists()
    assert a.state_dir != b.state_dir
    assert a.session_name('business-analyst') != b.session_name('business-analyst')
    assert snapshot(engine) == before


def test_same_id_distinct_workspaces_have_unique_sessions(engine):
    a = new_project(engine)
    b = bootstrap(resolve_context(engine, workspace=engine.parent / 'other', project='alpha', initialize=True, environ={}))
    assert a.session_name('business-analyst') != b.session_name('business-analyst')


def test_mock_fleet_ownership_and_stop_only_active_project(engine):
    a, b = new_project(engine, 'alpha'), new_project(engine, 'beta')
    gateway = Mock()
    gateway.list_agents.return_value = [{'name': b.session_name('business-analyst'), 'pane_id': 'foreign'}]
    gateway.create_tab.side_effect = [('t1', 'p1'), ('t2', 'p2'), ('t3', 'p3')]
    gateway.split.side_effect = [f's{i}' for i in range(10)]
    runner = Mock()
    runner.run.return_value = Result(0, '--model --sandbox --cd --add-dir --config --ask-for-approval')
    rt = Runtime(engine, context=a, gateway=gateway, runner=runner)
    try:
        assert FleetOrchestrator(rt).launch() == 13
        for call in gateway.start.call_args_list:
            assert call.args[0].startswith('alpha-')
            assert call.args[3].cwd == a.workspace_root
        owned = rt.state.get('agent:business-analyst')
        gateway.list_agents.return_value = [{'name': a.session_name('business-analyst'), 'pane_id': owned['pane_id'], 'agent_status': 'idle'}]
        assert rt.dispatcher.info('business-analyst')[0] == owned['pane_id']
        assert rt.dispatcher.dispatch('business-analyst', owned['pane_id'], 'write', 'one')
        assert str(a.tracker_path) in gateway.prompt.call_args.args[1]
        gateway.list_tabs.return_value = [{'tab_id': owned['tab_id']}, {'tab_id': 'foreign-tab'}]
        gateway.list_panes.return_value = [{'pane_id': owned['pane_id'], 'tab_id': owned['tab_id']}]
        assert close_owned_tabs(rt) == 1
        gateway.close_tab.assert_called_once_with(owned['tab_id'])
    finally:
        rt.close()


def test_git_refuses_parent_repository(engine):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, runner=Mock(), persist=False)
    with pytest.raises(ReconciliationRequired):
        GitService(rt).run(['git', 'status'])
    rt.runner.run.assert_not_called()


def test_same_project_speckit_conflict_starts_no_process(engine):
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx, runner=Mock())
    try:
        with project_lock(ctx, 'speckit'):
            with pytest.raises(ReconciliationRequired):
                rt.spec.execute('implement')
        rt.runner.run.assert_not_called()
    finally:
        rt.close()


def test_migration_dry_run_and_exclusive_copy(engine):
    (engine / 'documents').mkdir()
    (engine / 'documents/tracker_bmad.md').write_text('history', encoding='utf-8')
    (engine / 'utils').mkdir()
    (engine / 'utils/handoff_qa.md').write_text('handoff', encoding='utf-8')
    (engine / 'utils/tool.py').write_text('shared', encoding='utf-8')
    ctx = resolve_context(engine, workspace=engine.parent / 'Migración ñ', project='migration', initialize=True, environ={})
    before = snapshot(engine)
    rows = migrate(ctx)
    assert len(rows) == 2 and not ctx.workspace_root.exists()
    migrate(ctx, confirm=True)
    assert ctx.tracker_path.read_text() == 'history'
    assert ctx.output('handoffs/handoff_qa.md').read_text() == 'handoff'
    assert not ctx.output('handoffs/tool.py').exists()
    assert snapshot(engine) == before
    with pytest.raises(ConfigurationError):
        migrate(ctx, confirm=True)
    assert ctx.tracker_path.read_text() == 'history'


def test_legacy_warning_preserves_paths(engine):
    with pytest.warns(FutureWarning, match='legacy'):
        ctx = resolve_context(engine, environ={})
    assert ctx.tracker_path == engine / 'documents/tracker_bmad.md'
    assert ctx.state_dir == engine / '.bmad-runtime'
    assert ctx.session_name('business-analyst') == 'business-analyst'


def test_effective_config_for_shared_roles_uses_workspace_outputs(engine):
    ctx = new_project(engine)
    identity = ctx.output('project.json').read_bytes()
    rt = Runtime(engine, context=ctx)
    try:
        view = json.loads(Path(ctx.environment()['BMAD_CONFIG']).read_text(encoding='utf-8'))
        assert view['tracker'] == str(ctx.tracker_path)
        assert view['context'] == str(ctx.output('.specify/memory/constitution.md'))
        assert view['routes_bmad']['business-analyst'] == str(ctx.output('documents/business-analyst'))
        assert ctx.output('project.json').read_bytes() == identity
    finally:
        rt.close()


def test_output_symlink_escape(engine, tmp_path):
    ctx = new_project(engine)
    outside = tmp_path / 'outside'
    outside.mkdir()
    try:
        ctx.output('app/escape').symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Host does not permit creating symlinks; no privilege changes requested')
    with pytest.raises(ConfigurationError):
        ctx.output('app/escape/code.py')


def test_real_powershell_speckit_scripts_ab_without_agents_or_git(tmp_path):
    shell = shutil.which('pwsh')
    if not shell:
        pytest.skip('PowerShell unavailable')
    engine = Path(__file__).resolve().parents[1]
    a = bootstrap(resolve_context(engine, workspace=tmp_path / 'A ñ espacios', project='a', initialize=True, environ={}))
    b = bootstrap(resolve_context(engine, workspace=tmp_path / 'B ñ espacios', project='b', initialize=True, environ={}))
    def run_script(ctx, script, *args, extra=None):
        env = {**os.environ, **ctx.environment()}
        env.pop('SPECIFY_FEATURE_DIRECTORY', None)
        env.pop('SPECIFY_FEATURE', None)
        env.update(extra or {})
        return subprocess.run([shell, '-NoProfile', '-File', str(ctx.specify_dir / 'scripts/powershell' / script), *args],
                              cwd=engine, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    before_b = snapshot(b.workspace_root)
    result = run_script(a, 'create-new-feature.ps1', '-Json', '-ShortName', 'isolated', 'Isolated feature')
    assert result.returncode == 0, result.stderr
    feature = json.loads(a.output('.specify/feature.json').read_text(encoding='utf-8'))['feature_directory']
    assert a.output(feature).is_relative_to(a.specs_dir)
    result = run_script(a, 'setup-plan.ps1', '-Json')
    assert result.returncode == 0, result.stderr
    assert a.output(feature + '/plan.md').exists()
    assert snapshot(b.workspace_root) == before_b
    assert not a.output('.git').exists()
    before_feature = a.output('.specify/feature.json').read_bytes()
    result = run_script(a, 'setup-plan.ps1', '-Json', extra={'SPECIFY_FEATURE_DIRECTORY': '../outside'})
    assert result.returncode != 0
    assert a.output('.specify/feature.json').read_bytes() == before_feature


def test_workflow_uses_selected_tracker_and_config(engine, monkeypatch):
    from bmad_runtime import workflow
    ctx = new_project(engine)
    rt = Runtime(engine, context=ctx)
    for name in ('_runtime', 'ENGINE_ROOT', 'SKILLS_DIR', 'DIRECTORIO_RAIZ', 'TRACKER_PATH', 'RETRABAJO_STATE_PATH', 'RETRABAJO_CLASIFICACION_PATH'):
        monkeypatch.setattr(workflow, name, getattr(workflow, name))
    try:
        workflow.configure_project(rt)
        workflow.write_watcher_log('only alpha')
        assert 'only alpha' in ctx.tracker_path.read_text(encoding='utf-8')
        assert workflow.SKILLS_DIR == ctx.engine_root / 'skills'
        assert workflow.project_settings()['project_name'] == 'alpha'
        assert str(ctx.tracker_path) in workflow.texto_recordatorio('business-analyst')
        assert not (engine / 'documents/tracker_bmad.md').exists()
    finally:
        rt.close()
