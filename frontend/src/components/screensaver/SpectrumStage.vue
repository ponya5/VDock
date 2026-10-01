<script setup lang="ts">
/**
 * DL-123 — fullscreen spectrum screensaver stage.
 *
 * Mounted by ScreenSaver.vue when `screensaverStyle === 'spectrum'`: the
 * visualizer IS the screensaver — two stacked DPR-aware canvases, one
 * ~60 fps rAF loop (with a ~30 fps governor fallback + reduced-motion
 * cadence), and swappable skin renderers from services/spectrumSkins.ts.
 *
 * - Skin: `settingsStore.spectrumSkin`, or a shuffled pick when
 *   `spectrumShuffle` rotates it every `spectrumShuffleMinutes`. Shuffle is
 *   ephemeral — the saved skin is the "home" look, rotation never rewrites
 *   settings.
 * - Skin swaps cross-dissolve (DL-134): the incoming renderer draws on the
 *   back canvas while both layers fade through ~850 ms, then the outgoing
 *   renderer is retired. Fresh state per activation — per-skin history
 *   buffers never bleed across looks.
 * - Media bar (bottom-center, `spectrumMediaBar`): SMTC track + transport
 *   via `cross_platform` media actions. Every pointer event is `.stop`-ed —
 *   only a tap OUTSIDE the bar dismisses the saver.
 * - Honest states: stream never arrived → dim "capture unavailable" hint
 *   after a grace window; silent stream → skins relax to baseline (bands≈0).
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import socketClient from '@/api/socket'
import { useAudioSpectrum } from '@/services/audioSpectrum'
import {
  nowPlayingIcon,
  nowPlayingSourceLabel,
  useNowPlaying,
} from '@/services/nowPlaying'
import {
  getSpectrumSkin,
  pickNextSkin,
  type SpectrumFrame,
  type SpectrumRenderer,
} from '@/services/spectrumSkins'
import { useSettingsStore } from '@/stores/settings'
import { useMobileViewport } from '@/utils/mobileViewport'

// DL-135: `backdrop` keeps the visualizer mounted under the widget layer
// (spectrum overlay or the layout editor). Backdrop mode hides the media
// bar — its buttons would steal the drag gestures meant for widgets.
const props = withDefaults(defineProps<{ backdrop?: boolean }>(), { backdrop: false })

const settingsStore = useSettingsStore()
const spectrum = useAudioSpectrum()
const nowPlaying = useNowPlaying()
const { isMobileViewport } = useMobileViewport()

const BANDS = 20
const FRAME_MS = 16            // ~60 fps target — motion layers animate per frame
const REDUCED_FRAME_MS = 45    // ~22 fps under prefers-reduced-motion
const SLOW_FRAME_MS = 33       // governor fallback when draws miss budget
const GRACE_MS = 4000          // connect + first heartbeat before "unavailable"
const REDUCED = typeof window !== 'undefined'
  && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
// Cross-dissolve length — ambient saver pace, not UI-snappy. Keep in sync
// with the .spectrum-canvas opacity transition below (+reduced variant).
const XFADE_MS = REDUCED ? 350 : 850

const stageRef = ref<HTMLElement | null>(null)
const canvasARef = ref<HTMLCanvasElement | null>(null)
const canvasBRef = ref<HTMLCanvasElement | null>(null)
/** Which canvas layer is on top / opaque. -1 until the first mount frame. */
const frontLayer = ref(-1)
const graceExpired = ref(false)

/** The skin actually on screen (or fading in) — saved pick or shuffle's. */
const activeSkinId = ref(getSpectrumSkin(settingsStore.spectrumSkin).id)
const activeSkinLabel = computed(() => getSpectrumSkin(activeSkinId.value).label)

const streamAbsent = computed(() => spectrum.lastSeenAt === null && graceExpired.value)

// --- renderer lifecycle ------------------------------------------------------

const display = new Array<number>(BANDS).fill(0)

/** Each canvas owns one renderer; the back layer sits transparent until a
 *  swap promotes it. `skinId` only tracks what the layer last hosted. */
interface Layer { renderer: SpectrumRenderer | null; skinId: string }
const layers: Layer[] = [{ renderer: null, skinId: '' }, { renderer: null, skinId: '' }]
let retireTimer: number | undefined

