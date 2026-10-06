from services.workflow_service import WorkflowService

CICLO_SIN_UX = """
### [03-10-2026] HUMANO
- **Hora:** 09:10:00
- **Estado:** APPROVE
- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/005-HU_api_pura
@BA: arranca
### [03-10-2026] Business Analyst
- **Hora:** 09:20:00
- **Handoff:** @QA: audita
### [03-10-2026] QA Documental
- **Hora:** 09:30:00
- **Handoff:** @UX: diseña
### [03-10-2026] WATCHER
- **Hora:** 09:40:00
- **Mensaje:** ⏭️ [UX] Diseño UX omitido: la HU declara 'Requiere interfaz: No'.
- **Handoff:** @SA: La especificación inicial SDD ha concluido con éxito y el diseño UX se omite. Procede con el tech-design.
"""


def _stages(tmp_path, texto):
    tracker = tmp_path / "tracker_bmad.md"
    tracker.write_text(texto, encoding="utf-8")
    resp = WorkflowService(tracker).get_workflow_status()
    return resp, {s.stage_key: s for s in resp.stages}


def test_la_etapa_ux_omitida_se_marca_skipped_y_no_pendiente(tmp_path):
    resp, st = _stages(tmp_path, CICLO_SIN_UX)

    assert st["UX"].status == "SKIPPED" and not st["UX"].is_active
    assert st["QA"].status == "COMPLETED"
    assert st["SA"].status != "SKIPPED"


def test_la_etapa_omitida_cuenta_como_avance(tmp_path):
    con_omision, _ = _stages(tmp_path, CICLO_SIN_UX)
    sin_omision, _ = _stages(tmp_path, CICLO_SIN_UX.replace("Diseño UX omitido", "Diseño pendiente"))

    assert con_omision.completed_stages == sin_omision.completed_stages + 1


def test_sin_bloque_de_omision_la_etapa_ux_sigue_pendiente(tmp_path):
    _, st = _stages(tmp_path, CICLO_SIN_UX.replace("Diseño UX omitido", "Diseño pendiente"))

    assert st["UX"].status != "SKIPPED"
