import hashlib
import json
import re
from typing import Optional
from fastapi import APIRouter, HTTPException

from models.schemas import DecisionPayload
from services.tracker_service import TrackerService
from services.connection_manager import manager
from core.security import sanitize_feedback
from core.config import settings
from api.workflow import router as workflow_router
from api.artifacts import router as artifacts_router
from api.observability import router as observability_router
from api.git import router as git_router

router = APIRouter()
tracker_service = TrackerService(str(settings.TRACKER_FILE))

# Include feature routers
router.include_router(workflow_router)
router.include_router(artifacts_router)
router.include_router(observability_router)
router.include_router(git_router)


@router.get('/project')
async def get_project():
    return {'project_id': settings.PROJECT_ID if settings.HAS_PROJECT else None,
            'project_name': settings.PROJECT_NAME,
            'workspace_root': str(settings.WORKSPACE_ROOT) if settings.HAS_PROJECT else None}


@router.get('/projects')
async def get_projects():
    """List the engine registry without selecting or writing to a workspace."""
    from core.config import ENGINE_ROOT
    from bmad_runtime.context import read_json, absolute_path, validate_id
    from bmad_runtime.errors import ConfigurationError
    registry = read_json(ENGINE_ROOT / 'config_bmad.json').get('projects', {})
    if not isinstance(registry, dict):
        raise HTTPException(500, 'Invalid projects registry')
    rows = []
    for identity, path in registry.items():
        try:
            validate_id(identity)
            if not isinstance(path, str) or not path.strip():
                raise ConfigurationError('Invalid workspace path')
            rows.append({'project_id': identity, 'workspace_root': str(absolute_path(path, ENGINE_ROOT)),
                         'selected': settings.HAS_PROJECT and identity == settings.PROJECT_ID})
        except ConfigurationError as exc:
            raise HTTPException(500, 'Invalid projects registry') from exc
    return {'projects': rows}


@router.get('/project/context')
async def get_project_context():
    """Read-only context of this API process; never select a project from request paths."""
    from core.config import ENGINE_ROOT
    from bmad_runtime.context import ProjectContext
    from bmad_runtime.technical_context import PROJECT_CONSTITUTION, discover, document_index
    context = ProjectContext(ENGINE_ROOT, settings.WORKSPACE_ROOT, settings.PROJECT_ID,
                             settings.WORKSPACE_ROOT == ENGINE_ROOT)
    return {'project_id': context.project_id, 'constitution': PROJECT_CONSTITUTION,
            'docs': document_index(context, role='solutions-architect'),
            'discovery': discover(context)}


# -------------------------------------------------------------
# HU-001 Endpoints (Preserved for full backward compatibility)
# -------------------------------------------------------------

@router.get("/gates/status")
async def get_gate_status():
    """Returns current gate status from tracker (HU-001)."""
    content = tracker_service.read_tracker()
    
    blocks = content.split("###")
    if len(blocks) > 1:
        last_block = blocks[-1]
        # Un bloque que incluye la macro de cierre de rama es un cierre, no una consulta al humano
        cierre = re.search(r"^\s*(?:[-*]\s+)*(?:\*\*Handoff:\*\*\s*)?@WATCHER:\s*GITOPS-MERGE-CLOSE\s+\S+",
                           last_block, re.MULTILINE)
        if "@HUMANO:" in last_block and "HUMANO" not in last_block.split("\n")[0] and not cierre:
            status = "PENDING_DECISION"
        else:
            status = "APPROVED"
    else:
        status = "APPROVED"
        
    return {"status": status, "content": content}


_REVISOR_TOKEN = {"Code Review": "@CODE-REVIEW:", "QA Automation": "@QA-AUTO:"}
# Valores de 'Artefacto generado' que no nombran ningún entregable.
_SIN_ARTEFACTO = {"", "ninguno", "ninguna", "n/a", "na", "no", "-", "—", "pendiente", "no aplica"}


