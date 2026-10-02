import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.backend.services.connection_manager import manager

router = APIRouter(tags=["WebSockets Live Feed"])


async def handle_websocket_session(websocket: WebSocket):
    """
    Handles bidirectional WebSocket session with heartbeat, subscriptions
    and WS 1008 Policy Violation guard for malformed frames (ADR-011 / ADR-012).
    """
    await manager.connect(websocket)
    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                msg = json.loads(text_data)
            except Exception:
                # CB-04 / T027: Malformed frame must close with WS 1008 Policy Violation
                await websocket.close(code=1008, reason="InvalidProtocolFrame")
                manager.disconnect(websocket)
                return

            if not isinstance(msg, dict):
                await websocket.close(code=1008, reason="InvalidProtocolFrame")
                manager.disconnect(websocket)
                return

            event_type = msg.get("event") or msg.get("event_type")
            if event_type in ("PING", "HEARTBEAT_PING"):
                await manager.send_pong(websocket)
            elif event_type == "SUBSCRIBE_ARTIFACT":
                path = msg.get("path") or msg.get("resource_path")
                if path:
                    manager.subscribe_artifact(websocket, path)
            elif event_type == "UNSUBSCRIBE_ARTIFACT":
                path = msg.get("path") or msg.get("resource_path")
                if path:
                    manager.unsubscribe_artifact(websocket, path)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.websocket("/ws/v1/events")
async def websocket_canonical(websocket: WebSocket):
    """Canonical WebSocket endpoint for multiplexed live updates (ADR-011)."""
    await handle_websocket_session(websocket)


@router.websocket("/api/v1/ws/monitor")
async def websocket_monitor_alias(websocket: WebSocket):
    """Spec Kit interoperability alias for live monitoring."""
    await handle_websocket_session(websocket)


@router.websocket("/ws/hitl")
async def websocket_hitl_alias(websocket: WebSocket):
    """HITL decision channel alias."""
    await handle_websocket_session(websocket)


@router.websocket("/ws")
async def websocket_legacy_alias(websocket: WebSocket):
    """Legacy backward-compatible endpoint for HU-001."""
    await handle_websocket_session(websocket)
