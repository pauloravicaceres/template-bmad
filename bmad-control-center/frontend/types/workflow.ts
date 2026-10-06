export type StageKey = 'PM' | 'BA' | 'QA' | 'W-QA' | 'UX' | 'SA' | 'W-SA' | 'DA' | 'API' | 'QT' | 'W-IMP' | 'DEV-BACK' | 'DEV-FRONT' | 'QA-AUTO' | 'CR'

export type StageStatus = 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'SKIPPED'

export type WorkflowOverallStatus = 'IN_PROGRESS' | 'COMPLETED' | 'IDLE' | 'PAUSED_HITL'

export interface WorkflowStageStep {
  stage_key: StageKey
  stage_name: string
  agent_role: string
  order_index: number
  status: StageStatus
  is_active: boolean
  started_at: string | null
  completed_at: string | null
  origin_block_index: number | null
  generated_artifact_path: string | null
  /** Ciclo de retrabajo SDD: REJECTED = revisor que rechazó; REWORK = etapa que debe corregirse */
  rework_state?: 'REJECTED' | 'REWORK' | null
  rework_iteration?: number | null
  rework_max?: number | null
  rework_reason?: string | null
  /** Etapa estancada: el último evento del tracker es un aviso del vigilante o un error del Watcher */
  alert_state?: 'STALLED' | null
  alert_reason?: string | null
}

export interface WorkflowRework {
  active: boolean
  origin_stage: string
  origin_role: string
  iteration: number
  max_iterations: number
  reason: string
  pending_stages: string[]
  since_block_index: number
}

export interface WorkflowStatusResponse {
  active_stage: string
  overall_status: WorkflowOverallStatus
  active_agent_role: string | null
  active_artifact_in_progress: string | null
  last_updated: string
  total_stages: number
  completed_stages: number
  sync_channel: 'WEBSOCKET_LIVE' | 'POLLING_FALLBACK'
  stages: WorkflowStageStep[]
  rework?: WorkflowRework | null
  alert?: { type: 'STALLED'; message: string; since_block_index: number } | null
}
