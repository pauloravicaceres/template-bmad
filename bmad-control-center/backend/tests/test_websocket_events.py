import json
import pytest
from fastapi.testclient import TestClient

from main import app
from services.connection_manager import manager
from models.observability import SystemNoticePayload


class TestWebSocketEvents:
    """Tests for WebSocket event envelopes, heartbeat, and multiplexing (T008, T013)."""

    def test_handshake_and_heartbeat_pong(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as ws:
            ws.send_text(json.dumps({"event_type": "HEARTBEAT_PING"}))
            raw = ws.receive_text()
            data = json.loads(raw)
            assert data["event_type"] == "HEARTBEAT_PONG"
            assert data["resource_path"] == "/ws/v1/events"
            assert "payload" in data
            assert "server_time_utc" in data["payload"]
            assert data["payload"]["heartbeat_interval_seconds"] == 30

    def test_workflow_updated_broadcast_envelope(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as ws:
            # Simulate a workflow update broadcast
            workflow_mock = {
                "active_stage": "UX",
                "overall_status": "IN_PROGRESS",
                "active_agent_role": "Designer UX",
                "active_artifact_in_progress": "documents/designer-ux/ux_003.md",
                "latest_handoff": {
                    "from_agent": "QA Documental",
                    "target_agent": "UX",
                    "to_directive": "@UX: Procede con wireframes",
                    "block_index": 251,
                }
            }
            # Run coroutine synchronously in test
            import asyncio
            asyncio.run(manager.broadcast_workflow_updated(workflow_mock, coalesced_count=3))

            raw = ws.receive_text()
            msg = json.loads(raw)

            assert msg["event_type"] == "WORKFLOW_UPDATED"
            assert msg["resource_path"] == "handoffs/tracker_bmad.md"
            assert msg["coalesced_count"] == 3
            assert msg["payload"]["active_stage"] == "UX"
            assert msg["payload"]["agent_role"] == "Designer UX"
            assert msg["payload"]["has_pulse"] is True
            assert msg["payload"]["origin_block_index"] == 251
            assert msg["payload"]["handoff_target"] == "@UX: Procede con wireframes"

    def test_artifact_changed_broadcast_envelope(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as ws:
            import asyncio
            asyncio.run(manager.broadcast_artifact_changed(
                action="CREATED",
                path="documents/designer-ux/mock.md",
                size_bytes=1024,
                is_large_file=False,
                metadata_only=False,
                mime_type="text/markdown",
                coalesced_count=1
            ))

            raw = ws.receive_text()
            msg = json.loads(raw)

            assert msg["event_type"] == "ARTIFACT_CHANGED"
            assert msg["resource_path"] == "documents/designer-ux/mock.md"
            assert msg["payload"]["change_type"] == "created"
            assert msg["payload"]["is_new_tag"] is True
            assert msg["payload"]["file_metadata"]["filename"] == "mock.md"
            assert msg["payload"]["file_metadata"]["size_bytes"] == 1024
            assert msg["payload"]["file_metadata"]["metadata_only"] is False

    def test_system_notice_debounce_telemetry_broadcast(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as ws:
            notice = SystemNoticePayload(
                notice_code="DEBOUNCE_COALESCENCE_APPLIED",
                message="Se agruparon 5 escrituras consecutivas en documents/tracker_bmad.md",
                absorbed_mutations_count=5,
                window_duration_ms=200,
                coalesced_resource="documents/tracker_bmad.md",
            )
            import asyncio
            asyncio.run(manager.broadcast_system_notice(notice))

            raw = ws.receive_text()
            msg = json.loads(raw)

            assert msg["event_type"] == "SYSTEM_NOTICE"
            assert msg["coalesced_count"] == 5
            assert msg["payload"]["notice_code"] == "DEBOUNCE_COALESCENCE_APPLIED"
            assert msg["payload"]["absorbed_mutations_count"] == 5
            assert msg["payload"]["window_duration_ms"] == 200
