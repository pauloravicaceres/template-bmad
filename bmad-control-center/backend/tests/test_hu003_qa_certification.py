import pytest
import json
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from services.connection_manager import ConnectionManager
from services.event_debouncer import EventDebouncer
from core.security import (
    is_path_in_perimeter,
    increment_ignored_external_events,
    get_ignored_external_events_count,
    reset_ignored_external_events_count,
)
from models.observability import SystemNoticePayload


@pytest.fixture
def qa_client():
    """Cliente de pruebas para endpoints HTTP y WebSockets."""
    return TestClient(app)


class TestHU003WorkflowAndArtifactNotificationCertification:
    """Certificación de Criterios de Aceptación para notificaciones WebSocket estructuradas (SC-01 y SC-02)."""

    @pytest.mark.asyncio
    async def test_BroadcastWorkflowUpdated_CuandoSeEmiteMutacionEnTracker_DebeEntregarEnvelopeTipadoAClientes(self):
        # Arrange
        mgr = ConnectionManager()
        received_messages = []

        class DummyWebSocket:
            async def send_text(self, text: str):
                received_messages.append(json.loads(text))

        dummy_ws = DummyWebSocket()
        mgr.active_connections.append(dummy_ws)

        workflow_data = {
            "active_stage": "BA",
            "active_agent_role": "Business Analyst",
            "overall_status": "IN_PROGRESS",
            "active_artifact_in_progress": "documents/business-analyst/003-HU.md",
            "latest_handoff": {
                "target_agent": "BA",
                "to_directive": "@BA:",
                "block_index": 4,
            },
        }

        # Act
        await mgr.broadcast_workflow_updated(workflow_data, coalesced_count=2)

        # Assert
        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["event_type"] == "WORKFLOW_UPDATED"
        assert msg["resource_path"] == "documents/tracker_bmad.md"
        assert msg["coalesced_count"] == 2
        assert "timestamp" in msg
        assert msg["payload"]["active_stage"] == "BA"
        assert msg["payload"]["agent_role"] == "Business Analyst"
        assert msg["payload"]["handoff_target"] == "@BA:"
        assert msg["payload"]["has_pulse"] is True

    @pytest.mark.asyncio
    async def test_BroadcastArtifactChanged_CuandoSeCreaOModificaArchivo_DebeEntregarEnvelopeTipadoConMetadatos(self):
        # Arrange
        mgr = ConnectionManager()
        received_messages = []

        class DummyWebSocket:
            async def send_text(self, text: str):
                received_messages.append(json.loads(text))

        dummy_ws = DummyWebSocket()
        mgr.active_connections.append(dummy_ws)

        # Act
        await mgr.broadcast_artifact_changed(
            action="CREATED",
            path="documents/business-analyst/003-HU_observabilidad.md",
            size_bytes=10240,
            is_large_file=False,
            metadata_only=False,
            mime_type="text/markdown",
            coalesced_count=1,
        )

        # Assert
        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["event_type"] == "ARTIFACT_CHANGED"
        assert msg["resource_path"] == "documents/business-analyst/003-HU_observabilidad.md"
        assert msg["coalesced_count"] == 1
        assert msg["payload"]["change_type"] == "created"
        assert msg["payload"]["is_new_tag"] is True
        assert msg["payload"]["file_metadata"]["size_bytes"] == 10240
        assert msg["payload"]["file_metadata"]["mime_type"] == "text/markdown"
        assert msg["payload"]["file_metadata"]["metadata_only"] is False


