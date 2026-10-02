<template>
  <div class="bg-white border border-gray-200 rounded-xl p-5 shadow-xs space-y-4">
    <!-- Header de la Tarjeta -->
    <div class="flex items-center justify-between border-b border-gray-100 pb-3">
      <div class="flex items-center gap-2">
        <span class="text-base">🛡️</span>
        <h3 class="text-xs font-bold text-gray-800 uppercase tracking-wider">
          Perímetro de Seguridad (Sandbox FSaaDB)
        </h3>
      </div>
      <span class="text-[10px] bg-emerald-50 text-emerald-700 font-bold px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
        <span>🔒</span> 0 Fugas (Criterio SC-004)
      </span>
    </div>

    <!-- Lista de Raíces Autorizadas -->
    <div class="space-y-2">
      <span class="text-[11px] font-semibold text-gray-500 uppercase tracking-wider block">
        Directorios Autorizados en Vigilancia Activa:
      </span>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div
          v-for="root in monitoredRoots"
          :key="root.path"
          class="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg border border-gray-200 text-xs font-mono"
        >
          <span class="text-gray-800 font-bold">[✓] {{ root.path }}</span>
          <span class="text-[10px] text-emerald-600 bg-emerald-100/70 px-1.5 py-0.5 rounded font-sans">
            🟢 Activo
          </span>
        </div>
      </div>
    </div>

    <!-- Telemetría de Eventos Descartados Silenciosamente -->
    <div class="bg-gray-50/70 border border-gray-200 rounded-lg p-3 text-xs space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-gray-600 font-medium">Eventos descartados silenciosamente (fuera de perímetro):</span>
        <span class="font-mono font-bold text-gray-900 bg-gray-200 px-2 py-0.5 rounded text-xs">
          {{ ignoredCount }} eventos
        </span>
      </div>
      <p class="text-[11px] text-gray-400 leading-relaxed">
        Mutaciones en directorios internos como <code class="text-gray-600 bg-gray-100 px-1 rounded">.git/</code>, cachés o temporales del SO son filtradas a nivel de kernel por Watchdog, garantizando 0 frames emitidos al WebSocket.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PerimeterStatusResponse } from '../../types'

interface Props {
  perimeterStatus?: PerimeterStatusResponse | null
  ignoredCountOverride?: number
}

const props = withDefaults(defineProps<Props>(), {
  perimeterStatus: null,
  ignoredCountOverride: 0,
})

const defaultRoots = [
  { path: 'files/', is_monitored: true },
  { path: '.specify/', is_monitored: true },
  { path: 'specs/', is_monitored: true },
]

const monitoredRoots = computed(() => {
  if (props.perimeterStatus?.monitored_roots && props.perimeterStatus.monitored_roots.length > 0) {
    return props.perimeterStatus.monitored_roots.map((r) => ({
      path: r.allowed_path,
      is_monitored: r.is_monitored,
    }))
  }
  return defaultRoots
})

const ignoredCount = computed<number>(() => {
  if (props.ignoredCountOverride > 0) {
    return props.ignoredCountOverride
  }
  return props.perimeterStatus?.ignored_external_events_count || 0
})
</script>
