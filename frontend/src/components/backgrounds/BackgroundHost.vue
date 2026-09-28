<template>
  <component :is="component" v-if="!failed" :on-error="reportFailure" v-bind="$attrs" />
</template>

<script setup lang="ts">
// Error boundary for component-kind backgrounds. The ported renderers
// declare an `onError` prop but never call it — an init throw (e.g.
// `new Renderer()` when WebGL is refused or the context is lost) escapes
// as an uncaught Vue error and leaves a silent blank layer instead of the
// designed fallback. Capturing here makes every catalog entry fail soft:
// the component unmounts and the parent decides what shows instead.
import { ref, onErrorCaptured } from 'vue'
import type { Component } from 'vue'

defineOptions({ inheritAttrs: false })
defineProps<{ component: Component }>()
const emit = defineEmits<{ error: [err: unknown] }>()

const failed = ref(false)

const reportFailure = (err: unknown) => {
  if (failed.value) return
  failed.value = true
  emit('error', err)
}

onErrorCaptured((err) => {
  reportFailure(err)
  return false
})
</script>