class TestHU003DebouncerAndThrottlingCertification:
    """Certificación del mecanismo de coalescencia y absorción de ráfagas I/O (SC-04 / CB-02 / ADR-010)."""

    @pytest.mark.asyncio
    async def test_EventDebouncer_ConRafagaDeMutacionesEnVentanaDe200ms_DebeCoalescerEnUnSoloEvento(self):
        # Arrange
        loop = asyncio.get_running_loop()
        dispatched_counts = []

        async def dummy_dispatcher(coalesced_count: int):
            dispatched_counts.append(coalesced_count)

        # Debouncer con ventana de 100ms para testing rápido y determinista
        debouncer = EventDebouncer(loop=loop, window_ms=100)
        resource = "documents/tracker_bmad.md"

        # Act
        # Disparo de 4 escrituras consecutivas en rápida sucesión (<50ms entre cada una)
        for _ in range(4):
            debouncer.submit_event(
                resource_path=resource,
                event_type="WORKFLOW_UPDATED",
                dispatch_coro_factory=dummy_dispatcher,
            )
            await asyncio.sleep(0.01)

        # Esperar a que la ventana de debounce expire
        await asyncio.sleep(0.18)

        # Assert
        # Debe haberse emitido exactamente un único evento consolidado con conteo coalescido 4
        assert len(dispatched_counts) == 1
        assert dispatched_counts[0] == 4

    @pytest.mark.asyncio
    async def test_EventDebouncer_ConRafagaDeMutaciones_DebeInvocarCallbackSystemNoticeConTelemetria(self):
        # Arrange
        loop = asyncio.get_running_loop()
        system_notices = []

        async def dummy_dispatcher(coalesced_count: int):
            pass

        async def dummy_notice_cb(payload: SystemNoticePayload):
            system_notices.append(payload)

        debouncer = EventDebouncer(
            loop=loop,
            window_ms=80,
            system_notice_callback=dummy_notice_cb
        )
        resource = "documents/data-architect/schema.md"

        # Act
        # Disparo de 3 mutaciones consecutivas
        for _ in range(3):
            debouncer.submit_event(
                resource_path=resource,
                event_type="ARTIFACT_CHANGED",
                dispatch_coro_factory=dummy_dispatcher,
            )
            await asyncio.sleep(0.01)

        await asyncio.sleep(0.15)

        # Assert
        # Al coalescer más de 1 evento, debe dispararse una notificación de sistema
        assert len(system_notices) == 1
        notice = system_notices[0]
        assert notice.notice_code == "DEBOUNCE_COALESCENCE_APPLIED"
        assert notice.absorbed_mutations_count == 3
        assert "documents/data-architect/schema.md" in notice.coalesced_resource

    @pytest.mark.asyncio
    async def test_EventDebouncer_ConRutasDistintas_DebeMantenerBuffersIndependientes(self):
        # Arrange
        loop = asyncio.get_running_loop()
        dispatched_resources = []

        def make_dispatcher(path: str):
            async def d(count: int):
                dispatched_resources.append((path, count))
            return d

        debouncer = EventDebouncer(loop=loop, window_ms=80)

        # Act
        debouncer.submit_event(
            resource_path="documents/doc_a.md",
            event_type="ARTIFACT_CHANGED",
            dispatch_coro_factory=make_dispatcher("documents/doc_a.md"),
        )
        debouncer.submit_event(
            resource_path="documents/doc_b.md",
            event_type="ARTIFACT_CHANGED",
            dispatch_coro_factory=make_dispatcher("documents/doc_b.md"),
        )

        await asyncio.sleep(0.15)

        # Assert
        # Cada archivo debe despacharse independientemente
        assert len(dispatched_resources) == 2
        paths = [item[0] for item in dispatched_resources]
        assert "documents/doc_a.md" in paths
        assert "documents/doc_b.md" in paths


class TestHU003PerimeterSandboxingCertification:
    """Certificación de Sandboxing Perimetral y Descarte Silencioso (SC-05 / ADR-012)."""

    def test_IsPathInPerimeter_ConRutasFueraDeScopeOCarpetasOcultas_DebeRetornarFalseYDescartarSilenciosamente(self, tmp_path):
        # Arrange
        ws_root = tmp_path
        (ws_root / "documents").mkdir()

        # Act & Assert
        # Carpetas excluidas del perímetro
        assert is_path_in_perimeter(ws_root / ".git" / "COMMIT_EDITMSG", workspace_root=ws_root) is False
        assert is_path_in_perimeter(ws_root / ".idea" / "workspace.xml", workspace_root=ws_root) is False
        assert is_path_in_perimeter(ws_root / "node_modules" / "package.json", workspace_root=ws_root) is False
        assert is_path_in_perimeter(ws_root / "__pycache__" / "cache.pyc", workspace_root=ws_root) is False
        # Ruta completamente fuera del workspace
        assert is_path_in_perimeter("C:/Windows/System32/calc.exe", workspace_root=ws_root) is False

    def test_IsPathInPerimeter_ConRaicesAutorizadasdocumentsSpecsYSpecify_DebeRetornarTrue(self, tmp_path):
        # Arrange
        ws_root = tmp_path
        (ws_root / "documents").mkdir()
        (ws_root / "specs").mkdir()
        (ws_root / ".specify").mkdir()

        # Act & Assert
        assert is_path_in_perimeter(ws_root / "documents" / "tracker_bmad.md", workspace_root=ws_root) is True
        assert is_path_in_perimeter(ws_root / "specs" / "README.md", workspace_root=ws_root) is True
        assert is_path_in_perimeter(ws_root / ".specify" / "memory" / "constitution.md", workspace_root=ws_root) is True

    def test_GetPerimeterStatus_ConPeticionAlEndpointDeTelemetria_DebeReportarDirectoriosAutorizadosYEventosDescartados(self, qa_client):
        # Arrange
        reset_ignored_external_events_count()
        increment_ignored_external_events()
        increment_ignored_external_events()

        # Act
        response = qa_client.get("/api/v1/observability/perimeter/status")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["sandbox_status"] == "ACTIVE"
        assert payload["zero_leakage_verified"] is True
        assert payload["ignored_external_events_count"] >= 2
        monitored_paths = [r["allowed_path"] for r in payload["monitored_roots"]]
        assert "documents/" in monitored_paths
        assert "specs/" in monitored_paths
        assert ".specify/" in monitored_paths