def _handoff_a_revisor(payload: DecisionPayload, blocks) -> Optional[str]:
    """
    Si el último bloque es una consulta de un revisor (Code Review / QA Automation) dirigida al humano,
    devuelve el handoff que le entrega la respuesta. Sin él la decisión queda registrada en el tracker pero
    ningún agente la lee y el cierre de la HU no avanza.
    """
    if not blocks:
        return None
    last = blocks[-1]
    token = _REVISOR_TOKEN.get(last.get("author_role"))
    if not token or "HUMANO" not in last.get("handoff_targets", []):
        return None

    accion = "APROBÓ" if payload.action.value == "APPROVE" else "RECHAZÓ"
    # Una sola línea y sin '@' en las menciones del texto libre: sanitize_feedback deja "[@PM:_ESCAPED]", que
    # todavía contiene la etiqueta y el Watcher (que busca por coincidencia de texto) podría despachar a ese agente.
    respuesta = re.sub(r"@(?=[A-Za-z])", "", " ".join((payload.feedback or "").split()))[:1500]
    detalle = f" Respuesta: {respuesta}" if respuesta else " Sin comentarios adicionales."
    return (
        f"{token} El humano {accion} tu consulta de cierre.{detalle} "
        "Procede según su decisión; si autorizó cerrar la rama, emite el cierre como línea independiente."
    )


def _bloques_crudos(content: str):
    return [b for b in re.split(r"(?=^### \[)", content, flags=re.MULTILINE) if b.startswith("### [")]


def _es_humano(bloque: str) -> bool:
    autor = re.match(r"### \[[^\]\n]*\]\s*([^\n]*)", bloque)
    return bool(autor) and autor.group(1).strip().upper() == "HUMANO"


def _compuerta(content: str):
    """(huella de la compuerta, decisiones humanas registradas después de ella). La compuerta es el último
    bloque no humano: una decisión responde a él y solo a él."""
    bloques = _bloques_crudos(content)
    indice = max((i for i, b in enumerate(bloques) if not _es_humano(b)), default=-1)
    # Sin espacios de borde: el bloque gana un salto final cuando se anexa la decisión que lo responde.
    compuerta = bloques[indice].strip() if indice >= 0 else ""
    huella = hashlib.sha256(f"{indice}\0{compuerta}".encode("utf-8")).hexdigest()
    return huella, bloques[indice + 1:]


@router.post("/gates/{gate_id}/decision")
async def make_decision(gate_id: str, payload: DecisionPayload):
    """Records human decision with token sanitization into tracker (HU-001).

    Read, check, decide and append run under the project tracker lock: two simultaneous requests cannot both
    emit the handoff. The identical request is idempotent (op_id = gate + decision); a different decision after
    one that already emitted a handoff is rejected. Nothing external runs while the lock is held.

    Errors (header X-BMAD-Error): 503 `busy` (temporary lock, retry), 423 `integrity` (an engine/decision append is
    lost or uncertain: nothing is written until it is reconciled explicitly), 409 `conflict` (functional: the gate
    was already resolved or the decision changed meanwhile)."""
    from bmad_runtime.tracker_io import TrackerBusy, TrackerIntegrityError
    from bmad_runtime.errors import ReconciliationRequired
    try:
        with tracker_service.transaction() as tx:
            resultado = _registrar_decision(tx, payload)
    except TrackerBusy as exc:
        raise _decision_error(503, "busy", str(exc)) from exc
    except TrackerIntegrityError as exc:
        raise _decision_error(423, "integrity", "Integridad del tracker: la decisión no se registró y requiere "
                                                "reconciliación. " + str(exc), exc.operations) from exc
    except ReconciliationRequired as exc:
        raise _decision_error(409, "conflict", str(exc)) from exc

    # Emitir evento por WebSocket si est configurado (fuera del lock del tracker)
    try:
        from api.websockets import manager
        from services.workflow_service import WorkflowService
        wf_service = WorkflowService()
        wf_status = wf_service.get_workflow_status()

        import asyncio
        asyncio.create_task(
            manager.broadcast_workflow_updated(
                wf_status.model_dump(),
                coalesced_count=len(wf_status.history)
            )
        )
    except Exception as e:
        print(f"Error emitiendo evento de WorkflowUpdated tras decision: {e}")

    return resultado


_DECISION_ERRORS = {"busy": "TRACKER_BUSY", "integrity": "TRACKER_INTEGRITY", "conflict": "DECISION_CONFLICT",
                    "artifact": "ARTIFACT_REJECTED", "hu_open": "HU_OPEN_CONFLICT", "hu_state": "HU_STATE_BLOCKED"}


