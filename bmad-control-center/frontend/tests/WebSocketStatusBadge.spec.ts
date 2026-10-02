import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WebSocketStatusBadge from '../components/observability/WebSocketStatusBadge.vue'

describe('WebSocketStatusBadge Component', () => {
  it('EstadoConnected_DebeMostrarBadgeVerdeYLatencia', () => {
    // Act
    const wrapper = mount(WebSocketStatusBadge, {
      props: {
        status: 'CONNECTED',
        latencyMs: 14,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('[🟢 WS: CONECTADO]')
    expect(wrapper.text()).toContain('(14ms)')
  })

  it('EstadoReconnecting_DebeMostrarBadgeNaranjaConReintentosYBotonForzar', async () => {
    // Act
    const wrapper = mount(WebSocketStatusBadge, {
      props: {
        status: 'RECONNECTING',
        reconnectAttempt: 2,
        nextRetrySeconds: 4.2,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('[🟠 WS: RECONECTANDO (Intento 2 - 4.2s)]')
    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('↺ Forzar')

    await button.trigger('click')
    expect(wrapper.emitted('manual-reconnect')).toBeTruthy()
  })

  it('EstadoDisconnected_DebeMostrarBadgeRojoYBotonConectar', async () => {
    // Act
    const wrapper = mount(WebSocketStatusBadge, {
      props: {
        status: 'DISCONNECTED',
      },
    })

    // Assert
    expect(wrapper.text()).toContain('[🔴 WS: DESCONECTADO]')
    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('↺ Conectar')

    await button.trigger('click')
    expect(wrapper.emitted('manual-reconnect')).toBeTruthy()
  })
})
