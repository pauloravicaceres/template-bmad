"""Fase 4F-E1: la decisión de una compuerta se lee, valida y registra bajo el lock del tracker del proyecto."""
import json
import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import api.routes as routes
from bmad_runtime import workflow
from bmad_runtime.state import ProjectLock, StateStore
from bmad_runtime.tracker_io import TrackerConflict
from main import app
from services.tracker_service import TrackerService
from services.workflow_service import WorkflowService

PM = ("### [11-10-2026] Product Manager\n- **Hora:** 10:00:00\n"
      "- **Artefacto generado:** `docs/product-manager/mvp-pagos.md`\n"
      "- **Handoff:** @HUMANO: Revisa el MVP. La HU a delegar es 004-gestion-pagos.\n")


@pytest.fixture
def tracker():
    path = routes.tracker_service.writer.path      # isolated by conftest
    path.write_text(PM, encoding="utf-8")
    return path


def journal(service):
    store = StateStore.in_directory(service.writer.state_dir)
    try:
        return [json.loads(raw) for _, raw in store.db.execute("SELECT id,data FROM records WHERE id LIKE 'tracker_append:%'")]
    finally:
        store.close()


def approve(client=None, **extra):
    return (client or TestClient(app)).post("/api/v1/gates/1/decision", json={"action": "APPROVE", **extra})


def test_two_simultaneous_approvals_emit_one_branch_and_one_handoff(tracker):
    """R2 regression: with the read window widened, both requests used to emit BRANCH-CREATE + @BA."""
    original = WorkflowService._parse_blocks

    def slow(self, content):
        blocks = original(self, content)
        time.sleep(0.3)
        return blocks

    barrier, responses = threading.Barrier(2), []

    def post():
        client = TestClient(app)
        barrier.wait()
        responses.append(approve(client))

    with patch.object(WorkflowService, "_parse_blocks", slow):
        threads = [threading.Thread(target=post) for _ in range(2)]
        [t.start() for t in threads]
        [t.join() for t in threads]

    text = tracker.read_text(encoding="utf-8")
    assert [r.status_code for r in responses] == [200, 200]
    assert sorted(bool(r.json().get("replayed")) for r in responses) == [False, True]
    assert text.count("GITOPS-BRANCH-CREATE") == 1 and text.count("@BA:") == 1 and text.count("] HUMANO") == 1


def test_repeating_the_same_decision_is_idempotent(tracker):
    assert approve().status_code == 200
    second = approve()
    assert second.status_code == 200 and second.json()["replayed"] is True
    assert tracker.read_text(encoding="utf-8").count("] HUMANO") == 1


def test_a_different_decision_after_the_handoff_is_rejected_without_writing(tracker):
    assert approve().status_code == 200
    before = tracker.read_bytes()
    response = TestClient(app).post("/api/v1/gates/1/decision", json={"action": "REJECT", "feedback": "cambio de idea"})
    assert response.status_code == 409 and "ya fue resuelta" in response.json()["detail"]
    assert tracker.read_bytes() == before


def test_reject_then_approve_on_the_same_gate_is_still_allowed(tracker):
    client = TestClient(app)
    assert client.post("/api/v1/gates/1/decision", json={"action": "REJECT", "feedback": "falta alcance"}).status_code == 200
    assert approve(client).status_code == 200
    assert tracker.read_text(encoding="utf-8").count("] HUMANO") == 2


def test_retry_after_a_crash_between_write_and_confirmation_is_a_replay(tracker):
    client = TestClient(app, raise_server_exceptions=False)
    with patch("bmad_runtime.tracker_io.locate", side_effect=RuntimeError("process died after writing")):
        assert approve(client).status_code == 500
    assert [r["state"] for r in journal(routes.tracker_service)] == ["in_flight"]
    retry = approve(client)
    assert retry.status_code == 200 and retry.json()["replayed"] is True
    text = tracker.read_text(encoding="utf-8")
    assert text.count("GITOPS-BRANCH-CREATE") == 1 and text.count("] HUMANO") == 1
    assert [r["state"] for r in journal(routes.tracker_service)] == ["done"]