function swapSkin(id: string): void {
  // Same id already front (or fading in) → nothing to do.
  if (id === activeSkinId.value && layers[frontLayer.value]?.renderer) return
  // The layer that isn't in front hosts the newcomer. A mid-flight
  // crossfade just replaces whatever that canvas was still fading out.
  const next = frontLayer.value === 1 ? 0 : 1
  layers[next].renderer = getSpectrumSkin(id).create()
  layers[next].skinId = id
  activeSkinId.value = id
  frontLayer.value = next
  window.clearTimeout(retireTimer)
  retireTimer = window.setTimeout(() => {
    const old = frontLayer.value === 1 ? 0 : 1
    layers[old].renderer = null
    layers[old].skinId = ''
  }, XFADE_MS + 120)
}

watch(() => settingsStore.spectrumSkin, (id) => {
  // External change (Settings picker) always wins over a shuffle pick.
  if (id && id !== activeSkinId.value) swapSkin(id)
})

// --- shuffle -----------------------------------------------------------------

let shuffleTimer: ReturnType<typeof setInterval> | null = null

function armShuffle(): void {
  if (shuffleTimer) clearInterval(shuffleTimer)
  shuffleTimer = null
  const minutes = Number(settingsStore.spectrumShuffleMinutes)
  if (!settingsStore.spectrumShuffle || !Number.isFinite(minutes) || minutes <= 0) return
  shuffleTimer = setInterval(() => {
    swapSkin(pickNextSkin(activeSkinId.value))
  }, minutes * 60_000)
}

watch(
  () => [settingsStore.spectrumShuffle, settingsStore.spectrumShuffleMinutes],
  armShuffle,
  { immediate: true },
)

// --- canvas + rAF ------------------------------------------------------------

let rafId = 0
let lastFrame = 0
let lastT = 0
let startT = 0
let resizeObserver: ResizeObserver | null = null
let graceTimer: number | undefined
let frameCostMs = 0 // EMA of renderer.draw cost — drives the governor
let levelSm = 0     // smoothed overall level for the skins' glow/pulse

const layerCanvases = () => [canvasARef.value, canvasBRef.value]
// 2D contexts are cached — getContext is free-ish but called per layer
// per frame, which is wasted work on the panel's small CPU.
const layerCtxs: (CanvasRenderingContext2D | null)[] = [null, null]

