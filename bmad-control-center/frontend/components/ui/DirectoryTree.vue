<template>
  <ArtifactTreeExplorer
    :root-node="rootNode"
    :selected-path="selectedPath"
    :is-loading="isLoading"
    :new-paths="newPaths"
    @select-node="emit('select-node', $event)"
    @refresh="emit('refresh')"
  />
</template>

<script setup lang="ts">
import ArtifactTreeExplorer from '../artifacts/ArtifactTreeExplorer.vue'
import type { DirectoryNode } from '../../types'

interface Props {
  rootNode: DirectoryNode | null
  selectedPath?: string | null
  isLoading?: boolean
  newPaths?: Set<string>
}

withDefaults(defineProps<Props>(), {
  rootNode: null,
  selectedPath: null,
  isLoading: false,
})

const emit = defineEmits<{
  (e: 'select-node', node: DirectoryNode): void
  (e: 'refresh'): void
}>()
</script>
