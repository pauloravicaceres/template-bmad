import pytest
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.services.git_service import git_service


class TestGitApi:
    """Tests for Git Telemetry endpoints: /status, /commits, /branches (T008, T013)."""

    def test_get_git_status_live_endpoint(self):
        client = TestClient(app)
        response = client.get("/api/v1/git/status")
        assert response.status_code == 200

        data = response.json()
        assert "current_branch" in data
        assert isinstance(data["current_branch"], str) and len(data["current_branch"]) > 0
        assert "head_commit_hash" in data
        assert len(data["head_commit_hash"]) == 40
        assert len(data["head_commit_short"]) == 7
        assert "head_commit_message" in data
        assert "head_commit_author" in data
        assert data["is_syncing"] is False
        assert data["is_detached"] is False
        assert "working_tree" in data
        assert isinstance(data["working_tree"]["staged"], list)
        assert isinstance(data["working_tree"]["unstaged"], list)
        assert isinstance(data["working_tree"]["untracked"], list)
        assert isinstance(data["working_tree"]["conflicts"], list)
        assert data["total_modified_files"] >= 0

    def test_get_git_commits_pagination(self):
        client = TestClient(app)
        response = client.get("/api/v1/git/commits?limit=10&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert "commits" in data
        assert len(data["commits"]) <= 10
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert data["total_count"] > 0
        assert isinstance(data["has_more"], bool)
        assert data["execution_time_ms"] >= 0

        if data["commits"]:
            commit = data["commits"][0]
            assert "commit_hash" in commit
            assert len(commit["commit_hash"]) == 40
            assert "author_name" in commit
            assert "message" in commit
            assert "files" in commit

    def test_get_git_commits_invalid_pagination(self):
        client = TestClient(app)
        res_limit = client.get("/api/v1/git/commits?limit=0")
        assert res_limit.status_code in (400, 422)

        res_offset = client.get("/api/v1/git/commits?offset=-1")
        assert res_offset.status_code in (400, 422)

    def test_get_git_branches(self):
        client = TestClient(app)
        response = client.get("/api/v1/git/branches")
        assert response.status_code == 200

        data = response.json()
        assert "branches" in data
        assert data["total_branches"] >= 1
        assert any(b["is_current"] for b in data["branches"])
        current_b = next(b for b in data["branches"] if b["is_current"])
        assert isinstance(current_b["name"], str) and len(current_b["name"]) > 0
