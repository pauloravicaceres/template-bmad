<template>
  <div class="flex flex-col items-center justify-center p-8 bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl text-center min-h-[360px]">
    <!-- Icono y Titulo -->
    <div class="w-14 h-14 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-4 text-2xl shadow-xs">
      📁
    </div>

    <span class="text-xs font-bold tracking-wider text-blue-700 bg-blue-100/80 px-3 py-1 rounded-full uppercase mb-3">
      [ 📁 ETAPA SIN ENTREGABLES ]
    </span>

    <h3 class="text-base font-bold text-gray-800 mb-1">
      El agente '{{ displayAgentRole }}'
    </h3>
    <p class="text-xs text-gray-500 max-w-sm mb-4">
      aún no ha generado artefactos físicos en su carpeta de trabajo dentro del espacio de persistencia.
    </p>

    <!-- Estado actual -->
    <div class="bg-white border border-gray-200 rounded-lg p-3 max-w-xs w-full shadow-xs mb-4">
      <span class="text-[11px] text-gray-400 uppercase tracking-wider block mb-1">
        Estado actual de la etapa:
      </span>
      <span class="text-xs font-semibold text-amber-600 flex items-center justify-center gap-1.5">
        <span>⏳</span> {{ displayStageStatus }}
      </span>
    </div>

    <p class="text-xs text-gray-400 max-w-md">
      La vista se actualizará automáticamente cuando el agente emita su entrega a través del canal reactivo.
    </p>

    <div
      v-if="folderPath"
      class="mt-6 text-[11px] text-gray-500 bg-gray-100 px-3 py-1.5 rounded-md font-mono"
    >
      Carpeta: <span class="font-bold text-gray-700">{{ folderPath }}</span> (0 archivos encontrados)
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  folderPath?: string
  agentRole?: string
  stageStatus?: string
}

const props = withDefaults(defineProps<Props>(), {
  folderPath: '',
  agentRole: '',
  stageStatus: 'En espera de turno agéntico',
})

const displayAgentRole = computed<string>(() => {
  if (props.agentRole) return props.agentRole
  if (props.folderPath) {
    const segments = props.folderPath.split('/').filter(Boolean)
    const last = segments[segments.length - 1]
    if (last) {
      return last
        .split('-')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ')
    }
  }
  return 'Agente Asignado'
})

const displayStageStatus = computed<string>(() => {
  return props.stageStatus || 'En espera de turno agéntico'
})
</script>
