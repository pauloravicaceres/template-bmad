<template>
  <div class="bg-white border border-gray-200 rounded-lg shadow-xs p-4 mb-4">
    <!-- Header del Timeline -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-100 pb-3 mb-4 gap-2">
      <div class="flex items-center gap-2">
        <span class="text-sm">🔀</span>
        <h3 class="text-xs font-bold text-gray-800 uppercase tracking-wider">
          Historial de Commits (Ciclo de Vida Agéntico)
        </h3>
        <span class="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono font-semibold dark:bg-slate-700 dark:text-slate-100">
          {{ totalCount }} confirmaciones
        </span>
      </div>

      <!-- Filtro y controles -->
      <div class="flex items-center gap-2">
        <div class="relative flex items-center">
          <span class="absolute left-2.5 text-gray-400 text-xs">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filtrar mensaje o hash..."
            class="pl-7 pr-3 py-1 text-xs bg-gray-50 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 w-48 text-gray-700 font-mono"
          />
        </div>
      </div>
    </div>

    <!-- Si no hay commits -->
    <div
      v-if="commits.length === 0"
      class="text-center py-10 text-xs text-gray-400 bg-gray-50/50 rounded-lg border border-dashed border-gray-200 dark:bg-slate-800 dark:border-slate-700 dark:text-gray-300"
    >
      <span v-if="isLoading">⚙ Cargando historial de commits...</span>
      <span v-else>No se encontraron confirmaciones en el historial.</span>
    </div>

    <!-- Layout de Dos Columnas: Timeline Izquierdo + Detalle Derecho -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <!-- Columna Izquierda: Línea de Tiempo (7 cols) -->
      <div class="lg:col-span-7 flex flex-col h-[520px]">
        <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-2">
          Línea de Tiempo Cronológica
        </div>

        <div class="flex-1 overflow-y-auto pr-2 space-y-2 border-r border-gray-100">
          <div
            v-for="(commit, index) in filteredCommits"
            :key="commit.commit_hash"
            @click="onSelectCommit(commit)"
            :class="[
              'p-2.5 rounded-lg border cursor-pointer transition-all text-xs relative pl-6',
              selectedCommit?.commit_hash === commit.commit_hash
                ? 'bg-blue-50/80 border-blue-300 shadow-xs dark:bg-blue-950/60 dark:border-blue-700'
                : 'bg-gray-50/70 hover:bg-gray-100/70 border-gray-200/80 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-200'
            ]"
          >
            <!-- Línea conectora vertical -->
            <div
              v-if="index < filteredCommits.length - 1"
              class="absolute left-3 top-6 bottom-0 w-0.5 bg-gray-200 -mb-2"
            ></div>

            <!-- Nodo visual -->
            <span
              :class="[
                'absolute left-2 top-3 w-2.5 h-2.5 rounded-full border-2',
                index === 0
                  ? 'bg-blue-600 border-blue-400 ring-2 ring-blue-100'
                  : 'bg-white border-gray-400 dark:bg-slate-700 dark:border-slate-400'
              ]"
            ></span>

            <!-- Encabezado de commit -->
            <div class="flex items-center justify-between gap-1 mb-1">
              <div class="flex items-center gap-1.5 font-mono">
                <span class="font-bold text-blue-700 dark:text-blue-300">🔀 {{ commit.short_hash }}</span>
                <span
                  v-if="index === 0"
                  class="bg-blue-100 text-blue-800 text-[9px] px-1.5 py-0.2 rounded font-bold dark:bg-blue-900 dark:text-blue-100"
                >
                  HEAD
                </span>
              </div>
              <span class="text-[10px] text-gray-400 font-mono">
                {{ formatTime(commit.committed_at) }}
              </span>
            </div>

            <!-- Mensaje -->
            <div class="text-xs font-semibold text-gray-800 line-clamp-1 mb-1" :title="commit.message">
              "{{ commit.message }}"
            </div>

            <!-- Autor y agente -->
            <div class="flex items-center justify-between text-[10px] text-gray-500">
              <span class="truncate">
                👤 {{ commit.agent_role || commit.author_name }}
              </span>
              <span class="font-mono text-gray-400 shrink-0">
                {{ commit.files_changed_count }} archivos
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Detalle del Commit Seleccionado (5 cols) -->
      <div class="lg:col-span-5 bg-gray-50/90 border border-gray-200 rounded-lg p-3 flex flex-col h-[520px] dark:bg-slate-800 dark:border-slate-700">
        <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 border-b border-gray-200 pb-1.5 mb-2">
          Detalle del Commit Seleccionado
          <span v-if="selectedCommit" class="font-mono text-blue-700 dark:text-blue-300">
            [ {{ selectedCommit.short_hash }} ]
          </span>
        </div>

        <div v-if="selectedCommit" class="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
          <!-- Metadatos del commit -->
          <div class="space-y-1 bg-white p-2.5 rounded-md border border-gray-200/80 text-[11px] dark:bg-slate-900 dark:border-slate-700">
            <div>
              <span class="text-gray-400 font-mono">Hash:</span>
              <span class="font-mono text-gray-700 text-[10px] break-all ml-1 select-all">
                {{ selectedCommit.commit_hash }}
              </span>
            </div>
            <div>
              <span class="text-gray-400">Autor:</span>
              <span class="font-semibold text-gray-800 ml-1">
                {{ selectedCommit.author_name }} &lt;{{ selectedCommit.author_email }}&gt;
              </span>
            </div>
            <div>
              <span class="text-gray-400">Fecha:</span>
              <span class="text-gray-700 ml-1">
                {{ formatFullDate(selectedCommit.committed_at) }}
              </span>
            </div>
            <div class="pt-1 border-t border-gray-100">
              <span class="text-gray-400 block mb-0.5">Mensaje:</span>
              <div class="font-medium text-gray-900 bg-gray-50 p-1.5 rounded font-mono text-xs dark:bg-slate-800">
                {{ selectedCommit.message }}
              </div>
            </div>
          </div>

          <!-- Estadísticas de cambios -->
          <div class="bg-white p-2 rounded-md border border-gray-200/80 flex items-center justify-between text-[11px] font-mono dark:bg-slate-900 dark:border-slate-700">
            <span class="text-gray-600 font-semibold">
              {{ selectedCommit.files_changed_count }} mutaciones
            </span>
            <div class="flex items-center gap-2">
              <span class="text-emerald-700 font-bold dark:text-emerald-300">+{{ selectedCommit.insertions }}</span>
              <span class="text-red-600 font-bold dark:text-red-300">-{{ selectedCommit.deletions }}</span>
            </div>
          </div>

          <!-- Archivos modificados -->
          <div>
            <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
              Archivos Afectados ({{ selectedCommit.files?.length ?? selectedCommit.files_changed_count }})
            </div>

            <div v-if="selectedCommit.files && selectedCommit.files.length > 0" class="space-y-1">
              <template v-for="file in selectedCommit.files" :key="file.relative_path">
                <!-- Si es archivo binario o con diff omitido (>1MB) -->
                <GitBinaryDiffNotice
                  v-if="file.is_diff_omitted || file.is_binary"
                  :file-path="file.relative_path"
                  :size-bytes="file.size_bytes"
                />

                <!-- Archivo normal de texto -->
                <div
                  v-else
                  class="flex items-center justify-between py-1 px-2 bg-white rounded border border-gray-200/70 text-[10px] font-mono dark:bg-slate-900 dark:border-slate-700"
                >
                  <span class="truncate mr-2 text-gray-800" :title="file.relative_path">
                    {{ file.relative_path }}
                  </span>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <span v-if="file.insertions" class="text-emerald-700 font-semibold dark:text-emerald-300">+{{ file.insertions }}</span>
                    <span v-if="file.deletions" class="text-red-600 font-semibold dark:text-red-300">-{{ file.deletions }}</span>
                    <span class="bg-gray-100 text-gray-600 px-1 rounded text-[9px] uppercase">
                      {{ file.change_type }}
                    </span>
                  </div>
                </div>
              </template>
            </div>
            <div v-else class="text-[11px] text-gray-400 italic p-2 bg-white rounded border border-gray-100 dark:bg-slate-900 dark:border-slate-700 dark:text-gray-300">
              Desglose detallado no disponible para este commit.
            </div>
          </div>
        </div>

        <div v-else class="flex-1 flex items-center justify-center text-xs text-gray-400">
          Selecciona un commit del timeline para inspeccionar sus detalles.
        </div>

        <!-- Footer protegido -->
        <div class="mt-2 pt-2 border-t border-gray-200 text-[10px] text-gray-400 italic text-center">
          ℹ Visualización protegida contra mutaciones destructivas (Strict Read-Only).
        </div>
      </div>
    </div>

    <!-- Barra de Paginación -->
    <div class="mt-4 pt-3 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
      <div class="text-gray-500 text-[11px]">
        Página <span class="font-bold text-gray-800">{{ page }}</span> de <span class="font-bold text-gray-800">{{ totalPages }}</span>
        (Mostrando hasta 50 commits por página)
      </div>

      <div class="flex items-center gap-1.5">
        <button
          type="button"
          @click="emit('go-to-page', 1)"
          :disabled="page <= 1 || isLoading"
          class="px-2 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer text-xs"
        >
          ◀◀ Primera
        </button>

        <button
          type="button"
          @click="emit('prev-page')"
          :disabled="page <= 1 || isLoading"
          class="px-2.5 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer text-xs"
        >
          ◀ Anterior
        </button>

        <span class="px-2 font-mono text-[11px] text-gray-700">
          [ {{ page }} ]
        </span>

        <button
          type="button"
          @click="emit('next-page')"
          :disabled="page >= totalPages || isLoading"
          class="px-2.5 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer text-xs"
        >
          Siguiente ▶
        </button>

        <button
          type="button"
          @click="emit('go-to-page', totalPages)"
          :disabled="page >= totalPages || isLoading"
          class="px-2 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer text-xs"
        >
          Última ▶▶
        </button>

        <button
          v-if="hasMore"
          type="button"
          @click="emit('load-more')"
          :disabled="isLoading"
          class="ml-2 px-2.5 py-1 bg-blue-50 border border-blue-200 text-blue-700 rounded hover:bg-blue-100 disabled:opacity-40 cursor-pointer text-xs font-semibold dark:bg-blue-950/60 dark:border-blue-800 dark:text-blue-200 dark:hover:bg-blue-900"
        >
          ⚡ Cargar 50 Más
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { GitCommitItem } from '../../types'
import GitBinaryDiffNotice from './GitBinaryDiffNotice.vue'

