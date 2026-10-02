import pytest
from app.backend.services.git_service import git_service


class TestGitBinaryAndSanitization:
    """Tests for string sanitization, author fallback, and binary/1MB diff elision (T024 / CB-04 / CB-05)."""

    def test_sanitize_string_removes_null_bytes(self):
        dirty = "feat(auth): login\x00 injection\x00"
        clean = git_service._sanitize_string(dirty)
        assert "\x00" not in clean
        assert clean == "feat(auth): login injection"

    def test_infer_agent_role_from_messages(self):
        assert git_service._infer_agent_role("Paulo", "feat(auth): [TASK-001-BE-01]") == "Senior Backend Developer"
        assert git_service._infer_agent_role("Paulo", "feat(login): [TASK-001-FE-01]") == "Senior Frontend Developer"
        assert git_service._infer_agent_role("Paulo", "test(auth): [TASK-001-QA-01]") == "QA Automation"
        assert git_service._infer_agent_role("Business Analyst", "feat: spec") == "Business Analyst"
        assert git_service._infer_agent_role("Designer UX", "wireframes") == "Designer UX"

    @pytest.mark.asyncio
    async def test_commits_elide_diff_for_large_or_binary_files(self):
        # Inspect commits returned by get_commits
        response = await git_service.get_commits(limit=50)
        assert response.total_count > 0

        for commit in response.commits:
            for file_change in commit.files:
                if file_change.is_binary:
                    assert file_change.is_diff_omitted is True
