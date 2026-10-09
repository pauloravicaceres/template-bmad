import type {
  WorkflowStatusResponse,
  ArtifactTreeResponse,
  ArtifactContent,
  ApiErrorResponse,
  WebSocketMessage,
  GitStatusResponse,
  GitCommitListResponse,
  GitBranchListResponse,
} from '../types'


export class ApiClientError extends Error {
  public errorCode: string
  public statusCode: number
  public timestamp: string
  public path: string
  public metadata?: Record<string, unknown>

  constructor(
    message: string,
    errorCode: string,
    statusCode: number,
    timestamp: string,
    path: string,
    metadata?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.errorCode = errorCode
    this.statusCode = statusCode
    this.timestamp = timestamp
    this.path = path
    this.metadata = metadata
  }
}

export const DEFAULT_API_BASE = (import.meta.env.VITE_BMAD_API_BASE || 'http://localhost:8000/api/v1').replace(/\/$/, '')
export const DEFAULT_WS_URL = DEFAULT_API_BASE.replace(/^http/, 'ws').replace(/\/api\/v1$/, '/ws/v1/events')

export async function fetchWorkflowStatus(
  includeHistory = true,
  apiBase = DEFAULT_API_BASE
): Promise<WorkflowStatusResponse> {
  const url = `${apiBase}/workflow/status?include_history=${includeHistory}`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al obtener el estado del flujo`,
      errorData.error_code || 'HTTP_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || '/workflow/status',
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as WorkflowStatusResponse
}

export async function fetchArtifactsTree(
  root = 'all',
  apiBase = DEFAULT_API_BASE
): Promise<ArtifactTreeResponse> {
  const url = `${apiBase}/artifacts/tree?root=${encodeURIComponent(root)}`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al obtener el árbol de artefactos`,
      errorData.error_code || 'HTTP_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || '/artifacts/tree',
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as ArtifactTreeResponse
}

export async function fetchArtifactContent(
  filePath: string,
  apiBase = DEFAULT_API_BASE
): Promise<ArtifactContent> {
  const url = `${apiBase}/artifacts/content?path=${encodeURIComponent(filePath)}&_t=${Date.now()}`
    const response = await fetch(url, {
      headers: { Accept: 'application/json', 'Cache-Control': 'no-cache' },
      cache: 'no-store'
    })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al leer el artefacto`,
      errorData.error_code || 'HTTP_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || `/artifacts/content?path=${filePath}`,
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as ArtifactContent
}

export async function fetchPerimeterStatus(
  apiBase = DEFAULT_API_BASE
): Promise<import('../types').PerimeterStatusResponse> {
  const url = `${apiBase}/observability/perimeter/status`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    throw new ApiClientError(
      'Error al obtener el estado perimetral de observabilidad',
      'PERIMETER_ERROR',
      response.status,
      new Date().toISOString(),
      '/observability/perimeter/status'
    )
  }
  return (await response.json()) as import('../types').PerimeterStatusResponse
}

export async function fetchGitStatus(
  apiBase = DEFAULT_API_BASE
): Promise<GitStatusResponse> {
  const url = `${apiBase}/git/status`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al consultar estado de Git`,
      errorData.error_code || 'GIT_STATUS_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || '/git/status',
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as GitStatusResponse
}

export async function fetchGitCommits(
  limit = 50,
  offset = 0,
  branch?: string,
  apiBase = DEFAULT_API_BASE
): Promise<GitCommitListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  if (branch) {
    params.set('branch', branch)
  }
  const url = `${apiBase}/git/commits?${params.toString()}`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al consultar commits de Git`,
      errorData.error_code || 'GIT_COMMITS_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || '/git/commits',
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as GitCommitListResponse
}

export async function fetchGitBranches(
  apiBase = DEFAULT_API_BASE
): Promise<GitBranchListResponse> {
  const url = `${apiBase}/git/branches`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {}
    try {
      errorData = (await response.json()) as Partial<ApiErrorResponse>
    } catch {
      // formato no json
    }
    throw new ApiClientError(
      errorData.detail || `HTTP ${response.status}: Error al consultar ramas de Git`,
      errorData.error_code || 'GIT_BRANCHES_ERROR',
      response.status,
      errorData.timestamp || new Date().toISOString(),
      errorData.path || '/git/branches',
      errorData.metadata as Record<string, unknown> | undefined
    )
  }
  return (await response.json()) as GitBranchListResponse
}

export type WebSocketListener<T = unknown> = (msg: WebSocketMessage<T>) => void


export class ResilientWebSocketClient {
  private url: string
  private socket: WebSocket | null = null
  private listeners: Set<WebSocketListener> = new Set()
  private isExplicitlyClosed = false
  private retryAttempt = 0
  private maxRetryDelay = 10000
  private baseRetryDelay = 1000
  private heartbeatIntervalId: ReturnType<typeof setInterval> | null = null
  private reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null

  public onStatusChange?: (connected: boolean) => void

  constructor(url = DEFAULT_WS_URL) {
    this.url = url
  }

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    this.isExplicitlyClosed = false
    try {
      this.socket = new WebSocket(this.url)
    } catch (err) {
      this.scheduleReconnect()
      return
    }

    this.socket.onopen = () => {
      this.retryAttempt = 0
      this.onStatusChange?.(true)
      this.startHeartbeat()
    }

    this.socket.onmessage = (event: MessageEvent<string>) => {
      let parsed: WebSocketMessage
      try {
        parsed = JSON.parse(event.data) as WebSocketMessage
      } catch {
        parsed = { event: 'RAW_TEXT', data: event.data }
      }

      if (parsed.event === 'PONG') {
        return
      }

      for (const listener of this.listeners) {
        try {
          listener(parsed)
        } catch (listenerError) {
          console.error('[WebSocket] Error en listener:', listenerError)
        }
      }
    }

    this.socket.onclose = () => {
      this.stopHeartbeat()
      this.onStatusChange?.(false)
      if (!this.isExplicitlyClosed) {
        this.scheduleReconnect()
      }
    }

    this.socket.onerror = (err) => {
      console.warn('[WebSocket] Error de socket:', err)
    }
  }

  public send(payload: Record<string, unknown>): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload))
    }
  }

  public subscribe(listener: WebSocketListener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  public subscribeArtifact(path: string): void {
    this.send({
      event: 'SUBSCRIBE_ARTIFACT',
      data: { path },
    })
  }

  public close(): void {
    this.isExplicitlyClosed = true
    this.stopHeartbeat()
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId)
      this.reconnectTimeoutId = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatIntervalId = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ event: 'PING' }))
      }
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId)
      this.heartbeatIntervalId = null
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeoutId || this.isExplicitlyClosed) {
      return
    }

    const jitter = Math.random() * 500
    const delay = Math.min(
      this.baseRetryDelay * Math.pow(2, this.retryAttempt) + jitter,
      this.maxRetryDelay
    )
    this.retryAttempt++

    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectTimeoutId = null
      this.connect()
    }, delay)
  }
}
