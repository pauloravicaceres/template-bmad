import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GateControl from '../components/GateControl.vue'

const detalle = "Identificador de HU inválido: '003-HU_gestion.md' usa guiones bajos (snake_case no admitido)"

const fetchConDecision = (decision: { ok: boolean; status: number; body: unknown }) =>
  vi.fn().mockImplementation(async (_url: string, options?: { method?: string }) => {
    if (options?.method === 'POST') {
      return { ok: decision.ok, status: decision.status, json: async () => decision.body }
    }
    return { ok: true, status: 200, json: async () => ({ status: 'PENDING_DECISION' }) }
  })

describe('GateControl - rechazo de identificadores de HU', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Approve_CuandoBackendRechazaElIdentificador_DebeMostrarElMotivo', async () => {
    globalThis.fetch = fetchConDecision({ ok: false, status: 422, body: { detail: detalle } })
    const wrapper = mount(GateControl)
    await flushPromises()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toBe(detalle)
  })

  it('Approve_CuandoBackendAcepta_NoDebeMostrarError', async () => {
    globalThis.fetch = fetchConDecision({ ok: true, status: 200, body: { message: 'Decision recorded' } })
    const wrapper = mount(GateControl)
    await flushPromises()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })
})
