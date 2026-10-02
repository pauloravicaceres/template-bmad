<template>
  <WorkflowStepper
    :stages="stages"
    :active-stage-key="activeStageKey"
    @select-stage="emit('select-stage', $event)"
    @select-artifact="emit('select-artifact', $event)"
  />
</template>

<script setup lang="ts">
import WorkflowStepper from '../workflow/WorkflowStepper.vue'
import type { WorkflowStageStep } from '../../types'

interface Props {
  stages: WorkflowStageStep[]
  activeStageKey?: string
}

withDefaults(defineProps<Props>(), {
  stages: () => [],
  activeStageKey: '',
})

const emit = defineEmits<{
  (e: 'select-stage', stage: WorkflowStageStep): void
  (e: 'select-artifact', path: string): void
}>()
</script>
