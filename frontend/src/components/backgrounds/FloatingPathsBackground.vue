<template>
  <div class="floating-paths-background">
    <!-- Animated Grid Background -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="floatingGrid" width="60" height="60" patternUnits="userSpaceOnUse">
          <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(74, 0, 224, 0.05)" stroke-width="0.5" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#floatingGrid)" />
      <line x1="0" y1="20%" x2="100%" y2="20%" class="grid-line" style="animation-delay: 0.5s" />
      <line x1="0" y1="80%" x2="100%" y2="80%" class="grid-line" style="animation-delay: 1s" />
      <line x1="20%" y1="0" x2="20%" y2="100%" class="grid-line" style="animation-delay: 1.5s" />
      <line x1="80%" y1="0" x2="80%" y2="100%" class="grid-line" style="animation-delay: 2s" />
    </svg>

    <!-- Floating Elements -->
    <div class="floating-element" style="top: 25%; left: 15%; animation-delay: 0.5s"></div>
    <div class="floating-element" style="top: 60%; left: 85%; animation-delay: 1s"></div>
    <div class="floating-element" style="top: 40%; left: 10%; animation-delay: 1.5s"></div>
    <div class="floating-element" style="top: 75%; left: 90%; animation-delay: 2s"></div>
    <div class="floating-element" style="top: 30%; left: 70%; animation-delay: 2.5s"></div>
    <div class="floating-element" style="top: 80%; left: 20%; animation-delay: 3s"></div>

    <!-- Floating Paths -->
    <div class="absolute inset-0">
      <FloatingPaths :position="1" />
      <FloatingPaths :position="-1" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineComponent } from 'vue'

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
        <title>Background Paths</title>
        <path
          v-for="path in paths"
          :key="path.id"
          :d="path.d"
          stroke="currentColor"
          :stroke-width="path.width"
          :stroke-opacity="0.1 + path.id * 0.03"
          class="animated-path"
        />
      </svg>
    </div>
  `
})
</script>

<style scoped>
.floating-paths-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.grid-line {
  stroke: #4A00E0;
  stroke-width: 0.5;
  opacity: 0;
  stroke-dasharray: 5 5;
  stroke-dashoffset: 1000;
  animation: grid-draw 2s ease-out forwards;
}

@keyframes grid-draw {
  0% { stroke-dashoffset: 1000; opacity: 0; }
  50% { opacity: 0.2; }
  100% { stroke-dashoffset: 0; opacity: 0.1; }
}

.floating-element {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #4A00E0;
  border-radius: 50%;
  opacity: 0.3;
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.2; }
  25% { transform: translateY(-10px) translateX(5px); opacity: 0.6; }
  50% { transform: translateY(-5px) translateX(-3px); opacity: 0.4; }
  75% { transform: translateY(-15px) translateX(7px); opacity: 0.8; }
}

.animated-path {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: path-draw 20s linear infinite;
}

@keyframes path-draw {
  0% { stroke-dashoffset: 1000; opacity: 0.3; }
  50% { stroke-dashoffset: 500; opacity: 0.6; }
  100% { stroke-dashoffset: 0; opacity: 0.3; }
}
</style>
