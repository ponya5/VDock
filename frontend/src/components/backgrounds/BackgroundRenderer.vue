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
import { computed } from 'vue'
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
const preference = computed(() => store.backgroundPreference)
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
