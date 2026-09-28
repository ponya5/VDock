<template>
  <div class="background-renderer">
    <div v-if="failedId === current.id" class="background-renderer__fallback bg-fallback-animated" />
    <BackgroundHost
      v-else-if="current.kind === 'component'"
      :key="current.id"
      :component="current.component"
      @error="onBackgroundError"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { resolveBackground } from '@/data/backgrounds'
import BackgroundHost from './BackgroundHost.vue'

// Every component-kind background renders here, including the three that used
// to live in DashboardView. One value, one owner: that is what stops the two
// background settings from fighting.
//
// This deliberately uses plain reactivity. A previous version polled the store
// every 400ms and called $forceUpdate(), which left the dashboard transparent
// for up to 400ms before the replacement effect mounted -- the flicker.
const store = useSettingsStore()
const current = computed(() => resolveBackground(store.background))

// Components that can't initialize (e.g. WebGPU backgrounds on a browser with
// no adapter) report through their onError prop. Show a quiet gradient rather
// than leaving the dashboard a silent black screen. Components that don't
// declare the prop just ignore it.
const failedId = ref<string | null>(null)

const onBackgroundError = (err: unknown) => {
  if (failedId.value !== current.value.id) {
    console.warn('[background] fell back to gradient:', current.value.id, err)
    failedId.value = current.value.id
  }
}
</script>

<style scoped>
.background-renderer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -10;
  pointer-events: none;
}

/* Visuals live in the shared .bg-fallback-animated (main.css) — a failed
   component still leaves an animated scene, not a flat paint (DL-109). */
.background-renderer__fallback {
  position: absolute;
  inset: 0;
}
</style>
