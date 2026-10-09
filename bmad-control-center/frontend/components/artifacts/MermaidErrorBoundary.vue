<template>
  <div class="my-4">
    <!-- Estado: Cargando / Compilando -->
    <div
      v-if="isLoading"
      class="flex items-center justify-center p-6 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500"
    >
      <span class="animate-spin mr-2">⚙</span> Compilando diagrama Mermaid...
    </div>

    <!-- Estado Exitoso: Diagrama Renderizado (Happy Path) -->
    <div
      v-else-if="result?.success && result.svg"
      class="w-full bg-white border border-gray-200 rounded-lg p-4 shadow-xs overflow-x-auto"
    >
      <div
        class="flex justify-center items-center"
        v-html="result.svg"
      ></div>
    </div>

    <!-- Estado Fallido: Error Boundary (Sad Path - SC-03 / ADR-008) -->
    <div
      v-else
      class="w-full border border-amber-300 bg-amber-50/70 rounded-lg p-4 shadow-sm"
    >
      <!-- Header de Error Boundary -->
      <div class="flex items-center justify-between pb-2 border-b border-amber-200 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-amber-600 font-bold text-sm">⚠️ ERROR BOUNDARY:</span>
          <span class="text-xs font-semibold text-amber-900">
            Fallo de Sintaxis en Diagrama Mermaid
          </span>
        </div>
        <span class="text-[11px] bg-amber-100 text-amber-800 font-medium px-2 py-0.5 rounded border border-amber-300">
          (i) Error de Parseo
        </span>
      </div>

      <p class="text-xs text-amber-800 mb-3">
        El motor gráfico no pudo compilar el bloque Mermaid. Se despliega el código crudo para inspección técnica:
      </p>

      <!-- Bloque de código crudo -->
      <pre class="bg-gray-900 text-gray-100 text-xs p-3 rounded font-mono overflow-x-auto leading-relaxed border border-gray-800 mb-3"><code>{{ result?.rawCode || code }}</code></pre>

      <!-- Detalle emitido por el compilador -->
      <div
        v-if="result?.errorMessage"
        class="text-xs bg-amber-100/90 text-amber-950 p-2.5 rounded font-mono border border-amber-200"
      >
        <span class="font-bold">Detalle del compilador:</span> {{ result.errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useSafeMermaid, type MermaidRenderResult } from '../../composables/useSafeMermaid'

interface Props {
  code: string
  diagramId?: string
}

const props = withDefaults(defineProps<Props>(), {
  code: '',
  diagramId: '',
})

const { renderDiagram } = useSafeMermaid()
const isLoading = ref<boolean>(true)
const result = ref<MermaidRenderResult | null>(null)

let idCounter = 0
let themeObserver: MutationObserver | null = null
const generateUniqueId = (): string => {
  idCounter++
  return props.diagramId || `mermaid-diagram-${Date.now()}-${idCounter}`
}

const compile = async (): Promise<void> => {
  if (!props.code.trim()) {
    isLoading.value = false
    result.value = {
      success: false,
      errorMessage: 'El código del diagrama está vacío',
      rawCode: props.code,
    }
    return
  }

  isLoading.value = true
  const id = generateUniqueId()
  result.value = await renderDiagram(id, props.code)
  isLoading.value = false
}

onMounted(() => {
  compile()
  themeObserver = new MutationObserver(() => compile())
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

onBeforeUnmount(() => themeObserver?.disconnect())

watch(
  () => props.code,
  () => {
    compile()
  }
)
</script>
