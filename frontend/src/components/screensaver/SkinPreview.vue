<script setup lang="ts">
/**
 * DL-123 — live skin swatch for the settings picker.
 *
 * A small canvas running the real skin renderer on synthetic demo bands —
 * the picker shows what each skin actually looks like instead of a static
 * thumbnail. ~24 fps is plenty for a thumbnail and 7 swatches stay cheap.
 */
import { onMounted, onUnmounted, ref, watch } from 'vue'
import {
  demoBands,
  getSpectrumSkin,
  type SpectrumRenderer,
} from '@/services/spectrumSkins'

const props = defineProps<{ skinId: string }>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let renderer: SpectrumRenderer = getSpectrumSkin(props.skinId).create()
let rafId = 0
let lastFrame = 0
let startT = 0

const FRAME_MS = 42
const display = new Array<number>(20).fill(0)

watch(() => props.skinId, (id) => {
  renderer = getSpectrumSkin(id).create()
})

function sizeCanvas(): void {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round((canvas.clientWidth || 96) * dpr)
  canvas.height = Math.round((canvas.clientHeight || 56) * dpr)
  canvas.getContext('2d')?.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function tick(now: number): void {
  rafId = requestAnimationFrame(tick)
  if (now - lastFrame < FRAME_MS) return
  const dt = lastFrame ? (now - lastFrame) / 1000 : 0.04
  lastFrame = now
  if (!startT) startT = now
  const ctx = canvasRef.value?.getContext('2d')
  if (!ctx) return

  const target = demoBands(now / 1000)
  const decay = Math.exp(-dt * 2.4)
  for (let i = 0; i < 20; i++) {
    display[i] = Math.max(target[i], display[i] * decay)
  }
  renderer.draw(ctx, {
    bands: display,
    level: 60,
    live: true,
    w: ctx.canvas.clientWidth || 96,
    h: ctx.canvas.clientHeight || 56,
    t: (now - startT) / 1000,
    dt,
  })
}

onMounted(() => {
  sizeCanvas()
  rafId = requestAnimationFrame(tick)
})

onUnmounted(() => cancelAnimationFrame(rafId))
</script>

<template>
  <canvas ref="canvasRef" class="skin-preview"></canvas>
</template>

<style scoped>
.skin-preview {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
