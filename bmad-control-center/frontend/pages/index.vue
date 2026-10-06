<template>
  <div class="min-h-screen bg-gray-100 flex flex-col font-sans">
    <!-- Barra Superior de Control Center (UX Header con WebSocketStatusBadge y DebounceIndicator) -->
    <header class="bg-gray-900 text-white px-6 py-3 shadow-md flex items-center justify-between border-b border-gray-800">
      <div class="flex items-center gap-3">
        <span class="text-xl">⚡</span>
        <h1 class="text-sm font-bold tracking-wide">
          BMAD Control Center
        </h1>
        <!-- Swarm Status Badge -->
        <span
          :class="[
            'text-[11px] font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1.5 border',
            overallStatus === 'IN_PROGRESS'
              ? 'bg-blue-900/60 border-blue-500 text-blue-200'
              : overallStatus === 'COMPLETED'
              ? 'bg-emerald-900/60 border-emerald-500 text-emerald-200'
              : 'bg-gray-800 border-gray-600 text-gray-300'
          ]"
        >
          <span
            v-if="overallStatus === 'IN_PROGRESS'"
            class="h-2 w-2 rounded-full bg-blue-400 animate-pulse"
          ></span>
          <span>
            [● {{ overallStatusText }}]
          </span>
        </span>

        <!-- Debounce Coalescence Indicator (Estado 4 UX / ADR-010) -->
        <DebounceIndicator
          :coalesced-count="lastCoalescedCount"
          :window-duration-ms="200"
          :trigger-timestamp="debounceTriggerTimestamp"
        />

        <!-- View Switcher (Artefactos vs Telemetría Git) -->
        <div class="flex items-center bg-gray-800 p-0.5 rounded-lg border border-gray-700 ml-2">
          <button
            type="button"
            @click="activeView = 'artifacts'"
            :class="[
              'px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors cursor-pointer flex items-center gap-1.5',
              activeView === 'artifacts'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-gray-400 hover:text-white'
            ]"
          >
            <span>📁</span> Artefactos
          </button>
          <button
            type="button"
            @click="activeView = 'git'"
            :class="[
              'px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors cursor-pointer flex items-center gap-1.5',
              activeView === 'git'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-gray-400 hover:text-white'
            ]"
          >
            <span>🌿</span> Telemetría Git
            <span
              v-if="gitTelemetry.totalModifiedFiles.value > 0"
              class="bg-emerald-500 text-white text-[9px] px-1.5 py-0.2 rounded-full font-bold font-mono"
            >
              {{ gitTelemetry.totalModifiedFiles.value }}
            </span>
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3 text-xs">
        <!-- Telemetry & Observability Toggle Button -->
        <button
          type="button"
          @click="showTelemetryPanel = !showTelemetryPanel"
          :class="[
            'px-2.5 py-1 rounded-md text-[11px] font-semibold border transition-colors cursor-pointer flex items-center gap-1',
            showTelemetryPanel
              ? 'bg-blue-800 border-blue-500 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
          ]"
        >
          <span>📡</span> Telemetría
        </button>

        <!-- Live WebSocket Status Badge (Estado 1 y 3 UX / ADR-011) -->
        <WebSocketStatusBadge
          :status="connectionState"
          :latency-ms="latencyMs"
          :reconnect-attempt="reconnectAttempt"
          :next-retry-seconds="nextReconnectDelaySeconds"
          @manual-reconnect="reconnectManual"
        />

        <!-- Role Badge -->
        <div class="bg-gray-800 px-3 py-1 rounded-md border border-gray-700 text-gray-300 font-mono text-[11px]">
          Tech Lead | Local
        </div>
      </div>
    </header>

    <!-- Sub-header: Workflow Pipeline Monitor (Stepper de 8 etapas con pulso reactivo) -->
    <section class="p-4 bg-gray-50 border-b border-gray-200">
      <WorkflowStepper
          :stages="stages"
          :active-stage-key="activeStage"
          :overall-status="overallStatus"
          :active-agent-role="activeAgentRole"
          :selected-path="selectedPath"
          @select-stage="handleSelectStage"
          @select-artifact="handleSelectArtifactPath"
        />
    </section>

    <!-- Panel Colapsible de Telemetría y Observabilidad (EventLogStream & PerimeterSecurityCard) -->
    <section v-if="showTelemetryPanel" class="p-4 bg-gray-850 bg-gray-900/95 text-white border-b border-gray-800">
      <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Log de Eventos en Vivo -->
        <div class="h-64">
          <EventLogStream :events="eventsHistory" :max-items="30" />
        </div>
        <!-- Auditoría de Perímetro Sandboxing -->
        <div>
          <PerimeterSecurityCard :perimeter-status="perimeterData" />
        </div>
      </div>
    </section>

    <!-- Sección de HITL Gates (Colapsible / Preservada) -->
    <section v-if="showHitlSection" class="px-4 py-2 bg-amber-50/50 border-b border-amber-200">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-amber-900">
          Compuertas Human-in-the-Loop (HITL)
        </span>
        <button
          type="button"
          @click="showGateControl = !showGateControl"
          class="text-xs text-amber-800 hover:text-amber-950 underline cursor-pointer"
        >
          {{ showGateControl ? 'Ocultar panel HITL' : 'Mostrar panel HITL' }}
        </button>
      </div>
      <div v-if="showGateControl" class="mt-3">
        <GateControl />
      </div>
    </section>

    <!-- Área Principal de Trabajo -->
    <main class="flex-1 p-4 overflow-y-auto min-h-[calc(100vh-210px)]">
      <!-- VISTA 1: TELEMETRÍA GIT (HU-004) -->
      <div v-if="activeView === 'git'" class="max-w-7xl mx-auto space-y-4">
        <!-- Banner de Contención por Bloqueo .git/index.lock -->
        <GitLockWarningBanner :is-syncing="gitTelemetry.isSyncing.value" />

        <!-- Empty State si no existe .git/ (HTTP 404 / GIT_REPO_NOT_FOUND) -->
        <GitRepoEmptyState
          v-if="gitTelemetry.isRepoNotFound.value"
          @retry="gitTelemetry.loadGitStatus(false)"
          @go-to-artifacts="activeView = 'artifacts'"
        />

        <!-- Contenido normal del repositorio Git -->
        <template v-else>
          <!-- Resumen de Telemetría: Rama, HEAD y métricas de working tree -->
          <GitTelemetryOverview
            :status="gitTelemetry.gitStatus.value"
            :is-loading="gitTelemetry.isLoadingStatus.value"
            @refresh="gitTelemetry.refreshAll"
          />

          <!-- Acordeón Clasificador de Área de Trabajo -->
          <GitWorkingTreeClassifier
            :working-tree="gitTelemetry.workingTree.value"
          />

          <!-- Línea de Tiempo y Detalle de Commits -->
          <GitCommitTimeline
            :commits="gitTelemetry.commits.value"
            :selected-commit="gitTelemetry.selectedCommit.value"
            :total-count="gitTelemetry.totalCommits.value"
            :page="gitTelemetry.page.value"
            :total-pages="gitTelemetry.totalPages.value"
            :has-more="gitTelemetry.hasMore.value"
            :is-loading="gitTelemetry.isLoadingCommits.value"
            @select-commit="gitTelemetry.selectCommit"
            @next-page="gitTelemetry.nextPage"
            @prev-page="gitTelemetry.prevPage"
            @go-to-page="gitTelemetry.goToPage"
            @load-more="gitTelemetry.loadMore"
          />
        </template>
      </div>

      <!-- VISTA 2: EXPLORADOR Y VISOR DE ARTEFACTOS -->
      <div v-else class="grid grid-cols-12 gap-4 h-full">
        <!-- Panel Izquierdo: Explorador de Artefactos (con tag [✨ NUEVO]) -->
        <aside class="col-span-12 md:col-span-4 lg:col-span-3 h-full min-h-[400px]">
          <ArtifactTreeExplorer
            :root-node="tree"
            :selected-path="selectedPath"
            :is-loading="isLoadingTree"
            :new-paths="recentlyMutatedPaths"
            @select-node="handleTreeNodeSelect"
            @refresh="loadTree"
          />
        </aside>

        <!-- Panel Derecho: Visor de Entregable / Empty State / Error Card / Large File Card -->
        <section class="col-span-12 md:col-span-8 lg:col-span-9 h-full min-h-[400px]">
          <!-- Caso A: Large File Metadata-Only Card (Estado 6 UX / CB-05 / ADR-012) -->
          <LargeFileMetadataCard
            v-if="largeFileMetadata"
            :metadata="largeFileMetadata"
            :requested-path="selectedPath || ''"
            @back="largeFileMetadata = null"
          />

          <!-- Caso B: Error Card (404, 403, 413, 415) -->
          <ArtifactErrorCard
            v-else-if="contentError"
            :error="contentError"
            :requested-path="selectedPath || ''"
            :has-last-valid="Boolean(lastValidPath)"
            @refresh-tree="loadTree"
            @revert-valid="revertToLastValid"
            @clear-error="handleClearError"
          />

          <!-- Caso C: Carpeta Vacía Seleccionada (Estado 5 UX) -->
          <ArtifactEmptyState
            v-else-if="isEmptyFolder"
            :folder-path="selectedPath || ''"
            :agent-role="activeAgentRole || ''"
            stage-status="En espera de turno agéntico"
          />

          <!-- Caso D: Visor de Documento Markdown / Mermaid (Estado 1 UX / US1) -->
          <ArtifactViewer
            v-else
            :artifact="artifactContent"
            :is-loading="isLoadingContent"
            :sync-status="connectionState === 'CONNECTED' ? 'En vivo vía WebSockets' : 'Modo desconectado'"
          />
        </section>
      </div>
    </main>

    <!-- Toast de notificaciones de PrimeVue -->
    <Toast />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useWorkflow } from '../composables/useWorkflow'
