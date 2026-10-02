import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { useTrackerWebsocket } from '../composables/useTrackerWebsocket'
import * as apiClient from '../services/api_client'

vi.mock('../services/api_client', () => ({
  fetchWorkflowStatus: vi.fn().mockResolvedValue({}),
  fetchArtifactsTree: vi.fn().mockResolvedValue({}),
}))

describe('useTrackerWebsocket Composable', () => {
  let mockWebSocketInstances: MockWebSocket[] = []

  class MockWebSocket {
    url: string
    onopen: (() => void) | null = null
    onmessage: ((event: { data: string }) => void) | null = null
    onclose: (() => void) | null = null
    onerror: ((error: unknown) => void) | null = null
    readyState: number = 1
    sentMessages: string[] = []

    constructor(url: string) {
      this.url = url
      mockWebSocketInstances.push(this)
    }

    send(data: string) {
      this.sentMessages.push(data)
    }

    close() {
      if (this.onclose) {
        this.onclose()
      }
    }
  }

  beforeEach(() => {
    vi.useFakeTimers()
    mockWebSocketInstances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('AlConectarExitosamente_DebeCambiarEstadoAConnected', () => {
    // Arrange & Act
    const { connectionState, isConnected } = useTrackerWebsocket('ws://localhost:8000/ws')

    expect(mockWebSocketInstances).toHaveLength(1)
    const wsInstance = mockWebSocketInstances[0]

    // Simulate onopen
    wsInstance.onopen?.()

    // Assert
    expect(isConnected.value).toBe(true)
    expect(connectionState.value).toBe('CONNECTED')
  })

  it('AlCerrarConexionInesperadamente_DebeCambiarEstadoAReconnectingYProgramarBackoff', () => {
    // Arrange
    const { connectionState, isConnected, isReconnecting, reconnectAttempt } = useTrackerWebsocket('ws://localhost:8000/ws')
    const wsInstance = mockWebSocketInstances[0]
    wsInstance.onopen?.()

    // Act - Simular desconexión I/O
    wsInstance.onclose?.()

    // Assert
    expect(isConnected.value).toBe(false)
    expect(isReconnecting.value).toBe(true)
    expect(connectionState.value).toBe('RECONNECTING')
    expect(reconnectAttempt.value).toBe(1)
  })

  it('AlRecibirHeartbeatPong_DebeCalcularLatencyMs', () => {
    // Arrange
    const { latencyMs } = useTrackerWebsocket('ws://localhost:8000/ws')
    const wsInstance = mockWebSocketInstances[0]
    wsInstance.onopen?.()

    // Trigger Heartbeat timer (30s)
    vi.advanceTimersByTime(30000)
    expect(wsInstance.sentMessages).toHaveLength(1)
    expect(wsInstance.sentMessages[0]).toContain('HEARTBEAT_PING')

    // Act - Simulate PONG response 25ms later
    vi.advanceTimersByTime(25)
    wsInstance.onmessage?.({
      data: JSON.stringify({ event_type: 'HEARTBEAT_PONG', timestamp: Date.now() }),
    })

    // Assert
    expect(latencyMs.value).toBeGreaterThanOrEqual(25)
  })

  it('AlReconectarTrasDesconexion_DebeEjecutarStateCatchUpConcurrenteYCallback', async () => {
    // Arrange
    const onCatchUpSyncMock = vi.fn()
    const { connectionState } = useTrackerWebsocket({
      url: 'ws://localhost:8000/ws',
      onCatchUpSync: onCatchUpSyncMock,
    })

    const firstWs = mockWebSocketInstances[0]
    firstWs.onopen?.()
    expect(connectionState.value).toBe('CONNECTED')

    // Disconnect
    firstWs.onclose?.()
    expect(connectionState.value).toBe('RECONNECTING')

    // Advance timer to trigger reconnect (Backoff ~1s)
    vi.advanceTimersByTime(2000)
    expect(mockWebSocketInstances).toHaveLength(2)

    const secondWs = mockWebSocketInstances[1]

    // Act - onopen en la reconexión
    secondWs.onopen?.()

    // Flush promises
    await flushPromises()

    // Assert
    expect(apiClient.fetchWorkflowStatus).toHaveBeenCalled()
    expect(apiClient.fetchArtifactsTree).toHaveBeenCalled()
    expect(onCatchUpSyncMock).toHaveBeenCalled()
    expect(connectionState.value).toBe('CONNECTED')
  })

  it('AlLlamarReconnectManual_DebeForzarIntentoInmediato', () => {
    // Arrange
    const { connectionState, reconnectManual } = useTrackerWebsocket('ws://localhost:8000/ws')
    const firstWs = mockWebSocketInstances[0]
    firstWs.onopen?.()
    firstWs.onclose?.()

    expect(connectionState.value).toBe('RECONNECTING')
    expect(mockWebSocketInstances).toHaveLength(1)

    // Act
    reconnectManual()

    // Assert - nueva instancia creada inmediatamente sin esperar timer
    expect(mockWebSocketInstances).toHaveLength(2)
  })
})
