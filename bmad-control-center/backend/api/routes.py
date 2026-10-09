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
            'documents': document_index(context, role='solutions-architect'),
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


def _handoff_a_revisor(payload: DecisionPayload) -> Optional[str]:
    """
    Si el último bloque es una consulta de un revisor (Code Review / QA Automation) dirigida al humano,
    devuelve el handoff que le entrega la respuesta. Sin él la decisión queda registrada en el tracker pero
    ningún agente la lee y el cierre de la HU no avanza.
    """
    from services.workflow_service import WorkflowService
    blocks = WorkflowService()._parse_blocks(tracker_service.read_tracker())
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


@router.post("/gates/{gate_id}/decision")
async def make_decision(gate_id: str, payload: DecisionPayload):
    """Records human decision with token sanitization into tracker (HU-001)."""
    from datetime import datetime
    dt_str = datetime.now().strftime("%d-%m-%Y")
    hr_str = datetime.now().strftime("%H:%M:%S")

    handoff_text = _handoff_a_revisor(payload)
    if payload.action.value == "APPROVE" and not handoff_text:
        content_tracker = tracker_service.read_tracker()
        from services.workflow_service import WorkflowService
        ws = WorkflowService()
        blocks = ws._parse_blocks(content_tracker)
        
        if blocks:
            last_block = blocks[-1]
            author = last_block.get("author_role")
            art = last_block.get("generated_artifact") or ""
            filename = art.split("/")[-1] if art else "artefacto.md"
            
            if author in ["Product Analyst", "PA"]:
                handoff_text = f"@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {filename}. Procede con el análisis estratégico y la creación del Backlog del MVP."
            elif author in ["Business Storyteller", "BS"]:
                handoff_text = f"@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {filename}. Procede con la creación del PRODUCT BRIEF."
            elif author in ["Product Manager", "PM"]:
                import re
                handoff_str = last_block.get("handoff_directive") or ""
                # Determinar si es cierre de inicio de épica o cierre final
                if "100% concluido" in handoff_str or "no hay más épicas" in handoff_str.lower():
                    handoff_text = "@HUMANO: Proyecto completado exitosamente. No hay más acciones requeridas por el enjambre."
                else:
                    epic = payload.epic_id.strip() if payload.epic_id and payload.epic_id.strip() else None
                    if not epic:
                        match = re.search(r"delegar es\s+(\d{3}-HU_[\w_]+)", handoff_str)
                        if match:
                            epic = match.group(1)
                        else:
                            epic = "001-HU_epic_generica"
                    handoff_text = f"@WATCHER: GITOPS-BRANCH-CREATE feat/{epic}\n@BA: El MVP y Backlog han sido aprobados en el archivo {filename}. La rama feat/{epic} ha sido creada. Procede con el análisis de negocio y redacción de Historias de Usuario para la épica {epic}. Usa el identificador universal estricto para crear el archivo físico en documents/business-analyst."
            elif author in ["Business Analyst", "BA"]:
                handoff_text = f"@QA: La Historia de Usuario ha sido revisada en el archivo {filename}. Procede con la auditoría documental."
            elif author in ["QA Documental", "QA"]:
                handoff_text = f"@UX: El ciclo SDD ha concluido con éxito en {filename}. Procede con el diseño visual y wireframes."
            elif author in ["Designer UX", "UX"]:
                handoff_text = f"@SA: El diseño visual ha sido aprobado en {filename}. Define el stack tecnológico y reglas arquitectónicas."
            elif author in ["Solutions Architect", "SA"]:
                handoff_text = f"@DA: Las directrices de arquitectura técnica han sido aprobadas en {filename}. Procede con el MER."
            elif author in ["QA-Tech Senior", "QA-Tech", "QT"]:
                handoff_text = f"@DEV-BACK: La arquitectura técnica ha sido verificada en {filename}. Procede con la implementación del Backend."
    
    lines = [f"\n### [{dt_str}] HUMANO"]
    lines.append(f"- **Hora:** {hr_str}")
    lines.append(f"- **Estado:** {payload.action.value}")
    
    if payload.feedback:
        sanitized = sanitize_feedback(payload.feedback)
        lines.append(f"- **Feedback:** {sanitized}")
        
    if handoff_text:
        lines.append(f"- **Handoff:** {handoff_text}")
        
    decision_text = "\n".join(lines)
    tracker_service.append_decision(decision_text.strip())
    
    # Emitir evento por WebSocket si est configurado
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
        
    return {"message": "Decision recorded"}