import { useArtifacts } from '../composables/useArtifacts'
import { useTrackerWebsocket } from '../composables/useTrackerWebsocket'
import { useGitTelemetry } from '../composables/useGitTelemetry'
import { fetchPerimeterStatus } from '../services/api_client'
import type {
  DirectoryNode,
  WorkflowStageStep,
  WebSocketMessage,
  WorkflowUpdatedPayload,
  ArtifactChangedPayload,
  PerimeterStatusResponse,
  SystemNoticePayload,
  GitStatusEventPayload,
} from '../types'
import WorkflowStepper from '../components/workflow/WorkflowStepper.vue'
import ArtifactTreeExplorer from '../components/artifacts/ArtifactTreeExplorer.vue'
import ArtifactViewer from '../components/artifacts/ArtifactViewer.vue'
import ArtifactEmptyState from '../components/artifacts/ArtifactEmptyState.vue'
import ArtifactErrorCard from '../components/artifacts/ArtifactErrorCard.vue'
import WebSocketStatusBadge from '../components/observability/WebSocketStatusBadge.vue'
import DebounceIndicator from '../components/observability/DebounceIndicator.vue'
import PerimeterSecurityCard from '../components/observability/PerimeterSecurityCard.vue'
import LargeFileMetadataCard from '../components/observability/LargeFileMetadataCard.vue'
import EventLogStream from '../components/observability/EventLogStream.vue'
import GateControl from '../components/GateControl.vue'
import GitTelemetryOverview from '../components/git/GitTelemetryOverview.vue'
import GitWorkingTreeClassifier from '../components/git/GitWorkingTreeClassifier.vue'
import GitCommitTimeline from '../components/git/GitCommitTimeline.vue'
import GitLockWarningBanner from '../components/git/GitLockWarningBanner.vue'
import GitRepoEmptyState from '../components/git/GitRepoEmptyState.vue'

