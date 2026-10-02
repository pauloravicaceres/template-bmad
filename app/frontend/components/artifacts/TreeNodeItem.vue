<template>
  <div class="text-xs select-none">
    <!-- Fila del Nodo Actual -->
    <div
      @click="handleClick"
      :class="[
        'flex items-center gap-1.5 py-1 px-2 rounded-md cursor-pointer transition-colors duration-150',
        isSelected
          ? 'bg-blue-50 text-blue-700 font-semibold'
          : 'text-gray-700 hover:bg-gray-100/80'
      ]"
      :style="{ paddingLeft: `${depth * 14 + 6}px` }"
    >
      <!-- Icono de expansión para carpetas -->
      <span
        v-if="node.node_type === 'DIRECTORY'"
        @click.stop="emit('toggle-expand', node.node_id)"
        class="w-3.5 text-[9px] text-gray-400 hover:text-gray-700 flex items-center justify-center cursor-pointer"
      >
        {{ isExpanded ? '▼' : '►' }}
      </span>
      <span v-else class="w-3.5"></span>

      <!-- Icono de tipo de nodo -->
      <span class="text-xs">
        {{ node.node_type === 'DIRECTORY' ? '📁' : '📄' }}
      </span>

      <!-- Nombre del archivo / directorio -->
      <span class="truncate flex-1" :title="node.name">
        {{ node.name }}
      </span>

      <!-- Badges informativos -->
      <template v-if="node.node_type === 'DIRECTORY'">
        <span
          v-if="node.is_empty || node.child_file_count === 0"
          class="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.2 rounded font-medium border border-amber-200"
        >
          (0) [VACÍO]
        </span>
        <span
          v-else-if="node.child_file_count !== undefined"
          class="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.2 rounded font-mono"
        >
          ({{ node.child_file_count }})
        </span>
      </template>

      <!-- Badge de archivo recién creado o mutado (Estado 2 UX / US2) -->
      <span
        v-if="isNew && node.node_type === 'FILE'"
        class="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.2 rounded border border-emerald-300 animate-pulse"
      >
        [✨ NUEVO]
      </span>

      <!-- Badge de archivo activo -->
      <span
        v-if="isSelected && node.node_type === 'FILE'"
        class="text-[10px] bg-blue-100 text-blue-800 font-bold px-1.5 py-0.2 rounded"
      >
        [ACTIVO]
      </span>
    </div>

    <!-- Hijos Recursivos si está expandido -->
    <div v-if="node.node_type === 'DIRECTORY' && isExpanded && node.children && node.children.length > 0">
      <template v-for="child in node.children" :key="child.node_id">
        <TreeNodeItem
          :node="child"
          :selected-path="selectedPath"
          :expanded-nodes="expandedNodes"
          :new-paths="newPaths"
          :auto-expand="autoExpand"
          :depth="depth + 1"
          @toggle-expand="emit('toggle-expand', $event)"
          @select-node="emit('select-node', $event)"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DirectoryNode } from '../../types'

interface Props {
  node: DirectoryNode
  selectedPath?: string | null
  expandedNodes: Set<string>
  newPaths?: Set<string>
  autoExpand?: boolean
  depth?: number
}

const props = withDefaults(defineProps<Props>(), {
  selectedPath: null,
  autoExpand: false,
  depth: 0,
})

const emit = defineEmits<{
  (e: 'toggle-expand', nodeId: string): void
  (e: 'select-node', node: DirectoryNode): void
}>()

const isExpanded = computed<boolean>(() => {
  if (props.autoExpand) return true
  return props.expandedNodes.has(props.node.node_id)
})

const isSelected = computed<boolean>(() => {
  return props.selectedPath === props.node.relative_path
})

const isNew = computed<boolean>(() => {
  return Boolean(props.newPaths?.has(props.node.relative_path))
})

const handleClick = (): void => {
  if (props.node.node_type === 'DIRECTORY') {
    emit('toggle-expand', props.node.node_id)
  }
  emit('select-node', props.node)
}
</script>
