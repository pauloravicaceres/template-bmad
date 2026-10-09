import pytest
from services.git_service import GitService, GitRepoNotFoundError


class TestGitRepoNotFound:
    """Tests for uninitialized directory handling with 404 GIT_REPO_NOT_FOUND (T018 / US3 / ADR-015)."""

    @pytest.mark.anyio
    async def test_get_status_in_empty_dir_raises_not_found(self, tmp_path):
        service = GitService(workspace_root=tmp_path)
        with pytest.raises(GitRepoNotFoundError) as excinfo:
            await service.get_git_status()

        assert excinfo.value.status_code == 404
        assert excinfo.value.error_code == "GIT_REPO_NOT_FOUND"
        assert "git init" in excinfo.value.detail.lower()

    @pytest.mark.anyio
    async def test_get_commits_in_empty_dir_raises_not_found(self, tmp_path):
        service = GitService(workspace_root=tmp_path)
        with pytest.raises(GitRepoNotFoundError) as excinfo:
            await service.get_commits()

        assert excinfo.value.status_code == 404
        assert excinfo.value.error_code == "GIT_REPO_NOT_FOUND"

    @pytest.mark.anyio
    async def test_get_branches_in_empty_dir_raises_not_found(self, tmp_path):
        service = GitService(workspace_root=tmp_path)
        with pytest.raises(GitRepoNotFoundError) as excinfo:
            await service.get_branches()

        assert excinfo.value.status_code == 404
        assert excinfo.value.error_code == "GIT_REPO_NOT_FOUND"
