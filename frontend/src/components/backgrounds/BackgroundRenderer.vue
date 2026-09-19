<template>
  <div class="background-renderer">
    <component :is="current.component" v-if="current.kind === 'component'" :key="current.id" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { resolveBackground } from '@/data/backgrounds'

// Every component-kind background renders here, including the three that used
// to live in DashboardView. One value, one owner: that is what stops the two
// background settings from fighting.
//
// This deliberately uses plain reactivity. A previous version polled the store
// every 400ms and called $forceUpdate(), which left the dashboard transparent
// for up to 400ms before the replacement effect mounted -- the flicker.
const store = useSettingsStore()
const current = computed(() => resolveBackground(store.background))
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
</style>
