<template>
  <div class="bg-white border border-gray-200 rounded-lg shadow-xs p-4 mb-4">
    <!-- Header de la tarjeta -->
    <div class="flex items-center justify-between border-b border-gray-100 pb-3 mb-3">
      <div class="flex items-center gap-2">
        <span class="text-base">🌿</span>
        <h2 class="text-xs font-bold text-gray-800 uppercase tracking-wider">
          Telemetría Git | Estado del Repositorio Local (Read-Only)
        </h2>
        <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
          ● CONECTADO
        </span>
        <GitSpecialStateBadge
          :is-detached="status?.is_detached"
          :is-conflicted="status?.is_conflicted"
          :is-syncing="status?.is_syncing"
        />
      </div>

      <div class="flex items-center gap-2">
        <span class="text-[10px] text-gray-400 font-mono hidden sm:inline">
          Refresco reactivo &lt; 1s
        </span>
        <button
          type="button"
          @click="emit('refresh')"
          :disabled="isLoading"
          title="Actualizar telemetría Git"
          class="text-gray-400 hover:text-blue-600 p-1 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 cursor-pointer text-xs"
        >
          <span :class="['inline-block', isLoading ? 'animate-spin' : '']">↺</span>
        </button>
      </div>
    </div>

    <!-- 3 Tarjetas de Resumen (Grid) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <!-- Tarjeta 1: Rama Activa -->
      <div class="bg-gray-50 border border-gray-200/80 rounded-lg p-3">
        <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
          Rama Activa
        </div>
        <div class="text-xs font-mono font-bold text-gray-800 truncate mb-1" :title="status?.current_branch">
          🌿 {{ status?.current_branch || 'Desconocida' }}
        </div>
        <div class="text-[10px] text-gray-500">
          <span v-if="status?.upstream_branch" class="bg-gray-200 text-gray-700 px-1.5 py-0.2 rounded font-mono">
            Sincronizada con base: {{ status.upstream_branch }}
          </span>
          <span v-else class="text-gray-400 italic">
            Rama local
          </span>
        </div>
      </div>

      <!-- Tarjeta 2: Último Commit (HEAD) -->
      <div class="bg-gray-50 border border-gray-200/80 rounded-lg p-3">
        <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
          Último Commit (HEAD)
        </div>
        <div class="text-xs font-mono font-bold text-gray-800 truncate mb-1" :title="status?.head_commit_message">
          🔀 <span class="text-blue-600">{{ status?.head_commit_short || '-------' }}</span> - "{{ status?.head_commit_message || 'Sin commit' }}"
        </div>
        <div class="text-[10px] text-gray-500 truncate">
          👤 {{ status?.head_commit_author || 'Anónimo' }}
          <span v-if="status?.head_committed_at" class="text-gray-400 ml-1">
            | 🕒 {{ formatTime(status.head_committed_at) }}
          </span>
        </div>
      </div>

      <!-- Tarjeta 3: Resumen Working Tree -->
      <div class="bg-gray-50 border border-gray-200/80 rounded-lg p-3">
        <div class="text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-1">
          Estado del Área de Trabajo
        </div>
        <div class="text-xs font-bold text-gray-800 mb-1">
          ● {{ status?.total_modified_files ?? 0 }} Archivos Mutados
        </div>
        <div class="flex items-center gap-1.5 text-[10px] font-mono font-semibold">
          <span class="text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded">
            {{ status?.staged_count ?? 0 }} Staged
          </span>
          <span class="text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.2 rounded">
            {{ status?.unstaged_count ?? 0 }} Unstaged
          </span>
          <span class="text-gray-600 bg-gray-100 border border-gray-200 px-1.5 py-0.2 rounded">
            {{ status?.untracked_count ?? 0 }} Untracked
          </span>
        </div>
      </div>
    </div>

    <!-- Footer informativo -->
    <div class="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-[10px] text-gray-400 font-mono">
      <span>Repositorio: {{ status?.captured_at_utc ? `Capturado a las ${formatUtc(status.captured_at_utc)}` : 'En espera' }}</span>
      <span class="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
        Modo: Solo Lectura (Zero Mutaciones)
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GitStatusResponse } from '../../types'
import GitSpecialStateBadge from './GitSpecialStateBadge.vue'

interface Props {
  status: GitStatusResponse | null
  isLoading?: boolean
}

withDefaults(defineProps<Props>(), {
  status: null,
  isLoading: false,
})

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const formatTime = (isoString: string): string => {
  try {
    const d = new Date(isoString)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}

const formatUtc = (isoString: string): string => {
  try {
    const d = new Date(isoString)
    return d.toISOString().substring(11, 19) + ' UTC'
  } catch {
    return isoString
  }
}
</script>
