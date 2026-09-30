<script setup lang="ts">
/**
 * DL-117 — Winamp-style spectrum analyzer screensaver widget.
 *
 * 20 thin bottom-aligned bars fed by the backend's WASAPI loopback FFT
 * (`audio_spectrum` socket event via services/audioSpectrum.ts). Classic
 * analyzer look: a single bottom-anchored green→yellow→red gradient so bar
 * color maps to *height* (short bars stay green, tall bars tip red), bars
 * carved into segments, and a pale peak-hold cap that lingers then falls
 * slower than the bars.
 *
 * The backend already smooths bands; we add a per-bar fall on top so the
 * display breathes between the ≤14 Hz socket frames. Rendering is canvas +
 * rAF gated to ~15 fps — cheap enough to run on the 7" panel forever.
 *
 * States: live frames → animated bars; `live:false` → bars relax to a dim
 * flat baseline; nothing ever arrived → honest "unavailable" (after a short
 * grace so a normal ~2 s silent-heartbeat doesn't flash it).
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useAudioSpectrum } from '@/services/audioSpectrum'

defineProps<{ layoutEdit?: boolean }>()

const spectrum = useAudioSpectrum()

const BANDS = 20
const BAR_GAP = 4
const SEGMENT_PX = 4 // classic segmented-bar pitch: 3 px block + 1 px carve
const FRAME_MS = 66 // ~15 fps
const BAR_FALL = 0.85 // per-frame multiplier — rises snap, falls breathe
const PEAK_HOLD_MS = 350
const PEAK_FALL = 0.9 // slower than BAR_FALL: caps detach and drift down
const IDLE_STUB_PX = 2
const GRACE_MS = 3000 // covers connect + first silent heartbeat (~2 s)

const panelRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const graceExpired = ref(false)

const everSeen = computed(() => spectrum.lastSeenAt !== null)

// Per-bar animation state — plain arrays, written only inside the rAF loop.
const display = new Array<number>(BANDS).fill(0)
const peaks = new Array<number>(BANDS).fill(0)
const peakSince = new Array<number>(BANDS).fill(0)

let rafId = 0
let lastFrame = 0
let cssWidth = 0
let cssHeight = 0
let resizeObserver: ResizeObserver | null = null
let graceTimer: number | undefined

function sizeCanvas(): void {
  const canvas = canvasRef.value
  if (!canvas) return
  cssWidth = canvas.clientWidth || 240
  cssHeight = canvas.clientHeight || 80
  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(cssWidth * dpr)
  canvas.height = Math.round(cssHeight * dpr)
  const ctx = canvas.getContext('2d')
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function draw(ctx: CanvasRenderingContext2D, now: number): void {
  const w = cssWidth
  const h = cssHeight
  ctx.clearRect(0, 0, w, h)

  // A backend that died mid-stream would leave `live` stuck true; past
  // ~2 heartbeats without a payload, treat the stream as silent.
  const fresh = spectrum.lastSeenAt !== null
    && Date.now() - spectrum.lastSeenAt < 4000
  const live = spectrum.live && fresh
  const barW = Math.max((w - (BANDS - 1) * BAR_GAP) / BANDS, 2)
  const usableH = h - 4

  const gradient = ctx.createLinearGradient(0, h, 0, 0)
  gradient.addColorStop(0, '#35d45e')
  gradient.addColorStop(0.55, '#cfd63c')
  gradient.addColorStop(0.8, '#ef8a2a')
  gradient.addColorStop(1, '#e8402a')

  ctx.globalAlpha = live ? 1 : 0.45
  ctx.fillStyle = gradient

  for (let i = 0; i < BANDS; i++) {
    const target = live
      ? Math.max(0, Math.min(100, spectrum.bands[i] ?? 0))
      : 0
    display[i] = Math.max(target, display[i] * BAR_FALL)
    if (display[i] < 0.5) display[i] = 0

    if (display[i] >= peaks[i]) {
      peaks[i] = display[i]
      peakSince[i] = now
    } else if (now - peakSince[i] > PEAK_HOLD_MS) {
      peaks[i] *= PEAK_FALL
      if (peaks[i] < 0.5) peaks[i] = 0
    }

    const x = i * (barW + BAR_GAP)
    const barH = live
      ? (display[i] / 100) * usableH
      : IDLE_STUB_PX
    if (barH > 0.5) ctx.fillRect(x, h - barH, barW, barH)
  }

  // Carve the horizontal segment gaps out of the drawn bars.
  ctx.globalCompositeOperation = 'destination-out'
  for (let y = h - SEGMENT_PX; y > 0; y -= SEGMENT_PX) {
    ctx.fillRect(0, y, w, 1)
  }
  ctx.globalCompositeOperation = 'source-over'

  ctx.fillStyle = 'rgba(255, 255, 255, 0.16)'
  ctx.fillRect(0, h - 1, w, 1)

  // Peak caps sit above the carved bars — solid, brighter than any tip.
  ctx.fillStyle = live ? 'rgba(255, 246, 230, 0.95)' : 'rgba(255, 255, 255, 0.35)'
  for (let i = 0; i < BANDS; i++) {
    if (peaks[i] <= 0) continue
    const x = i * (barW + BAR_GAP)
    const capY = h - (peaks[i] / 100) * usableH - 3
    ctx.fillRect(x, Math.max(capY, 0), barW, 2.5)
  }
  ctx.globalAlpha = 1
}

function tick(now: number): void {
  rafId = requestAnimationFrame(tick)
  if (now - lastFrame < FRAME_MS) return
  lastFrame = now
  const ctx = canvasRef.value?.getContext('2d')
  if (ctx) draw(ctx, now)
}

onMounted(() => {
  graceTimer = window.setTimeout(() => { graceExpired.value = true }, GRACE_MS)
  if (panelRef.value) {
    resizeObserver = new ResizeObserver(sizeCanvas)
    resizeObserver.observe(panelRef.value)
  }
  sizeCanvas()
  rafId = requestAnimationFrame(tick)
})

// The canvas mounts late when the first frame arrives after the grace
// period — size it as soon as it exists so it never draws stretched.
watch(everSeen, async seen => {
  if (!seen) return
  await nextTick()
  if (panelRef.value && !resizeObserver) {
    resizeObserver = new ResizeObserver(sizeCanvas)
    resizeObserver.observe(panelRef.value)
  }
  sizeCanvas()
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  window.clearTimeout(graceTimer)
})
</script>

<template>
  <section class="ss-section ss-spectrum">
    <div class="ss-section-head">
      <h2>Spectrum</h2>
      <span class="ss-hairline"></span>
    </div>

    <div v-if="everSeen" ref="panelRef" class="ss-spectrum-panel">
      <canvas ref="canvasRef" class="ss-spectrum-canvas"></canvas>
    </div>

    <div v-else class="ss-empty ss-spectrum-empty">
      <FontAwesomeIcon :icon="['fas', 'wave-square']" class="ss-spectrum-icon" />
      <span>{{ graceExpired ? 'Audio capture unavailable' : 'Waiting for audio…' }}</span>
    </div>
  </section>
</template>

<style scoped>
/* Mirrors the .ss-section / .ss-section-head / .ss-empty conventions in
   ScreenSaver.vue — the parent can't reach into scoped styles, so each
   screensaver widget carries its own copy. */
.ss-section {
  display: flex;
  flex-direction: column;
  gap: clamp(0.8rem, 2vh, 1.6rem);
  width: 240px;
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ss-section-head {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}

.ss-section-head h2 {
  margin: 0;
  font-size: clamp(0.6rem, 1.1vw, 1rem);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.5);
}

.ss-hairline {
  flex-grow: 1;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.14);
}

.ss-spectrum-panel {
  width: 100%;
  height: 96px;
  padding: 8px;
  box-sizing: border-box;
  border-radius: 10px;
  background: rgba(6, 10, 14, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.ss-spectrum-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.ss-empty {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 10px 4px;
  font-size: 0.9em;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.55);
}

.ss-spectrum-icon {
  opacity: 0.6;
}
</style>
