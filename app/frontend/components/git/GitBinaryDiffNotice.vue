<template>
  <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 shadow-xs my-2">
    <div class="flex items-center justify-between font-semibold text-gray-800 mb-1">
      <div class="flex items-center gap-1.5">
        <span class="text-sm">📄</span>
        <span class="font-mono">{{ filePath }}</span>
      </div>
      <span class="bg-slate-200 text-slate-700 text-[10px] px-2 py-0.5 rounded font-mono font-bold">
        [ ARCHIVO BINARIO - DIFF TEXTUAL OMITIDO ]
      </span>
    </div>

    <div class="text-[11px] text-gray-500 space-y-0.5">
      <div v-if="sizeBytes">
        Tamaño: <span class="font-mono font-semibold">{{ formatSize(sizeBytes) }}</span> (> Límite de inspección 1 MB)
      </div>
      <div>
        Acción: Se omitió el desglose línea por línea para proteger el rendimiento del navegador (ADR-014 / CB-05). Metadatos cargados con éxito.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  filePath: string
  sizeBytes?: number
}

defineProps<Props>()

const formatSize = (bytes: number): string => {
  if (bytes >= 1048576) {
    return `${(bytes / 1048576).toFixed(2)} MB`
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${bytes} B`
}
</script>
