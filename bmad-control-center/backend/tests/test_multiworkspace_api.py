import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bmad_runtime.context import resolve_context
from bmad_runtime.workspace import bootstrap
from core.config import load_settings, settings
from services.tracker_service import TrackerService
from services.file_watcher import MultiDirectoryWatcherHandler
from api.routes import get_project, get_project_context


def test_empty_dashboard_is_read_only_and_has_no_watcher(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from main import app, file_watcher
    import core.config as config
    (tmp_path / 'config_bmad.json').write_text('{"projects":{}}', encoding='utf-8')
    monkeypatch.setattr(config, 'ENGINE_ROOT', tmp_path)
    monkeypatch.delenv('BMAD_WORKSPACE', raising=False)
    monkeypatch.delenv('BMAD_PROJECT', raising=False)
    empty = load_settings()
    assert not empty.HAS_PROJECT and empty.ALLOWED_ROOTS == []
    monkeypatch.setattr(settings, 'HAS_PROJECT', False)
    with TestClient(app) as client:
        assert client.get('/api/v1/project').json()['project_id'] is None
        assert client.get('/api/v1/projects').json() == {'projects': []}
        for path in ('/project/context', '/workflow/status', '/artifacts/tree', '/git/status'):
            assert client.get('/api/v1' + path).status_code == 409
        assert client.post('/api/v1/gates/1/decision', json={'action': 'APPROVE'}).status_code == 409
    file_watcher.start.assert_not_called()
    file_watcher.stop.assert_not_called()


def test_registry_displays_new_projects_without_switching_workspace(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from main import app
    import core.config as config
    registry_engine = tmp_path / 'registry'
    registry_engine.mkdir()
    configuration = registry_engine / 'config_bmad.json'
    configuration.write_text('{"projects":{}}', encoding='utf-8')
    ctx = bootstrap(resolve_context(registry_engine, workspace=tmp_path / 'new-project',
                                    project='new-project', initialize=True, environ={}))
    monkeypatch.setattr(config, 'ENGINE_ROOT', registry_engine)
    monkeypatch.setattr(settings, 'HAS_PROJECT', False)
    client = TestClient(app)
    assert client.get('/api/v1/projects').json()['projects'] == []
    configuration.write_text(json.dumps({'projects': {'new-project': str(ctx.workspace_root)}}), encoding='utf-8')
    assert client.get('/api/v1/projects').json()['projects'] == [{
        'project_id': 'new-project', 'workspace_root': str(ctx.workspace_root), 'selected': False}]
    assert client.get('/api/v1/project').json()['project_id'] is None
    monkeypatch.setenv('BMAD_PROJECT', 'new-project')
    monkeypatch.delenv('BMAD_WORKSPACE', raising=False)
    bound = load_settings()
    assert bound.HAS_PROJECT and bound.WORKSPACE_ROOT == ctx.workspace_root
    assert bound.TRACKER_FILE == ctx.tracker_path


def test_settings_bind_project_identity_tracker_and_perimeter(tmp_path, monkeypatch):
    engine = Path(__file__).resolve().parents[3]
    a = bootstrap(resolve_context(engine, workspace=tmp_path / 'A ñ', project='a', initialize=True, environ={}))
    b = bootstrap(resolve_context(engine, workspace=tmp_path / 'B ñ', project='b', initialize=True, environ={}))
    monkeypatch.setenv('BMAD_WORKSPACE', str(a.workspace_root))
    monkeypatch.setenv('BMAD_PROJECT', 'a')
    sa = load_settings()
    monkeypatch.setenv('BMAD_WORKSPACE', str(b.workspace_root))
    monkeypatch.setenv('BMAD_PROJECT', 'b')
    sb = load_settings()
    assert sa.PROJECT_ID == 'a' and sb.PROJECT_ID == 'b'
    assert sa.TRACKER_FILE == a.tracker_path and sb.TRACKER_FILE == b.tracker_path
    assert 'handoffs' in sa.ALLOWED_ROOTS
    TrackerService(str(sa.TRACKER_FILE)).append_decision('only a')
    assert TrackerService(str(sb.TRACKER_FILE)).read_tracker() == ''
    with patch.object(settings, 'TRACKER_FILE', sa.TRACKER_FILE), patch.object(settings, 'WORKSPACE_ROOT', sa.WORKSPACE_ROOT), patch.object(settings, 'PROJECT_ID', sa.PROJECT_ID):
        handler = object.__new__(MultiDirectoryWatcherHandler)
        assert handler._is_tracker(str(a.tracker_path))
        assert not handler._is_tracker(str(b.tracker_path))
        assert asyncio.run(get_project())['project_id'] == 'a'


def test_api_rejects_unknown_or_missing_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv('BMAD_WORKSPACE', str(tmp_path / 'missing'))
    monkeypatch.setenv('BMAD_PROJECT', 'missing')
    from bmad_runtime.errors import ConfigurationError
    with pytest.raises(ConfigurationError):
        load_settings()


def test_api_context_reads_only_its_workspace(tmp_path):
    engine = Path(__file__).resolve().parents[3]
    ctx = bootstrap(resolve_context(engine, workspace=tmp_path / 'Python', project='python', initialize=True, environ={}))
    ctx.output('requirements.txt').write_text('fastapi==0.115\n', encoding='utf-8')
    with patch.object(settings, 'WORKSPACE_ROOT', ctx.workspace_root), patch.object(settings, 'PROJECT_ID', ctx.project_id):
        result = asyncio.run(get_project_context())
    assert result['project_id'] == 'python'
    assert result['constitution'] == '.specify/memory/constitution.md'
    assert 'fastapi' in str(result)
    assert 'Angular' not in str(result) and 'PrimeNG' not in str(result)
