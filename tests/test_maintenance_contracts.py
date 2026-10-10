"""Audit regressions: configuration and path boundaries; no external services."""
import json
import os

import pytest

from bmad_runtime.config import Selection
from bmad_runtime.context import resolve_context
from bmad_runtime.errors import ConfigurationError
from bmad_runtime.providers import ClaudeProvider, CodexProvider
from bmad_runtime import workspace


def test_profile_compilation_does_not_require_an_application(tmp_path, monkeypatch):
    from unittest.mock import Mock
    from bmad_runtime import workflow
    (tmp_path / 'config_bmad.json').write_text('{"projects":{}}')
    monkeypatch.setattr(workflow, 'ENGINE_ROOT', tmp_path)
    monkeypatch.setattr(workflow, '_runtime', None)
    compiler = Mock()
    monkeypatch.setattr(workflow, 'compilar_agentes_modulares', compiler)
    assert workflow.main(['--compile-profiles']) == 0
    compiler.assert_called_once_with()
    assert not (tmp_path / 'docs').exists()
    monkeypatch.setenv('BMAD_PROJECT', 'unselected')
    with pytest.raises(SystemExit):
        workflow.main(['--compile-profiles'])
    compiler.assert_called_once_with()


def test_backend_tasks_without_layout_are_not_skipped_by_technology(tmp_path, monkeypatch):
    from bmad_runtime import workflow
    feature = tmp_path / '.specify/feature.json'
    feature.parent.mkdir()
    feature.write_text('{"feature_directory":"specs/001"}')
    tasks = tmp_path / 'specs/001/tasks.md'
    tasks.parent.mkdir(parents=True)
    tasks.write_text('- [ ] T001 Implement server/main.py\n')
    monkeypatch.setattr(workflow, '_runtime', None)
    monkeypatch.setattr(workflow, 'ENGINE_ROOT', tmp_path)
    monkeypatch.setattr(workflow, 'DIRECTORIO_RAIZ', tmp_path)
    assert not workflow.backend_sin_tareas_pendientes()
    tasks.write_text('- [X] T001 Implement server/main.py\n')
    assert workflow.backend_sin_tareas_pendientes()


@pytest.mark.parametrize('action', ['init', 'migrate'])
def test_workspace_cli_materializes_selected_config(tmp_path, monkeypatch, action):
    engine = tmp_path / 'motor'
    engine.mkdir()
    (engine / 'config_bmad.json').write_text(json.dumps({'ai': {'defaults': {'provider': 'claude'}}}))
    selected = engine / 'selected.json'
    selected.write_text(json.dumps({'ai': {'defaults': {
        'provider': 'codex', 'model': 'gpt-6-astra', 'options': {'effort': 'high'}}}}))
    destination = tmp_path / 'Proyecto ñ'
    monkeypatch.setattr(workspace, 'ENGINE_ROOT', engine)
    monkeypatch.chdir(tmp_path)
    args = [action, '--workspace', str(destination), '--project', 'audit', '--config', 'selected.json']
    if action == 'migrate':
        args.append('--confirm')
    assert workspace.main(args) == 0
    actual = json.loads((destination / 'state/config_bmad.json').read_text(encoding='utf-8'))
    assert actual['ai']['defaults'] == {
        'provider': 'codex', 'model': 'gpt-6-astra', 'options': {'effort': 'high'}}


def test_missing_explicit_config_fails_before_bootstrap(tmp_path, monkeypatch):
    engine = tmp_path / 'motor'
    engine.mkdir()
    (engine / 'config_bmad.json').write_text('{}')
    monkeypatch.setattr(workspace, 'ENGINE_ROOT', engine)
    destination = tmp_path / 'project'
    assert workspace.main(['init', '--workspace', str(destination), '--project', 'audit',
                           '--config', 'missing.json']) == 1
    assert not destination.exists()


@pytest.mark.skipif(os.name != 'nt', reason='Windows case-insensitive directory contract')
def test_shared_engine_directory_rejected_with_different_casing(tmp_path):
    engine = tmp_path / 'motor'
    engine.mkdir()
    with pytest.raises(ConfigurationError, match='overlaps'):
        resolve_context(engine, workspace=engine / 'Docs/new', project='audit', initialize=True, environ={})


@pytest.mark.parametrize('provider,key', [
    (ClaudeProvider, 'effort'), (ClaudeProvider, 'permission_mode'), (CodexProvider, 'sandbox')])
@pytest.mark.parametrize('value', [[], {}, None, True, 3])
def test_invalid_native_option_is_a_configuration_error(provider, key, value):
    with pytest.raises(ConfigurationError):
        provider().validate(Selection(provider.identifier, options={key: value}))


@pytest.mark.parametrize('mode', ['interactive', 'headless'])
def test_direct_claude_commands_validate_options(tmp_path, mode):
    profile = tmp_path / 'AGENTS.md'
    profile.write_text('Role')
    provider = ClaudeProvider()
    selection = Selection('claude', options={'effort': 'ultra'})
    with pytest.raises(ConfigurationError):
        if mode == 'interactive':
            provider.interactive(selection, tmp_path, profile)
        else:
            provider.headless(selection, tmp_path, 'prompt', profile, {})


@pytest.mark.parametrize('output', ['absolute', 'docs/../app/file.md', '../other/file.md'])
def test_workflow_without_runtime_obeys_workspace_output_contract(tmp_path, monkeypatch, output):
    from bmad_runtime import workflow

    monkeypatch.setattr(workflow, '_runtime', None)
    monkeypatch.setattr(workflow, 'DIRECTORIO_RAIZ', tmp_path)
    monkeypatch.setattr(workflow, 'ENGINE_ROOT', tmp_path)
    assert workflow.project_output('docs/file.md') == tmp_path / 'docs/file.md'
    if output == 'absolute':
        output = str(tmp_path / 'docs/file.md')
    with pytest.raises(ConfigurationError):
        workflow.project_output(output)
