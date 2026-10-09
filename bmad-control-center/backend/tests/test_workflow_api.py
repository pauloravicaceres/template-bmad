import pytest
from fastapi.testclient import TestClient
from main import app
from services.workflow_service import WorkflowService
import api.workflow as workflow_module


@pytest.fixture
def isolated_workflow_client(tmp_path):
    """Fixture providing a TestClient with WorkflowService pointing to a temporary tracker file."""
    temp_tracker = tmp_path / "tracker_bmad.md"
    temp_service = WorkflowService(tracker_path=temp_tracker)
    workflow_module.workflow_service = temp_service
    client = TestClient(app)
    return client, temp_service, temp_tracker


class TestWorkflowApi:
    """Tests for GET /api/v1/workflow/status and /api/v1/workflow/state (US1)."""

    def test_get_workflow_status_when_tracker_does_not_exist_returns_idle(self, isolated_workflow_client):
        client, _, _ = isolated_workflow_client

        response = client.get("/api/v1/workflow/status")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "IDLE"
        assert data["total_stages"] == 15
        assert data["completed_stages"] == 0
        assert len(data["stages"]) == 15
        assert all(s["status"] == "PENDING" for s in data["stages"])

    def test_get_workflow_state_alias_returns_same_data_and_contract_fields(self, isolated_workflow_client):
        client, _, temp_tracker = isolated_workflow_client
        content = """
### [30-09-2026] Product Manager
- **Hora:** 23:10:00
- **Artefacto generado:** `specs/README.md`
- **Estado:** Épica asignada
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @BA: Delegar refinamiento funcional
"""
        temp_tracker.write_text(content.strip(), encoding="utf-8")

        response = client.get("/api/v1/workflow/state")

        assert response.status_code == 200
        data = response.json()
        assert data["active_stage"] == "BA"
        assert data["active_agent_role"] == "Business Analyst"
        assert data["overall_status"] == "IN_PROGRESS"
        assert data["completed_stages"] == 1
        # Interoperability fields
        assert "current_stage" in data
        assert "status" in data
        assert "history" in data

    def test_get_workflow_status_parses_in_progress_stage_correctly(self, isolated_workflow_client):
        client, _, temp_tracker = isolated_workflow_client
        tracker_text = """
### [30-09-2026] Product Manager
- **Hora:** 23:10:00
- **Artefacto generado:** `specs/README.md`
- **Estado:** Épica lista
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @BA: Refinar

### [30-09-2026] Business Analyst
- **Hora:** 23:14:00
- **Artefacto generado:** `documents/business-analyst/002-HU.md`
- **Estado:** BDD completado
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @QA: Auditoría documental

### [30-09-2026] QA Documental
- **Hora:** 23:18:00
- **Artefacto generado:** `documents/qa-documental/aprobado_002.md`
- **Estado:** Aprobado 100%
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @UX: Diseñar wireframes
"""
        temp_tracker.write_text(tracker_text.strip(), encoding="utf-8")

        response = client.get("/api/v1/workflow/status?include_history=true")

        assert response.status_code == 200
        data = response.json()
        assert data["active_stage"] == "UX"
        assert data["active_agent_role"] == "Designer UX"
        assert data["completed_stages"] == 3
        assert len(data["history"]) == 3

        # Verify stages list
        stages = {s["stage_key"]: s for s in data["stages"]}
        assert stages["PM"]["status"] == "COMPLETED"
        assert stages["BA"]["status"] == "COMPLETED"
        assert stages["QA"]["status"] == "COMPLETED"
        assert stages["UX"]["status"] == "IN_PROGRESS"
        assert stages["UX"]["is_active"] is True
        assert stages["SA"]["status"] == "PENDING"

    def test_get_workflow_status_when_pipeline_completed(self, isolated_workflow_client):
        client, _, temp_tracker = isolated_workflow_client
        tracker_text = """
### [30-09-2026] SecOps
- **Hora:** 23:47:30
- **Artefacto generado:** `documents/qa-tech/tech-design_002.md`
- **Estado:** Auditoría Adversarial Exitosa
- **⚠️ Puntos Abiertos:** Ninguno
- **Handoff:** @WATCHER: GITOPS-MERGE-CLOSE feat/001-HU_prueba
"""
        temp_tracker.write_text(tracker_text.strip(), encoding="utf-8")

        response = client.get("/api/v1/workflow/status")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "COMPLETED"
        assert data["active_stage"] == "COMPLETED"
