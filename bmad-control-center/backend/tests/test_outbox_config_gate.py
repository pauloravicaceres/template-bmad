"""Fase 4F-E5 §11: el Control Center no acepta lo que el watcher en ejecución (otro --config) rechazaría."""
import time

from bmad_runtime.policy_audit import RECORD
from bmad_runtime.state import StateStore
from bmad_runtime.watcher_service import SESSION_PROTOCOL
from test_hu_enforcement_gate import (HU_A, HU_B, approve, context, journal, opened, pm_gate,  # noqa: F401
                                            tracker, watcher_opened, ws)


def running_watcher(root, hu_mode, heartbeat=None):
    """Lo que deja un watcher arrancado con `--config` propio: sus políticas y un latido."""
    store = StateStore(context(root))
    try:
        store.put(RECORD, {'config_source': str(root / 'scratch.json'), 'pid': 1, 'time': time.time(),
                           'policies': {'outbox': 'direct', 'outbox_agents': [], 'hu_lifecycle': hu_mode,
                                        'artifacts': 'warn', 'guard': 'observe'}})
        store.put('watcher', {'pid': 1, 'protocol': SESSION_PROTOCOL, 'started': time.time(),
                              'heartbeat': time.time() if heartbeat is None else heartbeat})
    finally:
        store.close()


def second_hu(ws, tracker):
    tracker.write_text(pm_gate(HU_A) + opened(HU_A), encoding="utf-8")
    watcher_opened(ws, tracker, HU_A)
    with tracker.open("a", encoding="utf-8") as handle:
        handle.write(pm_gate(HU_B))


def test_running_watcher_in_enforce_makes_the_gate_enforce(ws, tracker):
    second_hu(ws, tracker)                                   # sin project.json: el Control Center calcula observe
    running_watcher(ws, "enforce")
    before = tracker.read_bytes()
    r = approve()
    assert r.status_code == 409 and r.json()["metadata"]["hu_lifecycle"]["code"] == "HU_ANOTHER_OPEN"
    assert tracker.read_bytes() == before and journal(ws) == []


def test_stale_or_observing_watcher_keeps_the_configured_mode(ws, tracker):
    second_hu(ws, tracker)
    running_watcher(ws, "enforce", heartbeat=time.time() - 3600)      # watcher detenido hace una hora
    r = approve()
    assert r.status_code == 200 and "hu_lifecycle" not in r.json()


def test_watcher_in_observe_never_relaxes_an_enforce_project(ws, tracker):
    (ws / "project.json").write_text('{"schema_version": 1, "project_id": "%s", "config": {"ai": {"hu_lifecycle": '
                                     '{"mode": "enforce"}}}}' % context(ws).project_id, encoding="utf-8")
    second_hu(ws, tracker)
    running_watcher(ws, "observe")
    r = approve()
    assert r.status_code == 409
