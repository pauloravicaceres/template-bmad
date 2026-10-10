import pytest
import json
from fastapi.testclient import TestClient
from main import app


class TestWebSocketsApi:
    """Tests for WebSockets endpoints and protocol (Heartbeat and Multiplexing)."""

    def test_websocket_canonical_ping_pong_protocol(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as websocket:
            # Send PING
            websocket.send_text(json.dumps({"event": "PING"}))
            data = websocket.receive_text()
            response = json.loads(data)
            assert response["event"] == "PONG"
            assert "timestamp" in response

    def test_websocket_monitor_alias_ping_pong(self):
        client = TestClient(app)
        with client.websocket_connect("/api/v1/ws/monitor") as websocket:
            websocket.send_text(json.dumps({"event": "PING"}))
            data = websocket.receive_text()
            response = json.loads(data)
            assert response["event"] == "PONG"

    def test_websocket_subscription_and_clean_disconnect(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/v1/events") as websocket:
            websocket.send_text(json.dumps({
                "event": "SUBSCRIBE_ARTIFACT",
                "path": "docs/business-analyst/002-HU.md"
            }))
            # Still responsive to ping
            websocket.send_text(json.dumps({"event": "PING"}))
            data = websocket.receive_text()
            response = json.loads(data)
            assert response["event"] == "PONG"
