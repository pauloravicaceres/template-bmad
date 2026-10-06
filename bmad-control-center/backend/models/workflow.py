from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowStageStep(BaseModel):
    """Represents one of the 8 canonical stages in the BMAD pipeline."""
    stage_key: str  # PM, BA, QA, UX, SA, DA, API, QT
    stage_name: str
    agent_role: str
    order_index: int
    status: str  # COMPLETED, IN_PROGRESS, PENDING, SKIPPED
    is_active: bool = False
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    origin_block_index: Optional[int] = None
    generated_artifact_path: Optional[str] = None
    # Ciclo de retrabajo SDD: REJECTED (revisor que rechazó) | REWORK (etapa que debe corregirse)
    rework_state: Optional[str] = None
    rework_iteration: Optional[int] = None
    rework_max: Optional[int] = None
    rework_reason: Optional[str] = None
    # Etapa estancada: el último evento del tracker es un aviso del vigilante o un error del Watcher
    alert_state: Optional[str] = None
    alert_reason: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Overall workflow state projection response."""
    active_stage: Optional[str] = None
    overall_status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, IDLE, PAUSED_HITL
    active_agent_role: Optional[str] = None
    active_artifact_in_progress: Optional[str] = None
    last_updated: Optional[str] = None
    total_stages: int = 8
    completed_stages: int = 0
    sync_channel: str = "WEBSOCKET_LIVE"
    stages: List[WorkflowStageStep] = Field(default_factory=list)
    
    # Interoperability fields for /api/v1/workflow/state contract compatibility
    current_stage: Optional[str] = None
    status: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    # Retrabajo activo tras un rechazo de Code Review / QA Automation (None si no hay)
    rework: Optional[Dict[str, Any]] = None
    # Alerta global (STALLED) cuando el flujo se detuvo y el Watcher lo dejó anotado
    alert: Optional[Dict[str, Any]] = None


# Alias for WorkflowStatusResponse
WorkflowState = WorkflowStatusResponse
