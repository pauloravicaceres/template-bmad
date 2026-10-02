import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ArtifactViewer from '../components/artifacts/ArtifactViewer.vue'
import type { ArtifactContent } from '../types'
import mermaid from 'mermaid'

describe('ArtifactViewer Component', () => {
  const mockArtifact: ArtifactContent = {
    relative_path: 'files/business-analyst/002-HU_monitoreo.md',
    filename: '002-HU_monitoreo.md',
    raw_content: '# Especificación Técnica\n\nEste es un párrafo explicativo.\n\n```mermaid\nflowchart TD\nStart --> Stop\n```\n\nFin del documento.',
    detected_format: 'MARKDOWN',
    encoding: 'utf-8',
    size_bytes: 1024,
    is_oversized: false,
    is_unsupported_media: false,
    mime_type: 'text/markdown',
    last_modified: '2026-09-30T23:14:00Z',
  }

  it('SinArtefactoSeleccionado_DebeRenderizarMensajeInformativo', () => {
    // Act
    const wrapper = mount(ArtifactViewer, {
      props: {
        artifact: null,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('Sin archivo seleccionado')
    expect(wrapper.text()).toContain('Selecciona un documento Markdown desde el explorador')
  })

  it('ConArtefactoValido_DebeRenderizarHeaderDeMetadatosYContenidoMarkdown', async () => {
    // Arrange
    vi.spyOn(mermaid, 'parse').mockResolvedValue(true as any)
    vi.spyOn(mermaid, 'render').mockResolvedValue({
      svg: '<svg id="diagram-rendered"></svg>',
    } as any)

    // Act
    const wrapper = mount(ArtifactViewer, {
      props: {
        artifact: mockArtifact,
        isLoading: false,
        syncStatus: 'En vivo vía WebSockets',
      },
    })
    await flushPromises()

    // Assert
    expect(wrapper.text()).toContain('VISOR DE ENTREGABLE: 002-HU_monitoreo.md')
    expect(wrapper.text()).toContain('files/business-analyst/002-HU_monitoreo.md')
    expect(wrapper.text()).toContain('Formato: UTF-8 MARKDOWN | Tamaño: 1 KB')
    expect(wrapper.text()).toContain('En vivo vía WebSockets')
    expect(wrapper.html()).toContain('<h1>Especificación Técnica</h1>')
    expect(wrapper.text()).toContain('Este es un párrafo explicativo.')
    expect(wrapper.text()).toContain('Fin del documento.')
    expect(wrapper.html()).toContain('<svg id="diagram-rendered">')
  })
})
