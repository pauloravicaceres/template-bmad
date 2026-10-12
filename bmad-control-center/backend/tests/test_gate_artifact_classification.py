"""Fase 4F-E2: la aprobación clasifica el artefacto citado (bmad_runtime.artifacts) dentro de la transacción E1."""
import json

import pytest
from fastapi.testclient import TestClient

import api.routes as routes
from core.config import settings
from main import app


def bloque(autor, artefacto, handoff="@HUMANO: revisa el entregable"):
    return (f"### [10-10-2026] {autor}\n- **Hora:** 12:00:00\n- **Artefacto generado:** `{artefacto}`\n"
            f"- **Estado:** listo para revisión\n- **Handoff:** {handoff}\n")


@pytest.fixture
def ws():
    return settings.WORKSPACE_ROOT          # isolated per test by conftest


@pytest.fixture
def tracker():
    return routes.tracker_service.writer.path


def gate(tracker, autor, artefacto, handoff="@HUMANO: revisa el entregable"):
    tracker.write_text(bloque(autor, artefacto, handoff), encoding="utf-8")
    return tracker.read_bytes()


def write(root, relative, text="contenido"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def approve(**extra):
    return TestClient(app).post("/api/v1/gates/1/decision", json={"action": "APPROVE", **extra})


def test_present_artifact_is_approved_without_warnings(ws, tracker):
    write(ws, "docs/product-analyst/pb-reservas.md")
    gate(tracker, "Product Analyst", "docs/product-analyst/pb-reservas.md")
    r = approve()
    assert r.status_code == 200
    [artifact] = r.json()["artifacts"]
    assert (artifact["status"], artifact["path"]) == ("PRESENT", "docs/product-analyst/pb-reservas.md")
    assert r.json()["warnings"] == []
    assert "@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo pb-reservas.md" in \
        tracker.read_text(encoding="utf-8")


def test_missing_artifact_is_approved_with_a_structured_warning(tracker):
    gate(tracker, "Product Analyst", "docs/product-analyst/pb-reservas.md")
    r = approve()
    assert r.status_code == 200 and "@PM:" in tracker.read_text(encoding="utf-8")
    assert r.json()["warnings"] == [{
        "code": "ARTIFACT_MISSING", "status": "MISSING", "reference": "docs/product-analyst/pb-reservas.md",
        "path": "docs/product-analyst/pb-reservas.md", "gate": "product-analyst", "reason": "not_found",
        "detail": "docs/product-analyst/pb-reservas.md no existe en el workspace."}]


@pytest.mark.parametrize("artefacto, status", [
    ("../fuera/pb-reservas.md", "OUTSIDE"),
    ("docs/../../fuera/pb-reservas.md", "OUTSIDE"),
    ("\\\\servidor\\recurso\\pb-reservas.md", "OUTSIDE"),
    ("https://www.figma.com/file/x/Reservas", "OUTSIDE"),
    ("../beta/docs/product-analyst/pb-beta.md", "OTHER_PROJECT"),
])
def test_outside_and_other_project_artifacts_are_rejected_without_writing(ws, tracker, artefacto, status):
    beta = ws.parent / "beta"
    write(beta, "docs/product-analyst/pb-beta.md")
    (beta / "project.json").write_text(json.dumps({"schema_version": 1, "project_id": "beta"}), encoding="utf-8")
    before = gate(tracker, "Product Analyst", artefacto)
    r = approve()
    assert r.status_code == 422 and r.headers["X-BMAD-Error"] == "artifact"
    assert (r.json()["error_code"], r.json()["metadata"]["artifact"]["status"]) == ("ARTIFACT_REJECTED", status)
    assert tracker.read_bytes() == before


def test_ambiguous_bare_name_is_rejected_with_its_candidates(ws, tracker):
    write(ws, "docs/product-analyst/pb-reservas.md")
    write(ws, "docs/product-analyst/v2/pb-reservas.md")
    before = gate(tracker, "Product Analyst", "pb-reservas.md")
    r = approve()
    assert r.status_code == 422 and r.json()["metadata"]["artifact"]["candidates"] == [
        "docs/product-analyst/pb-reservas.md", "docs/product-analyst/v2/pb-reservas.md"]
    assert tracker.read_bytes() == before


def test_a_unique_bare_name_is_resolved_and_its_path_reported(ws, tracker):
    write(ws, "docs/product-analyst/pb-reservas.md")
    gate(tracker, "Product Analyst", "pb-reservas.md")
    r = approve()
    assert r.status_code == 200 and r.json()["artifacts"][0]["path"] == "docs/product-analyst/pb-reservas.md"


def test_figma_is_external_allowed_only_in_the_ux_gate(tracker):
    url = "https://www.figma.com/file/AbC123/Reservas"
    gate(tracker, "Designer UX", url)
    r = approve()
    assert r.status_code == 200 and r.json()["artifacts"][0]["status"] == "EXTERNAL_ALLOWED"
    assert f"@SA: El diseño visual ha sido aprobado en {url}." in tracker.read_text(encoding="utf-8")
    # A later UX gate (appended: rewriting the tracker would lose the journaled decision, an E1.1 incident).
    with tracker.open("a", encoding="utf-8") as handle:
        handle.write("\n" + bloque("Designer UX", "https://figma.com.evil.com/file/x"))
    before = tracker.read_bytes()
    rejected = approve()
    assert rejected.status_code == 422 and rejected.json()["metadata"]["artifact"]["reason"] == "host_not_allowed"
    assert tracker.read_bytes() == before


def test_the_pm_gate_reports_the_future_hu_of_the_next_stage(ws, tracker):
    write(ws, "docs/product-manager/mvp-pagos.md")
    gate(tracker, "Product Manager", "docs/product-manager/mvp-pagos.md",
         "@HUMANO: Revisa el MVP. La HU a delegar es 004-gestion-pagos.")
    r = approve()
    assert r.status_code == 200
    assert [(a["status"], a["path"]) for a in r.json()["artifacts"]] == [
        ("PRESENT", "docs/product-manager/mvp-pagos.md"), ("FUTURE", "docs/business-analyst/004-gestion-pagos.md")]
    assert r.json()["warnings"] == []


def test_a_missing_mvp_is_never_future(tracker):
    gate(tracker, "Product Manager", "docs/product-manager/mvp-pagos.md",
         "@HUMANO: Revisa el MVP. La HU a delegar es 004-gestion-pagos.")
    assert [a["status"] for a in approve().json()["artifacts"]] == ["MISSING", "FUTURE"]


def test_hu_naming_is_checked_before_the_location(ws, tracker):
    write(ws, "docs/business-analyst/003-gestion_clientes.md")
    before = gate(tracker, "Business Analyst", "docs/business-analyst/003-gestion_clientes.md")
    r = approve()
    assert r.status_code == 422 and "snake_case" in r.json()["detail"] and tracker.read_bytes() == before
    before = gate(tracker, "Business Analyst", "../otro/docs/business-analyst/003-gestion-clientes.md")
    r = approve()
    assert r.status_code == 422 and r.json()["error_code"] == "ARTIFACT_REJECTED" and tracker.read_bytes() == before


def test_undeclared_artifact_keeps_its_previous_422(tracker):
    before = gate(tracker, "Product Analyst", "ninguno")
    r = approve()
    assert r.status_code == 422 and "Artefacto generado" in r.json()["detail"] and tracker.read_bytes() == before


def test_replay_and_e1_errors_are_unchanged(ws, tracker):
    write(ws, "docs/product-analyst/pb-reservas.md")
    gate(tracker, "Product Analyst", "docs/product-analyst/pb-reservas.md")
    assert approve().status_code == 200
    replay = approve()
    assert replay.json() == {"message": "Decision recorded", "replayed": True}
    assert tracker.read_text(encoding="utf-8").count("] HUMANO") == 1
    routes.tracker_service.writer.grace = 0
    tracker.write_text(bloque("Product Analyst", "docs/product-analyst/pb-reservas.md"), encoding="utf-8")
    lost = approve()
    assert lost.status_code == 423 and lost.json()["error_code"] == "TRACKER_INTEGRITY"


def test_policy_off_restores_the_previous_behaviour(tracker, monkeypatch):
    import bmad_runtime.artifacts as artifacts
    monkeypatch.setattr(artifacts, "load_policy", lambda root: artifacts.policy_from_config({"mode": "off"}))
    gate(tracker, "Product Analyst", "../fuera/pb-reservas.md")
    r = approve()
    assert r.status_code == 200 and "artifacts" not in r.json()
