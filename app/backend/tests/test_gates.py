import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
import app.backend.api.routes as routes
from app.backend.services.tracker_service import TrackerService


@pytest.fixture
def client_with_isolated_tracker(tmp_path):
    """Fixture que proporciona un TestClient con TrackerService aislado en un archivo temporal."""
    test_tracker_path = tmp_path / "tracker_bmad.md"
    isolated_service = TrackerService(str(test_tracker_path))
    routes.tracker_service = isolated_service
    client = TestClient(app)
    return client, isolated_service, test_tracker_path


class TestGatesStatusEndpoint:
    """Pruebas para el endpoint GET /api/v1/gates/status (US1 / Hidratación de Estado)."""

    def test_GetGateStatus_CuandoTrackerContieneCompuertaPendiente_DebeRetornarPendingDecision(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        service.append_decision("### [30-09-2026] Business Analyst\n- **Estado:** PENDING_DECISION\n- **Handoff:** @HUMANO: Revisar compuerta")

        # Act
        response = client.get("/api/v1/gates/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING_DECISION"
        assert "PENDING" in data["content"]

    def test_GetGateStatus_CuandoTrackerContieneHandoffHumano_DebeRetornarPendingDecision(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        service.append_decision("### [01-10-2026] Product Analyst\n- **Estado:** OK\n- **Handoff:** @HUMANO: El Product Brief está listo para revisión.")

        # Act
        response = client.get("/api/v1/gates/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING_DECISION"

    def test_GetGateStatus_CuandoTrackerNoTieneCompuertaPendiente_DebeRetornarApproved(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        service.append_decision("### [30-09-2026] Tech Lead\n- **Estado:** APPROVED\n- **Handoff:** @PM: Continuar ejecución")

        # Act
        response = client.get("/api/v1/gates/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"



class TestGatesApproveDecision:
    """Pruebas para el endpoint POST /api/v1/gates/{gate_id}/decision con APPROVE (US1 - Happy & Sad Paths)."""

    def test_MakeDecision_ConAccionApprove_DebeRegistrarDecisionYRetornar200(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "001"
        payload = {"action": "APPROVE"}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Decision recorded"
        # Verificar mutación atómica en el tracker
        tracker_content = service.read_tracker()
        assert f"DECISION [{gate_id}]: APPROVE" in tracker_content

    def test_MakeDecision_ConAccionApproveYFeedbackOpcional_DebeRegistrarAmbosYRetornar200(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "002"
        payload = {"action": "APPROVE", "feedback": "Excelente trabajo del equipo"}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 200
        tracker_content = service.read_tracker()
        assert f"DECISION [{gate_id}]: APPROVE" in tracker_content
        assert "Feedback: Excelente trabajo del equipo" in tracker_content


class TestGatesRejectDecision:
    """Pruebas para el endpoint POST /api/v1/gates/{gate_id}/decision con REJECT (US2 y US3)."""

    def test_MakeDecision_ConAccionRejectYFeedbackValido_DebeRegistrarDecisionYRetornar200(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "003"
        payload = {"action": "REJECT", "feedback": "Subsanar criterios de aceptación BDD"}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Decision recorded"
        tracker_content = service.read_tracker()
        assert f"DECISION [{gate_id}]: REJECT" in tracker_content
        assert "Feedback: Subsanar criterios de aceptación BDD" in tracker_content

    def test_MakeDecision_ConAccionRejectYTokenReservadoEnFeedback_DebeSanitizarTokenYRetornar200(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "004"
        payload = {"action": "REJECT", "feedback": "Corregir entregable antes de notificar a @PM: y @BA:"}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 200
        tracker_content = service.read_tracker()
        # Verificar que los tokens agénticos fueron sanitizados contra inyecciones no autorizadas
        assert "[@PM:_ESCAPED]" in tracker_content
        assert "[@BA:_ESCAPED]" in tracker_content
        # Confirmar que ningún token crudo quedó expuesto
        assert "@PM:" not in tracker_content.replace("[@PM:_ESCAPED]", "")
        assert "@BA:" not in tracker_content.replace("[@BA:_ESCAPED]", "")

    def test_MakeDecision_ConAccionRejectYSinFeedback_DebeRetornar422YNoModificarTracker(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "005"
        payload = {"action": "REJECT"}
        contenido_original = service.read_tracker()

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 422
        # Verificar que el tracker permanece intacto (Cero mutación parcial)
        assert service.read_tracker() == contenido_original

    def test_MakeDecision_ConAccionRejectYFeedbackVacio_DebeRetornar422YNoModificarTracker(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "006"
        payload = {"action": "REJECT", "feedback": ""}
        contenido_original = service.read_tracker()

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 422
        assert service.read_tracker() == contenido_original

    def test_MakeDecision_ConAccionRejectYFeedbackSoloEspacios_DebeRetornar422YNoModificarTracker(self, client_with_isolated_tracker):
        # Arrange
        client, service, _ = client_with_isolated_tracker
        gate_id = "007"
        payload = {"action": "REJECT", "feedback": "     \t "}
        contenido_original = service.read_tracker()

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 422
        assert service.read_tracker() == contenido_original


class TestGatesEdgeCasesAndSadPaths:
    """Pruebas para Casos Borde y Sad Paths generales (Acciones inválidas, payloads corruptos)."""

    def test_MakeDecision_ConAccionDesconocida_DebeRetornar422(self, client_with_isolated_tracker):
        # Arrange
        client, _, _ = client_with_isolated_tracker
        gate_id = "008"
        payload = {"action": "CANCEL"}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 422

    def test_MakeDecision_ConPayloadVacio_DebeRetornar422(self, client_with_isolated_tracker):
        # Arrange
        client, _, _ = client_with_isolated_tracker
        gate_id = "009"
        payload = {}

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/decision", json=payload)

        # Assert
        assert response.status_code == 422
