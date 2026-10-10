import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from services.artifact_service import ArtifactService
from services.workflow_service import WorkflowService
import api.artifacts as artifacts_module
import api.workflow as workflow_module


@pytest.fixture
def qa_isolated_environment(tmp_path):
    """
    Fixture QA que crea un espacio de trabajo hermético con los tres directorios autorizados
    (docs/, specs/, .specify/) para certificar de forma adversarial la HU-002.
    """
    docs_dir = tmp_path / "docs"
    specs_dir = tmp_path / "specs"
    specify_dir = tmp_path / ".specify"

    docs_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)
    specify_dir.mkdir(parents=True)

    # Entregable de BA con Markdown y bloques Mermaid (SC-01)
    ba_dir = docs_dir / "business-analyst"
    ba_dir.mkdir()
    hu_doc = ba_dir / "002-HU_monitoreo.md"
    hu_doc.write_text(
        "# Monitoreo en Vivo\n\n```mermaid\nsequenceDiagram\nTL->>API: GET status\n```\nFin de spec.",
        encoding="utf-8"
    )

    # Directorio de SA completamente vacío para validar Empty State (SC-05 / CB-05)
    sa_dir = docs_dir / "solutions-architect"
    sa_dir.mkdir()

    # Archivo de especificación en specs/
    readme_spec = specs_dir / "README.md"
    readme_spec.write_text("# Product State Ledger\nACTIVE: 001\nREADY-FOR-DEV: 002", encoding="utf-8")

    # Archivo en .specify/
    const_file = specify_dir / "constitution.md"
    const_file.write_text("# Constitucion Tecnica BMAD\nPrincipio I: FSaaDB", encoding="utf-8")

    # Archivo que supera el límite de 5MB (5.5 MB) para validar CB-04
    huge_file = docs_dir / "data-architect" / "huge_payload.sql"
    huge_file.parent.mkdir(parents=True, exist_ok=True)
    with open(huge_file, "wb") as f:
        f.seek(5500000)
        f.write(b"\0")

    # Archivo binario (PNG) para validar CB-04 / 415
    png_file = docs_dir / "designer-ux" / "wireframe.png"
    png_file.parent.mkdir(parents=True, exist_ok=True)
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    # Tracker con estado en progreso para workflow (SC-01)
    tracker_path = docs_dir / "tracker_bmad.md"
    tracker_content = """
### [30-09-2026] Product Manager
- **Hora:** 23:10:00
- **Artefacto generado:** `specs/README.md`
- **Estado:** Asignación de HU 002
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @BA: Refinamiento funcional

### [30-09-2026] Business Analyst
- **Hora:** 23:14:00
- **Artefacto generado:** `docs/business-analyst/002-HU_monitoreo.md`
- **Estado:** BDD completado
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @QA: Auditoría documental
"""
    tracker_path.write_text(tracker_content.strip(), encoding="utf-8")

    # Inyección de servicios aislados
    isolated_artifact_service = ArtifactService(workspace_root=tmp_path)
    isolated_workflow_service = WorkflowService(tracker_path=tracker_path)

    artifacts_module.artifact_service = isolated_artifact_service
    workflow_module.workflow_service = isolated_workflow_service

    client = TestClient(app)
    return client, tmp_path


