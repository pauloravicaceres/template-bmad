import json
import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

ENGINE_ROOT = Path(__file__).resolve().parents[3]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))
from bmad_runtime.context import resolve_context
from bmad_runtime.config import effective_config


class Settings(BaseModel):
    """Central configuration for BMAD Backend."""
    PROJECT_NAME: str = "BMAD Control Center"
    PROJECT_ID: str = "legacy"
    HAS_PROJECT: bool = True
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
    """One immutable project per API process, including its websocket/event caches."""
    if not os.environ.get('BMAD_WORKSPACE') and not os.environ.get('BMAD_PROJECT'):
        return Settings(PROJECT_ID='', HAS_PROJECT=False, ALLOWED_ROOTS=[])
    context = resolve_context(ENGINE_ROOT)
    data = effective_config(context)
    return Settings(
        PROJECT_ID=context.project_id,
        PROJECT_NAME=data.get('project_name', context.project_id),
        WORKSPACE_ROOT=context.workspace_root,
        TRACKER_FILE=context.tracker_path,
        ALLOWED_ROOTS=["documents", "specs", ".specify"] + ([] if context.legacy else ['handoffs'])
    )


settings = load_settings()
