<template>
  <div class="flex flex-col items-center justify-center p-8 bg-white border border-dashed border-gray-300 rounded-xl text-center shadow-xs my-4">
    <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-xl mb-3 text-gray-500">
      ⚪
    </div>

    <h3 class="text-sm font-bold text-gray-800 uppercase tracking-wide mb-1">
      Repositorio Git No Detectado
    </h3>

    <p class="text-xs text-gray-600 max-w-md mb-4 leading-relaxed">
      No se encontró un subdirectorio <code class="px-1.5 py-0.5 bg-gray-100 text-gray-800 rounded font-mono text-[11px]">.git/</code>
      en el espacio de trabajo local.
    </p>

    <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 text-left text-xs max-w-md w-full mb-4">
      <div class="text-[11px] font-semibold text-gray-700 mb-1">
        El resto de módulos del BMAD Dashboard operan con total normalidad:
      </div>
      <ul class="text-[11px] text-gray-600 space-y-0.5">
        <li class="flex items-center gap-1.5">
          <span class="text-emerald-500 font-bold">✓</span> Centro de Comando HITL (Aprobaciones / Feedback)
        </li>
        <li class="flex items-center gap-1.5">
          <span class="text-emerald-500 font-bold">✓</span> Monitor de Workflow y Explorador de Artefactos
        </li>
        <li class="flex items-center gap-1.5">
          <span class="text-emerald-500 font-bold">✓</span> Observabilidad de Eventos FSaaDB
        </li>
      </ul>
    </div>

    <div class="bg-slate-900 text-slate-200 rounded-md px-3 py-2 text-[11px] font-mono max-w-md w-full mb-5 text-left flex items-center justify-between">
      <span>git init && git add .</span>
      <span class="text-slate-400 text-[10px]"># inicializar</span>
    </div>

    <div class="flex items-center gap-3">
      <button
        type="button"
        @click="emit('retry')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-xs transition-colors cursor-pointer"
      >
        <span>↺</span> Reintentar Detección
      </button>

      <button
        type="button"
        @click="emit('go-to-artifacts')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-md transition-colors cursor-pointer border border-gray-200"
      >
        <span>📁</span> Ir al Explorador de Artefactos
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  (e: 'retry'): void
  (e: 'go-to-artifacts'): void
}>()
</script>
