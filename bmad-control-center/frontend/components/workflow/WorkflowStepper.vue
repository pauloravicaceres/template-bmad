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
    <div class="flex items-center gap-2 overflow-x-auto py-2">
      <template v-for="(stage, index) in stages" :key="stage.stage_key">
        <!-- Stage Step -->
        <button
          type="button"
          @click="onStageClick(stage)"
          :class="[
            'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 border whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-offset-1',
            stage.is_active || stage.status === 'IN_PROGRESS'
              ? 'bg-blue-50 border-blue-500 text-blue-900 shadow-sm ring-2 ring-blue-400 ring-offset-1'
              : stage.status === 'COMPLETED'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100 cursor-pointer'
              : 'bg-gray-50 border-gray-200 text-gray-400 hover:bg-gray-100'
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
              <span class="text-gray-400">○</span>
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
          v-if="index < stages.length - 1"
          class="text-gray-300 font-bold select-none text-xs flex-shrink-0"
        >
          ──▶
        </span>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WorkflowStageStep } from '../../types'

interface Props {
  stages: WorkflowStageStep[]
  activeStageKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  stages: () => [],
  activeStageKey: '',
})

const emit = defineEmits<{
  (e: 'select-stage', stage: WorkflowStageStep): void
  (e: 'select-artifact', path: string): void
}>()

const completedCount = computed<number>(() => {
  return props.stages.filter((s) => s.status === 'COMPLETED').length
})

const totalCount = computed<number>(() => {
  return props.stages.length || 8
})

const onStageClick = (stage: WorkflowStageStep): void => {
  emit('select-stage', stage)
  if (stage.generated_artifact_path) {
    emit('select-artifact', stage.generated_artifact_path)
  }
}
</script>