function sizeCanvas(): void {
  const dpr = window.devicePixelRatio || 1
  const canvases = layerCanvases()
  for (let i = 0; i < canvases.length; i++) {
    const canvas = canvases[i]
    if (!canvas) continue
    const w = canvas.clientWidth || window.innerWidth
    const h = canvas.clientHeight || window.innerHeight
    canvas.width = Math.round(w * dpr)
    canvas.height = Math.round(h * dpr)
    layerCtxs[i] = canvas.getContext('2d')
    layerCtxs[i]?.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
}

function tick(now: number): void {
  rafId = requestAnimationFrame(tick)
  // Governor: if draws consistently cost more than a 60 fps frame can
  // spend, settle to ~30 fps rather than jank — a low-power panel still
  // gets fluid motion instead of uneven frames.
  const budget = REDUCED ? REDUCED_FRAME_MS
    : frameCostMs > 14 ? SLOW_FRAME_MS : FRAME_MS
  if (now - lastFrame < budget) return
  const dt = lastT ? Math.min((now - lastT) / 1000, 0.5) : 0.016
  lastFrame = now
  lastT = now
  if (!startT) startT = now

  // Shared envelope — asymmetric lerp: fast attack (~50 ms constant,
  // bridging the backend's emit cadence so band steps never stair-step on
  // screen), slower release keeps decays graceful. A jump bigger than
  // SPIKE_SNAP skips the lerp entirely — real transients hit full height
  // on the frame they land instead of being shaved.
  const SPIKE_SNAP = 16
  const attack = Math.exp(-dt * 18)
  const release = Math.exp(-dt * 5)
  const fresh = spectrum.lastSeenAt !== null
    && Date.now() - spectrum.lastSeenAt < 4000
  const live = spectrum.live && fresh
  for (let i = 0; i < BANDS; i++) {
    const target = live ? (spectrum.bands[i] ?? 0) : 0
    if (target > display[i] + SPIKE_SNAP) {
      display[i] = target
    } else {
      display[i] = target + (display[i] - target) * (target > display[i] ? attack : release)
    }
    if (display[i] < 0.3) display[i] = 0
  }
  // Same smoothing for the overall level the skins pulse their glow with.
  levelSm += ((live ? spectrum.level : 0) - levelSm) * Math.min(1, dt * 12)

  const stage = stageRef.value
  const frame: SpectrumFrame = {
    bands: display,
    level: levelSm,
    live,
    w: stage?.clientWidth || window.innerWidth,
    h: stage?.clientHeight || window.innerHeight,
    t: (now - startT) / 1000,
    dt,
  }

  // Mobile landscape overscan: radial skins size by min(w,h), so on a
  // wide-short panel they shrink to a small disc. Zoom the canvas about
  // the center so the visuals keep stage presence — edges crop, which is
  // intentional per the mobile ask ("if part of the animation is cut due
  // to the landscape view, so be it"). sqrt() keeps it gentle: 1.7:1 →
  // ~1.3x, 2:1 → ~1.4x. Bars-based skins just get chunkier bars.
  const zoom = isMobileViewport.value && frame.w > frame.h
    ? Math.min(1.45, Math.sqrt(frame.w / frame.h))
    : 1

  // Draw each live layer — during a crossfade both run at once.
  const drawStart = performance.now()
  for (let i = 0; i < 2; i++) {
    const r = layers[i].renderer
    const ctx = layerCtxs[i]
    if (r && ctx) {
      if (zoom > 1) {
        ctx.save()
        ctx.translate(frame.w / 2, frame.h / 2)
        ctx.scale(zoom, zoom)
        ctx.translate(-frame.w / 2, -frame.h / 2)
        r.draw(ctx, frame)
        ctx.restore()
      } else {
        r.draw(ctx, frame)
      }
    }
  }
  frameCostMs = frameCostMs * 0.92 + (performance.now() - drawStart) * 0.08
}

onMounted(() => {
  layers[0].renderer = getSpectrumSkin(activeSkinId.value).create()
  layers[0].skinId = activeSkinId.value
  graceTimer = window.setTimeout(() => { graceExpired.value = true }, GRACE_MS)
  if (stageRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(sizeCanvas)
    resizeObserver.observe(stageRef.value)
  }
  sizeCanvas()
  // Soft entrance: let the first frame paint before the layer fades in.
  rafId = requestAnimationFrame((now) => {
    frontLayer.value = 0
    tick(now)
  })
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  if (shuffleTimer) clearInterval(shuffleTimer)
  window.clearTimeout(graceTimer)
  window.clearTimeout(retireTimer)
})

// --- media bar ---------------------------------------------------------------

const mediaBarOn = computed(() => settingsStore.spectrumMediaBar !== false && !props.backdrop)
const track = computed(() => nowPlaying.track.value)
const playing = computed(() => nowPlaying.playing.value)
// Site-aware label/icon: "YouTube" + its logo beats "chrome.exe" + a
// music note when the backend has attributed the session to a site.
const sourceLabel = computed(() => nowPlayingSourceLabel(track.value))
const brandIcon = computed(() => nowPlayingIcon(track.value))
const brandClass = computed(() =>
  track.value?.site ? `is-${track.value.site.toLowerCase()}` : '')

// position_s arrives per track change; while playing we extrapolate locally
// from the moment the payload landed (server ts is not comparable to ours).
const posAnchor = ref<{ pos: number; at: number } | null>(null)
watch(() => track.value?.ts, () => {
  const p = track.value?.position_s
  posAnchor.value = typeof p === 'number' ? { pos: p, at: Date.now() } : null
}, { immediate: true })

const nowTick = ref(Date.now())
let posTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => { posTimer = setInterval(() => { nowTick.value = Date.now() }, 1000) })
onUnmounted(() => { if (posTimer) clearInterval(posTimer) })

const progressPct = computed(() => {
  const t = track.value
  const dur = t?.duration_s ?? 0
  if (!t || !dur || !posAnchor.value) return null
  const pos = playing.value
    ? posAnchor.value.pos + (nowTick.value - posAnchor.value.at) / 1000
    : posAnchor.value.pos
  return Math.min(100, Math.max(0, (pos / dur) * 100))
})

function media(action: string): void {
  // Fire-and-forget — the backend's cross_platform handler maps these to OS
  // media keys, which reach whichever app SMTC is reporting.
  void socketClient.executeAction({
    type: 'cross_platform',
    config: { action },
  }).catch(() => { /* transport failure — nothing to show mid-screensaver */ })
}
</script>

