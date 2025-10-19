<template>
  <div class="floating-paths-v2-background">
    <!-- Floating Paths -->
    <div class="absolute inset-0">
      <FloatingPaths :position="1" />
      <FloatingPaths :position="-1" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineComponent } from 'vue'

interface Path {
  id: number
  d: string
  color: string
  width: number
}

const FloatingPaths = defineComponent({
  props: {
    position: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const paths = ref<Path[]>([])

    onMounted(() => {
      paths.value = Array.from({ length: 36 }, (_, i) => ({
        id: i,
        d: `M-${380 - i * 5 * props.position} -${189 + i * 6}C-${
          380 - i * 5 * props.position
        } -${189 + i * 6} -${312 - i * 5 * props.position} ${216 - i * 6} ${
          152 - i * 5 * props.position
        } ${343 - i * 6}C${616 - i * 5 * props.position} ${470 - i * 6} ${
          684 - i * 5 * props.position
        } ${875 - i * 6} ${684 - i * 5 * props.position} ${875 - i * 6}`,
        color: `rgba(15,23,42,${0.1 + i * 0.03})`,
        width: 0.5 + i * 0.03,
      }))
    })

    return {
      paths
    }
  },
  template: `
    <div class="absolute inset-0 pointer-events-none">
      <svg class="w-full h-full text-slate-950 dark:text-white" viewBox="0 0 696 316" fill="none">
        <title>Background Paths V2</title>
        <path
          v-for="path in paths"
          :key="path.id"
          :d="path.d"
          stroke="currentColor"
          :stroke-width="path.width"
          :stroke-opacity="0.1 + path.id * 0.03"
          class="animated-path-v2"
        />
      </svg>
    </div>
  `
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
