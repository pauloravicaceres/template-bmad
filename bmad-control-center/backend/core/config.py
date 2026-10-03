import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Settings(BaseModel):
    """Central configuration for BMAD Backend."""
    PROJECT_NAME: str = "BMAD Control Center"
    VERSION: str = "1.1.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    MAX_PAYLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB (5,242,880 bytes)
    LARGE_FILE_THRESHOLD_BYTES: int = 5 * 1024 * 1024  # 5 MB
    DEBOUNCE_WINDOW_MS: int = 200
    HEARTBEAT_INTERVAL_SECONDS: int = 30
    
    # Workspace & File-System as Database boundaries
    WORKSPACE_ROOT: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])
    TRACKER_FILE: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3] / "documents" / "tracker_bmad.md")
    ALLOWED_ROOTS: List[str] = ["documents", "specs", ".specify"]

    model_config = ConfigDict(arbitrary_types_allowed=True)


def load_settings() -> Settings:
    """Loads settings dynamically inspecting config_bmad.json if present."""
    current_file = Path(__file__).resolve()
    # Path(__file__) is bmad-control-center/backend/core/config.py -> parents[3] is project root
    workspace_root = current_file.parents[3]
    config_file = workspace_root / "config_bmad.json"
    
    tracker_path = workspace_root / "documents" / "tracker_bmad.md"
    project_name = "BMAD Control Center"

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "tracker" in data:
                    tracker_path = Path(data["tracker"])
                if "project_name" in data:
                    project_name = data["project_name"]
        except Exception:
            pass

    return Settings(
        PROJECT_NAME=project_name,
        WORKSPACE_ROOT=workspace_root,
        TRACKER_FILE=tracker_path,
        ALLOWED_ROOTS=["documents", "specs", ".specify"]
    )


settings = load_settings()