def _decision_error(status: int, kind: str, detail: str, operations=None, metadata=None) -> HTTPException:
    """Error de decisión con su clase en error_code (ADR-05) y en la cabecera X-BMAD-Error."""
    exc = HTTPException(status, detail, headers={"X-BMAD-Error": kind})
    exc.error_code = _DECISION_ERRORS[kind]
    if operations:
        exc.metadata = {"operations": list(operations)}
    if metadata:
        exc.metadata = metadata
    return exc


class _Artefactos:
    """Clasificación (bmad_runtime.artifacts) de los artefactos que cita una aprobación. Corre dentro de la
    transacción del tracker: solo sistema de archivos local y acotado, nunca red. En modo warn, OUTSIDE,
    OTHER_PROJECT y AMBIGUOUS se rechazan (422 ARTIFACT_REJECTED, sin escribir); MISSING pasa con advertencia."""

    def __init__(self, author):
        from bmad_runtime.artifacts import ArtifactClassifier, gate_for_author, load_policy, registered_workspaces
        from core.config import ENGINE_ROOT
        self.policy = load_policy(ENGINE_ROOT)
        self.rule = gate_for_author(author, self.policy)
        self.classifier = ArtifactClassifier(settings.WORKSPACE_ROOT, project_id=settings.PROJECT_ID,
                                             engine_root=ENGINE_ROOT, registry=registered_workspaces(ENGINE_ROOT))
        self.revisados = []

    def revisar(self, referencia, rule=None, future=()):
        """Clasificación aceptada de `referencia`, o None con la política en off."""
        if self.policy["mode"] == "off":
            return None
        clasificacion = self.classifier.classify(referencia, rule or self.rule, future=future)
        if clasificacion.rejected:
            raise _decision_error(422, "artifact", f"Artefacto rechazado ({clasificacion.status}): "
                                                   f"{clasificacion.detail} No se registró la aprobación.",
                                  metadata={"artifact": clasificacion.to_dict()})
        self.revisados.append(clasificacion)
        return clasificacion

    def respuesta(self):
        if not self.revisados:
            return {}
        return {"artifacts": [c.to_dict() for c in self.revisados],
                "warnings": [w for c in self.revisados for w in c.warnings()]}


def _contexto_proyecto():
    from core.config import ENGINE_ROOT
    from bmad_runtime.context import ProjectContext
    return ProjectContext(ENGINE_ROOT, settings.WORKSPACE_ROOT, settings.PROJECT_ID,
                          settings.WORKSPACE_ROOT == ENGINE_ROOT)


def _modo_hu_watcher(context):
    """Modo ai.hu_lifecycle del watcher en ejecución (latido reciente), leído del SQLite en solo lectura; None si no
    hay watcher activo o no se puede leer."""
    from bmad_runtime.policy_audit import running_policies
    from bmad_runtime.state import StateStore
    try:
        store = StateStore.open_readonly(context)
    except Exception:
        return None
    if store is None:
        return None
    try:
        return (running_policies(store) or {}).get("hu_lifecycle")
    except Exception:
        return None
    finally:
        store.close()


def _preflight_hu(hu):
    """Fase 4F-E4, solo con ai.hu_lifecycle.mode = enforce: una aprobación que generaría BRANCH-CREATE se bloquea
    antes de escribir nada si el proyecto ya tiene otra HU abierta (409 HU_OPEN_CONFLICT) o su estado no se puede
    demostrar (423 HU_STATE_BLOCKED, con la evidencia en metadata). La misma HU es idempotente. Es informativo: el
    watcher revalida siempre bajo su lock. Solo lectura local (Git, tracker, SQLite en modo ro); nunca red."""
    from bmad_runtime.hu_enforcement import CONFLICT_CODES, preflight
    from bmad_runtime.hu_lifecycle import load_policy
    context = _contexto_proyecto()
    try:
        modo = load_policy(context)["mode"]
    except Exception as exc:
        raise _decision_error(423, "hu_state", f"No se pudo leer la política ai.hu_lifecycle ({type(exc).__name__}); "
                                               "no se registró la aprobación.") from exc
    if modo != "enforce" and _modo_hu_watcher(context) == "enforce":
        # Fase 4F-E5 §11: el watcher en ejecución usa otra configuración (--config) con enforce; el Control Center
        # aplica la más estricta para no aceptar aquí lo que el watcher rechazaría.
        modo = "enforce"
    if modo != "enforce":
        return None
    decision = preflight(context, hu)
    if decision.rejected:
        conflicto = decision.code in CONFLICT_CODES
        raise _decision_error(409 if conflicto else 423, "hu_open" if conflicto else "hu_state",
                              f"{decision.message} No se registró la aprobación.",
                              metadata={"hu_lifecycle": decision.to_dict()})
    return decision