<template>
  <div ref="stageRef" class="spectrum-stage">
    <!-- Two stacked layers so a skin swap cross-dissolves: the newcomer
         renders on the back canvas and rides opacity in while the old
         skin fades out beneath it (DL-134). -->
    <canvas
      ref="canvasARef"
      class="spectrum-canvas"
      :class="{ 'is-front': frontLayer === 0 }"
    ></canvas>
    <canvas
      ref="canvasBRef"
      class="spectrum-canvas"
      :class="{ 'is-front': frontLayer === 1 }"
    ></canvas>

    <div v-if="streamAbsent" class="spectrum-off">
      <FontAwesomeIcon :icon="['fas', 'wave-square']" class="spectrum-off-icon" />
      <span>Audio capture unavailable</span>
    </div>

    <div class="spectrum-tag">
      <span class="spectrum-dot" :class="{ 'is-live': spectrum.live }"></span>
      {{ activeSkinLabel }}
    </div>

    <!-- The bar stops every pointer event — taps here must never reach the
         saver's root dismiss handler; only a tap outside it wakes the deck. -->
    <div
      v-if="mediaBarOn"
      class="spectrum-media"
      :class="{ 'has-track': !!track }"
      @click.stop
      @touchstart.stop
      @pointerdown.stop
    >
      <div class="spectrum-media-head">
        <img
          v-if="nowPlaying.artUrl.value"
          :src="nowPlaying.artUrl.value"
          alt=""
          class="spectrum-media-art"
        >
        <FontAwesomeIcon
          v-else-if="brandIcon"
          :icon="brandIcon"
          class="spectrum-media-art spectrum-media-art-icon spectrum-media-brand"
          :class="brandClass"
        />
        <FontAwesomeIcon v-else :icon="['fas', 'music']" class="spectrum-media-art spectrum-media-art-icon" />

        <div class="spectrum-media-text">
          <span v-if="track" class="spectrum-media-kicker">
            Now playing<span v-if="sourceLabel" class="spectrum-media-source"> · {{ sourceLabel }}</span>
          </span>
          <span class="spectrum-media-title">{{ track?.title || 'Nothing playing' }}</span>
          <span class="spectrum-media-artist">{{ track?.artist || '—' }}</span>
          <div v-if="progressPct !== null" class="spectrum-media-progress">
            <span :style="{ width: `${progressPct}%` }"></span>
          </div>
        </div>
      </div>

      <div class="spectrum-media-btns">
        <button type="button" class="spectrum-media-btn" aria-label="Previous track" @click="media('media_previous')">
          <FontAwesomeIcon :icon="['fas', 'backward-step']" />
        </button>
        <!-- One state-split transport (DL-128/DL-137): media_play_stop
             resolves backend-side — stop while playing, play otherwise —
             so the face mirrors what the press will do. -->
        <button
          type="button"
          class="spectrum-media-btn spectrum-media-play"
          :aria-label="playing ? 'Stop' : 'Play'"
          @click="media('media_play_stop')"
        >
          <FontAwesomeIcon :icon="['fas', playing ? 'stop' : 'play']" />
        </button>
        <button type="button" class="spectrum-media-btn" aria-label="Next track" @click="media('media_next')">
          <FontAwesomeIcon :icon="['fas', 'forward-step']" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.spectrum-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.spectrum-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  opacity: 0;
  /* ease-in-out reads as an even dissolve — the two layers are always
     complementary mid-fade, so total light stays roughly constant. */
  transition: opacity 850ms ease-in-out;
}

.spectrum-canvas.is-front {
  opacity: 1;
  z-index: 1;
}

/* Overlays always sit above whichever canvas is on top. */
.spectrum-off { z-index: 2; }
.spectrum-tag { z-index: 2; }
.spectrum-media { z-index: 2; }

.spectrum-off {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.35);
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: clamp(11px, 1.4vw, 15px);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.spectrum-off-icon {
  font-size: clamp(22px, 3vw, 34px);
  opacity: 0.6;
}

.spectrum-tag {
  position: absolute;
  top: max(14px, env(safe-area-inset-top));
  right: max(16px, env(safe-area-inset-right));
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.38);
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: clamp(10px, 1.2vw, 13px);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.spectrum-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
}

.spectrum-dot.is-live {
  background: #35d45e;
  box-shadow: 0 0 8px rgba(53, 212, 94, 0.8);
}

