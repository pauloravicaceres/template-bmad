"""Dashboard fixtures never inspect or mutate an operator's repository."""
from unittest.mock import Mock

import pytest


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture(autouse=True)
def isolated_dashboard(tmp_path, monkeypatch):
    from core.config import settings
    from services.git_service import GitService, git_service
    from services.tracker_service import TrackerService
    from services.workflow_service import WorkflowService
    import api.routes as routes
    import api.workflow as workflow
    import main

    root = tmp_path / 'dashboard-workspace'
    root.mkdir()
    (root / '.git').mkdir()
    tracker = root / 'handoffs/tracker_bmad.md'
    tracker.parent.mkdir()
    tracker.write_text('', encoding='utf-8')
    monkeypatch.setattr(settings, 'HAS_PROJECT', True)
    monkeypatch.setattr(settings, 'PROJECT_ID', 'dashboard-test')
    monkeypatch.setattr(settings, 'WORKSPACE_ROOT', root)
    monkeypatch.setattr(settings, 'TRACKER_FILE', tracker)
    monkeypatch.setattr(settings, 'ALLOWED_ROOTS', ['documents', 'specs', '.specify', 'handoffs'])
    monkeypatch.setattr(routes, 'tracker_service', TrackerService(str(tracker)))
    monkeypatch.setattr(workflow, 'workflow_service', WorkflowService(tracker_path=tracker))
    monkeypatch.setattr(main.file_watcher, 'start', Mock())
    monkeypatch.setattr(main.file_watcher, 'stop', Mock())
    monkeypatch.setattr(git_service, 'workspace_root', root)
    monkeypatch.setattr(git_service, '_last_snapshot', None)
    monkeypatch.setattr(git_service, '_cached_total_count', None)

    async def git_output(service, *args, **kwargs):
        assert service.workspace_root == root, 'Git double cannot access another workspace'
        digest = 'a' * 40
        if args[0] == 'status':
            return '# branch.head main\n', '', 0
        if args[0] == 'rev-list':
            return '20', '', 0
        if args[0] == 'branch':
            return '\x1f'.join(('main', digest, digest[:7], '', '*')), '', 0
        if args[:2] == ('log', '-1'):
            return '\x1f'.join((digest, digest[:7], 'Test', '2026-01-01T00:00:00Z', 'feat: fixture')), '', 0
        if args[0] == 'log':
            offset = int(next(a.split('=')[1] for a in args if a.startswith('--skip=')))
            limit = int(next(a[2:] for a in args if a.startswith('-n')))
            rows = ['\x1f'.join(('COMMIT_START', f'{i:040x}', f'{i:040x}'[:7], 'Test',
                                 'test@example.invalid', '2026-01-01T00:00:00Z', 'feat: fixture'))
                    + '\nA\timage.png\n' for i in range(offset, min(offset + limit, 20))]
            return '\n'.join(rows), '', 0
        raise AssertionError(f'Unexpected Git command: {args}')

    monkeypatch.setattr(GitService, '_run_git_command', git_output)