def _registrar_decision(tx, payload: DecisionPayload):
    """Cuerpo de la transacción de make_decision; corre con el lock del tracker tomado."""
    from datetime import datetime
    from services.workflow_service import WorkflowService
    dt_str = datetime.now().strftime("%d-%m-%Y")
    hr_str = datetime.now().strftime("%H:%M:%S")

    # Un envío anterior interrumpido entre la escritura y su confirmación se resuelve antes de decidir.
    tx.writer.recover()
    content_tracker = tx.writer.read()
    huella, decisiones = _compuerta(content_tracker)
    sanitized = sanitize_feedback(payload.feedback) if payload.feedback else ""
    op_id = "gate:" + hashlib.sha256(
        f"{huella}\0{payload.action.value}\0{sanitized}\0{payload.epic_id or ''}".encode("utf-8")).hexdigest()[:48]
    if tx.writer.status(op_id) == "lost":
        # Pérdida ya resuelta por el operador (reemisión autorizada o cerrada): si la decisión original volvió al
        # tracker, esa copia es la entrega. Solo verifica evidencia bajo el lock; nunca escribe el tracker.
        tx.writer.reconcile(op_id)
    if tx.writer.delivered(op_id):
        # Reintento o doble envío de la misma decisión sobre la misma compuerta: sus bytes siguen en el tracker.
        return {"message": "Decision recorded", "replayed": True}
    if any("- **Handoff:**" in decision for decision in decisiones):
        raise _decision_error(409, "conflict", "La compuerta ya fue resuelta: una decisión humana posterior al último "
                                               "bloque emitió su handoff. Espera el siguiente bloque del agente; no se "
                                               "registró nada.")

    blocks = WorkflowService()._parse_blocks(content_tracker)
    handoff_text = _handoff_a_revisor(payload, blocks)
    artefactos = None
    ciclo_hu = None
    if payload.action.value == "APPROVE" and not handoff_text:
        if blocks:
            last_block = blocks[-1]
            author = last_block.get("author_role")
            art = last_block.get("generated_artifact") or ""
            nombre_artefacto = re.split(r"[\\/]", art.strip())[-1] if art.strip() else ""
            artefactos = _Artefactos(author)

            def artefacto_declarado():
                # Un handoff que cita el entregable aprobado necesita uno real: nunca un nombre genérico.
                if art.lower().strip(" .`") in _SIN_ARTEFACTO or not nombre_artefacto:
                    raise HTTPException(422, f"El último bloque de {author} no declara un 'Artefacto generado' "
                                             "válido; no se registra la aprobación ni el handoff.")
                clasificacion = artefactos.revisar(art)
                # El handoff cita el nombre declarado (o la URL externa autorizada completa).
                return clasificacion.cited if clasificacion else nombre_artefacto

            if author in ["Product Analyst", "PA"]:
                handoff_text = f"@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {artefacto_declarado()}. Procede con el análisis estratégico y la creación del Backlog del MVP."
            elif author in ["Business Storyteller", "BS"]:
                handoff_text = f"@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {artefacto_declarado()}. Procede con la creación del PRODUCT BRIEF."
            elif author in ["Product Manager", "PM"]:
                handoff_str = last_block.get("handoff_directive") or ""
                # Determinar si es cierre de inicio de épica o cierre final
                if "100% concluido" in handoff_str or "no hay más épicas" in handoff_str.lower():
                    handoff_text = "@HUMANO: Proyecto completado exitosamente. No hay más acciones requeridas por el enjambre."
                else:
                    from bmad_runtime.hu_naming import hu_id_from_delegation, hu_name_error
                    epic = payload.epic_id.strip() if payload.epic_id and payload.epic_id.strip() else None
                    epic = epic or hu_id_from_delegation(handoff_str)
                    # Sin identificador válido no se registra la aprobación: nunca una rama genérica ni inventada.
                    error = hu_name_error(f"{epic}.md") if epic else (
                        "el handoff del PM no contiene 'delegar es NNN-nombre-en-kebab-case' y no se indicó epic_id")
                    if error:
                        raise HTTPException(422, f"Identificador de HU inválido: {error}")
                    # Una HU abierta por proyecto (E4): nada se registra si la apertura no puede autorizarse.
                    ciclo_hu = _preflight_hu(epic)
                    handoff_text = f"@WATCHER: GITOPS-BRANCH-CREATE feat/{epic}\n@BA: El MVP y Backlog han sido aprobados en el archivo {artefacto_declarado()}. La rama feat/{epic} ha sido creada. Procede con el análisis de negocio y redacción de Historias de Usuario para la épica {epic}. Usa el identificador universal estricto para crear el archivo físico en docs/business-analyst."
                    # Regla FUTURE explícita: este handoff ordena al BA crear exactamente esta HU en la etapa siguiente.
                    from bmad_runtime.artifacts import gate_for_author
                    hu_futura = f"docs/business-analyst/{epic}.md"
                    artefactos.revisar(hu_futura, gate_for_author("Business Analyst", artefactos.policy),
                                       future=(hu_futura,))
            elif author in ["Business Analyst", "BA"]:
                from bmad_runtime.hu_naming import hu_name_error
                # La HU llega a QA solo con un archivo que cumple el contrato: nunca un nombre genérico ni inventado.
                hu = nombre_artefacto
                error = hu_name_error(hu) if hu else ("el último bloque del BA no declara 'Artefacto generado'; "
                                                         "se espera NNN-nombre-en-kebab-case.md")
                if error:
                    raise HTTPException(422, f"Historia de usuario inválida: {error}. No se registra la aprobación.")
                artefactos.revisar(art)          # nombre válido; ahora su ubicación (nunca otra HU en su lugar)
                handoff_text =f"@QA: La Historia de Usuario ha sido revisada en el archivo {hu}. Procede con la auditoría documental."
            elif author in ["QA Documental", "QA"]:
                handoff_text = f"@UX: El ciclo SDD ha concluido con éxito en {artefacto_declarado()}. Procede con el diseño visual y wireframes."
            elif author in ["Designer UX", "UX"]:
                handoff_text = f"@SA: El diseño visual ha sido aprobado en {artefacto_declarado()}. Define el stack tecnológico y reglas arquitectónicas."
            elif author in ["Solutions Architect", "SA"]:
                handoff_text = f"@DA: Las directrices de arquitectura técnica han sido aprobadas en {artefacto_declarado()}. Procede con el MER."
            elif author in ["QA-Tech Senior", "QA-Tech", "QT"]:
                handoff_text = f"@DEV-BACK: La arquitectura técnica ha sido verificada en {artefacto_declarado()}. Procede con la implementación del Backend."
    
    lines = [f"\n### [{dt_str}] HUMANO"]
    lines.append(f"- **Hora:** {hr_str}")
    lines.append(f"- **Estado:** {payload.action.value}")
    
    if payload.feedback:
        lines.append(f"- **Feedback:** {sanitized}")

    if handoff_text:
        lines.append(f"- **Handoff:** {handoff_text}")

    decision_text = "\n".join(lines)
    result = tx.append_decision(decision_text.strip(), op_id=op_id)
    if result.replayed:      # the lost original reappeared before the authorized reissue: nothing was written
        return {"message": "Decision recorded", "replayed": True}
    respuesta = {"message": "Decision recorded", **(artefactos.respuesta() if artefactos else {})}
    if ciclo_hu:
        respuesta["hu_lifecycle"] = ciclo_hu.to_dict()
    # Una reemisión autorizada por el operador (state --authorize-reissue) escribe la decisión una sola vez.
    if result.reissued:
        respuesta["reissued"] = True
    return respuesta