.spectrum-media {
  position: absolute;
  left: 50%;
  bottom: max(18px, env(safe-area-inset-bottom));
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: clamp(10px, 1.6vw, 16px);
  padding: clamp(8px, 1.4vh, 14px) clamp(14px, 2vw, 22px);
  background: rgba(10, 10, 22, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 999px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 10px 34px rgba(0, 0, 0, 0.5);
  cursor: default;
  user-select: none;
  -webkit-user-select: none;
  max-width: min(92vw, 560px);
  transition: border-radius 220ms ease, padding 220ms ease;
}

.spectrum-media-head {
  display: flex;
  align-items: center;
  gap: clamp(10px, 1.6vw, 16px);
  min-width: 0;
}

/* With a live track the pill becomes a now-playing card — art presented
   properly, controls beneath — still anchored bottom-center so it never
   dwarfs the visualizer (≲ a third of the screen height). */
.spectrum-media.has-track {
  flex-direction: column;
  align-items: stretch;
  gap: clamp(12px, 1.8vh, 18px);
  width: min(94vw, 560px);
  padding: clamp(14px, 2.4vh, 22px) clamp(18px, 3vw, 28px);
  border-radius: clamp(18px, 2.8vh, 26px);
}

.spectrum-media.has-track .spectrum-media-head {
  gap: clamp(12px, 1.8vw, 16px);
  animation: spectrum-media-in 260ms ease;
}

@keyframes spectrum-media-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.spectrum-media-art {
  width: clamp(44px, 7vh, 56px);
  height: clamp(44px, 7vh, 56px);
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  transition: width 220ms ease, height 220ms ease, border-radius 220ms ease;
}

.spectrum-media.has-track .spectrum-media-art {
  width: clamp(88px, 15vh, 120px);
  height: clamp(88px, 15vh, 120px);
  border-radius: 14px;
}

.spectrum-media-art-icon {
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.06);
  font-size: clamp(18px, 2.6vh, 24px);
}

/* Brand glyph fallback when the app supplies no art — the site color
   makes it recognizable at a glance. */
.spectrum-media-brand {
  font-size: clamp(22px, 3.4vh, 32px);
}
.spectrum-media-brand.is-youtube { color: #ff4a45; }
.spectrum-media-brand.is-spotify { color: #1db954; }
.spectrum-media-brand.is-twitch  { color: #9146ff; }
.spectrum-media.has-track .spectrum-media-brand {
  font-size: clamp(34px, 6vh, 48px);
}

.spectrum-media-kicker {
  color: rgba(255, 255, 255, 0.38);
  font-size: clamp(11px, 1.4vw, 14px);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.spectrum-media-source {
  color: rgba(255, 255, 255, 0.28);
}

.spectrum-media-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

.spectrum-media.has-track .spectrum-media-text {
  flex: 1;
}

.spectrum-media-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: clamp(15px, 2vw, 20px);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 34vw;
}

.spectrum-media-artist {
  color: rgba(255, 255, 255, 0.5);
  font-size: clamp(12px, 1.5vw, 15px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 34vw;
}

.spectrum-media.has-track .spectrum-media-title {
  font-size: clamp(20px, 2.8vw, 32px);
  max-width: none;
}

.spectrum-media.has-track .spectrum-media-artist {
  font-size: clamp(15px, 2vw, 20px);
  max-width: none;
}

.spectrum-media.has-track .spectrum-media-progress {
  margin-top: 5px;
}

.spectrum-media-progress {
  margin-top: 3px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.12);
  overflow: hidden;
}

.spectrum-media-progress span {
  display: block;
  height: 100%;
  background: rgba(255, 255, 255, 0.75);
  transition: width 1s linear;
}

.spectrum-media-btns {
  display: flex;
  align-items: center;
  gap: 6px;
}

.spectrum-media.has-track .spectrum-media-btns {
  justify-content: center;
}

.spectrum-media-btn {
  width: clamp(42px, 7vh, 56px);
  height: clamp(42px, 7vh, 56px);
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: clamp(14px, 2.2vh, 19px);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 140ms ease, transform 140ms ease;
}

.spectrum-media-btn:active {
  transform: scale(0.92);
  background: rgba(255, 255, 255, 0.18);
}

.spectrum-media-play {
  width: clamp(50px, 8.6vh, 68px);
  height: clamp(50px, 8.6vh, 68px);
  background: rgba(255, 255, 255, 0.92);
  color: #0a0a16;
  font-size: clamp(17px, 2.6vh, 22px);
}

.spectrum-media-play:active {
  background: #ffffff;
}

@media (prefers-reduced-motion: reduce) {
  /* Crossfade stays (opacity aids comprehension) but shortens. */
  .spectrum-canvas { transition-duration: 350ms; }
  .spectrum-media-btn,
  .spectrum-media-progress span {
    transition: none;
  }
}
</style>