def test_busy_tracker_returns_503_without_writing(tracker, monkeypatch):
    service = TrackerService(str(tracker), timeout=0.2)
    monkeypatch.setattr(routes, "tracker_service", service)
    other = ProjectLock.at(service.writer.state_dir / "tracker.lock")
    assert other.acquire()
    try:
        response = approve()
    finally:
        other.release()
    assert response.status_code == 503
    assert tracker.read_text(encoding="utf-8") == PM


def test_lock_is_released_before_the_websocket_broadcast(tracker):
    seen = []

    def status(self):
        lock = ProjectLock.at(routes.tracker_service.writer.state_dir / "tracker.lock")
        seen.append(lock.acquire())
        lock.release()
        raise RuntimeError("broadcast skipped in test")

    with patch.object(WorkflowService, "get_workflow_status", status):
        assert approve().status_code == 200
    assert seen == [True]


def test_merge_conflict_alert_is_a_pending_human_gate(tracker):
    tracker.write_text("### [11-10-2026] Code Review\n- **Hora:** 12:00:00\n"
                       "@WATCHER: GITOPS-MERGE-CLOSE feat/004-gestion-pagos\n- **Handoff:** @PM: HU cerrada.\n"
                       + workflow.alerta_conflicto_gitops("feat/004-gestion-pagos", "main",
                                                          "python -m bmad_runtime.state --acknowledge event:x --confirm"),
                       encoding="utf-8")
    last = WorkflowService()._parse_blocks(tracker.read_text(encoding="utf-8"))[-1]
    assert (last["author_role"], last["merge_close"]) == ("WATCHER", None)
    assert TestClient(app).get("/api/v1/gates/status").json()["status"] == "PENDING_DECISION"


def test_projects_do_not_share_the_decision_lock(tmp_path):
    alpha = tmp_path / "alfa" / "handoffs" / "tracker_bmad.md"
    beta = tmp_path / "beta" / "handoffs" / "tracker_bmad.md"
    service_a, service_b = TrackerService(str(alpha), timeout=0.2), TrackerService(str(beta), timeout=0.2)
    assert service_a.writer.state_dir != service_b.writer.state_dir
    with service_a.transaction():
        service_b.append_decision("### [11-10-2026] HUMANO\n- **Estado:** APPROVE")
    assert "APPROVE" in beta.read_text(encoding="utf-8") and not alpha.exists()


# ----------------------------------------------------------------------------- Fase 4F-E1.1
def lose_the_decision(tracker):
    """APPROVE, then an agent's whole-file rewrite drops the HUMANO block and its BRANCH-CREATE."""
    routes.tracker_service.writer.grace = 0
    first = approve()
    assert first.status_code == 200 and "replayed" not in first.json()
    tracker.write_text(PM, encoding="utf-8")
    detected = approve()
    assert detected.status_code == 423 and detected.headers["X-BMAD-Error"] == "integrity"
    [key] = routes.tracker_service.writer.audit()[1]
    assert key in detected.json()["detail"]
    return key


def test_lost_and_acknowledged_decision_is_never_replayed(tracker):
    """E1 defect: after the acknowledgement the same APPROVE answered 200 replayed with nothing in the tracker."""
    key = lose_the_decision(tracker)
    writer = routes.tracker_service.writer
    writer.acknowledge(key)                      # == python -m bmad_runtime.state --acknowledge <key> --confirm
    retry = approve()
    assert retry.status_code == 423 and retry.headers["X-BMAD-Error"] == "integrity"
    assert "requiere reconciliación" in retry.json()["detail"] and "--reconcile" in retry.json()["detail"]
    assert retry.json()["error_code"] == "TRACKER_INTEGRITY" and retry.json()["metadata"]["operations"] == [key]
    assert "replayed" not in retry.text
    assert tracker.read_text(encoding="utf-8") == PM, "no automatic second handoff"
    pending = [r for r in journal(routes.tracker_service) if r["state"] != "done"]
    assert [(r["state"], bool(r["acknowledged"])) for r in pending] == [("lost", True)]


