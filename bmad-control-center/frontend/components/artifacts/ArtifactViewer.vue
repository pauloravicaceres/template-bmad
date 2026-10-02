<template>
  <div class="flex flex-col h-full bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
    <!-- Header de Metadatos del Archivo (Estado 1 UX) -->
    <div class="px-4 py-3 border-b border-gray-200 bg-gray-50 flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2 min-w-0">
        <span class="text-base">📄</span>
        <div class="min-w-0">
          <h2 class="text-xs font-bold text-gray-800 truncate" :title="artifact?.filename">
            VISOR DE ENTREGABLE: {{ artifact?.filename || 'Ningún archivo seleccionado' }}
          </h2>
          <p class="text-[11px] text-gray-500 font-mono truncate" :title="artifact?.relative_path">
            {{ artifact?.relative_path || 'Ruta activa: no seleccionada' }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span
          v-if="artifact"
          class="text-[10px] bg-gray-100 text-gray-700 px-2 py-0.5 rounded border border-gray-200 font-mono"
        >
          Formato: {{ artifact.encoding?.toUpperCase() || 'UTF-8' }} {{ artifact.detected_format }} | Tamaño: {{ formatBytes(artifact.size_bytes) }}
        </span>
        <span class="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200 font-medium flex items-center gap-1">
          <span>🟢</span> {{ syncStatus || 'En vivo vía WebSockets' }}
        </span>
      </div>
    </div>

    <!-- Contenedor Principal de Visualización -->
    <div class="flex-1 overflow-y-auto p-6 bg-white">
      <div v-if="isLoading" class="flex items-center justify-center p-12 text-xs text-gray-400">
        <span class="animate-spin mr-2">⚙</span> Cargando contenido del artefacto...
      </div>

      <div v-else-if="!artifact" class="flex flex-col items-center justify-center p-16 text-center text-gray-400">
        <span class="text-4xl mb-3">📋</span>
        <h3 class="text-sm font-semibold text-gray-600 mb-1">Sin archivo seleccionado</h3>
        <p class="text-xs max-w-sm text-gray-400">
          Selecciona un documento Markdown desde el explorador de artefactos lateral para inspeccionar su contenido y diagramas.
        </p>
      </div>

      <div v-else class="space-y-4 max-w-none">
        <template v-for="segment in segments" :key="segment.id">
          <!-- Bloque HTML compilado desde Markdown -->
          <div
            v-if="segment.type === 'html'"
            class="markdown-body prose prose-sm max-w-none text-gray-800 leading-relaxed text-xs [&>h1]:text-lg [&>h1]:font-bold [&>h1]:mt-4 [&>h1]:mb-2 [&>h1]:border-b [&>h1]:pb-1 [&>h2]:text-base [&>h2]:font-bold [&>h2]:mt-3 [&>h2]:mb-1.5 [&>h3]:text-sm [&>h3]:font-bold [&>h3]:mt-2 [&>h3]:mb-1 [&>p]:mb-2 [&>ul]:list-disc [&>ul]:ml-4 [&>ul]:mb-2 [&>ol]:list-decimal [&>ol]:ml-4 [&>ol]:mb-2 [&>pre]:bg-gray-900 [&>pre]:text-gray-100 [&>pre]:p-3 [&>pre]:rounded-md [&>pre]:overflow-x-auto [&>pre]:mb-2 [&>code]:bg-gray-100 [&>code]:text-red-600 [&>code]:px-1 [&>code]:py-0.5 [&>code]:rounded [&>code]:font-mono [&>code]:text-[11px] [&>table]:w-full [&>table]:border [&>table]:border-collapse [&>table]:mb-3 [&>table_th]:border [&>table_th]:p-1.5 [&>table_th]:bg-gray-50 [&>table_td]:border [&>table_td]:p-1.5"
            v-html="segment.content"
          ></div>

          <!-- Bloque de Diagrama Mermaid Aislado (MermaidErrorBoundary) -->
          <MermaidErrorBoundary
            v-else-if="segment.type === 'mermaid'"
            :code="segment.content"
            :diagram-id="segment.id"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ArtifactContent } from '../../types'
import MermaidErrorBoundary from './MermaidErrorBoundary.vue'

interface Props {
  artifact: ArtifactContent | null
  isLoading?: boolean
  syncStatus?: string
}

const props = withDefaults(defineProps<Props>(), {
  artifact: null,
  isLoading: false,
  syncStatus: 'En vivo vía WebSockets',
})

interface Segment {
  id: string
  type: 'html' | 'mermaid'
  content: string
}

const segments = computed<Segment[]>(() => {
  if (!props.artifact || !props.artifact.raw_content) {
    return []
  }

  let raw = props.artifact.raw_content

  // [REQUERIMIENTO] Invertir orden del tracker (acciones recientes primero)
  if (props.artifact.filename === 'tracker_bmad.md' || props.artifact.relative_path.includes('tracker_bmad.md')) {
    const blocks = raw.split(/(?=^###\s+\[)/m)
    // Reordenar: bloques con ### primero (en orden inverso), y cualquier texto inicial al final
    raw = blocks.reverse().join('\n---\n\n') // Add a separator for better readability if desired, or just join('\n')
  }
  // Si no es markdown, se renderiza preformateado
  if (props.artifact.detected_format !== 'MARKDOWN') {
    return [
      {
        id: 'raw-text',
        type: 'html',
        content: `<pre class="bg-gray-50 p-4 rounded border text-xs font-mono whitespace-pre-wrap">${escapeHtml(raw)}</pre>`,
      },
    ]
  }

  // Dividir el documento por bloques ```mermaid ... ```
  const parts = raw.split(/(```mermaid[\s\S]*?```)/g)
  const result: Segment[] = []

  let index = 0
  for (const part of parts) {
    if (!part) continue
    index++

    if (part.startsWith('```mermaid') && part.endsWith('```')) {
      const code = part.replace(/^```mermaid\s*/, '').replace(/```$/, '').trim()
      result.push({
        id: `mermaid-block-${index}`,
        type: 'mermaid',
        content: code,
      })
    } else {
      if (part) {
        // Escapar etiquetas <script> y <style> para evitar que el renderizador v-html del DOM trunce o interprete tags de script crudo
        const sanitizedPart = part.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, (match) => escapeHtml(match))
                                  .replace(/<script\b([^>]*)>/gi, '&lt;script$1&gt;')
                                  .replace(/<\/script>/gi, '&lt;/script&gt;')
        const html = marked.parse(sanitizedPart, { breaks: true, gfm: true }) as string
        result.push({
          id: `html-block-${index}`,
          type: 'html',
          content: html,
        })
      }
    }
  }

  return result
})

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}
</script>
