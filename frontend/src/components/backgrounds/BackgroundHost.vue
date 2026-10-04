<template>
  <div
    v-if="embedded"
    ref="hostRef"
    class="background-host-embedded"
  >
    <component :is="component" v-if="!failed" :on-error="reportFailure" v-bind="$attrs" />
  </div>
  <component
    v-else
    :is="component"
    v-if="!failed"
    :on-error="reportFailure"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
// Error boundary for component-kind backgrounds. The ported renderers
// declare an `onError` prop but never call it — an init throw (e.g.
// `new Renderer()` when WebGL is refused or the context is lost) escapes
// as an uncaught Vue error and leaves a silent blank layer instead of the
// designed fallback. Capturing here makes every catalog entry fail soft:
// the component unmounts and the parent decides what shows instead.
import { ref, onErrorCaptured, onMounted, onUnmounted, watch } from 'vue'
import type { Component } from 'vue'
import { syncEmbeddedPreviewCanvases } from '@/utils/oglCanvasLayout'

defineOptions({ inheritAttrs: false })
const props = defineProps<{ component: Component; embedded?: boolean }>()
const emit = defineEmits<{ error: [err: unknown] }>()

const failed = ref(false)
const hostRef = ref<HTMLElement | null>(null)

const reportFailure = (err: unknown) => {
  if (failed.value) return
  failed.value = true
  emit('error', err)
}

onErrorCaptured((err) => {
  reportFailure(err)
  return false
})

watch(
  () => props.component,
  () => {
    failed.value = false
  },
)

let resizeObserver: ResizeObserver | null = null
let syncFrame = 0

function scheduleEmbeddedCanvasSync() {
  if (!props.embedded || !hostRef.value) return
  if (syncFrame) return
  syncFrame = requestAnimationFrame(() => {
    syncFrame = 0
    if (hostRef.value) syncEmbeddedPreviewCanvases(hostRef.value)
  })
}

onMounted(() => {
  if (!props.embedded || !hostRef.value) return
  scheduleEmbeddedCanvasSync()
  resizeObserver = new ResizeObserver(scheduleEmbeddedCanvasSync)
  resizeObserver.observe(hostRef.value)
})

onUnmounted(() => {
  if (syncFrame) cancelAnimationFrame(syncFrame)
  resizeObserver?.disconnect()
  resizeObserver = null
})
</script>

<style scoped>
.background-host-embedded {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

/* Component roots often use position:fixed + 100vw for full-dashboard layout. */
.background-host-embedded :deep(> *) {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  min-width: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  transform: none !important;
}

.background-host-embedded :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block !important;
}
</style>
