<template>
  <transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="transform -translate-y-2 opacity-0"
    enter-to-class="transform translate-y-0 opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="transform translate-y-0 opacity-100"
    leave-to-class="transform -translate-y-2 opacity-0"
  >
    <div
      v-if="isSyncing"
      class="bg-amber-50 border border-amber-300 rounded-lg p-3 text-xs text-amber-900 shadow-xs mb-3"
      role="alert"
    >
      <div class="flex items-center justify-between font-bold mb-1">
        <div class="flex items-center gap-1.5">
          <span class="text-sm">⚠️</span>
          <span>TRANSACCIÓN GIT EN CURSO (.git/index.lock detectado)</span>
        </div>
        <span class="bg-amber-200 text-amber-800 text-[10px] px-2 py-0.5 rounded font-mono">
          [ ⏳ Sincronización Automática ]
        </span>
      </div>
      <p class="text-amber-800 text-[11px] leading-relaxed">
        El orquestador o un proceso Git local está escribiendo en el repositorio. Para evitar contención y errores 5xx,
        la interfaz despliega de forma segura el último snapshot cacheado en memoria. La sincronización se completará automáticamente
        tan pronto se libere el bloqueo.
      </p>
    </div>
  </transition>
</template>

<script setup lang="ts">
interface Props {
  isSyncing: boolean
}

defineProps<Props>()
</script>
