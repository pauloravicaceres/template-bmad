from contextlib import contextmanager
from typing import Optional

from core.config import settings
from bmad_runtime.tracker_io import TrackerWriter


class TrackerService:
    """Control Center access to the project tracker through the engine's TrackerWriter
    (project lock in the state directory, SQLite journal, read-back verification)."""

    def __init__(self, file_path: Optional[str] = None, state_dir: Optional[str] = None, timeout: float = 5):
        self.file_path = str(file_path or settings.TRACKER_FILE)
        self.writer = TrackerWriter(self.file_path, state_dir, timeout=timeout)

    def read_tracker(self) -> str:
        with self.writer.locked():
            return self.writer.read()

    def append_decision(self, decision: str, op_id: Optional[str] = None):
        return self.writer.append(f"\n{decision}\n\n", op_id=op_id, source="control-center")

    @contextmanager
    def transaction(self):
        """Read, decide and append under one lock. Only local parsing may run inside: never network,
        websockets or provider calls."""
        with self.writer.locked():
            yield self

    def replace_tracker_content(self, new_content: str):
        """Test fixtures only; production code never rewrites the tracker."""
        self.writer.replace_for_tests(new_content)
