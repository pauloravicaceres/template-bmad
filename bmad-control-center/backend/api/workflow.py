from fastapi import APIRouter, Query, Depends
from models.workflow import WorkflowStatusResponse
from services.workflow_service import WorkflowService

router = APIRouter(tags=["Workflow Monitor"])
workflow_service = WorkflowService()


@router.get("/workflow/status", response_model=WorkflowStatusResponse, summary="Proyección del estado del pipeline agéntico")
async def get_workflow_status(
    include_history: bool = Query(True, description="Incluir historial detallado de transiciones previas")
) -> WorkflowStatusResponse:
    """
    Retorna la proyección en memoria del pipeline agéntico extraído de files/tracker_bmad.md.
    Identifica la fase activa, el rol del agente en turno y el estado de las 8 fases canónicas.
    """
    return workflow_service.get_workflow_status(include_history=include_history)


@router.get("/workflow/state", response_model=WorkflowStatusResponse, summary="Alias interoperable para estado del workflow")
async def get_workflow_state(
    include_history: bool = Query(True, description="Incluir historial detallado de transiciones previas")
) -> WorkflowStatusResponse:
    """Ruta de interoperabilidad alineada con contracts/api-contract.md."""
    return workflow_service.get_workflow_status(include_history=include_history)
