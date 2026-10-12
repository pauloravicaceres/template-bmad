"""Fase 4F-E4: preflight de una HU abierta por proyecto antes de aprobar una compuerta que genera BRANCH-CREATE."""
import json
import os
import shutil
import subprocess
import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import api.routes as routes
from core.config import ENGINE_ROOT, settings
from main import app
from bmad_runtime.context import ProjectContext
from bmad_runtime.state import StateStore
from bmad_runtime.watcher_service import read_tracker
from services.workflow_service import WorkflowService

HU_A, HU_B, HU_C = "001-registrar-cliente", "002-gestion-pagos", "003-reportes-ventas"


def pm_gate(hu):
    return ("### [11-10-2026] Product Manager\n- **Hora:** 10:00:00\n"
            "- **Artefacto generado:** `docs/product-manager/mvp-pagos.md`\n"
            f"- **Handoff:** @HUMANO: Revisa el MVP. La HU a delegar es {hu}.\n")


def opened(hu):
    return ("### [11-10-2026] HUMANO\n- **Hora:** 10:05:00\n- **Estado:** APPROVE\n"
            f"- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{hu}\n")


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CEILING_DIRECTORIES"] = str(root.parent)
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=BMAD Test", "-c", "user.email=bmad@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True, env=env)


@pytest.fixture
def ws():
    """Workspace del conftest con un repositorio Git real (el doble de GitService sigue activo para el dashboard)."""
    root = settings.WORKSPACE_ROOT
    shutil.rmtree(root / ".git")
    git(root, "init", "-q", "-b", "main")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "init")
    return root


@pytest.fixture
def tracker():
    return routes.tracker_service.writer.path


def mode(root, value):
    (root / "project.json").write_text(json.dumps({"schema_version": 1, "project_id": settings.PROJECT_ID, "config": {
        "ai": {"hu_lifecycle": {"mode": value}}}}), encoding="utf-8")


def context(root):
    return ProjectContext(ENGINE_ROOT, root, settings.PROJECT_ID)


def watcher_opened(root, tracker, hu):
    """Lo que deja el watcher tras abrir `hu`: la rama y el evento de la macro terminado en el SQLite del proyecto."""
    git(root, "branch", f"feat/{hu}")
    lines = read_tracker(tracker).lines
    number = max(i for i, line in enumerate(lines) if f"GITOPS-BRANCH-CREATE feat/{hu}" in line)
    store = StateStore(context(root))
    try:
        store.put("event:" + StateStore.fingerprint(number, lines[number]), {"state": "done"})
    finally:
        store.close()


def journal(root):
    store = StateStore.open_readonly(context(root))
    if store is None:
        return []
    try:
        return [key for key, _ in store.db.execute("SELECT id,data FROM records WHERE id LIKE 'tracker_append:%'")]
    finally:
        store.close()


def approve(client=None, **extra):
    return (client or TestClient(app)).post("/api/v1/gates/1/decision", json={"action": "APPROVE", **extra})


def test_free_project_is_approved_and_reports_the_decision(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A), encoding="utf-8")
    r = approve()
    assert r.status_code == 200 and r.json()["hu_lifecycle"]["code"] == "HU_OPEN_ALLOWED"
    assert f"@WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}" in tracker.read_text(encoding="utf-8")


def test_another_open_hu_is_409_and_nothing_is_recorded(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A) + opened(HU_A), encoding="utf-8")
    watcher_opened(ws, tracker, HU_A)
    with tracker.open("a", encoding="utf-8") as handle:
        handle.write(pm_gate(HU_B))
    before = tracker.read_bytes()
    r = approve()
    assert r.status_code == 409 and r.headers["X-BMAD-Error"] == "hu_open"
    body = r.json()
    assert body["error_code"] == "HU_OPEN_CONFLICT"
    assert (body["metadata"]["hu_lifecycle"]["code"], body["metadata"]["hu_lifecycle"]["open_hu"]) == \
        ("HU_ANOTHER_OPEN", HU_A)
    assert tracker.read_bytes() == before and journal(ws) == []


