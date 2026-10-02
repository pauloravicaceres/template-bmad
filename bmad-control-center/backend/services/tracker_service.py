import os
import json
from pathlib import Path
from typing import Optional
from filelock import FileLock, Timeout
from core.config import settings

class TrackerService:
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = str(file_path or settings.TRACKER_FILE)
        self.lock_path = f"{self.file_path}.lock"
        self.lock = FileLock(self.lock_path, timeout=5)

    def read_tracker(self) -> str:
        with self.lock:
            if not os.path.exists(self.file_path):
                return ""
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()

    def append_decision(self, decision: str):
        with self.lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{decision}\n")

    def replace_tracker_content(self, new_content: str):
        with self.lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