def test_an_authorized_reissue_records_the_decision_once(tracker):
    key = lose_the_decision(tracker)
    writer = routes.tracker_service.writer
    writer.acknowledge(key)
    assert writer.reconcile(key)["outcome"] == "absent"
    writer.authorize_reissue(key)
    reissued = approve()
    assert reissued.status_code == 200 and reissued.json()["reissued"] is True and "replayed" not in reissued.json()
    again = approve()
    assert again.status_code == 200 and again.json()["replayed"] is True
    text = tracker.read_text(encoding="utf-8")
    assert text.count("] HUMANO") == 1 and text.count("GITOPS-BRANCH-CREATE") == 1 and text.count("@BA:") == 1
    [record] = [r for r in journal(routes.tracker_service) if r.get("lost_evidence")]
    assert record["resolution"]["kind"] == "reissued" and record["history"][0]["event"] == "done->lost"


def test_an_accepted_loss_is_not_reissued_by_the_same_approval(tracker):
    key = lose_the_decision(tracker)
    writer = routes.tracker_service.writer
    writer.acknowledge(key)
    writer.accept_loss(key)
    retry = approve()
    assert retry.status_code == 423 and "pérdida se cerró" in retry.json()["detail"]
    assert tracker.read_text(encoding="utf-8") == PM


def test_the_restored_original_answers_the_authorized_retry_as_a_replay(tracker):
    routes.tracker_service.writer.grace = 0
    assert approve().status_code == 200
    original = tracker.read_bytes()
    tracker.write_text(PM, encoding="utf-8")
    assert approve().status_code == 423
    writer = routes.tracker_service.writer
    [key] = writer.audit()[1]
    writer.acknowledge(key)
    writer.authorize_reissue(key)
    tracker.write_bytes(original)                # the agent restores an older read that still had the decision
    retry = approve()
    assert retry.status_code == 200 and retry.json()["replayed"] is True
    text = tracker.read_text(encoding="utf-8")
    assert text.count("] HUMANO") == 1 and text.count("GITOPS-BRANCH-CREATE") == 1


def test_error_kinds_are_distinguishable(tracker, monkeypatch):
    assert approve().status_code == 200
    conflict = TestClient(app).post("/api/v1/gates/1/decision", json={"action": "REJECT", "feedback": "otra"})
    assert conflict.status_code == 409 and conflict.headers["X-BMAD-Error"] == "conflict"
    service = TrackerService(str(tracker), timeout=0.2)
    monkeypatch.setattr(routes, "tracker_service", service)
    reconciling = ProjectLock.at(service.writer.state_dir / "tracker.lock")    # state CLI reconciling
    assert reconciling.acquire()
    try:
        busy = approve()
    finally:
        reconciling.release()
    assert busy.status_code == 503 and busy.headers["X-BMAD-Error"] == "busy"
    assert (conflict.json()["error_code"], busy.json()["error_code"]) == ("DECISION_CONFLICT", "TRACKER_BUSY")


def test_cli_approval_after_a_control_center_decision_is_rejected(tracker, monkeypatch):
    from utils import approve_step
    monkeypatch.setattr(approve_step, "TRACKER_PATH", tracker)
    reviewed = tracker.stat().st_size            # the operator opens approve_step
    assert approve().status_code == 200          # meanwhile the Control Center approves
    before = tracker.read_bytes()
    with pytest.raises(TrackerConflict):
        approve_step.registrar_aprobacion("@WATCHER: GITOPS-BRANCH-CREATE feat/004-gestion-pagos\n@BA: empieza",
                                          "mvp-pagos.md", reviewed)
    assert tracker.read_bytes() == before
