<template>
  <ArtifactViewer
    :artifact="artifact"
    :is-loading="isLoading"
    :sync-status="syncStatus"
  />
</template>

<script setup lang="ts">
import ArtifactViewer from '../artifacts/ArtifactViewer.vue'
import type { ArtifactContent } from '../../types'

interface Props {
  artifact: ArtifactContent | null
  isLoading?: boolean
  syncStatus?: string
}

withDefaults(defineProps<Props>(), {
  artifact: null,
  isLoading: false,
  syncStatus: 'En vivo vía WebSockets',
})
</script>