// Notificaciones flotantes
let toast: ReturnType<typeof useToast> | null = null
try {
  toast = useToast()
} catch {
  // Toast context fallback
}

// Composables
const {
  activeStage,
  overallStatus,
  activeAgentRole,
  activeArtifactInProgress,
  stages,
  loadWorkflow,
  handleWorkflowUpdated,
} = useWorkflow()

const {
  tree,
  isLoadingTree,
  selectedPath,
  artifactContent,
  isLoadingContent,
  contentError,
  lastValidPath,
  isEmptyFolder,
  recentlyMutatedPaths,
  largeFileMetadata,
  loadTree,
  selectArtifact,
  revertToLastValid,
  handleArtifactChanged,
} = useArtifacts()

// Estado de Vista Activa (Artefactos vs Telemetría Git)
const activeView = ref<'artifacts' | 'git'>('artifacts')
const gitTelemetry = useGitTelemetry({ autoLoad: true })

// WebSocket Resiliente con State Catch-Up Pattern (T006, T018, T019)
const {
  connectionState,
  lastMessage,
  latencyMs,
  reconnectAttempt,
  nextReconnectDelaySeconds,
  reconnectManual,
} = useTrackerWebsocket({
  url: 'ws://localhost:8000/ws/v1/events',
  onCatchUpSync: async () => {
    await Promise.allSettled([loadWorkflow(), loadTree(), gitTelemetry.refreshAll()])
    toast?.add({
      severity: 'success',
      summary: '🟢 Reconexión Exitosa',
      detail: 'Estado del ecosistema sincronizado con el backend local (State Catch-Up)',
      life: 3000,
    })
  },
})


// Estado local de Observabilidad y Telemetría
const showHitlSection = ref<boolean>(true)
const showGateControl = ref<boolean>(false)
const showTelemetryPanel = ref<boolean>(false)

const eventsHistory = ref<WebSocketMessage[]>([])
const perimeterData = ref<PerimeterStatusResponse | null>(null)
const lastCoalescedCount = ref<number>(1)
const debounceTriggerTimestamp = ref<number>(0)

const overallStatusText = computed<string>(() => {
  if (overallStatus.value === 'IN_PROGRESS') {
    return `ENJAMBRE ACTIVO: FASE ${activeStage.value} - ${activeAgentRole.value || ''}`
  }
  if (overallStatus.value === 'COMPLETED') {
    return 'ENJAMBRE COMPLETADO: TODAS LAS ETAPAS CERRADAS'
  }
  return 'ENJAMBRE EN ESPERA'
})

