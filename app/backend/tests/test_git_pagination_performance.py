import time
import pytest
from fastapi.testclient import TestClient

from app.backend.main import app


class TestGitPaginationPerformance:
    """Tests for pagination SLA (< 300ms response time / SC-001 / ADR-014)."""

    def test_commits_pagination_under_300ms_sla(self):
        client = TestClient(app)
        response = client.get("/api/v1/git/commits?limit=50&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["commits"]) <= 50
        # Verify strict backend execution SLA < 300ms (SC-001)
        assert data["execution_time_ms"] < 300, f"Expected backend execution < 300ms, got {data['execution_time_ms']}ms"
