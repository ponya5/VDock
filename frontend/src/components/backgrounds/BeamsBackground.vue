<template>
  <div class="beams-background">
    <canvas ref="canvasRef" class="absolute inset-0" style="filter: blur(15px)" />
    
    <div class="absolute inset-0 bg-neutral-950/5 backdrop-blur-[50px] animated-overlay"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Beam {
  x: number
  y: number
  width: number
  length: number
  angle: number
  speed: number
  opacity: number
  hue: number
  pulse: number
  pulseSpeed: number
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
const beamsRef = ref<Beam[]>([])
const animationFrameRef = ref<number>(0)
const MINIMUM_BEAMS = 20

const opacityMap = {
  subtle: 0.7,
  medium: 0.85,
  strong: 1,
}

function createBeam(width: number, height: number): Beam {
  const angle = -35 + Math.random() * 10
  return {
    x: Math.random() * width * 1.5 - width * 0.25,
    y: Math.random() * height * 1.5 - height * 0.25,
    width: 30 + Math.random() * 60,
    length: height * 2.5,
    angle: angle,
    speed: 0.6 + Math.random() * 1.2,
    opacity: 0.12 + Math.random() * 0.16,
    hue: 190 + Math.random() * 70,
    pulse: Math.random() * Math.PI * 2,
    pulseSpeed: 0.02 + Math.random() * 0.03,
  }
}

function resetBeam(beam: Beam, index: number, totalBeams: number, canvas: HTMLCanvasElement): Beam {
  const column = index % 3
  const spacing = canvas.width / 3

  beam.y = canvas.height + 100
  beam.x = column * spacing + spacing / 2 + (Math.random() - 0.5) * spacing * 0.5
  beam.width = 100 + Math.random() * 100
  beam.speed = 0.5 + Math.random() * 0.4
  beam.hue = 190 + (index * 70) / totalBeams
  beam.opacity = 0.2 + Math.random() * 0.1
  return beam
}

function drawBeam(ctx: CanvasRenderingContext2D, beam: Beam, intensity: keyof typeof opacityMap) {
  ctx.save()
  ctx.translate(beam.x, beam.y)
  ctx.rotate((beam.angle * Math.PI) / 180)

  // Calculate pulsing opacity
  const pulsingOpacity = beam.opacity * (0.8 + Math.sin(beam.pulse) * 0.2) * opacityMap[intensity]

  const gradient = ctx.createLinearGradient(0, 0, 0, beam.length)

  // Enhanced gradient with multiple color stops
  gradient.addColorStop(0, `hsla(${beam.hue}, 85%, 65%, 0)`)
  gradient.addColorStop(0.1, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity * 0.5})`)
  gradient.addColorStop(0.4, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity})`)
  gradient.addColorStop(0.6, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity})`)
  gradient.addColorStop(0.9, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity * 0.5})`)
  gradient.addColorStop(1, `hsla(${beam.hue}, 85%, 65%, 0)`)

  ctx.fillStyle = gradient
  ctx.fillRect(-beam.width / 2, 0, beam.width, beam.length)
  ctx.restore()
}

function animate(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, intensity: keyof typeof opacityMap) {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.filter = "blur(35px)"

  const totalBeams = beamsRef.value.length
  beamsRef.value.forEach((beam, index) => {
    beam.y -= beam.speed
    beam.pulse += beam.pulseSpeed

    // Reset beam when it goes off screen
    if (beam.y + beam.length < -100) {
      resetBeam(beam, index, totalBeams, canvas)
    }

    drawBeam(ctx, beam, intensity)
  })

  animationFrameRef.value = requestAnimationFrame(() => animate(canvas, ctx, intensity))
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext("2d")
  if (!ctx) return

  const updateCanvasSize = () => {
    const dpr = window.devicePixelRatio || 1
    canvas.width = window.innerWidth * dpr
    canvas.height = window.innerHeight * dpr
    canvas.style.width = `${window.innerWidth}px`
    canvas.style.height = `${window.innerHeight}px`
    ctx.scale(dpr, dpr)

    const totalBeams = MINIMUM_BEAMS * 1.5
    beamsRef.value = Array.from({ length: totalBeams }, () => createBeam(canvas.width, canvas.height))
  }

  updateCanvasSize()
  window.addEventListener("resize", updateCanvasSize)

  animate(canvas, ctx, 'strong')

  onUnmounted(() => {
    window.removeEventListener("resize", updateCanvasSize)
    if (animationFrameRef.value) {
      cancelAnimationFrame(animationFrameRef.value)
    }
  })
})
</script>

<style scoped>
.beams-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #0a0a0a;
}

.animated-overlay {
  animation: overlay-pulse 10s ease-in-out infinite;
}

@keyframes overlay-pulse {
  0%, 100% { opacity: 0.05; }
  50% { opacity: 0.15; }
}
</style>
