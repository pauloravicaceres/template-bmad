<template>
  <div class="bg-white border border-gray-200 rounded-lg shadow-xs p-4 mb-4">
    <div class="flex items-center justify-between border-b border-gray-100 pb-2 mb-3">
      <div class="flex items-center gap-2">
        <span class="text-sm">📁</span>
        <h3 class="text-xs font-bold text-gray-800 uppercase tracking-wider">
          Área de Trabajo (Working Directory)
        </h3>
      </div>
      <span class="text-[10px] font-mono text-gray-500 font-semibold">
        Total: {{ totalCount }} mutaciones
      </span>
    </div>

    <!-- Si no hay archivos modificados -->
    <div
      v-if="totalCount === 0"
      class="text-center py-6 text-xs text-gray-400 bg-gray-50/60 rounded-md border border-dashed border-gray-200 font-mono dark:bg-slate-800 dark:border-slate-700 dark:text-gray-300"
    >
      ✨ Repositorio limpio. No hay modificaciones en el área de trabajo.
    </div>

    <div v-else class="space-y-3">
      <!-- 🔴 Conflictos de Fusión (si existen) -->
      <div v-if="conflicts.length > 0" class="border border-red-200 rounded-md overflow-hidden dark:border-red-900">
        <button
          type="button"
          @click="toggleSection('conflicts')"
          class="w-full flex items-center justify-between px-3 py-2 bg-red-50/80 text-red-800 text-xs font-bold hover:bg-red-100/70 transition-colors cursor-pointer text-left dark:bg-red-950/70 dark:text-red-200 dark:hover:bg-red-950"
        >
          <div class="flex items-center gap-1.5">
            <span class="text-[10px]">{{ isExpanded.conflicts ? '▼' : '►' }}</span>
            <span>🔴 ARCHIVOS EN CONFLICTO ({{ conflicts.length }})</span>
          </div>
          <span class="text-[10px] bg-red-200 text-red-900 px-1.5 py-0.2 rounded font-mono font-bold dark:bg-red-900 dark:text-red-100">
            Requiere resolución humana
          </span>
        </button>

        <div v-if="isExpanded.conflicts" class="p-2 space-y-1 bg-white dark:bg-slate-900">
          <div
            v-for="file in conflicts"
            :key="file.relative_path"
            class="flex items-center justify-between text-xs py-1 px-2 rounded bg-red-50/40 text-red-900 font-mono dark:bg-red-950/40 dark:text-red-200"
          >
            <div class="flex items-center gap-2 truncate">
              <span class="font-bold text-red-600 dark:text-red-300">[!]</span>
              <span class="truncate" :title="file.relative_path">{{ file.relative_path }}</span>
            </div>
            <span class="text-[10px] text-red-700 bg-red-100 px-1.5 py-0.2 rounded shrink-0 dark:bg-red-900 dark:text-red-200">
              Conflicto
            </span>
          </div>
        </div>
      </div>

      <!-- 🟢 Staged Changes -->
      <div class="border border-emerald-200 rounded-md overflow-hidden">
        <button
          type="button"
          @click="toggleSection('staged')"
          class="w-full flex items-center justify-between px-3 py-2 bg-emerald-50/80 text-emerald-800 text-xs font-bold hover:bg-emerald-100/70 transition-colors cursor-pointer text-left dark:bg-emerald-950/70 dark:text-emerald-200 dark:hover:bg-emerald-950"
        >
          <div class="flex items-center gap-1.5">
            <span class="text-[10px]">{{ isExpanded.staged ? '▼' : '►' }}</span>
            <span>🟢 STAGED CHANGES ({{ staged.length }})</span>
          </div>
          <span class="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-mono dark:bg-emerald-900 dark:text-emerald-100">
            Preparados para confirmación
          </span>
        </button>

        <div v-if="isExpanded.staged" class="p-2 space-y-1 bg-white dark:bg-slate-900">
          <div v-if="staged.length === 0" class="text-xs text-gray-400 py-1 px-2 italic">
            No hay cambios staged
          </div>
          <div
            v-for="file in staged"
            :key="file.relative_path"
            class="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-emerald-50/30 font-mono transition-colors dark:hover:bg-emerald-950/40"
          >
            <div class="flex items-center gap-2 truncate flex-1 mr-2">
              <span class="font-bold text-emerald-600 dark:text-emerald-300">[+]</span>
              <span class="truncate text-gray-800" :title="file.relative_path">{{ file.relative_path }}</span>
            </div>
            <div class="flex items-center gap-2 text-[10px] shrink-0">
              <span v-if="file.lines_added !== undefined" class="text-emerald-700 font-semibold dark:text-emerald-300">
                +{{ file.lines_added }}
              </span>
              <span v-if="file.lines_deleted !== undefined" class="text-red-600 font-semibold dark:text-red-300">
                -{{ file.lines_deleted }}
              </span>
              <span class="bg-gray-100 text-gray-600 px-1.5 py-0.2 rounded dark:bg-slate-800 dark:text-slate-200">
                {{ file.status_code || 'Staged' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 🟡 Unstaged Changes -->
      <div class="border border-amber-200 rounded-md overflow-hidden">
        <button
          type="button"
          @click="toggleSection('unstaged')"
          class="w-full flex items-center justify-between px-3 py-2 bg-amber-50/80 text-amber-800 text-xs font-bold hover:bg-amber-100/70 transition-colors cursor-pointer text-left dark:bg-amber-950/70 dark:text-amber-200 dark:hover:bg-amber-950"
        >
          <div class="flex items-center gap-1.5">
            <span class="text-[10px]">{{ isExpanded.unstaged ? '▼' : '►' }}</span>
            <span>🟡 UNSTAGED CHANGES ({{ unstaged.length }})</span>
          </div>
          <span class="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-mono dark:bg-amber-900 dark:text-amber-100">
            Modificados en disco
          </span>
        </button>

        <div v-if="isExpanded.unstaged" class="p-2 space-y-1 bg-white dark:bg-slate-900">
          <div v-if="unstaged.length === 0" class="text-xs text-gray-400 py-1 px-2 italic">
            No hay cambios unstaged
          </div>
          <div
            v-for="file in unstaged"
            :key="file.relative_path"
            class="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-amber-50/30 font-mono transition-colors dark:hover:bg-amber-950/40"
          >
            <div class="flex items-center gap-2 truncate flex-1 mr-2">
              <span class="font-bold text-amber-600 dark:text-amber-300">[M]</span>
              <span class="truncate text-gray-800" :title="file.relative_path">{{ file.relative_path }}</span>
            </div>
            <div class="flex items-center gap-2 text-[10px] shrink-0">
              <span class="bg-gray-100 text-gray-600 px-1.5 py-0.2 rounded dark:bg-slate-800 dark:text-slate-200">
                {{ file.status_code || 'Modificado' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- ⚪ Untracked Files -->
      <div class="border border-gray-200 rounded-md overflow-hidden">
        <button
          type="button"
          @click="toggleSection('untracked')"
          class="w-full flex items-center justify-between px-3 py-2 bg-gray-50 text-gray-700 text-xs font-bold hover:bg-gray-100 transition-colors cursor-pointer text-left dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          <div class="flex items-center gap-1.5">
            <span class="text-[10px]">{{ isExpanded.untracked ? '▼' : '►' }}</span>
            <span>⚪ UNTRACKED FILES ({{ untracked.length }})</span>
          </div>
          <span class="text-[10px] bg-gray-200 text-gray-700 px-1.5 py-0.2 rounded font-mono dark:bg-slate-700 dark:text-slate-100">
            No indexados
          </span>
        </button>

        <div v-if="isExpanded.untracked" class="p-2 space-y-1 bg-white dark:bg-slate-900">
          <div v-if="untracked.length === 0" class="text-xs text-gray-400 py-1 px-2 italic">
            No hay archivos untracked
          </div>
          <div
            v-for="file in untracked"
            :key="file.relative_path"
            class="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-gray-100/60 font-mono transition-colors dark:hover:bg-slate-800"
          >
            <div class="flex items-center gap-2 truncate flex-1 mr-2">
              <span class="font-bold text-gray-500">[?]</span>
              <span class="truncate text-gray-800" :title="file.relative_path">{{ file.relative_path }}</span>
            </div>
            <span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.2 rounded shrink-0 dark:bg-slate-800 dark:text-slate-200">
              Nuevo
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import type { GitWorkingTree } from '../../types'

interface Props {
  workingTree?: GitWorkingTree | null
}

const props = withDefaults(defineProps<Props>(), {
  workingTree: () => ({
    staged: [],
    unstaged: [],
    untracked: [],
    conflicts: [],
  }),
})

const isExpanded = reactive({
  staged: true,
  unstaged: true,
  untracked: true,
  conflicts: true,
})

const toggleSection = (section: keyof typeof isExpanded) => {
  isExpanded[section] = !isExpanded[section]
}

const staged = computed(() => props.workingTree?.staged ?? [])
const unstaged = computed(() => props.workingTree?.unstaged ?? [])
const untracked = computed(() => props.workingTree?.untracked ?? [])
const conflicts = computed(() => props.workingTree?.conflicts ?? [])

const totalCount = computed(() => {
  return staged.value.length + unstaged.value.length + untracked.value.length + conflicts.value.length
})
</script>
