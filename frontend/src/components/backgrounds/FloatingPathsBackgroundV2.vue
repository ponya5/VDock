<template>
  <div class="floating-paths-v2-background">
    <!-- Floating Paths -->
    <div class="absolute inset-0">
      <div class="absolute inset-0 pointer-events-none">
        <svg class="w-full h-full text-slate-950 dark:text-white" viewBox="0 0 696 316" fill="none">
          <title>Background Paths V2</title>
          <path
            v-for="path in pathsA"
            :key="path.id"
            :d="path.d"
            stroke="currentColor"
            :stroke-width="path.width"
            :stroke-opacity="0.1 + path.id * 0.03"
            class="animated-path-v2"
          />
        </svg>
      </div>
      <div class="absolute inset-0 pointer-events-none">
        <svg class="w-full h-full text-slate-950 dark:text-white" viewBox="0 0 696 316" fill="none">
          <title>Background Paths V2</title>
          <path
            v-for="path in pathsB"
            :key="path.id"
            :d="path.d"
            stroke="currentColor"
            :stroke-width="path.width"
            :stroke-opacity="0.1 + path.id * 0.03"
            class="animated-path-v2"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Path {
  id: number
  d: string
  color: string
  width: number
}

function generatePaths(position: number): Path[] {
  return Array.from({ length: 36 }, (_, i) => ({
    id: i,
    d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${
      380 - i * 5 * position
    } -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${
      152 - i * 5 * position
    } ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${
      684 - i * 5 * position
    } ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
    color: `rgba(15,23,42,${0.1 + i * 0.03})`,
    width: 0.5 + i * 0.03,
  }))
}

const pathsA = ref<Path[]>([])
const pathsB = ref<Path[]>([])

onMounted(() => {
  pathsA.value = generatePaths(1)
  pathsB.value = generatePaths(-1)
})
</script>

<style scoped>
.floating-paths-v2-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.animated-path-v2 {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: path-draw-v2 25s linear infinite;
}

@keyframes path-draw-v2 {
  0% { stroke-dashoffset: 1000; opacity: 0.2; }
  25% { stroke-dashoffset: 750; opacity: 0.4; }
  50% { stroke-dashoffset: 500; opacity: 0.6; }
  75% { stroke-dashoffset: 250; opacity: 0.4; }
  100% { stroke-dashoffset: 0; opacity: 0.2; }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .floating-paths-v2-background {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  }
}
</style>
