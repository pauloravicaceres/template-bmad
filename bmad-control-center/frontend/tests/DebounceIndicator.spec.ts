import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import DebounceIndicator from '../components/observability/DebounceIndicator.vue'

describe('DebounceIndicator Component', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('NoDebeMostrarBadgeSiCoalescedCountEsUno', () => {
    // Act
    const wrapper = mount(DebounceIndicator, {
      props: {
        coalescedCount: 1,
        windowDurationMs: 200,
      },
    })

    // Assert
    expect(wrapper.text()).toBe('')
  })

  it('DebeMostrarBadgeCuandoCoalescedCountEsMayorAUno', async () => {
    // Act
    const wrapper = mount(DebounceIndicator, {
      props: {
        coalescedCount: 4,
        windowDurationMs: 200,
      },
    })
    await wrapper.vm.$nextTick()

    // Assert
    expect(wrapper.text()).toContain('Buffer Debounce: 4 mutaciones (200ms)')
  })

  it('DebeOcultarBadgeDespuesDeDosSegundos', async () => {
    // Act
    const wrapper = mount(DebounceIndicator, {
      props: {
        coalescedCount: 3,
        windowDurationMs: 200,
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Buffer Debounce: 3 mutaciones (200ms)')

    // Advance 2000ms
    vi.advanceTimersByTime(2000)
    await wrapper.vm.$nextTick()

    // Assert
    expect(wrapper.find('div').exists()).toBe(false)
  })

  it('AlCambiarTriggerTimestamp_DebeReactivarVisibilidad', async () => {
    // Arrange
    const wrapper = mount(DebounceIndicator, {
      props: {
        coalescedCount: 1,
        triggerTimestamp: 0,
      },
    })
    expect(wrapper.text()).toBe('')

    // Act
    await wrapper.setProps({
      coalescedCount: 5,
      triggerTimestamp: Date.now(),
    })

    // Assert
    expect(wrapper.text()).toContain('Buffer Debounce: 5 mutaciones (200ms)')
  })
})
