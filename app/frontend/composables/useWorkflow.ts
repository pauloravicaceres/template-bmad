import { ref, computed } from 'vue'
import type {
  WorkflowStatusResponse,
  WorkflowStageStep,
  StageKey,
  WorkflowOverallStatus,
  WorkflowUpdatedPayload,
} from '../types'
import { fetchWorkflowStatus } from '../services/api_client'

export const CANONICAL_STAGES: Array<{ key: StageKey; name: string; role: string; order: number }> = [
  { key: 'PM', name: 'Product Manager', role: 'Product Manager', order: 1 },
  { key: 'BA', name: 'Business Analyst', role: 'Business Analyst', order: 2 },
  { key: 'QA', name: 'QA Documental', role: 'QA Documental', order: 3 },
  { key: 'UX', name: 'Designer UX', role: 'Designer UX', order: 4 },
  { key: 'SA', name: 'Solutions Architect', role: 'Solutions Architect', order: 5 },
  { key: 'DA', name: 'Data Architect', role: 'Data Architect', order: 6 },
  { key: 'API', name: 'API Architect', role: 'API Architect', order: 7 },
  { key: 'QT', name: 'QA-Tech Senior', role: 'QA-Tech Senior', order: 8 },
]

export function buildDefaultStages(activeStageKey?: string): WorkflowStageStep[] {
  let foundActive = false
  return CANONICAL_STAGES.map((s) => {
    let status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' = 'PENDING'
    let isActive = false

    if (activeStageKey && s.key === activeStageKey) {
      status = 'IN_PROGRESS'
      isActive = true
      foundActive = true
    } else if (!foundActive && activeStageKey) {
      status = 'COMPLETED'
    }

    return {
      stage_key: s.key,
      stage_name: s.name,
      agent_role: s.role,
      order_index: s.order,
      status,
      is_active: isActive,
      started_at: null,
      completed_at: null,
      origin_block_index: null,
      generated_artifact_path: null,
    }
  })
}

export function useWorkflow(apiBase?: string) {
  const workflowState = ref<WorkflowStatusResponse | null>(null)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const activeStage = computed<string>(() => workflowState.value?.active_stage || 'IDLE')
  const overallStatus = computed<WorkflowOverallStatus>(() => workflowState.value?.overall_status || 'IDLE')
  const activeAgentRole = computed<string | null>(() => workflowState.value?.active_agent_role || null)
  const activeArtifactInProgress = computed<string | null>(
    () => workflowState.value?.active_artifact_in_progress || null
  )
  const completedStages = computed<number>(() => workflowState.value?.completed_stages || 0)
  const totalStages = computed<number>(() => workflowState.value?.total_stages || 8)
  const syncChannel = computed<string>(() => workflowState.value?.sync_channel || 'WEBSOCKET_LIVE')

  const stages = computed<WorkflowStageStep[]>(() => {
    if (workflowState.value && workflowState.value.stages && workflowState.value.stages.length > 0) {
      return workflowState.value.stages
    }
    return buildDefaultStages(workflowState.value?.active_stage)
  })

  const loadWorkflow = async (): Promise<void> => {
    isLoading.value = true
    error.value = null
    try {
      const data = await fetchWorkflowStatus(true, apiBase)
      workflowState.value = data
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al conectar con la API de workflow'
      error.value = msg
    } finally {
      isLoading.value = false
    }
  }

  const handleWorkflowUpdated = (payload: WorkflowUpdatedPayload | WorkflowStatusResponse): void => {
    const agentRole = ('agent_role' in payload ? payload.agent_role : null) || payload.active_agent_role || null
    const artifactPath = ('last_artifact_path' in payload ? payload.last_artifact_path : null) || ('active_artifact_in_progress' in payload ? payload.active_artifact_in_progress : null) || null
    const completedStages = payload.completed_stages !== undefined ? payload.completed_stages : 0
    const totalStages = payload.total_stages !== undefined ? payload.total_stages : 8

    if (!workflowState.value) {
      workflowState.value = {
        active_stage: payload.active_stage,
        overall_status: (payload.overall_status as WorkflowOverallStatus) || 'IN_PROGRESS',
        active_agent_role: agentRole,
        active_artifact_in_progress: artifactPath,
        last_updated: payload.last_updated || new Date().toISOString(),
        total_stages: totalStages,
        completed_stages: completedStages,
        sync_channel: 'WEBSOCKET_LIVE',
        stages: payload.stages && payload.stages.length > 0 ? payload.stages : buildDefaultStages(payload.active_stage),
      }
    } else {
      workflowState.value.active_stage = payload.active_stage
      workflowState.value.overall_status =
        (payload.overall_status as WorkflowOverallStatus) || workflowState.value.overall_status
      workflowState.value.active_agent_role = agentRole
      workflowState.value.active_artifact_in_progress = artifactPath
      workflowState.value.last_updated = payload.last_updated || new Date().toISOString()
      workflowState.value.completed_stages = completedStages
      if (payload.stages && payload.stages.length > 0) {
        workflowState.value.stages = payload.stages
      } else {
        workflowState.value.stages = buildDefaultStages(payload.active_stage)
      }
    }
  }

  return {
    workflowState,
    isLoading,
    error,
    activeStage,
    overallStatus,
    activeAgentRole,
    activeArtifactInProgress,
    stages,
    completedStages,
    totalStages,
    syncChannel,
    loadWorkflow,
    handleWorkflowUpdated,
  }
}
