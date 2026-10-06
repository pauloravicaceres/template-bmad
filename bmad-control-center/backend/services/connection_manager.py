import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional, Union, Any
from fastapi import WebSocket

from core.config import settings
from models.observability import (
    FileMetadataRecord,
    SystemNoticePayload,
)


class ConnectionManager:
    """
    Manages active WebSockets connections, heartbeat PING/PONG and event multiplexing
    with full compliance to ADR-011 and ADR-012.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    async def connect(self, websocket: WebSocket):
        """Accepts incoming WebSocket connection and registers client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        """Removes disconnected WebSocket cleanly."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    def subscribe_artifact(self, websocket: WebSocket, artifact_path: str):
        """Registers a client subscription to a specific artifact path."""
        norm_path = artifact_path.replace("\\", "/").strip("/")
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(norm_path)

    def unsubscribe_artifact(self, websocket: WebSocket, artifact_path: str):
        """Unregisters a client subscription."""
        norm_path = artifact_path.replace("\\", "/").strip("/")
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(norm_path)

    async def send_personal_message(self, message: Union[str, dict], websocket: WebSocket):
        """Sends a message to a specific connection."""
        try:
            payload = message if isinstance(message, str) else json.dumps(message)
            await websocket.send_text(payload)
        except Exception:
            self.disconnect(websocket)

    async def send_pong(self, websocket: WebSocket):
        """Responds to PING heartbeat with PONG and HEARTBEAT_PONG (ADR-011)."""
        now_iso = self._now_iso()
        event_id = str(uuid.uuid4())
        pong_payload = {
            "server_time_utc": now_iso,
            "active_clients_count": len(self.active_connections),
            "heartbeat_interval_seconds": settings.HEARTBEAT_INTERVAL_SECONDS,
        }
        msg = {
            "event_id": event_id,
            "event_type": "HEARTBEAT_PONG",
            "resource_path": "/ws/v1/events",
            "timestamp": now_iso,
            "coalesced_count": 1,
            "payload": pong_payload,
            # Dual output compatibility for legacy and HU-002
            "event": "PONG",
            "data": pong_payload,
        }
        await self.send_personal_message(msg, websocket)

    async def broadcast(self, message: Union[str, dict]):
        """Broadcasts a payload to all connected clients."""
        payload = message if isinstance(message, str) else json.dumps(message)
        dead_connections: List[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)

    async def broadcast_workflow_updated(self, workflow_data: dict, coalesced_count: int = 1):
        """Emits WORKFLOW_UPDATED event with enriched payload and debouncing count (ADR-010)."""
        now_iso = self._now_iso()
        event_id = str(uuid.uuid4())

        stage = workflow_data.get("active_stage")
        agent_role = workflow_data.get("active_agent_role")
        latest_handoff = workflow_data.get("latest_handoff") or {}
        target_agent = latest_handoff.get("target_agent") or ""
        to_directive = latest_handoff.get("to_directive") or (f"@{target_agent}:" if target_agent else "")
        block_idx = latest_handoff.get("block_index")
        artifact_path = workflow_data.get("active_artifact_in_progress")

        payload = {
            "active_stage": stage,
            "agent_role": agent_role,
            "action_type": f"Handoff -> {target_agent}" if target_agent else "Workflow Status Update",
            "origin_block_index": block_idx,
            "handoff_target": to_directive,
            "last_artifact_path": artifact_path,
            "last_open_points": "Ninguno",
            "has_pulse": True,
            # Estado completo proyectado por el backend (incluye etapas paralelas como DEV-BACK/DEV-FRONT)
            "overall_status": workflow_data.get("overall_status"),
            "active_agent_role": agent_role,
            "active_artifact_in_progress": artifact_path,
            "last_updated": workflow_data.get("last_updated"),
            "total_stages": workflow_data.get("total_stages"),
            "completed_stages": workflow_data.get("completed_stages"),
            "stages": workflow_data.get("stages") or [],
            "rework": workflow_data.get("rework"),
            "alert": workflow_data.get("alert"),
            # Dual output compatibility
            "current_stage": stage,
            "status": workflow_data.get("overall_status"),
        }

        event_payload = {
            "event_id": event_id,
            "event_type": "WORKFLOW_UPDATED",
            "resource_path": "documents/tracker_bmad.md",
            "timestamp": now_iso,
            "coalesced_count": coalesced_count,
            "payload": payload,
            # HU-002 compatibility
            "event": "WORKFLOW_UPDATED",
            "data": workflow_data,
        }
        await self.broadcast(event_payload)

    async def broadcast_artifact_changed(
        self,
        action: str,
        path: str,
        size_bytes: int,
        is_large_file: bool = False,
        metadata_only: bool = False,
        mime_type: str = "text/plain",
        coalesced_count: int = 1,
    ):
        """Emits ARTIFACT_CHANGED event with Metadata-Only policy support (ADR-012)."""
        now_iso = self._now_iso()
        event_id = str(uuid.uuid4())
        norm_path = path.replace("\\", "/")
        filename = os.path.basename(norm_path)

        file_metadata = {
            "relative_path": norm_path,
            "filename": filename,
            "size_bytes": size_bytes,
            "mime_type": mime_type,
            "is_large_file": is_large_file,
            "metadata_only": metadata_only,
            "updated_at": now_iso,
        }

        payload = {
            "change_type": action.lower(),
            "relative_path": norm_path,
            "is_new_tag": action.lower() == "created",
            "file_metadata": file_metadata,
            # Dual output compatibility for HU-002
            "action": action.upper(),
            "path": norm_path,
            "type": "FILE",
        }

        event_payload = {
            "event_id": event_id,
            "event_type": "ARTIFACT_CHANGED",
            "resource_path": norm_path,
            "timestamp": now_iso,
            "coalesced_count": coalesced_count,
            "payload": payload,
            # HU-002 compatibility
            "event": "ARTIFACT_CHANGED",
            "data": {
                "action": action.upper(),
                "path": norm_path,
                "size_bytes": size_bytes,
            },
        }
        await self.broadcast(event_payload)

    async def broadcast_artifact_tree_changed(
        self,
        action: str,
        target_path: str,
        is_directory: bool,
        parent_path: Optional[str] = None,
    ):
        """Emits ARTIFACT_TREE_CHANGED event."""
        norm_target = target_path.replace("\\", "/")
        norm_parent = parent_path.replace("\\", "/") if parent_path else None

        event_payload = {
            "event": "ARTIFACT_TREE_CHANGED",
            "timestamp": self._now_iso(),
            "data": {
                "action": action,
                "target_path": norm_target,
                "is_directory": is_directory,
                "parent_path": norm_parent,
            },
            # Dual output compatibility
            "payload": {
                "action": action,
                "path": norm_target,
                "type": "DIRECTORY" if is_directory else "FILE",
            },
        }
        await self.broadcast(event_payload)

    async def broadcast_system_notice(self, notice: SystemNoticePayload):
        """Emits SYSTEM_NOTICE event for debounce coalescence telemetry."""
        now_iso = self._now_iso()
        event_id = str(uuid.uuid4())
        notice_dict = notice.model_dump()

        event_payload = {
            "event_id": event_id,
            "event_type": "SYSTEM_NOTICE",
            "resource_path": notice.coalesced_resource,
            "timestamp": now_iso,
            "coalesced_count": notice.absorbed_mutations_count,
            "payload": notice_dict,
            # Dual output compatibility
            "event": "SYSTEM_NOTICE",
            "data": notice_dict,
        }
        await self.broadcast(event_payload)

    async def broadcast_git_status_changed(self, payload: dict, coalesced_count: int = 1):
        """Emits GIT_STATUS_CHANGED event (ADR-014)."""
        now_iso = self._now_iso()
        event_id = str(uuid.uuid4())

        event_payload = {
            "event_id": event_id,
            "event_type": "GIT_STATUS_CHANGED",
            "resource_path": ".git/HEAD",
            "timestamp": now_iso,
            "coalesced_count": coalesced_count,
            "payload": payload,
            # Dual output compatibility
            "event": "GIT_STATUS_CHANGED",
            "data": payload,
        }
        await self.broadcast(event_payload)


# Global connection manager instance
manager = ConnectionManager()
