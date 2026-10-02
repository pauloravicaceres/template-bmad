<template>
  <div class="bg-white border border-amber-300 rounded-xl p-6 shadow-sm max-w-2xl mx-auto my-6 space-y-4">
    <!-- Header -->
    <div class="flex items-center gap-2 pb-3 border-b border-amber-200">
      <span class="text-xl">⚠️</span>
      <h3 class="text-xs font-bold text-amber-900 uppercase tracking-wide">
        Notificación: Artefacto Extenso Detectado (Política Metadata-Only)
      </h3>
    </div>

    <!-- Metadata Details -->
    <div class="bg-amber-50/70 p-3.5 rounded-lg border border-amber-200 space-y-2 text-xs font-mono">
      <div class="flex items-center justify-between">
        <span class="text-gray-500">Ruta detectada:</span>
        <span class="font-bold text-amber-950 truncate max-w-sm">{{ displayPath }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-gray-500">Tamaño físico:</span>
        <span class="font-bold text-red-700">{{ formattedSize }}</span>
      </div>
      <div v-if="metadata?.mime_type" class="flex items-center justify-between">
        <span class="text-gray-500">Tipo MIME:</span>
        <span class="text-gray-800">{{ metadata.mime_type }}</span>
      </div>
    </div>

    <!-- Explanatory note -->
    <p class="text-xs text-gray-600 leading-relaxed">
      El archivo seleccionado excede el umbral máximo de previsualización web (5 MB). Conforme a la política de seguridad y contención de memoria (ADR-009 y ADR-012), el contenido crudo no se vuelca a través del WebSocket para prevenir saturación de la memoria del navegador.
    </p>

    <div class="text-[11px] text-gray-500 bg-gray-50 p-2.5 rounded border border-gray-200">
      <span class="font-semibold text-gray-700">Acción recomendada:</span> Abrir e inspeccionar el archivo directamente desde el sistema de archivos local o editor del desarrollador (VS Code / IDE).
    </div>

    <!-- Actions -->
    <div class="flex gap-2 pt-2">
      <button
        type="button"
        @click="emit('back')"
        class="bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer transition-colors"
      >
        ◀ Volver al Explorador de Archivos
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FileMetadataRecord } from '../../types'

interface Props {
  metadata?: FileMetadataRecord | null
  requestedPath?: string
}

const props = withDefaults(defineProps<Props>(), {
  metadata: null,
  requestedPath: '',
})

const emit = defineEmits<{
  (e: 'back'): void
}>()

const displayPath = computed<string>(() => {
  return props.metadata?.relative_path || props.requestedPath || 'Desconocido'
})

const formattedSize = computed<string>(() => {
  const bytes = props.metadata?.size_bytes || 0
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
})
</script>
