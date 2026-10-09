import { afterEach, describe, expect, it, vi } from 'vitest'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.resetModules()
})

describe('Project backend selection', () => {
  it('keeps HTTP and websocket on the same selected project backend', async () => {
    vi.stubEnv('VITE_BMAD_API_BASE', 'http://localhost:8002/api/v1/')
    vi.resetModules()
    const { DEFAULT_API_BASE, DEFAULT_WS_URL } = await import('../services/api_client')
    expect(DEFAULT_API_BASE).toBe('http://localhost:8002/api/v1')
    expect(DEFAULT_WS_URL).toBe('ws://localhost:8002/ws/v1/events')
  })
})
