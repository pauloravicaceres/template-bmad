import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import Index from '../pages/index.vue'

vi.mock('../components/WorkspaceDashboard.vue', () => ({ default: { template: '<div>Workspace activo</div>' } }))
afterEach(() => vi.unstubAllGlobals())

describe('Registro de workspaces', () => {
  it('arranca vacío sin montar el dashboard ni consultar artefactos o sesiones', async () => {
    const fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ project_id: null }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ projects: [] }) })
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(Index)
    await flushPromises()
    expect(wrapper.text()).toContain('No hay proyectos registrados')
    expect(wrapper.text()).not.toContain('Workspace activo')
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('muestra el registro y supervisa solamente el proyecto seleccionado', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ project_id: 'a', project_name: 'Proyecto A' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ projects: [
        { project_id: 'a', workspace_root: '/work/a', selected: true },
        { project_id: 'b', workspace_root: '/work/b', selected: false },
      ] }) }))
    const wrapper = mount(Index)
    await flushPromises()
    expect(wrapper.text()).toContain('Proyecto A')
    expect(wrapper.findAll('li')).toHaveLength(2)
    expect(wrapper.text()).toContain('Workspace activo')
  })

  it('permite actualizar el registro tras inicializar un workspace', async () => {
    const fetch = vi.fn().mockImplementation(async (url: string) => ({ ok: true,
      json: async () => url.endsWith('/projects') ? { projects: [] } : { project_id: null },
    }))
    vi.stubGlobal('fetch', fetch)
    const wrapper = mount(Index)
    await flushPromises()
    fetch.mockImplementation(async (url: string) => ({ ok: true,
      json: async () => url.endsWith('/projects')
        ? { projects: [{ project_id: 'nuevo', workspace_root: '/work/nuevo', selected: false }] }
        : { project_id: null },
    }))
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('nuevo')
    expect(wrapper.text()).not.toContain('Workspace activo')
  })
})
