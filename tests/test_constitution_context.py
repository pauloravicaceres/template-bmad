"""Context isolation: all provider commands are prepared, never run."""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from bmad_runtime.config import AGENT_PHASES
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ConfigurationError
from bmad_runtime.runtime import Runtime
from bmad_runtime.services import interactive_command
from bmad_runtime.technical_context import assemble, discover, document_index, MAX_PROMPT
from test_multiworkspace import engine, new_project

ROOT = Path(__file__).resolve().parents[1]


def write(ctx, relative, text):
    path = ctx.output(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def stack(ctx, frontend, backend):
    write(ctx, 'web/package.json', json.dumps({'dependencies': {frontend: '1.2.3'}}))
    if backend == 'Python':
        write(ctx, 'server/pyproject.toml', '[project]\nrequires-python = ">=3.12"\ndependencies = ["fastapi==0.115"]')
    else:
        write(ctx, 'server/Api.csproj', '<Project><PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
    write(ctx, '.specify/memory/constitution.md', f'# Proyecto {ctx.project_id}\nDecisión aprobada: {frontend} / {backend}.\n')


def test_incompatible_workspaces_and_all_roles(engine):
    (engine / 'constitution.md').write_text('# Operación global\nRespetar aislamiento y GitOps.', encoding='utf-8')
    a, b = new_project(engine, 'a'), new_project(engine, 'b')
    stack(a, '@angular/core', '.NET')
    stack(b, 'react', 'Python')
    write(a, 'documents/architecture/frontend.md', 'Angular-only rules')
    for role in AGENT_PHASES:
        pa, pb = assemble(a, role=role), assemble(b, role=role)
        assert 'Operación global' in pa and 'Operación global' in pb
        assert '@angular/core' in pa and 'Python' not in pa
        assert 'Python' in pb and '@angular/core' not in pb
        assert str(a.workspace_root) not in pb
        assert len(pa) < MAX_PROMPT
    assert 'documents/architecture/frontend.md' not in document_index(a, role='product-manager')
    assert 'documents/architecture/frontend.md' in document_index(a, role='dev-frontend')


def test_brownfield_without_docs_observations_not_approval(engine):
    ctx = new_project(engine)
    write(ctx, 'server/requirements.txt', 'fastapi==0.115\n--index-url https://user:secret@example.invalid\n')
    write(ctx, 'web/package.json', '{"dependencies":{"react":"19.0.0","private":"https://user:secret@host"}}')
    write(ctx, '.env', 'SECRET=do-not-read')
    write(ctx, 'secrets/package.json', '{"dependencies":{"leaked":"SECRET"}}')
    snapshot = discover(ctx)
    assert snapshot['mode'] == 'brownfield'
    assert all(row['status'] == 'observado' for row in snapshot['observations'])
    assert snapshot['differences']
    assert 'fastapi' in str(snapshot) and 'react' in str(snapshot)
    assert 'secret@' not in str(snapshot) and 'leaked' not in str(snapshot)
    assert 'do-not-read' not in assemble(ctx, role='solutions-architect')


def test_greenfield_neutral_and_existing_approved_constraints(engine):
    ctx = new_project(engine)
    prompt = assemble(ctx, operation='plan')
    assert 'greenfield' in prompt and 'pendiente' in prompt
    assert all(value not in prompt for value in ('Angular', '.NET', 'PostgreSQL'))
    write(ctx, '.specify/memory/constitution.md', '# Stack aprobado\nGo con almacenamiento en archivos.\n')
    assert 'Go con almacenamiento' in assemble(ctx, role='dev-backend')
    assert discover(ctx)['mode'] == 'greenfield'


@pytest.mark.parametrize('provider', ['claude', 'codex'])
def test_real_preparation_and_effort_are_provider_independent(engine, provider):
    ctx = new_project(engine, provider)
    stack(ctx, 'react', 'Python')
    identity = json.loads(ctx.output('project.json').read_text())
    identity['config'] = {'ai': {'defaults': {'provider': provider, 'options': {'effort': 'high'}},
                               'phases': {'D': {'options': {'effort': 'high'}}}}}
    write(ctx, 'project.json', json.dumps(identity))
    rt = Runtime(engine, context=ctx, persist=False, runner=Mock())
    selection, adapter = rt.factory.resolve(agent='dev-backend')
    command = interactive_command(rt.config, adapter, selection, 'dev-backend')
    assert command.cwd == ctx.workspace_root
    assert 'CONTEXTO BMAD' in ' '.join(command.argv)
    assert '.specify/memory/constitution.md' in ' '.join(command.argv)
    assert selection.options['effort'] == 'high'
    _, _, spec = rt.spec.prepare('implement', 'tarea específica')
    assert 'Python' in spec.stdin and 'tarea específica' in spec.stdin
    assert spec.env['BMAD_TRACKER'] == str(ctx.tracker_path)
    rt.runner.run.assert_not_called()


def test_dispatch_refreshes_decisions_and_stays_local(engine):
    ctx = new_project(engine)
    stack(ctx, 'react', 'Python')
    gateway = Mock()
    rt = Runtime(engine, context=ctx, gateway=gateway)
    try:
        rt.state.put('agent:dev-backend', {'provider': 'codex', 'model': 'gpt-6-astra',
                                          'pane_id': 'p', 'state': 'ready'})
        gateway.list_agents.return_value = [{'name': ctx.session_name('dev-backend'), 'pane_id': 'p', 'agent_status': 'idle'}]
        assert rt.dispatcher.dispatch('dev-backend', 'p', 'implementar HU', 'first')
        prompt = gateway.prompt.call_args.args[1]
        assert 'Python' in prompt and prompt.endswith('implementar HU')
        write(ctx, '.specify/memory/constitution.md', '# Enmienda aprobada local\nNuevo requisito técnico.\n')
        rt.dispatcher.dispatch('dev-backend', 'p', 'revisar HU', 'second')
        assert 'Nuevo requisito técnico' in gateway.prompt.call_args.args[1]
    finally:
        rt.close()


def test_no_engine_memory_fallback_or_duplicate_documents(engine):
    write(ProjectContext(engine, engine, 'legacy', True), '.specify/memory/constitution.md', '# Foreign Angular stack')
    ctx = new_project(engine)
    ctx.output('.specify/memory/constitution.md').unlink()
    assert 'Foreign' not in assemble(ctx, role='solutions-architect')
    write(ctx, 'documents/architecture/architecture.md', 'a' * 60_000)
    prompt = assemble(ctx, role='solutions-architect')
    assert prompt.count('DOCUMENTO LOCAL: ' + ctx.output('documents/architecture/architecture.md').as_posix()) == 1
    assert 'a' * 100 not in prompt
    assert len(prompt) < MAX_PROMPT


def test_global_policy_and_shared_profiles_are_technology_neutral():
    policy = (ROOT / 'constitution.md').read_text(encoding='utf-8')
    forbidden = ('Angular', 'PrimeNG', 'PostgreSQL', 'Carter', 'HU-035', 'HU-036', 'app/backend', 'app/frontend')
    assert all(word not in policy for word in forbidden)
    for role in ('dev-backend', 'dev-frontend', 'qa-auto', 'code-review', 'devops'):
        profile = (ROOT / role / 'AGENTS.md').read_text(encoding='utf-8')
        assert all(word not in profile for word in forbidden[:4])


def test_clean_engine_requires_selection_and_bootstraps_neutral_projects(tmp_path):
    from bmad_runtime.context import resolve_context
    from bmad_runtime.workspace import bootstrap
    config = json.loads((ROOT / 'config_bmad.json').read_text(encoding='utf-8'))
    assert config['projects'] == {}
    assert not {'project_name', 'project_type', 'context', 'tracker', 'routes_bmad', 'created_at'} & config.keys()
    with pytest.raises(ConfigurationError, match='Select a workspace'):
        resolve_context(ROOT, environ={})
    a = bootstrap(resolve_context(ROOT, workspace=tmp_path / 'new', project='new', initialize=True, environ={}))
    assert a.tracker_path.read_text(encoding='utf-8') == ''
    assert not a.output('.specify/feature.json').exists()
    assert not a.output('.specify/memory/rework_state.json').exists()
    assert not a.output('state/state.sqlite3').exists()
    assert discover(a)['mode'] == 'greenfield'
    assert 'Estado: pendiente' in a.output('.specify/memory/constitution.md').read_text(encoding='utf-8')
    assert not list(a.output('app').iterdir())


def test_brownfield_layout_override_outside_app(engine):
    ctx = new_project(engine)
    identity = json.loads(ctx.output('project.json').read_text())
    identity['config'] = {'code_dirs': {'backend': 'server', 'frontend': 'web'}}
    write(ctx, 'project.json', json.dumps(identity))
    rt = Runtime(engine, context=ctx, persist=False)
    assert rt.config.raw['code_dirs'] == {'backend': 'server', 'frontend': 'web'}


def test_brownfield_readme_uses_discovered_source_roots(engine, monkeypatch):
    from bmad_runtime import workflow
    ctx = new_project(engine)
    stack(ctx, 'react', 'Python')
    rt = Runtime(engine, context=ctx, persist=False)
    monkeypatch.setattr(workflow, '_runtime', rt)
    monkeypatch.setattr(workflow, 'DIRECTORIO_RAIZ', ctx.workspace_root)
    assert workflow.ruta_readme_codigo('backend') == 'server/README.md'
    assert workflow.ruta_readme_codigo('frontend') == 'web/README.md'


def test_watcher_does_not_append_global_policy(engine, monkeypatch):
    from bmad_runtime import workflow
    ctx = new_project(engine)
    write(ctx, '.specify/memory/constitution.md', '# Decisión aprobada\nStack propio\n')
    monkeypatch.setattr(workflow, '_runtime', Mock(context=ctx))
    before = ctx.output('.specify/memory/constitution.md').read_bytes()
    workflow.validar_constitucion_gitops()
    assert ctx.output('.specify/memory/constitution.md').read_bytes() == before


def test_lockfile_versions_and_ci_are_observed_without_scripts(engine):
    ctx = new_project(engine)
    write(ctx, 'package.json', '{"dependencies":{"react":"^19.0.0"},"scripts":{"install":"NEVER_RUN"}}')
    write(ctx, 'package-lock.json', '{"packages":{"node_modules/react":{"version":"19.1.0"},"node_modules/transitive":{"version":"2.0"}}}')
    write(ctx, '.github/workflows/ci.yml', 'secret: NEVER_READ\n')
    data = discover(ctx)
    assert any(o['technology'] == 'react' and o['version'] == '19.1.0' for o in data['observations'])
    assert '.github/workflows/ci.yml' in data['evidence']
    assert 'NEVER' not in str(data) and 'transitive' not in str(data)


def test_context_record_never_overwrites_approved_inventory(engine, monkeypatch, capsys):
    from bmad_runtime import workspace
    ctx = new_project(engine)
    monkeypatch.setattr(workspace, 'ENGINE_ROOT', engine)
    write(ctx, 'documents/architecture/tech-stack.md', 'Aprobado: decisión humana')
    write(ctx, 'requirements.txt', 'fastapi==0.115\n')
    assert workspace.main(['context', '--workspace', str(ctx.workspace_root), '--record']) == 0
    capsys.readouterr()
    assert ctx.output('documents/architecture/tech-stack.md').read_text(encoding='utf-8') == 'Aprobado: decisión humana'
    recorded = json.loads(ctx.output('documents/architecture/stack-observations.json').read_text(encoding='utf-8'))
    assert recorded['differences'] and recorded['mode'] == 'brownfield'


def test_nested_workspaces_and_links_are_not_scanned(engine):
    ctx = new_project(engine)
    write(ctx, 'nested/project.json', '{"project_id":"foreign"}')
    write(ctx, 'nested/package.json', '{"dependencies":{"FOREIGN":"1.0"}}')
    assert 'FOREIGN' not in str(discover(ctx))
    other = new_project(engine, 'other')
    write(other, 'package.json', '{"dependencies":{"ESCAPED":"1.0"}}')
    try:
        ctx.output('linked').symlink_to(other.workspace_root, target_is_directory=True)
    except OSError:
        pytest.skip('Symlink creation unavailable on this host')
    assert 'ESCAPED' not in str(discover(ctx))
