<template>
  <div class="background-renderer">
    <DarkVeil v-if="preference === 'particles'" />
    <FloatingLines v-if="preference === 'waves'" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useSettingsStore } from '@/stores/settings';
import DarkVeil from './DarkVeil.vue';
import FloatingLines from './FloatingLines.vue';

const store = useSettingsStore();
const preference = computed(() => store.backgroundPreference);
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
