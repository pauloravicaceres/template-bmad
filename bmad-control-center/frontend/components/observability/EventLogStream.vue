<template>
  <div class="bg-white border border-gray-200 rounded-lg shadow-xs overflow-hidden flex flex-col h-full">
    <!-- Header -->
    <div class="p-3 border-b border-gray-100 bg-gray-50/70 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-xs">📡</span>
        <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">
          Log de Eventos en Vivo (WS Stream)
        </h3>
      </div>
      <span class="text-[10px] text-gray-400 font-mono">
        {{ recentEvents.length }} eventos
      </span>
    </div>

    <!-- Events List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-2 text-xs font-sans">
      <div v-if="recentEvents.length === 0" class="text-center p-6 text-gray-400 text-xs">
        En espera de eventos en tiempo real...
      </div>

      <div
        v-for="(ev, idx) in recentEvents"
        :key="ev.event_id || idx"
        class="p-2.5 rounded-lg border transition-all text-xs space-y-1 bg-gray-50/80 hover:bg-gray-100/60"
        :class="getEventBorderClass(ev.event_type || ev.event)"
      >
        <!-- Top row: Type, Time, Badge -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5 font-bold">
            <span :class="getEventDotClass(ev.event_type || ev.event)">●</span>
            <span class="font-mono text-[11px]">{{ ev.event_type || ev.event || 'UNKNOWN' }}</span>
          </div>
          <span class="text-[10px] text-gray-400 font-mono">
            {{ formatTime(ev.timestamp) }}
          </span>
        </div>

        <!-- Details -->
        <div class="text-[11px] text-gray-600 font-mono pl-3 space-y-0.5 border-l border-gray-200 ml-1">
          <div v-if="ev.resource_path" class="truncate">
            <span class="text-gray-400">Recurso:</span> {{ ev.resource_path }}
          </div>
          <div v-if="getAgentRole(ev)">
            <span class="text-gray-400">Agente:</span> <span class="font-semibold text-gray-800">{{ getAgentRole(ev) }}</span>
          </div>
          <div v-if="getAction(ev)" class="truncate">
            <span class="text-gray-400">Acción:</span> {{ getAction(ev) }}
          </div>
          <div v-if="ev.coalesced_count && ev.coalesced_count > 1" class="text-amber-700 font-bold">
            ⚡ Coalescencia: {{ ev.coalesced_count }} mutaciones
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WebSocketMessage } from '../../types'

interface Props {
  events: WebSocketMessage[]
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  events: () => [],
  maxItems: 25,
})

const recentEvents = computed<WebSocketMessage[]>(() => {
  return [...props.events].slice(-props.maxItems).reverse()
})

const formatTime = (ts?: string): string => {
  if (!ts) return new Date().toLocaleTimeString()
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString()
  } catch {
    return ts
  }
}

const getAgentRole = (ev: WebSocketMessage): string | null => {
  const p = (ev.payload || ev.data) as Record<string, unknown> | undefined
  if (p && typeof p === 'object') {
    return (p.agent_role as string) || (p.active_agent_role as string) || null
  }
  return null
}

const getAction = (ev: WebSocketMessage): string | null => {
  const p = (ev.payload || ev.data) as Record<string, unknown> | undefined
  if (p && typeof p === 'object') {
    return (p.action_type as string) || (p.change_type as string) || (p.message as string) || null
  }
  return null
}

const getEventBorderClass = (type?: string): string => {
  if (type === 'WORKFLOW_UPDATED') return 'border-blue-200'
  if (type === 'ARTIFACT_CHANGED') return 'border-emerald-200'
  if (type === 'SYSTEM_NOTICE') return 'border-yellow-300 bg-yellow-50/50'
  return 'border-gray-200'
}

const getEventDotClass = (type?: string): string => {
  if (type === 'WORKFLOW_UPDATED') return 'text-blue-500'
  if (type === 'ARTIFACT_CHANGED') return 'text-emerald-500'
  if (type === 'SYSTEM_NOTICE') return 'text-yellow-600'
  return 'text-gray-400'
}
</script>
