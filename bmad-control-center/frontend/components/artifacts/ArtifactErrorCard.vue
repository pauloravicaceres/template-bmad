<template>
  <div class="p-6 bg-white border rounded-xl shadow-sm max-w-2xl mx-auto my-6">
    <!-- Estado 2 UX: Error 404 Not Found -->
    <div v-if="is404" class="space-y-4">
      <div class="flex items-center gap-2 pb-3 border-b border-amber-200">
        <span class="text-xl">⚠️</span>
        <h3 class="text-sm font-bold text-amber-900 uppercase">
          Artefacto No Encontrado (HTTP 404)
        </h3>
      </div>

      <p class="text-xs text-gray-700">
        El archivo solicitado ya no existe en el sistema de archivos local:
      </p>
      <div class="bg-amber-50 text-amber-950 font-mono text-xs p-2.5 rounded border border-amber-200 break-all">
        {{ targetPath }}
      </div>

      <div class="text-xs text-gray-500 space-y-1">
        <span class="font-semibold block text-gray-700">Posibles causas:</span>
        <ul class="list-disc list-inside space-y-0.5 ml-1">
          <li>El archivo fue renombrado o eliminado externamente.</li>
          <li>La tarea agéntica fue reiniciada y el artefacto fue purgado.</li>
        </ul>
      </div>

      <div class="flex flex-wrap gap-2 pt-2">
        <button
          type="button"
          @click="emit('refresh-tree')"
          class="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
        >
          <span>↺</span> Actualizar Árbol de Artefactos
        </button>
        <button
          v-if="hasLastValid"
          type="button"
          @click="emit('revert-valid')"
          class="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
        >
          <span>◀</span> Volver al Último Válido
        </button>
      </div>
    </div>

    <!-- Estado 4 UX: Error 403 Forbidden (Path Traversal Guard) -->
    <div v-else-if="is403" class="space-y-4">
      <div class="flex items-center gap-2 pb-3 border-b border-red-200">
        <span class="text-xl">🛑</span>
        <h3 class="text-sm font-bold text-red-900 uppercase">
          Acceso Denegado por Seguridad (HTTP 403 Forbidden)
        </h3>
      </div>

      <div class="text-xs text-gray-700">
        Ruta solicitada:
        <span class="font-mono bg-red-50 text-red-950 px-2 py-1 rounded border border-red-200 block mt-1 break-all">
          {{ targetPath }}
        </span>
      </div>

      <div class="bg-red-50/60 border border-red-200 rounded-lg p-3 text-xs text-red-900 space-y-2">
        <span class="font-bold flex items-center gap-1.5 text-red-800">
          <span>🛡️</span> POLÍTICA DE SEGURIDAD DEL ESPACIO DE TRABAJO:
        </span>
        <p class="leading-relaxed">
          El explorador opera en modo estricto de Sandbox. Solo se autoriza la lectura pasiva de entregables dentro de los siguientes directorios autorizados:
        </p>
        <ul class="list-disc list-inside ml-2 font-mono text-[11px] text-red-800">
          <li>docs/ (Entregables y artefactos agénticos)</li>
          <li>.specify/ (Constitución y especificaciones de gobernanza)</li>
          <li>specs/ (Especificaciones Spec Kit y State Ledger)</li>
        </ul>
        <p class="text-[11px] text-red-700">
          Cualquier intento de escape de directorio relativo (../) o acceso a rutas del SO queda bloqueado y auditado.
        </p>
      </div>

      <div class="pt-2">
        <button
          type="button"
          @click="emit('clear-error')"
          class="flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
        >
          <span>🛡️</span> Volver a la Zona Segura
        </button>
      </div>
    </div>

    <!-- Estado 6 UX: Error 413 Payload Too Large o 415 Unsupported Media Type -->
    <div v-else-if="is413 || is415" class="space-y-4">
      <div class="flex items-center gap-2 pb-3 border-b border-amber-200">
        <span class="text-xl">⚠️</span>
        <h3 class="text-sm font-bold text-amber-900 uppercase">
          Archivo No Renderizable en Modo Texto ({{ is413 ? 'HTTP 413' : 'HTTP 415' }})
        </h3>
      </div>

      <div class="flex items-center justify-between bg-amber-50 p-3 rounded-lg border border-amber-200 text-xs font-mono">
        <span class="text-amber-950 truncate max-w-sm">{{ targetPath }}</span>
        <span v-if="error?.metadata?.size_bytes" class="text-amber-800 font-semibold">
          {{ formatBytes(Number(error.metadata.size_bytes)) }}
        </span>
      </div>

      <p class="text-xs text-gray-600 leading-relaxed">
        El archivo seleccionado {{ is413 ? 'excede el límite máximo de previsualización (5 MB)' : 'posee un formato binario no representable en modo texto' }}.
        Para preservar el rendimiento y memoria del navegador, no se renderiza como documento Markdown.
      </p>

      <div class="text-xs text-gray-500 space-y-1">
        <span class="font-semibold text-gray-700 block">Acciones recomendadas:</span>
        <ul class="list-disc list-inside space-y-0.5 ml-1">
          <li>Abrir el archivo directamente en el editor del desarrollador (VS Code / IDE).</li>
          <li v-if="is413">Inspeccionar fragmentos mediante herramientas locales de consola.</li>
        </ul>
      </div>

      <div class="flex flex-wrap gap-2 pt-2">
        <button
          type="button"
          @click="emit('clear-error')"
          class="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
        >
          <span>◀</span> Volver al Explorador de Archivos
        </button>
      </div>
    </div>

    <!-- Error Generico -->
    <div v-else class="space-y-4">
      <div class="flex items-center gap-2 pb-3 border-b border-gray-200">
        <span class="text-xl">⚠️</span>
        <h3 class="text-sm font-bold text-gray-900 uppercase">
          Error al Cargar Artefacto
        </h3>
      </div>
      <p class="text-xs text-gray-600">
        {{ error?.message || 'Ocurrió un error inesperado al acceder al archivo.' }}
      </p>
      <div class="pt-2">
        <button
          type="button"
          @click="emit('refresh-tree')"
          class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg"
        >
          Reintentar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiClientError } from '../../services/api_client'

interface Props {
  error: ApiClientError | null
  requestedPath?: string
  hasLastValid?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  error: null,
  requestedPath: '',
  hasLastValid: false,
})

const emit = defineEmits<{
  (e: 'refresh-tree'): void
  (e: 'revert-valid'): void
  (e: 'clear-error'): void
}>()

const targetPath = computed<string>(() => {
  return props.requestedPath || props.error?.path || 'Desconocido'
})

const is404 = computed<boolean>(() => {
  return (
    props.error?.statusCode === 404 ||
    props.error?.errorCode === 'ARTIFACT_NOT_FOUND'
  )
})

const is403 = computed<boolean>(() => {
  return (
    props.error?.statusCode === 403 ||
    props.error?.errorCode === 'PATH_TRAVERSAL_DETECTED'
  )
})

const is413 = computed<boolean>(() => {
  return (
    props.error?.statusCode === 413 ||
    props.error?.errorCode === 'PAYLOAD_TOO_LARGE'
  )
})

const is415 = computed<boolean>(() => {
  return (
    props.error?.statusCode === 415 ||
    props.error?.errorCode === 'UNSUPPORTED_MEDIA_TYPE'
  )
})

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}
</script>
