export type StageKey = 'PM' | 'BA' | 'QA' | 'UX' | 'SA' | 'DA' | 'API' | 'QT'

export type StageStatus = 'COMPLETED' | 'IN_PROGRESS' | 'PENDING'

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
}
