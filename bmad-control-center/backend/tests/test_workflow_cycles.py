from services.workflow_service import WorkflowService

CICLO_1_COMPLETO = """
### [03-10-2026] Product Manager
- **Hora:** 09:00:00
- **Handoff:** @HUMANO: valida las épicas
### [03-10-2026] HUMANO
- **Hora:** 09:10:00
- **Estado:** APPROVE
- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/001-HU_a
@BA: arranca
### [03-10-2026] Business Analyst
- **Hora:** 09:20:00
- **Handoff:** @QA: audita
### [03-10-2026] QA Documental
- **Hora:** 09:30:00
- **Handoff:** @UX: diseña
### [03-10-2026] Designer UX
- **Hora:** 09:40:00
- **Handoff:** @SA: arquitectura
### [03-10-2026] Solutions Architect
- **Hora:** 09:50:00
- **Handoff:** @DA: modelo
### [03-10-2026] Data Architect
- **Hora:** 10:00:00
- **Handoff:** @API: contratos
### [03-10-2026] API Architect
- **Hora:** 10:10:00
- **Handoff:** @QT: audita
### [03-10-2026] QA Tech
- **Hora:** 10:20:00
- **Handoff:** @DEV-BACK: arquitectura validada
### [03-10-2026] Senior Backend Developer
- **Hora:** 10:30:00
- **Handoff:** @DEV-FRONT: sigue
### [03-10-2026] Senior Frontend Developer
- **Hora:** 10:40:00
- **Handoff:** @QA-AUTO: pruebas
### [03-10-2026] QA Automation
- **Hora:** 10:50:00
- **Handoff:** @CODE-REVIEW: revisa
### [03-10-2026] Code Review
- **Hora:** 11:00:00
- **Estado:** APROBADO
- **Handoff:** @PM: siguiente historia
"""

PM_ABRE_CICLO_2 = """
### [03-10-2026] Product Manager
- **Hora:** 11:10:00
- **Estado:** Ledger actualizado.
@WATCHER: GITOPS-BRANCH-CREATE feat/002-HU_b
- **Handoff:** @BA: Iniciar el análisis de la épica 002.
"""


def _stages(tmp_path, texto):
    tracker = tmp_path / "tracker_bmad.md"
    tracker.write_text(texto, encoding="utf-8")
    resp = WorkflowService(tracker).get_workflow_status()
    return resp, {s.stage_key: s for s in resp.stages}


def test_una_hu_completa_se_ve_con_todas_las_etapas_en_verde(tmp_path):
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO)

    assert st["PM"].status == "COMPLETED" and st["BA"].status == "COMPLETED"
    assert st["QA-AUTO"].status == "COMPLETED" and st["CR"].status == "COMPLETED"


def test_al_abrir_la_hu_siguiente_el_pipeline_se_reinicia(tmp_path):
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO + PM_ABRE_CICLO_2)

    assert resp.active_stage == "BA"
    assert resp.overall_status == "IN_PROGRESS"
    assert st["PM"].status == "COMPLETED"
    assert st["BA"].status == "IN_PROGRESS" and st["BA"].is_active
    for clave in ("QA", "UX", "SA", "DA", "API", "QT", "DEV-BACK", "DEV-FRONT", "QA-AUTO", "CR"):
        assert st[clave].status == "PENDING", f"{clave} no debe arrastrar el verde de la HU anterior"
    assert resp.completed_stages == 1


def test_el_historial_conserva_todos_los_ciclos(tmp_path):
    resp, _ = _stages(tmp_path, CICLO_1_COMPLETO + PM_ABRE_CICLO_2)

    assert len(resp.history) == 14  # 13 bloques de la HU anterior + el PM que abre la siguiente
    assert resp.history[0]["author_role"] == "Product Manager"
    assert resp.history[-1]["author_role"] == "Product Manager"


def test_cuando_la_macro_esta_en_el_bloque_humano_el_pm_previo_se_conserva(tmp_path):
    # Primer ciclo real: el PM termina y la macro la emite el HUMANO que aprueba. El PM debe seguir en verde.
    texto = CICLO_1_COMPLETO.split("### [03-10-2026] Business Analyst")[0] + """
### [03-10-2026] Business Analyst
- **Hora:** 09:20:00
- **Handoff:** @QA: audita
"""
    resp, st = _stages(tmp_path, texto)

    assert st["PM"].status == "COMPLETED"
    assert st["BA"].status == "COMPLETED"
    assert resp.active_stage == "QA"


HU_SIN_PM_TRAS_CIERRE = """
### [05-10-2026] HUMANO
- **Hora:** 08:00:00
- **Estado:** APPROVE
- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/035-HU_ui
@BA: deuda técnica
### [05-10-2026] Business Analyst
- **Hora:** 08:31:00
- **Handoff:** @QA: audita
### [05-10-2026] QA Documental
- **Hora:** 08:48:00
- **Handoff:** @UX: diseña
### [05-10-2026] Diseñador UX
- **Hora:** 08:57:10
- **Handoff:** @SA: arquitectura
"""


def test_una_hu_abierta_sin_bloque_de_pm_no_arrastra_el_ciclo_cerrado(tmp_path):
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO + CIERRE_CON_AVISO_A_HUMANO + HU_SIN_PM_TRAS_CIERRE)

    assert resp.overall_status == "IN_PROGRESS"
    assert resp.active_stage == "SA"
    assert st["SA"].status == "IN_PROGRESS" and st["SA"].is_active
    assert st["UX"].status == "COMPLETED", "'Diseñador UX' también es la etapa UX"
    for clave in ("DA", "API", "QT", "DEV-BACK", "DEV-FRONT", "QA-AUTO", "CR"):
        assert st[clave].status == "PENDING", f"{clave} no debe arrastrar el verde de la HU cerrada"


