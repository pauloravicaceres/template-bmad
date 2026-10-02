import json
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


# -------------------------------------------------------------
# HU-001 Endpoints (Preserved for full backward compatibility)
# -------------------------------------------------------------

@router.get("/gates/status")
async def get_gate_status():
    """Returns current gate status from tracker (HU-001)."""
    content = tracker_service.read_tracker()
    
    # Evaluar si existe un handoff al humano o estado PENDING sin una decision posterior que lo haya cerrado
    has_human_handoff = "@HUMANO" in content or "PENDING" in content
    
    if has_human_handoff:
        last_human_index = max(content.rfind("@HUMANO"), content.rfind("PENDING"))
        last_decision_index = content.rfind("DECISION [")
        if last_decision_index > last_human_index:
            status = "APPROVED"
        else:
            status = "PENDING_DECISION"
    else:
        status = "APPROVED"
        
    return {"status": status, "content": content}


@router.post("/gates/{gate_id}/decision")
async def make_decision(gate_id: str, payload: DecisionPayload):
    """Records human decision with token sanitization into tracker (HU-001)."""
    decision_text = f"DECISION [{gate_id}]: {payload.action.value}"
    
    if payload.feedback:
        sanitized = sanitize_feedback(payload.feedback)
        decision_text += f"\nFeedback: {sanitized}"
    
    # Si la acción es APPROVE, derivar el mensaje de Handoff apropiado al siguiente agente
    if payload.action.value == "APPROVE":
        content = tracker_service.read_tracker()
        from services.workflow_service import WorkflowService
        ws = WorkflowService()
        blocks = ws._parse_blocks(content)
        
        if blocks:
            last_block = blocks[-1]
            author = last_block.get("author_role")
            art = last_block.get("generated_artifact") or ""
            filename = art.split("/")[-1] if art else "artefacto.md"
            
            # Matriz de handoff según approve_step.py
            handoff_msg = None
            if author in ["Product Analyst", "PA"]:
                handoff_msg = f"- **Handoff:** @PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {filename}. Procede con el análisis estratégico y la creación del Backlog del MVP."
            elif author in ["Business Storyteller", "BS"]:
                handoff_msg = f"- **Handoff:** @PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {filename}. Procede con la creación del PRODUCT BRIEF."
            elif author in ["Product Manager", "PM"]:
                handoff_msg = f"- **Handoff:** @BA: El MVP y Backlog han sido aprobados en el archivo {filename}. Procede con el análisis de negocio y redacción de Historias de Usuario."
            elif author in ["Business Analyst", "BA"]:
                handoff_msg = f"- **Handoff:** @QA: La Historia de Usuario ha sido revisada en el archivo {filename}. Procede con la auditoría documental."
            elif author in ["QA Documental", "QA"]:
                handoff_msg = f"- **Handoff:** @UX: El ciclo SDD ha concluido con éxito en {filename}. Procede con el diseño visual y wireframes."
            elif author in ["Designer UX", "UX"]:
                handoff_msg = f"- **Handoff:** @SA: El diseño visual ha sido aprobado en {filename}. Define el stack tecnológico y reglas arquitectónicas."
            elif author in ["Solutions Architect", "SA"]:
                handoff_msg = f"- **Handoff:** @DA: Las directrices de arquitectura técnica han sido aprobadas en {filename}. Procede con el MER."
            elif author in ["QA-Tech Senior", "QA-Tech", "QT"]:
                handoff_msg = f"- **Handoff:** @DEV-BACK: La arquitectura técnica ha sido verificada en {filename}. Procede con la implementación del Backend."
            
            if handoff_msg:
                decision_text += f"\n{handoff_msg}"

    tracker_service.append_decision(decision_text)
    
    # Broadcast state change
    await manager.broadcast({
        "event": "GATE_STATE_CHANGED",
        "gate_id": gate_id,
        "action": payload.action.value
    })
    return {"message": "Decision recorded"}
