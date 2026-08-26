<template>
  <div class="background-renderer">
    <DarkVeil v-if="preference === 'particles'" />
    <FloatingLines v-if="preference === 'waves'" />
    <Lightning v-if="preference === 'lightning'" />
    <LightPillar v-if="preference === 'light-pillar'" />
    <FloatingLinesWave v-if="preference === 'floating-lines-wave'" />
    <PrismaticBurst v-if="preference === 'prismatic-burst'" />
    <Iridescence v-if="preference === 'iridescence'" />
    <Silk v-if="preference === 'silk'" />
    <LightRays v-if="preference === 'light-rays'" />
    <Aurora v-if="preference === 'aurora'" />
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, onBeforeUnmount, onMounted, ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import DarkVeil from './DarkVeil.vue'
import FloatingLines from './FloatingLines.vue'
import Lightning from './Lightning.vue'
import LightPillar from './LightPillar.vue'
import FloatingLinesWave from './FloatingLinesWave.vue'
import PrismaticBurst from './PrismaticBurst.vue'
import Iridescence from './Iridescence.vue'
import Silk from './Silk.vue'
import LightRays from './LightRays.vue'
import Aurora from './Aurora.vue'

const store = useSettingsStore()
const instance = getCurrentInstance()

// This component is mounted once at the App.vue root and lives for the
// entire app session. In practice, changes to `backgroundPreference` applied
// from an external source (a remote settings-sync update relayed over
// WebSocket/BroadcastChannel from another browser tab/window) do not
// reliably re-trigger this component's render via normal computed/watch
// dependency tracking for such a long-lived, root-level singleton. Rather
// than depend on that tracking, a cheap interval compares the store's
// current value against what's currently rendered and forces an update the
// moment they diverge — this is a plain string comparison a couple of times
// per second, negligible cost, and guarantees the visible background always
// matches the setting regardless of where the change originated.
const preference = ref(store.backgroundPreference)
let syncIntervalId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  syncIntervalId = setInterval(() => {
    if (preference.value !== store.backgroundPreference) {
      preference.value = store.backgroundPreference
      instance?.proxy?.$forceUpdate()
    }
  }, 400)
})

onBeforeUnmount(() => {
  if (syncIntervalId !== null) {
    clearInterval(syncIntervalId)
    syncIntervalId = null
  }
})
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
