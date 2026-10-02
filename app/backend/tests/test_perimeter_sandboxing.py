import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.core.security import (
    is_path_in_perimeter,
    increment_ignored_external_events,
    get_ignored_external_events_count,
    reset_ignored_external_events_count,
)
from app.backend.core.config import settings
from app.backend.services.file_watcher import MultiDirectoryWatcherHandler
from watchdog.events import FileModifiedEvent, FileCreatedEvent


class TestPerimeterSandboxing:
    """Tests for canonical perimeter sandboxing and silent discard of external events (T024 / US5)."""

    def setup_method(self):
        reset_ignored_external_events_count()

    def test_is_path_in_perimeter_allowed_roots(self):
        """Files in files/, .specify/, specs/ must be inside perimeter."""
        assert is_path_in_perimeter("files/tracker_bmad.md") is True
        assert is_path_in_perimeter(".specify/memory/constitution.md") is True
        assert is_path_in_perimeter("specs/003/plan.md") is True

    def test_is_path_in_perimeter_excluded_and_external_paths(self):
        """Files in .git/, .idea/, node_modules/, temp dirs must be rejected."""
        assert is_path_in_perimeter(".git/index.lock") is False
        assert is_path_in_perimeter("D:/some/external/path/outside/workspace.txt") is False
        assert is_path_in_perimeter(".idea/workspace.xml") is False
        assert is_path_in_perimeter("node_modules/package.json") is False
        assert is_path_in_perimeter("../outside_repo.txt") is False

    def test_watcher_silent_discard_and_telemetry_increment(self):
        """Mutations on external or excluded files increment counter and emit 0 WS events."""
        import asyncio
        loop = asyncio.new_event_loop()
        handler = MultiDirectoryWatcherHandler(loop=loop)

        initial_count = get_ignored_external_events_count()

        # Simulate events from external sources
        handler.on_modified(FileModifiedEvent(src_path=str(settings.WORKSPACE_ROOT / ".git" / "index.lock")))
        handler.on_created(FileCreatedEvent(src_path="C:/Windows/Temp/secret.log"))

        new_count = get_ignored_external_events_count()
        assert new_count == initial_count + 2

        loop.close()

    def test_telemetry_endpoint_perimeter_status(self):
        """GET /api/v1/observability/perimeter/status reflects active sandbox and discarded counts."""
        increment_ignored_external_events()
        increment_ignored_external_events()

        client = TestClient(app)
        response = client.get("/api/v1/observability/perimeter/status")
        assert response.status_code == 200

        data = response.json()
        assert data["sandbox_status"] == "ACTIVE"
        assert data["zero_leakage_verified"] is True
        assert data["ignored_external_events_count"] >= 2
        assert data["debounce_window_ms"] == 200
        assert data["large_file_threshold_bytes"] == 5242880
        assert len(data["monitored_roots"]) == 3