class TestHU003WebSocketProtocolGuardCertification:
    """Certificación de Seguridad del Protocolo WebSocket y Cierre WS 1008 ante tramas malformadas (CB-04 / CB-01)."""

    def test_WebSocketFrameProtocol_ConTramaNoJson_DebeCerrarInmediatamenteConCodigo1008(self, qa_client):
        # Arrange & Act
        with qa_client.websocket_connect("/ws/v1/events") as ws:
            # Enviar texto crudo no JSON (viola protocolo tipado)
            ws.send_text("THIS_IS_NOT_A_VALID_JSON_FRAME")
            
            # Assert
            # El servidor debe cerrar la conexión inmediatamente con código 1008 (Policy Violation)
            with pytest.raises(Exception):
                ws.receive_text()

    def test_WebSocketFrameProtocol_ConTramaNoObjeto_DebeCerrarInmediatamenteConCodigo1008(self, qa_client):
        # Arrange & Act
        with qa_client.websocket_connect("/ws/v1/events") as ws:
            # Enviar JSON primitivo (ej. número o lista en lugar de objeto dict)
            ws.send_text("12345")

            # Assert
            with pytest.raises(Exception):
                ws.receive_text()

    def test_WebSocketHeartbeat_ConPing_DebeRetornarPongConServerTimeYActiveClients(self, qa_client):
        # Arrange & Act
        with qa_client.websocket_connect("/ws/v1/events") as ws:
            ping_msg = json.dumps({"event": "PING"})
            ws.send_text(ping_msg)
            raw_response = ws.receive_text()
            response = json.loads(raw_response)

            # Assert
            assert response["event_type"] == "HEARTBEAT_PONG"
            assert response["event"] == "PONG"
            assert "server_time_utc" in response["payload"]
            assert response["payload"]["active_clients_count"] >= 1
            assert "timestamp" in response


class TestHU003LargeFileMetadataOnlyPolicyCertification:
    """Certificación de la Política Metadata-Only para archivos mayores a 5MB (CB-05 / ADR-012)."""

    @pytest.mark.asyncio
    async def test_BroadcastArtifactChanged_ConArchivoMayorA5MB_DebeEstablecerMetadataOnlyTrueYIsLargeFileTrue(self):
        # Arrange
        mgr = ConnectionManager()
        received_messages = []

        class DummyWebSocket:
            async def send_text(self, text: str):
                received_messages.append(json.loads(text))

        mgr.active_connections.append(DummyWebSocket())

        # Archivo de 6 MB (> 5 MB)
        size_6mb = 6 * 1024 * 1024

        # Act
        await mgr.broadcast_artifact_changed(
            action="MODIFIED",
            path="documents/data-architect/large_export.sql",
            size_bytes=size_6mb,
            is_large_file=True,
            metadata_only=True,
            mime_type="application/sql",
            coalesced_count=1,
        )

        # Assert
        assert len(received_messages) == 1
        meta = received_messages[0]["payload"]["file_metadata"]
        assert meta["is_large_file"] is True
        assert meta["metadata_only"] is True
        assert meta["size_bytes"] == size_6mb
        # El envelope NO debe contener ningún campo de contenido crudo (raw_content)
        assert "raw_content" not in received_messages[0]
        assert "raw_content" not in received_messages[0]["payload"]