class TestHU002WorkflowCertification:
    """Certificación de Criterios de Aceptación para Workflow Status y Stepper (SC-01)."""

    def test_GetWorkflowStatus_ConHistorialValido_DebeRetornarEtapaActivaY15EtapasCanonicas(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment

        # Act
        response = client.get("/api/v1/workflow/status?include_history=true")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["overall_status"] == "IN_PROGRESS"
        assert payload["active_stage"] == "QA"
        assert payload["active_agent_role"] == "QA Documental"
        assert payload["completed_stages"] == 2
        assert payload["total_stages"] == 15
        assert len(payload["stages"]) == 15
        # Verificar trazabilidad histórica de handoffs
        assert len(payload["history"]) == 2
        assert payload["history"][0]["author_role"] == "Product Manager"
        assert payload["history"][1]["author_role"] == "Business Analyst"

    def test_GetWorkflowStatus_CuandoTrackerNoExiste_DebeRetornarEstadoIdleCon15EtapasPendientes(self, tmp_path):
        # Arrange
        non_existent_tracker = tmp_path / "docs" / "inexistente.md"
        workflow_module.workflow_service = WorkflowService(tracker_path=non_existent_tracker)
        client = TestClient(app)

        # Act
        response = client.get("/api/v1/workflow/status")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["overall_status"] == "IDLE"
        assert payload["active_stage"] is None
        assert payload["completed_stages"] == 0
        assert all(s["status"] == "PENDING" for s in payload["stages"])

    def test_GetWorkflowState_ConLlamadaAlAlias_DebeRetornarEstructuraIdenticaConCamposContrato(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment

        # Act
        response = client.get("/api/v1/workflow/state")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["active_stage"] == "QA"
        # Verificar campos interoperables para api-contract.md
        assert "current_stage" in payload
        assert "status" in payload
        assert "history" in payload


class TestHU002ArtifactTreeAndEmptyStateCertification:
    """Certificación del Árbol de Artefactos y Detección de Empty States (SC-01, SC-05, CB-05)."""

    def test_GetArtifactsTree_ConDirectoriosValidos_DebeRetornarArbolJerarquicoConConteoDeArchivos(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment

        # Act
        response = client.get("/api/v1/artifacts/tree")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert "root_node" in payload
        root = payload["root_node"]
        assert root["type"] == "DIRECTORY"
        # Verificar raíces autorizadas presentes
        root_names = [child["name"] for child in root["children"]]
        assert "docs" in root_names
        assert "specs" in root_names
        assert ".specify" in root_names

    def test_GetArtifactsTree_ConDirectorioVacio_DebeMarcarIsEmptyTrueYConteoCero(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment

        # Act
        response = client.get("/api/v1/artifacts/tree")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        documents_folder = next(c for c in payload["root_node"]["children"] if c["name"] == "docs")
        sa_node = next(c for c in documents_folder["children"] if c["name"] == "solutions-architect")

        assert sa_node["is_empty"] is True
        assert sa_node["child_file_count"] == 0
        assert sa_node["type"] == "DIRECTORY"


class TestHU002ArtifactContentAndSecurityCertification:
    """Certificación de Lectura Documental, Path Traversal Guard y Códigos de Error (SC-01, SC-02, SC-04, CB-01, CB-02, CB-04)."""

    def test_GetArtifactContent_ConMarkdownYDiagramaMermaid_DebeRetornarContenidoCompletoYTipoMarkdown(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        doc_path = "docs/business-analyst/002-HU_monitoreo.md"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={doc_path}")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["relative_path"] == "docs/business-analyst/002-HU_monitoreo.md"
        assert payload["filename"] == "002-HU_monitoreo.md"
        assert payload["detected_format"] == "MARKDOWN"
        assert payload["encoding"] == "utf-8"
        assert "sequenceDiagram" in payload["raw_content"]
        assert payload["is_oversized"] is False
        assert payload["is_unsupported_media"] is False

    def test_GetArtifactContent_ConArchivoInexistente_DebeRetornarHttp404NotFoundYDetalleRfc7807(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        ghost_path = "docs/business-analyst/inexistente.md"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={ghost_path}")

        # Assert
        assert response.status_code == 404
        error = response.json()
        assert error["error_code"] == "ARTIFACT_NOT_FOUND"
        assert "no existe" in error["detail"].lower()

    def test_GetArtifactContent_ConEscapePuntosParentDirectory_DebeRetornarHttp403Forbidden(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        attack_vector = "docs/../../etc/passwd"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={attack_vector}")

        # Assert
        assert response.status_code == 403
        error = response.json()
        assert error["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_GetArtifactContent_ConEscapeProfundoYDiagonalInversaWindows_DebeRetornarHttp403Forbidden(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        windows_vector = r"docs\..\..\..\Windows\System32\cmd.exe"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={windows_vector}")

        # Assert
        assert response.status_code == 403
        error = response.json()
        assert error["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_GetArtifactContent_ConCodificacionUrlDeTraversal_DebeRetornarHttp403Forbidden(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        encoded_vector = "docs/%2e%2e/%2e%2e/secret.txt"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={encoded_vector}")

        # Assert
        assert response.status_code == 403
        error = response.json()
        assert error["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_GetArtifactContent_ConRutaFueraDeDirectoriosPermitidos_DebeRetornarHttp403Forbidden(self, qa_isolated_environment):
        # Arrange
        client, tmp_path = qa_isolated_environment
        unauthorized_file = tmp_path / "secret_root.env"
        unauthorized_file.write_text("SECRET=123", encoding="utf-8")

        # Act
        response = client.get("/api/v1/artifacts/content?path=secret_root.env")

        # Assert
        assert response.status_code == 403
        error = response.json()
        assert error["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_GetArtifactContent_ConArchivoSuperiorA5MB_DebeRetornarHttp413PayloadTooLarge(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        oversized_path = "docs/data-architect/huge_payload.sql"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={oversized_path}")

        # Assert
        assert response.status_code == 413
        error = response.json()
        assert error["error_code"] == "PAYLOAD_TOO_LARGE"
        assert "5 mb" in error["detail"].lower()

    def test_GetArtifactContent_ConArchivoBinarioPng_DebeRetornarHttp415UnsupportedMediaType(self, qa_isolated_environment):
        # Arrange
        client, _ = qa_isolated_environment
        binary_path = "docs/designer-ux/wireframe.png"

        # Act
        response = client.get(f"/api/v1/artifacts/content?path={binary_path}")

        # Assert
        assert response.status_code == 415
        error = response.json()
        assert error["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert "binario" in error["detail"].lower() or "no soportado" in error["detail"].lower()


class TestHU002WebSocketCommunicationCertification:
    """Certificación del canal reactivo WebSocket y protocolo de latidos PING/PONG."""

    def test_WebSocketEvents_ConPingCanonico_DebeResponderConPongYTimestamp(self):
        # Arrange
        client = TestClient(app)

        # Act & Assert
        with client.websocket_connect("/ws/v1/events") as websocket:
            websocket.send_text(json.dumps({"event": "PING"}))
            raw_data = websocket.receive_text()
            data = json.loads(raw_data)

            assert data["event"] == "PONG"
            assert "timestamp" in data

    def test_WebSocketEvents_ConSuscripcionActiva_DebeMantenerConexionAbierta(self):
        # Arrange
        client = TestClient(app)

        # Act & Assert
        with client.websocket_connect("/ws/v1/events") as websocket:
            websocket.send_text(json.dumps({
                "event": "SUBSCRIBE_ARTIFACT",
                "path": "docs/business-analyst/002-HU_monitoreo.md"
            }))
            # Latido PING de confirmación
            websocket.send_text(json.dumps({"event": "PING"}))
            raw_data = websocket.receive_text()
            data = json.loads(raw_data)

            assert data["event"] == "PONG"