def test_una_mencion_de_la_macro_en_prosa_no_reinicia_el_pipeline(tmp_path):
    prosa = """
### [03-10-2026] Code Review
- **Hora:** 11:05:00
- **Estado:** APROBADO. Confirmar si se emite `@WATCHER: GITOPS-BRANCH-CREATE feat/003-x` más adelante.
- **Handoff:** @PM: siguiente
"""
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO + prosa)

    assert st["QA-AUTO"].status == "COMPLETED", "una cita en prosa no debe abrir un ciclo nuevo"


CIERRE_CON_AVISO_A_HUMANO = """
### [04-10-2026] Code Review
- **Hora:** 00:05:00
- **Estado:** APROBADO. HU certificada y rama consolidada.
@WATCHER: GITOPS-MERGE-CLOSE feat/001-HU_a
- **Handoff:** @HUMANO: HU certificada; aviso informativo de cierre.
"""

CONSULTA_REAL_AL_HUMANO = """
### [04-10-2026] Code Review
- **Hora:** 00:05:00
- **Estado:** APROBADO CON RESERVAS.
- **Handoff:** @HUMANO: Decide cómo cerrar.
  1. ¿Autorizas el cierre?
"""


def test_un_cierre_de_rama_con_aviso_a_humano_no_queda_por_aprobar(tmp_path):
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO + CIERRE_CON_AVISO_A_HUMANO)

    assert resp.overall_status == "COMPLETED"
    assert st["CR"].status == "COMPLETED"
    assert not resp.active_agent_role or "HUMANO" not in resp.active_agent_role


def test_una_consulta_real_al_humano_sigue_marcando_por_aprobar(tmp_path):
    resp, st = _stages(tmp_path, CICLO_1_COMPLETO + CONSULTA_REAL_AL_HUMANO)

    assert resp.active_stage == "CR"
    assert resp.active_agent_role and "HUMANO" in resp.active_agent_role


def test_la_macro_de_cierre_citada_en_prosa_no_cuenta_como_cierre(tmp_path):
    prosa = CONSULTA_REAL_AL_HUMANO.replace(
        "APROBADO CON RESERVAS.", "Confirmar si se emite `@WATCHER: GITOPS-MERGE-CLOSE feat/001-HU_a` luego.")
    resp, _ = _stages(tmp_path, CICLO_1_COMPLETO + prosa)

    assert resp.active_agent_role and "HUMANO" in resp.active_agent_role


# ---------------------------------------------------------------------------
# Avisos del Watcher (vigilante / errores): anotaciones, no pasos en curso
# ---------------------------------------------------------------------------
HASTA_API = CICLO_1_COMPLETO.split("### [03-10-2026] QA Tech")[0]

AVISO_VIGILANTE = """
### [04-10-2026] WATCHER
- **Hora:** 02:47:20
- **Mensaje:** ⚠️ [Vigilante] El agente 'qa-tech' terminó su turno 3 veces sin registrar su bloque en el tracker.
"""

ERROR_DEL_WATCHER = """
### [04-10-2026] WATCHER
- **Hora:** 02:47:20
- **Mensaje:** 🚨 ERROR [SDD Negocio]: Spec Kit no respetó la carpeta fijada 'specs/003-HU_x'.
"""


def test_un_aviso_del_vigilante_no_ilumina_la_caja_del_watcher_y_marca_estancada_la_etapa_real(tmp_path):
    resp, st = _stages(tmp_path, HASTA_API + AVISO_VIGILANTE)

    assert resp.active_stage == "QT"
    assert st["QT"].status == "IN_PROGRESS" and st["QT"].alert_state == "STALLED"
    assert "Vigilante" in st["QT"].alert_reason
    assert st["W-QA"].status != "IN_PROGRESS", "el aviso no es Spec Kit trabajando"
    assert resp.alert and resp.alert["type"] == "STALLED"


def test_un_error_del_watcher_tampoco_cuenta_como_paso_en_curso(tmp_path):
    resp, st = _stages(tmp_path, HASTA_API + ERROR_DEL_WATCHER)

    assert resp.active_stage == "QT"
    assert st["QT"].alert_state == "STALLED"
    assert not any(s.status == "IN_PROGRESS" and s.stage_key.startswith("W-") for s in resp.stages)


def test_un_mensaje_informativo_del_watcher_sigue_siendo_un_paso_en_curso(tmp_path):
    informativo = """
### [04-10-2026] WATCHER
- **Hora:** 02:30:45
- **Mensaje:** ⚙️ [SDD Auto-Runner] Estructurando plan de arquitectura técnica (/speckit.plan)...
"""
    texto = CICLO_1_COMPLETO.split("### [03-10-2026] Data Architect")[0] + informativo
    resp, st = _stages(tmp_path, texto)

    assert resp.alert is None
    assert st["W-SA"].status == "IN_PROGRESS", "el Spec Kit real sí debe iluminar su caja"
    assert all(s.alert_state is None for s in resp.stages)


def test_la_alerta_desaparece_cuando_el_agente_vuelve_a_registrar(tmp_path):
    qt = """
### [04-10-2026] QA Tech
- **Hora:** 09:30:00
- **Estado:** AUDITADO Y APROBADO.
- **Handoff:** @DEV-BACK: arquitectura validada
"""
    resp, st = _stages(tmp_path, HASTA_API + AVISO_VIGILANTE + qt)

    assert resp.alert is None
    assert all(s.alert_state is None for s in resp.stages)
    assert st["QT"].status == "COMPLETED"
