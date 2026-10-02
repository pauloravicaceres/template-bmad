<template>
  <div class="flex flex-col h-full bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
    <!-- Header del Explorador -->
    <div class="p-3 border-b border-gray-100 bg-gray-50/70 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm">📁</span>
        <h2 class="text-xs font-bold uppercase tracking-wider text-gray-700">
          Explorador de Artefactos
        </h2>
      </div>
      <button
        type="button"
        @click="emit('refresh')"
        :disabled="isLoading"
        title="Actualizar árbol de artefactos"
        class="text-gray-400 hover:text-blue-600 p-1 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 cursor-pointer"
      >
        <span :class="['inline-block text-xs', isLoading ? 'animate-spin' : '']">↺</span>
      </button>
    </div>

    <!-- Caja de Búsqueda / Filtro -->
    <div class="p-2 border-b border-gray-100">
      <div class="relative flex items-center">
        <span class="absolute left-2.5 text-gray-400 text-xs">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar archivo... (Filtro)"
          class="w-full pl-7 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white transition-all text-gray-700"
        />
        <button
          v-if="searchQuery"
          type="button"
          @click="searchQuery = ''"
          class="absolute right-2 text-gray-400 hover:text-gray-600 text-xs"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Lista o Arbol de Nodos -->
    <div class="flex-1 overflow-y-auto p-2">
      <!-- Loading State -->
      <div v-if="isLoading && !rootNode" class="flex items-center justify-center p-8 text-xs text-gray-400">
        <span class="animate-spin mr-2">⚙</span> Cargando estructura...
      </div>

      <!-- Empty Root -->
      <div v-else-if="!filteredTree || (filteredTree.length === 0)" class="text-center p-6 text-xs text-gray-400">
        No se encontraron archivos coincidentes.
      </div>

      <!-- Recursive Tree List -->
      <div v-else class="space-y-0.5">
        <template v-for="node in filteredTree" :key="node.node_id">
          <TreeNodeItem
            :node="node"
            :selected-path="selectedPath"
            :expanded-nodes="expandedNodes"
            :new-paths="newPaths"
            :auto-expand="Boolean(searchQuery.trim())"
            @toggle-expand="toggleExpand"
            @select-node="onNodeSelect"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DirectoryNode } from '../../types'
import TreeNodeItem from './TreeNodeItem.vue'

interface Props {
  rootNode: DirectoryNode | null
  selectedPath?: string | null
  isLoading?: boolean
  newPaths?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  rootNode: null,
  selectedPath: null,
  isLoading: false,
})

const emit = defineEmits<{
  (e: 'select-node', node: DirectoryNode): void
  (e: 'refresh'): void
}>()

const searchQuery = ref<string>('')
const expandedNodes = ref<Set<string>>(new Set(['files', 'specs']))

const toggleExpand = (nodeId: string): void => {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

const onNodeSelect = (node: DirectoryNode): void => {
  emit('select-node', node)
}

// Filtro recursivo
function filterNode(node: DirectoryNode, query: string): DirectoryNode | null {
  if (node.name === '.specify' || node.relative_path === '.specify') {
    return null
  }
  const matches = node.name.toLowerCase().includes(query)
  if (node.node_type === 'FILE') {
    return matches ? { ...node } : null
  }

  const filteredChildren: DirectoryNode[] = []
  if (node.children) {
    for (const child of node.children) {
      const res = filterNode(child, query)
      if (res) filteredChildren.push(res)
    }
  }

  if (matches || filteredChildren.length > 0) {
    return {
      ...node,
      children: filteredChildren,
    }
  }
  return null
}

const filteredTree = computed<DirectoryNode[]>(() => {
  if (!props.rootNode) return []
  const initialNodes = (
    props.rootNode.children && props.rootNode.children.length > 0
      ? props.rootNode.children
      : [props.rootNode]
  ).filter(n => n.name !== '.specify' && n.relative_path !== '.specify')

  const query = searchQuery.value.trim().toLowerCase()
  if (!query) {
    return initialNodes
      .map(n => filterNode(n, ''))
      .filter((n): n is DirectoryNode => n !== null)
  }

  const result: DirectoryNode[] = []
  for (const n of initialNodes) {
    const filtered = filterNode(n, query)
    if (filtered) {
      result.push(filtered)
    }
  }
  return result
})
</script>
