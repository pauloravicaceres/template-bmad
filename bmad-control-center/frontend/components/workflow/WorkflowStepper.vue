<template>
  <div class="w-full bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500">
        Pipeline de Agentes (Workflow Progress)
      </h3>
      <span class="text-xs font-medium text-gray-500">
        {{ completedCount }} de {{ totalCount }} etapas completadas
      </span>
    </div>

    <!-- Stepper horizontal con scroll responsivo -->
    <div class="flex items-center gap-3 overflow-x-auto py-2">
      <template v-for="(group, gIndex) in groupedStages" :key="group.name">
        <!-- Contenedor del Grupo -->
        <div class="flex flex-col gap-2 bg-gray-50 border border-gray-100 rounded-xl p-2.5">
          <!-- Título del Grupo -->
          <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">
            {{ group.name }}
          </div>
          
          <!-- Botones de Etapa -->
          <div class="flex items-center gap-2">
            <template v-for="(stage, sIndex) in group.stages" :key="stage.stage_key">
              <!-- Stage Step -->
              <button
                type="button"
                @click="onStageClick(stage)"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 border whitespace-nowrap focus:outline-none focus:ring-offset-1',
                  stage.is_active || stage.status === 'IN_PROGRESS'
                    ? 'bg-blue-50 text-blue-900 shadow-sm ' + (localSelectedStageKey === stage.stage_key ? 'border-blue-600 ring-2 ring-blue-500 scale-[1.02]' : 'border-blue-500 ring-1 ring-blue-200')
                    : stage.status === 'COMPLETED'
                      ? 'bg-emerald-50 text-emerald-800 cursor-pointer ' + (localSelectedStageKey === stage.stage_key ? 'border-emerald-600 ring-2 ring-emerald-500 scale-[1.02]' : 'border-emerald-300 hover:bg-emerald-100')
                      : 'bg-white text-gray-400 cursor-pointer ' + (localSelectedStageKey === stage.stage_key ? 'border-gray-500 ring-2 ring-gray-400 bg-gray-50 scale-[1.02]' : 'border-gray-200 hover:bg-gray-50')
                ]"
                :title="stage.agent_role"
              >
                <!-- Status Icon -->
                <span class="flex items-center justify-center w-5 h-5 rounded-full text-[11px] font-bold">
                  <template v-if="stage.status === 'COMPLETED'">
                    <span class="text-emerald-600">✓</span>
                  </template>
                  <template v-else-if="stage.is_active || stage.status === 'IN_PROGRESS'">
                    <span class="relative flex h-2.5 w-2.5">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-600"></span>
                    </span>
                  </template>
                  <template v-else>
                    <span class="text-gray-400">·</span>
                  </template>
                </span>

                <!-- Stage Key & Name -->
                <div class="flex flex-col text-left">
                  <div class="flex items-center gap-1.5">
                    <span class="font-bold">{{ stage.stage_key }}</span>
                    <span class="text-[11px] opacity-80 hidden sm:inline">{{ stage.stage_name }}</span>
                  </div>
                  <span
                    v-if="stage.is_active || stage.status === 'IN_PROGRESS'"
                    class="text-[10px] text-blue-600 font-semibold tracking-wide"
                  >
                    [● EN PROGRESO]
                  </span>
                </div>
              </button>

              <!-- Connector Arrow -->
              <span
                v-if="sIndex < group.stages.length - 1"
                class="text-gray-300 font-bold select-none text-xs flex-shrink-0"
              >
                →
              </span>
            </template>
          </div>
        </div>

        <!-- Connector Arrow BETWEEN GROUPS -->
        <div v-if="gIndex < groupedStages.length - 1" class="flex-shrink-0 text-gray-300 px-1">
          <svg class="w-5 h-5 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path>
          </svg>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { WorkflowStageStep } from '../../types'

interface Props {
  stages: WorkflowStageStep[]
  activeStageKey?: string
  selectedPath?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  stages: () => [],
  activeStageKey: '',
  selectedPath: null,
})

const localSelectedStageKey = ref<string | null>(null)

watch(() => props.selectedPath, (newPath) => {
  if (newPath) {
    const stage = props.stages.find(s => s.generated_artifact_path === newPath)
    if (stage) {
      localSelectedStageKey.value = stage.stage_key
    }
  }
}, { immediate: true })

const emit = defineEmits<{
  (e: 'select-stage', stage: WorkflowStageStep): void
  (e: 'select-artifact', path: string): void
}>()

const completedCount = computed<number>(() => {
  return props.stages.filter((s) => s.status === 'COMPLETED').length
})

const totalCount = computed<number>(() => {
  return props.stages.length || 12
})

// Lógica de Agrupación por Categorías
const groupedStages = computed(() => {
  const allStages = props.stages || []
  
  // Categoría 1: Negocio y Producto (PM, BA, QA, UX)
  const negocio = allStages.filter(s => ['PM', 'BA', 'QA', 'UX'].includes(s.stage_key))
  
  // Categoría 2: Arquitectura e Ingeniería (SA, DA, API, QT)
  const arquitectura = allStages.filter(s => ['SA', 'DA', 'API', 'QT'].includes(s.stage_key))
  
  // Categoría 3: Desarrollo y Despliegue (DEV-BACK, DEV-FRONT, QA-AUTO, CR)
  const desarrollo = allStages.filter(s => ['DEV-BACK', 'DEV-FRONT', 'QA-AUTO', 'CR'].includes(s.stage_key))
  
  // Si no hacen match estricto, los agrupamos dinámicamente según índice o fallbacks
  const groups = []
  if (negocio.length > 0) groups.push({ name: 'Negocio y Producto', stages: negocio })
  if (arquitectura.length > 0) groups.push({ name: 'Arquitectura e Ingeniería', stages: arquitectura })
  if (desarrollo.length > 0) groups.push({ name: 'Desarrollo y Despliegue', stages: desarrollo })
  
  // Rescate de etapas no mapeadas por si se expande en el futuro
  const mappedKeys = new Set([...negocio, ...arquitectura, ...desarrollo].map(s => s.stage_key))
  const unmapped = allStages.filter(s => !mappedKeys.has(s.stage_key))
  if (unmapped.length > 0) {
    groups.push({ name: 'Otros', stages: unmapped })
  }
  
  return groups
})

const onStageClick = (stage: WorkflowStageStep): void => {
  localSelectedStageKey.value = stage.stage_key
  emit('select-stage', stage)
  if (stage.generated_artifact_path) {
    emit('select-artifact', stage.generated_artifact_path)
  }
}
</script>