def test_pending_opening_of_another_hu_is_409(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A) + opened(HU_A) + pm_gate(HU_B), encoding="utf-8")   # el watcher aún no la procesó
    before = tracker.read_bytes()
    r = approve()
    assert r.status_code == 409 and r.json()["metadata"]["hu_lifecycle"]["code"] == "HU_OPENING_IN_PROGRESS"
    assert tracker.read_bytes() == before


def test_same_hu_is_idempotent(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A) + opened(HU_A), encoding="utf-8")
    watcher_opened(ws, tracker, HU_A)
    with tracker.open("a", encoding="utf-8") as handle:
        handle.write(pm_gate(HU_A))
    r = approve()
    assert r.status_code == 200 and r.json()["hu_lifecycle"]["code"] == "HU_OPEN_RESUME"


def test_uncertain_state_is_423_with_stable_code_and_evidence(ws, tracker):
    mode(ws, "enforce")
    git(ws, "branch", f"feat/{HU_C}")                       # rama sin historial: podría ser una HU abierta
    tracker.write_text(pm_gate(HU_A), encoding="utf-8")
    before = tracker.read_bytes()
    r = approve()
    assert r.status_code == 423 and r.headers["X-BMAD-Error"] == "hu_state"
    decision = r.json()["metadata"]["hu_lifecycle"]
    assert (r.json()["error_code"], decision["code"], decision["status"]) == \
        ("HU_STATE_BLOCKED", "HU_STATE_UNKNOWN", "unknown")
    assert any(cause.startswith("unresolved:") for cause in decision["causes"])
    assert tracker.read_bytes() == before and journal(ws) == []


def test_unreadable_project_json_blocks_instead_of_disabling_the_preflight(ws, tracker):
    """E4.1: un project.json ilegible no puede degradar en silencio un proyecto en enforce a observe."""
    (ws / "project.json").write_text('{"config": {"ai": {"hu_lifecycle": {"mode": "enfor', encoding="utf-8")
    tracker.write_text(pm_gate(HU_A), encoding="utf-8")
    before = tracker.read_bytes()
    r = approve()
    assert r.status_code == 423 and r.json()["error_code"] == "HU_STATE_BLOCKED"
    assert tracker.read_bytes() == before and journal(ws) == []


def test_observe_mode_keeps_the_previous_behaviour(ws, tracker):
    tracker.write_text(pm_gate(HU_A) + opened(HU_A), encoding="utf-8")
    watcher_opened(ws, tracker, HU_A)
    with tracker.open("a", encoding="utf-8") as handle:
        handle.write(pm_gate(HU_B))
    r = approve()                                           # sin project.json: observe por defecto
    assert r.status_code == 200 and "hu_lifecycle" not in r.json()
    assert f"GITOPS-BRANCH-CREATE feat/{HU_B}" in tracker.read_text(encoding="utf-8")


def test_double_concurrent_approval_emits_one_branch_create(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A), encoding="utf-8")
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
    assert [r.status_code for r in responses] == [200, 200]
    assert sorted(bool(r.json().get("replayed")) for r in responses) == [False, True]
    text = tracker.read_text(encoding="utf-8")
    assert text.count("GITOPS-BRANCH-CREATE") == 1 and text.count("@BA:") == 1


def test_replay_of_a_delivered_approval_is_not_blocked_by_the_hu_it_opened(ws, tracker):
    mode(ws, "enforce")
    tracker.write_text(pm_gate(HU_A), encoding="utf-8")
    assert approve().status_code == 200
    watcher_opened(ws, tracker, HU_A)                       # el watcher abrió la HU de esa aprobación
    r = approve()
    assert r.status_code == 200 and r.json()["replayed"] is True
    assert tracker.read_text(encoding="utf-8").count("GITOPS-BRANCH-CREATE") == 1
