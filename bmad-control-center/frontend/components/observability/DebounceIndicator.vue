<template>
  <transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="transform scale-95 opacity-0"
    enter-to-class="transform scale-100 opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="transform scale-100 opacity-100"
    leave-to-class="transform scale-95 opacity-0"
  >
    <div
      v-if="show"
      class="inline-flex items-center gap-1.5 bg-yellow-100 border border-yellow-400 text-yellow-900 dark:bg-amber-950/80 dark:border-amber-700 dark:text-amber-200 px-2.5 py-0.5 rounded-full text-[11px] font-medium shadow-xs"
    >
      <span class="text-xs">⚡</span>
      <span>
        Buffer Debounce: {{ coalescedCount }} mutaciones ({{ windowDurationMs }}ms)
      </span>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

interface Props {
  coalescedCount?: number
  windowDurationMs?: number
  triggerTimestamp?: number
}

const props = withDefaults(defineProps<Props>(), {
  coalescedCount: 1,
  windowDurationMs: 200,
  triggerTimestamp: 0,
})

const show = ref<boolean>(false)
let hideTimer: ReturnType<typeof setTimeout> | null = null

const activate = (): void => {
  if (props.coalescedCount > 1) {
    show.value = true
    if (hideTimer) clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      show.value = false
    }, 2000)
  }
}

watch(
  () => props.triggerTimestamp,
  () => {
    activate()
  }
)

onMounted(() => {
  if (props.coalescedCount > 1) {
    activate()
  }
})
</script>
