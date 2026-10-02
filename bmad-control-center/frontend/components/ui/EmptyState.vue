<template>
  <ArtifactEmptyState
    :folder-path="folderPath"
    :agent-role="agentRole"
    :stage-status="stageStatus"
  />
</template>

<script setup lang="ts">
import ArtifactEmptyState from '../artifacts/ArtifactEmptyState.vue'

interface Props {
  folderPath?: string
  agentRole?: string
  stageStatus?: string
}

withDefaults(defineProps<Props>(), {
  folderPath: '',
  agentRole: '',
  stageStatus: 'En espera de turno agéntico',
})
</script>
