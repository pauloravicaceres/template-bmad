import { ref, computed, onMounted, onUnmounted, getCurrentInstance } from 'vue'
import type { WebSocketMessage } from '../types'
import { fetchWorkflowStatus, fetchArtifactsTree } from '../services/api_client'

export type ConnectionStatus = 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED'

export interface UseTrackerWebsocketOptions {
  url?: string
  apiBase?: string
  onCatchUpSync?: () => void | Promise<void>
}

export function useTrackerWebsocket(optionsOrUrl: string | UseTrackerWebsocketOptions = 'ws://localhost:8000/ws') {
  const url = typeof optionsOrUrl === 'string' ? optionsOrUrl : optionsOrUrl.url || 'ws://localhost:8000/ws'
  const apiBase = typeof optionsOrUrl === 'object' ? optionsOrUrl.apiBase : undefined
  const onCatchUpSync = typeof optionsOrUrl === 'object' ? optionsOrUrl.onCatchUpSync : undefined

  const socket = ref<WebSocket | null>(null)
  const isConnected = ref<boolean>(false)
  const connectionState = ref<ConnectionStatus>('DISCONNECTED')
  const lastMessage = ref<WebSocketMessage | string | null>(null)
  const latencyMs = ref<number>(0)
  const reconnectAttempt = ref<number>(0)
  const nextReconnectDelaySeconds = ref<number>(0)

  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let isClosedExplicitly = false
  let lastPingTimestamp = 0
  let hasConnectedOnce = false

  const isReconnecting = computed<boolean>(() => connectionState.value === 'RECONNECTING')

  const triggerStateCatchUp = async (): Promise<void> => {
    try {
      await Promise.allSettled([
        fetchWorkflowStatus(true, apiBase),
        fetchArtifactsTree('all', apiBase),
      ])
      if (onCatchUpSync) {
        await onCatchUpSync()
      }
    } catch (e) {
      console.warn('[useTrackerWebsocket] Error durante State Catch-Up REST:', e)
    }
  }

  const connect = (): void => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    try {
      socket.value = new WebSocket(url)
    } catch {
      isConnected.value = false
      connectionState.value = 'RECONNECTING'
      scheduleReconnect()
      return
    }

    socket.value.onopen = () => {
      isConnected.value = true
      connectionState.value = 'CONNECTED'
      startHeartbeat()

      // Si es una reconexion (ya habia estado conectado antes o hubo reintentos), ejecutar State Catch-Up
      if (hasConnectedOnce || reconnectAttempt.value > 0) {
        triggerStateCatchUp()
      }
      hasConnectedOnce = true
      reconnectAttempt.value = 0
      nextReconnectDelaySeconds.value = 0
    }

    socket.value.onmessage = (event: MessageEvent<string>) => {
      let parsed: WebSocketMessage | string
      try {
        parsed = JSON.parse(event.data) as WebSocketMessage
      } catch {
        parsed = event.data
      }

      // Si es respuesta PONG / HEARTBEAT_PONG, calcular latencia
      if (typeof parsed === 'object' && parsed !== null) {
        const evType = parsed.event || parsed.event_type
        if (evType === 'PONG' || evType === 'HEARTBEAT_PONG') {
          if (lastPingTimestamp > 0) {
            latencyMs.value = Math.max(1, Date.now() - lastPingTimestamp)
          }
          return
        }
      }

      lastMessage.value = parsed
    }

    socket.value.onclose = () => {
      isConnected.value = false
      stopHeartbeat()

      if (!isClosedExplicitly) {
        connectionState.value = 'RECONNECTING'
        scheduleReconnect()
      } else {
        connectionState.value = 'DISCONNECTED'
      }
    }

    socket.value.onerror = () => {
      // Manejo sin lanzar excepcion no capturada
    }
  }

  const scheduleReconnect = (): void => {
    if (isClosedExplicitly || reconnectTimer) {
      return
    }

    // Algoritmo de Backoff Exponencial con Jitter (1s, 2s, 4s, 8s, max 10s)
    const baseDelay = 1000 * Math.pow(2, reconnectAttempt.value)
    const jitter = Math.random() * 300
    const delayMs = Math.min(baseDelay + jitter, 10000)

    reconnectAttempt.value++
    nextReconnectDelaySeconds.value = Math.round(delayMs / 100) / 10

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delayMs)
  }

  const reconnectManual = (): void => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    isClosedExplicitly = false
    reconnectAttempt.value = 0
    connectionState.value = 'RECONNECTING'
    connect()
  }

  const startHeartbeat = (): void => {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (socket.value && socket.value.readyState === 1 && typeof socket.value.send === 'function') {
        lastPingTimestamp = Date.now()
        socket.value.send(JSON.stringify({ event: 'PING', event_type: 'HEARTBEAT_PING' }))
      }
    }, 30000)
  }

  const stopHeartbeat = (): void => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  const send = (payload: Record<string, unknown> | string): void => {
    if (socket.value && socket.value.readyState === 1 && typeof socket.value.send === 'function') {
      const data = typeof payload === 'string' ? payload : JSON.stringify(payload)
      socket.value.send(data)
    }
  }

  const close = (): void => {
    isClosedExplicitly = true
    stopHeartbeat()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket.value) {
      socket.value.close()
    }
    connectionState.value = 'DISCONNECTED'
    isConnected.value = false
  }

  if (getCurrentInstance()) {
    onMounted(() => {
      connect()
    })

    onUnmounted(() => {
      close()
    })
  } else {
    connect()
  }

  return {
    socket,
    isConnected,
    isReconnecting,
    connectionState,
    lastMessage,
    latencyMs,
    reconnectAttempt,
    nextReconnectDelaySeconds,
    reconnectManual,
    send,
    connect,
    close,
  }
}

