import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.backend.main import app


class TestWebSocketMalformedFrame:
    """Tests for WS 1008 Policy Violation on malformed or non-dict frames (T027 / CB-04)."""

    def test_malformed_json_frame_closes_with_ws_1008(self):
        client = TestClient(app)
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws/v1/events") as ws:
                # Send invalid raw string that fails json.loads
                ws.send_text("MALFORMED_NON_JSON_DATA{{{:::")
                # Next receive should fail because server closed connection
                ws.receive_text()

        assert excinfo.value.code == 1008

    def test_non_dict_json_frame_closes_with_ws_1008(self):
        client = TestClient(app)
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws/v1/events") as ws:
                # Send valid JSON but not a dictionary (e.g. integer or list)
                ws.send_text("[1, 2, 3]")
                ws.receive_text()

        assert excinfo.value.code == 1008

    def test_raw_primitive_string_closes_with_ws_1008(self):
        client = TestClient(app)
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws/v1/events") as ws:
                ws.send_text('"plain string not dict"')
                ws.receive_text()

        assert excinfo.value.code == 1008
