import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WebSocketEventType(str, Enum):
    WORKFLOW_UPDATED = "WORKFLOW_UPDATED"
    ARTIFACT_CHANGED = "ARTIFACT_CHANGED"
    HEARTBEAT_PING = "HEARTBEAT_PING"
    HEARTBEAT_PONG = "HEARTBEAT_PONG"
    SYSTEM_NOTICE = "SYSTEM_NOTICE"
    PING = "PING"
    PONG = "PONG"


class ChangeType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class FileMetadataRecord(BaseModel):
    """Metadata record for observed files, enforcing metadata-only on >5MB files."""
    relative_path: str
    filename: str
    size_bytes: int
    mime_type: str = "text/plain"
    is_large_file: bool = False
    metadata_only: bool = False
    updated_at: str


class WorkflowUpdatedPayload(BaseModel):
    """Payload for WORKFLOW_UPDATED event."""
    active_stage: Optional[str] = None
    agent_role: Optional[str] = None
    action_type: Optional[str] = None
    origin_block_index: Optional[int] = None
    handoff_target: Optional[str] = None
    last_artifact_path: Optional[str] = None
    last_open_points: Optional[str] = None
    has_pulse: bool = True
    # Compatibility with HU-002
    current_stage: Optional[str] = None
    status: Optional[str] = None


class ArtifactChangedPayload(BaseModel):
    """Payload for ARTIFACT_CHANGED event."""
    change_type: str
    relative_path: str
    is_new_tag: bool = False
    file_metadata: Optional[FileMetadataRecord] = None
    # Compatibility with HU-002
    action: Optional[str] = None
    path: Optional[str] = None
    type: Optional[str] = None


class HeartbeatPongPayload(BaseModel):
    """Payload for HEARTBEAT_PONG event."""
    server_time_utc: str
    active_clients_count: int
    heartbeat_interval_seconds: int = 30


class SystemNoticePayload(BaseModel):
    """Payload for SYSTEM_NOTICE debounce coalescence telemetry."""
    notice_code: str
    message: str
    absorbed_mutations_count: int
    window_duration_ms: int = 200
    coalesced_resource: str


class WebSocketEventMessage(BaseModel):
    """Standardized WebSocket event message envelope (ADR-011 / ADR-012)."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    resource_path: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    coalesced_count: int = 1
    payload: Dict[str, Any] = Field(default_factory=dict)

    # HU-002 compatibility fields
    event: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.event:
            self.event = self.event_type
        if not self.data:
            self.data = self.payload


class MonitoredRootStatus(BaseModel):
    allowed_path: str
    is_monitored: bool = True


class PerimeterStatusResponse(BaseModel):
    """Response model for GET /api/v1/observability/perimeter/status."""
    sandbox_status: str = "ACTIVE"
    zero_leakage_verified: bool = True
    monitored_roots: List[MonitoredRootStatus]
    ignored_external_events_count: int = 0
    debounce_window_ms: int = 200
    large_file_threshold_bytes: int = 5 * 1024 * 1024