interface Props {
  commits: GitCommitItem[]
  selectedCommit?: GitCommitItem | null
  totalCount?: number
  page?: number
  totalPages?: number
  hasMore?: boolean
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedCommit: null,
  totalCount: 0,
  page: 1,
  totalPages: 1,
  hasMore: false,
  isLoading: false,
})

const emit = defineEmits<{
  (e: 'select-commit', commit: GitCommitItem): void
  (e: 'next-page'): void
  (e: 'prev-page'): void
  (e: 'go-to-page', page: number): void
  (e: 'load-more'): void
}>()

const searchQuery = ref<string>('')

const filteredCommits = computed<GitCommitItem[]>(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return props.commits
  return props.commits.filter(
    (c) =>
      c.message.toLowerCase().includes(query) ||
      c.short_hash.toLowerCase().includes(query) ||
      c.author_name.toLowerCase().includes(query) ||
      (c.agent_role && c.agent_role.toLowerCase().includes(query))
  )
})

const onSelectCommit = (commit: GitCommitItem): void => {
  emit('select-commit', commit)
}

const formatTime = (isoString: string): string => {
  try {
    const d = new Date(isoString)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return isoString
  }
}

const formatFullDate = (isoString: string): string => {
  try {
    const d = new Date(isoString)
    return d.toLocaleString()
  } catch {
    return isoString
  }
}
</script>
