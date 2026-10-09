import asyncio
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from services.git_service import git_service
from core.config import settings


class TestGitLockContention:
    """Tests for lockfile contention resilience and fallback to cached snapshot (T017 / US3 / ADR-015)."""

    @pytest.mark.anyio
    async def test_lockfile_triggers_cached_snapshot_fallback(self, tmp_path):
        # First ensure we have a valid snapshot in memory
        initial_status = await git_service.get_git_status()
        assert initial_status.is_syncing is False

        # Create a simulated .git/index.lock
        lock_file = settings.WORKSPACE_ROOT / ".git" / "index.lock"
        try:
            lock_file.write_text("locked", encoding="utf-8")

            # Request status while locked
            status_under_lock = await git_service.get_git_status()

            # Must return 200 OK snapshot with is_syncing=True (0% 5xx errors)
            assert status_under_lock.is_syncing is True
            assert status_under_lock.current_branch == initial_status.current_branch
        finally:
            if lock_file.exists():
                lock_file.unlink()

        # After releasing lock, is_syncing must return to False
        recovered_status = await git_service.get_git_status()
        assert recovered_status.is_syncing is False

    def test_api_endpoint_under_lock_returns_200_ok(self):
        client = TestClient(app)
        # Seed snapshot
        client.get("/api/v1/git/status")

        lock_file = settings.WORKSPACE_ROOT / ".git" / "index.lock"
        try:
            lock_file.write_text("locked", encoding="utf-8")
            res = client.get("/api/v1/git/status")
            assert res.status_code == 200
            data = res.json()
            assert data["is_syncing"] is True
        finally:
            if lock_file.exists():
                lock_file.unlink()
