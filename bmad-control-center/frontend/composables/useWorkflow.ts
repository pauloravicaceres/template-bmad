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
  { key: 'W-QA', name: 'Spec Kit', role: 'WATCHER', order: 4 },
  { key: 'UX', name: 'Designer UX', role: 'Designer UX', order: 5 },
  { key: 'SA', name: 'Solutions Architect', role: 'Solutions Architect', order: 6 },
  { key: 'W-SA', name: 'Spec Kit', role: 'WATCHER', order: 7 },
  { key: 'DA', name: 'Data Architect', role: 'Data Architect', order: 8 },
  { key: 'API', name: 'API Architect', role: 'API Architect', order: 9 },
  { key: 'QT', name: 'QA-Tech Senior', role: 'QA-Tech Senior', order: 10 },
  { key: 'W-IMP', name: 'Spec Kit', role: 'WATCHER', order: 11 },
  { key: 'DEV-BACK', name: 'Dev Backend', role: 'Senior Backend Developer', order: 12 },
  { key: 'DEV-FRONT', name: 'Dev Frontend', role: 'Senior Frontend Developer', order: 13 },
  { key: 'QA-AUTO', name: 'QA Automation', role: 'QA Automation', order: 14 },
  { key: 'CR', name: 'Code Review', role: 'SecOps', order: 15 },
]

export function buildDefaultStages(activeStageKey?: string): WorkflowStageStep[] {
  const activeIndex = CANONICAL_STAGES.findIndex((s) => s.key === activeStageKey)

  return CANONICAL_STAGES.map((s, idx) => {
    let status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' = 'PENDING'
    let isActive = false

    if (activeIndex !== -1) {
      if (idx < activeIndex) {
        status = 'COMPLETED'
      } else if (idx === activeIndex) {
        status = 'IN_PROGRESS'
        isActive = true
      } else {
        status = 'PENDING'
      }
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
  const totalStages = computed<number>(() => workflowState.value?.total_stages || 15)
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
    const totalStages = payload.total_stages !== undefined ? payload.total_stages : 15

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
