<template>
  <div class="inline-flex items-center gap-2">
    <!-- Badge Conectado (Happy Path) -->
    <div
      v-if="status === 'CONNECTED'"
      class="inline-flex items-center gap-1.5 bg-emerald-950/70 border border-emerald-500/60 text-emerald-300 px-2.5 py-1 rounded-md text-xs font-mono shadow-xs"
    >
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <span class="font-bold">[🟢 WS: CONECTADO]</span>
      <span v-if="latencyMs > 0" class="text-[10px] text-emerald-400 opacity-90">
        ({{ latencyMs }}ms)
      </span>
    </div>

    <!-- Badge Reconectando (Sad Path - SC-03 / ADR-011) -->
    <div
      v-else-if="status === 'RECONNECTING'"
      class="inline-flex items-center gap-2 bg-amber-950/80 border border-amber-500 text-amber-300 px-2.5 py-1 rounded-md text-xs font-mono shadow-xs"
    >
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
      </span>
      <span class="font-bold">
        [🟠 WS: RECONECTANDO {{ reconnectAttempt > 0 ? `(Intento ${reconnectAttempt} - ${nextRetrySeconds}s)` : '' }}]
      </span>
      <button
        type="button"
        @click="emit('manual-reconnect')"
        class="bg-amber-600 hover:bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded cursor-pointer transition-colors"
        title="Forzar reconexión inmediata"
      >
        ↺ Forzar
      </button>
    </div>

    <!-- Badge Desconectado -->
    <div
      v-else
      class="inline-flex items-center gap-2 bg-red-950/80 border border-red-500 text-red-300 px-2.5 py-1 rounded-md text-xs font-mono shadow-xs"
    >
      <span class="h-2 w-2 rounded-full bg-red-500"></span>
      <span class="font-bold">[🔴 WS: DESCONECTADO]</span>
      <button
        type="button"
        @click="emit('manual-reconnect')"
        class="bg-red-700 hover:bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded cursor-pointer transition-colors"
      >
        ↺ Conectar
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConnectionStatus } from '../../composables/useTrackerWebsocket'

interface Props {
  status: ConnectionStatus
  latencyMs?: number
  reconnectAttempt?: number
  nextRetrySeconds?: number
}

withDefaults(defineProps<Props>(), {
  latencyMs: 0,
  reconnectAttempt: 0,
  nextRetrySeconds: 0,
})

const emit = defineEmits<{
  (e: 'manual-reconnect'): void
}>()
</script>
