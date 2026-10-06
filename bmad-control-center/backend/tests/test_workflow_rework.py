from services.workflow_service import WorkflowService

FASES_PREVIAS = """
### [03-10-2026] Product Manager
- **Hora:** 09:00:00
- **Handoff:** @BA: sigue
### [03-10-2026] Business Analyst
- **Hora:** 09:01:00
- **Handoff:** @QA: sigue
### [03-10-2026] QA Documental
- **Hora:** 09:02:00
- **Handoff:** @UX: sigue
### [03-10-2026] Designer UX
- **Hora:** 09:03:00
- **Handoff:** @SA: sigue
### [03-10-2026] Solutions Architect
- **Hora:** 09:04:00
- **Handoff:** @DA: sigue
### [03-10-2026] Data Architect
- **Hora:** 09:05:00
- **Handoff:** @API: sigue
### [03-10-2026] API Architect
- **Hora:** 09:06:00
- **Handoff:** @QT: sigue
### [03-10-2026] QA Tech
- **Hora:** 09:07:00
- **Handoff:** @DEV-BACK: la arquitectura fue validada
### [03-10-2026] WATCHER
- **Hora:** 09:08:00
- **Mensaje:** ⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...
### [03-10-2026] Senior Backend Developer
- **Hora:** 09:09:00
- **Handoff:** @DEV-FRONT: Inicia implementación frontend.
### [03-10-2026] WATCHER
- **Hora:** 09:10:00
- **Mensaje:** ⚡ [SDD Auto-Runner] Ejecutando implementación Frontend (/speckit.implement)...
### [03-10-2026] Senior Frontend Developer
- **Hora:** 09:11:00
- **Handoff:** @QA-AUTO: Inicia pruebas.
### [03-10-2026] QA Automation
- **Hora:** 09:12:00
- **Estado:** Pruebas aprobadas.
- **Handoff:** @CODE-REVIEW: audita.
"""

RECHAZO = """
### [03-10-2026] Code Review
- **Hora:** 09:13:00
- **Estado:** [RECHAZADO] Falta ValidationBehavior.
- **Handoff:** @DEV-BACK: corrige los hallazgos 1 a 4. @DEV-FRONT: corrige los hallazgos 5 a 8. @QA-AUTO: revalida.
"""


def _stages(tmp_path, texto):
    tracker = tmp_path / "tracker_bmad.md"
    tracker.write_text(texto, encoding="utf-8")
    resp = WorkflowService(tracker).get_workflow_status()
    return resp, {s.stage_key: s for s in resp.stages}


def test_rechazo_de_code_review_marca_rechazado_y_reabre_las_etapas_dev(tmp_path):
    resp, st = _stages(tmp_path, FASES_PREVIAS + RECHAZO)

    assert resp.overall_status == "IN_PROGRESS"
    assert resp.rework["origin_stage"] == "CR"
    assert resp.rework["pending_stages"] == ["DEV-BACK", "DEV-FRONT", "QA-AUTO"]
    assert st["CR"].rework_state == "REJECTED"
    assert st["DEV-BACK"].rework_state == "REWORK" and st["DEV-BACK"].status == "IN_PROGRESS"  # primer destinatario del handoff
    assert st["DEV-FRONT"].rework_state == "REWORK" and st["DEV-FRONT"].status == "PENDING"
    assert st["QA-AUTO"].rework_state == "REWORK" and st["QA-AUTO"].status == "PENDING"


def test_el_watcher_en_retrabajo_mantiene_w_imp_activo_y_lee_la_iteracion(tmp_path):
    watcher = """
### [03-10-2026] WATCHER
- **Hora:** 09:14:00
- **Mensaje:** 🔁 [SDD Retrabajo] Iteración 1/2 (origen: Code Review). Reconciliando spec, plan y tasks (/speckit-converge)...
### [03-10-2026] WATCHER
- **Hora:** 09:15:00
- **Mensaje:** ⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...
"""
    resp, st = _stages(tmp_path, FASES_PREVIAS + RECHAZO + watcher)

    assert resp.active_stage == "W-IMP"
    assert st["W-IMP"].status == "IN_PROGRESS"
    assert st["DEV-BACK"].status == "IN_PROGRESS"  # el watcher ejecuta el backend
    assert st["DEV-FRONT"].status == "PENDING" and st["DEV-FRONT"].rework_state == "REWORK"  # el frontend espera su turno
    assert st["DEV-BACK"].rework_iteration == 1 and st["DEV-BACK"].rework_max == 2


def test_sin_rechazo_no_hay_retrabajo(tmp_path):
    resp, st = _stages(tmp_path, FASES_PREVIAS)

    assert resp.rework is None
    assert all(s.rework_state is None for s in resp.stages)


def test_aprobacion_posterior_cierra_el_retrabajo(tmp_path):
    aprobado = """
### [03-10-2026] Code Review
- **Hora:** 09:30:00
- **Estado:** APROBADO.
- **Handoff:** @WATCHER: GITOPS-MERGE-CLOSE feat/x
"""
    resp, _ = _stages(tmp_path, FASES_PREVIAS + RECHAZO + aprobado)

    assert resp.rework is None
