<template>
  <canvas ref="canvasRef" class="floating-lines-wave-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  lineCount?: number
  lineDistance?: number
  bendRadius?: number
  bendStrength?: number
  interactive?: boolean
  parallax?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  lineCount: 5,
  lineDistance: 5,
  bendRadius: 5,
  bendStrength: -0.5,
  interactive: true,
  parallax: true,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const mouse = { x: 0.5, y: 0.5 }
  const parallaxOffset = { x: 0, y: 0 }

  const resize = () => {
    canvas.width = canvas.clientWidth
    canvas.height = canvas.clientHeight
  }
  resize()
  window.addEventListener('resize', resize, { passive: true })

  const onMouseMove = (e: MouseEvent) => {
    if (!props.interactive && !props.parallax) return
    const rect = canvas.getBoundingClientRect()
    mouse.x = (e.clientX - rect.left) / rect.width
    mouse.y = (e.clientY - rect.top) / rect.height
  }
  if (props.interactive || props.parallax) {
    window.addEventListener('mousemove', onMouseMove, { passive: true })
  }

  const WAVE_COLORS = ['#E945F5', '#2F4BC0', '#E945F5']
  const WAVES = ['top', 'middle', 'bottom'] as const

  interface Line {
    wave: typeof WAVES[number]
    offset: number
    speed: number
    phase: number
    colorIdx: number
    alpha: number
  }

  const lines: Line[] = []
  WAVES.forEach((wave, wi) => {
    for (let i = 0; i < props.lineCount; i++) {
      lines.push({
        wave,
        offset: (i / props.lineCount) * props.lineDistance * 0.01,
        speed: 0.3 + Math.random() * 0.4,
        phase: Math.random() * Math.PI * 2,
        colorIdx: wi % WAVE_COLORS.length,
        alpha: 0.4 + Math.random() * 0.5,
      })
    }
  })

  const waveBaseY = (wave: typeof WAVES[number], h: number) => {
    if (wave === 'top') return h * 0.2
    if (wave === 'middle') return h * 0.5
    return h * 0.8
  }

  const render = (ts: number) => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resize()
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const { width: w, height: h } = canvas
    ctx.clearRect(0, 0, w, h)

    if (props.parallax) {
      parallaxOffset.x += ((mouse.x - 0.5) * 30 - parallaxOffset.x) * 0.05
      parallaxOffset.y += ((mouse.y - 0.5) * 20 - parallaxOffset.y) * 0.05
    }

    const t = ts * 0.001

    for (const line of lines) {
      const baseY = waveBaseY(line.wave, h) + parallaxOffset.y
      const color = WAVE_COLORS[line.colorIdx]

      ctx.beginPath()
      ctx.strokeStyle = color
      ctx.globalAlpha = line.alpha
      ctx.lineWidth = 1.5

      const segments = 80
      for (let s = 0; s <= segments; s++) {
        const x = (s / segments) * w + parallaxOffset.x
        const nx = s / segments

        // quadratic bezier-like bend via sine
        const bend = Math.sin(nx * Math.PI) * props.bendStrength * h * 0.15
        const wave = Math.sin(nx * props.bendRadius + t * line.speed + line.phase) * 20
        const mouseInfluence = props.interactive
          ? Math.sin((nx - mouse.x) * Math.PI * 2) * (mouse.y - 0.5) * 40
          : 0

        const y = baseY + line.offset * h + bend + wave + mouseInfluence

        if (s === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }

      ctx.shadowColor = color
      ctx.shadowBlur = 8
      ctx.stroke()
      ctx.shadowBlur = 0
    }

    ctx.globalAlpha = 1
    rafId = requestAnimationFrame(render)
  }

  const onVis = () => { if (!document.hidden && rafId === 0) requestAnimationFrame(render) }
  document.addEventListener('visibilitychange', onVis)
  rafId = requestAnimationFrame(render)

  cleanup = () => {
    cancelAnimationFrame(rafId)
    rafId = 0
    window.removeEventListener('resize', resize)
    window.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('visibilitychange', onVis)
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.floating-lines-wave-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
  display: block;
}
</style>
