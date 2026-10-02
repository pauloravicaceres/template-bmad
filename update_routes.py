import os
import re

filepath = "bmad-control-center/backend/api/routes.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_func = """@router.post("/gates/{gate_id}/decision")
async def make_decision(gate_id: str, payload: DecisionPayload):
    \"\"\"Records human decision with token sanitization into tracker (HU-001).\"\"\"
    from datetime import datetime
    dt_str = datetime.now().strftime("%d-%m-%Y")
    hr_str = datetime.now().strftime("%H:%M:%S")
    
    handoff_text = None
    if payload.action.value == "APPROVE":
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
                handoff_text = f"@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {filename}. Procede con el anlisis estratgico y la creacin del Backlog del MVP."
            elif author in ["Business Storyteller", "BS"]:
                handoff_text = f"@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {filename}. Procede con la creacin del PRODUCT BRIEF."
            elif author in ["Product Manager", "PM"]:
                handoff_text = f"@BA: El MVP y Backlog han sido aprobados en el archivo {filename}. Procede con el anlisis de negocio y redaccin de Historias de Usuario."
            elif author in ["Business Analyst", "BA"]:
                handoff_text = f"@QA: La Historia de Usuario ha sido revisada en el archivo {filename}. Procede con la auditora documental."
            elif author in ["QA Documental", "QA"]:
                handoff_text = f"@UX: El ciclo SDD ha concluido con xito en {filename}. Procede con el diseo visual y wireframes."
            elif author in ["Designer UX", "UX"]:
                handoff_text = f"@SA: El diseo visual ha sido aprobado en {filename}. Define el stack tecnolgico y reglas arquitectnicas."
            elif author in ["Solutions Architect", "SA"]:
                handoff_text = f"@DA: Las directrices de arquitectura tcnica han sido aprobadas en {filename}. Procede con el MER."
            elif author in ["QA-Tech Senior", "QA-Tech", "QT"]:
                handoff_text = f"@DEV-BACK: La arquitectura tcnica ha sido verificada en {filename}. Procede con la implementacin del Backend."
    
    decision_text = f"\\n### [{dt_str}] HUMANO\\n"
    decision_text += f"- **Estado:** {payload.action.value}\\n"
    decision_text += f"- **Hora:** {hr_str}\\n"
    
    if payload.feedback:
        sanitized = sanitize_feedback(payload.feedback)
        decision_text += f"- **Feedback:** {sanitized}\\n"
        
    if handoff_text:
        decision_text += f"- **Handoff:** {handoff_text}\\n"
        
    tracker_service.append_decision(decision_text.strip())
    
    # Emitir evento por WebSocket si est configurado
    try:
        from api.websockets import manager
        from services.workflow_service import WorkflowService
        wf_service = WorkflowService()
        wf_status = wf_service.get_workflow_status()
        
        # Necesitamos correr el broadcast_workflow_updated en el loop asncrono
        import asyncio
        asyncio.create_task(
            manager.broadcast_workflow_updated(
                wf_status.model_dump(),
                coalesced_count=len(wf_status.history)
            )
        )
    except Exception as e:
        print(f"Error emitiendo evento de WorkflowUpdated tras decision: {e}")
        
    return {"status": "success", "decision": payload.action.value}"""

# Find the start of make_decision to end of file, or just replace the block.
# I will use a regex to replace everything from @router.post("/gates/{gate_id}/decision") to the end.

pattern = re.compile(r'@router\.post\("/gates/\{gate_id\}/decision"\).*', re.DOTALL)
content = re.sub(pattern, new_func, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)