// Handlers de Interacción
const handleSelectStage = (stage: WorkflowStageStep): void => {
  if (stage.generated_artifact_path) {
    activeView.value = 'artifacts'
    selectArtifact(stage.generated_artifact_path)
  }
}

const handleSelectArtifactPath = (path: string): void => {
  activeView.value = 'artifacts'
  selectArtifact(path)
}

const handleTreeNodeSelect = (node: DirectoryNode): void => {
  selectArtifact(node.relative_path, node)
}

const handleClearError = (): void => {
  if (lastValidPath.value) {
    revertToLastValid()
  } else {
    contentError.value = null
    selectedPath.value = null
  }
}

// Reactividad de Mensajes WebSocket (HU-003)
watch(lastMessage, (msg: WebSocketMessage | string | null) => {
  if (!msg || typeof msg !== 'object') return

  // Agregar al historial de telemetria
  eventsHistory.value.push(msg)

  const eventType = msg.event_type || msg.event
  const payload = (msg.payload || msg.data) as Record<string, unknown> | undefined

  // Amortiguacion de rafagas / Debounce indicator (US4 / ADR-010)
  if (msg.coalesced_count && msg.coalesced_count > 1) {
    lastCoalescedCount.value = msg.coalesced_count
    debounceTriggerTimestamp.value = Date.now()
  }

  // 1. Evento WORKFLOW_UPDATED (US1 / T011, T012)
  if (eventType === 'WORKFLOW_UPDATED' && payload) {
    handleWorkflowUpdated(payload as unknown as WorkflowUpdatedPayload)
    const agentName = (payload.agent_role as string) || (payload.active_agent_role as string) || 'Agente'
    const action = (payload.action_type as string) || `Fase ${payload.active_stage || ''}`
    
    if (payload.handoff_target === 'HUMANO' || (typeof payload.handoff_directive === 'string' && payload.handoff_directive.includes('@HUMANO'))) {
      showGateControl.value = true
    }

    // Si el visor tiene abierto el tracker_bmad.md, recargar en tiempo real
    if (selectedPath.value && selectedPath.value.includes('tracker_bmad.md')) {
      selectArtifact(selectedPath.value)
    }

    toast?.add({
      severity: 'info',
      summary: '⚡ Evento de Flujo',
      detail: `${agentName}: ${action}`,
      life: 4000,
    })
  }

  // 1b. Evento GATE_STATE_CHANGED
  else if (eventType === 'GATE_STATE_CHANGED') {
    showGateControl.value = true
  }

  // 2. Evento ARTIFACT_CHANGED (US2 / T016)
  else if (eventType === 'ARTIFACT_CHANGED' && payload) {
    handleArtifactChanged(payload as unknown as ArtifactChangedPayload)
    const relPath = (payload.relative_path as string) || msg.resource_path || ''
    const changeType = (payload.change_type as string) || 'modificado'
    toast?.add({
      severity: 'success',
      summary: '📄 Artefacto Notificado',
      detail: `Archivo ${changeType}: ${relPath}`,
      life: 4000,
    })
  }

  // 3. Evento SYSTEM_NOTICE (US4)
  else if (eventType === 'SYSTEM_NOTICE' && payload) {
    const notice = payload as unknown as SystemNoticePayload
    if (notice.absorbed_mutations_count) {
      lastCoalescedCount.value = notice.absorbed_mutations_count
      debounceTriggerTimestamp.value = Date.now()
    }
  }

  // 4. Evento GIT_STATUS_CHANGED (HU-004 / T006, T012)
  else if (eventType === 'GIT_STATUS_CHANGED') {
    gitTelemetry.handleWebSocketMessage(msg as unknown as WebSocketMessage<GitStatusEventPayload>)
    const gitPayload = payload as unknown as GitStatusEventPayload | undefined
    const branch = gitPayload?.current_branch || 'HEAD'
    const hash = gitPayload?.head_hash_short || 'commit'
    toast?.add({
      severity: 'info',
      summary: '🌿 Repositorio Git Actualizado',
      detail: `Rama: ${branch} | HEAD: ${hash}`,
      life: 3500,
    })
  }
})

onMounted(async () => {
  await Promise.allSettled([
    loadWorkflow(),
    loadTree(),
    gitTelemetry.refreshAll(),
    fetchPerimeterStatus()
      .then((data) => {
        perimeterData.value = data
      })
      .catch(() => {}),
  ])

  if (activeArtifactInProgress.value) {
    await selectArtifact(activeArtifactInProgress.value)
  }
})
</script>
