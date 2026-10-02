import { ref } from 'vue'
import mermaid from 'mermaid'

export interface MermaidRenderResult {
  success: boolean
  svg?: string
  errorMessage?: string
  rawCode: string
}

let isInitialized = false

export function useSafeMermaid() {
  const isRendering = ref<boolean>(false)

  const ensureInitialized = (): void => {
    if (!isInitialized && typeof window !== 'undefined') {
      try {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'loose',
          theme: 'default',
          suppressErrorRendering: true,
        })
        isInitialized = true
      } catch (e) {
        console.warn('Fallo al inicializar mermaid:', e)
      }
    }
  }

  const renderDiagram = async (id: string, code: string): Promise<MermaidRenderResult> => {
    ensureInitialized()
    isRendering.value = true

    try {
      // Intento de parseo sintactico
      const isValid = await mermaid.parse(code).catch((parseErr) => {
        throw parseErr
      })

      if (isValid === false) {
        throw new Error('Sintaxis de diagrama Mermaid no válida')
      }

      const { svg } = await mermaid.render(id, code)
      isRendering.value = false
      return {
        success: true,
        svg,
        rawCode: code,
      }
    } catch (err: unknown) {
      isRendering.value = false
      const errorMsg =
        err instanceof Error ? err.message : String(err || 'Error de parseo en sintaxis Mermaid')
      return {
        success: false,
        errorMessage: errorMsg,
        rawCode: code,
      }
    }
  }

  return {
    isRendering,
    renderDiagram,
  }
}
