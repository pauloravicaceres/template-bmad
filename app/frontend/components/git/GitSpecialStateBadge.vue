<template>
  <div class="inline-flex items-center gap-1.5 flex-wrap">
    <!-- Detached HEAD Badge -->
    <span
      v-if="isDetached"
      class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 border border-amber-300 text-amber-800"
      title="El puntero HEAD no está asociado a una rama de característica"
    >
      <span>⚠️</span>
      <span>[DETACHED HEAD]</span>
    </span>

    <!-- Merge Conflict Badge -->
    <span
      v-if="isConflicted"
      class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-red-100 border border-red-300 text-red-800 animate-pulse"
      title="Hay conflictos de fusión pendientes en el working tree"
    >
      <span>⚠️</span>
      <span>[CONFLICTO DE FUSIÓN]</span>
    </span>

    <!-- Syncing / Lock contention Badge -->
    <span
      v-if="isSyncing"
      class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 border border-blue-300 text-blue-800"
      title="Transacción Git en curso, visualizando snapshot seguro en memoria"
    >
      <span class="animate-spin text-xs">↺</span>
      <span>[SINCRONIZANDO]</span>
    </span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isDetached?: boolean
  isConflicted?: boolean
  isSyncing?: boolean
}

withDefaults(defineProps<Props>(), {
  isDetached: false,
  isConflicted: false,
  isSyncing: false,
})
</script>
