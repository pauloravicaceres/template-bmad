import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import MermaidErrorBoundary from '../components/artifacts/MermaidErrorBoundary.vue'
import mermaid from 'mermaid'

describe('MermaidErrorBoundary Component (SC-003 / ADR-008)', () => {
  it('CompilacionExitosa_DebeInyectarSvgEnContenedor', async () => {
    // Arrange
    vi.spyOn(mermaid, 'parse').mockResolvedValue(true as any)
    vi.spyOn(mermaid, 'render').mockResolvedValue({
      svg: '<svg id="diagram-1"><g>Diagram Content</g></svg>',
    } as any)

    // Act
    const wrapper = mount(MermaidErrorBoundary, {
      props: {
        code: 'flowchart TD\nA-->B',
        diagramId: 'test-diagram-1',
      },
    })
    await flushPromises()

    // Assert
    expect(wrapper.html()).toContain('<svg id="diagram-1">')
    expect(wrapper.text()).not.toContain('ERROR BOUNDARY')
  })

  it('ErrorDeSintaxisMermaid_DebeCapturarExcepcionYRenderizarTarjetaAmbarConCodigoCrudo', async () => {
    // Arrange
    const invalidSyntax = 'sequenceDiagram\nOperador ->> Servidor: POST -->> (ERROR)'
    vi.spyOn(mermaid, 'parse').mockRejectedValue(
      new Error("Parse error on line 2: Unexpected token '-->>'")
    )

    // Act
    const wrapper = mount(MermaidErrorBoundary, {
      props: {
        code: invalidSyntax,
        diagramId: 'test-diagram-err',
      },
    })
    await flushPromises()

    // Assert
    expect(wrapper.text()).toContain('ERROR BOUNDARY: Fallo de Sintaxis en Diagrama Mermaid')
    expect(wrapper.text()).toContain('(i) Error de Parseo')
    expect(wrapper.text()).toContain("Unexpected token '-->>'")
    expect(wrapper.text()).toContain(invalidSyntax)
    // No debe lanzar excepcion ni romper la vista (SC-003)
  })

  it('CodigoVacio_DebeManejarloSinRomperEjecucion', async () => {
    // Act
    const wrapper = mount(MermaidErrorBoundary, {
      props: {
        code: '',
      },
    })
    await flushPromises()

    // Assert
    expect(wrapper.text()).toContain('ERROR BOUNDARY')
    expect(wrapper.text()).toContain('El código del diagrama está vacío')
  })
})
