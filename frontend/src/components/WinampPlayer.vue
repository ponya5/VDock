<script setup lang="ts">
/**
 * Winamp player mode (DL-136): the main screen rendered as a Winamp
 * 2.x-style player. Real data throughout — SMTC now-playing feeds the
 * LCD/marquee/playlist, the WASAPI spectrum feeds the analyzer, the
 * transport row and volume slider dispatch the same cross_platform
 * actions the deck buttons use.
 *
 * What SMTC can't do, the UI doesn't fake: SHUFFLE/REPEAT are local LED
 * toggles, balance is a spring-back cosmetic slider, and the kbps slot
 * shows the track's source label since no bitrate exists for streams.
 * The equalizer is honest in the display domain: its sliders mask the
 * analyzer's rendered bands (±12 dB) rather than pretending to touch
 * the audio path.
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import socketClient from '@/api/socket'
import { useNowPlaying } from '@/services/nowPlaying'
import { useAudioSpectrum } from '@/services/audioSpectrum'

const emit = defineEmits<{ exit: [] }>()

const nowPlaying = useNowPlaying()
const spectrum = useAudioSpectrum()
const track = computed(() => nowPlaying.track.value)
const playing = computed(() => nowPlaying.playing.value)

function media(action: string): void {
  void socketClient.executeAction({
    type: 'cross_platform',
    config: { action },
  }).catch(() => { /* transport failure — nothing actionable here */ })
}

// --- LCD clock: position_s anchored per track, ticked locally -----------

const posAnchor = ref<{ pos: number; at: number } | null>(null)
watch(() => track.value?.ts, () => {
  const p = track.value?.position_s
  posAnchor.value = typeof p === 'number' ? { pos: p, at: Date.now() } : null
}, { immediate: true })

const nowTick = ref(Date.now())
let tickTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => { tickTimer = setInterval(() => { nowTick.value = Date.now() }, 500) })
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer) })

function fmtTime(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

const elapsed = computed(() => {
  if (!track.value || !posAnchor.value) return null
  return playing.value
    ? posAnchor.value.pos + (nowTick.value - posAnchor.value.at) / 1000
    : posAnchor.value.pos
})
const lcdTime = computed(() => (elapsed.value === null ? '--:--' : fmtTime(elapsed.value)))

/** "4. Artist – Title (3:50)" — the classic marquee line. */
const marqueeText = computed(() => {
  const t = track.value
  if (!t) return '*** VDock — nothing playing ***'
  const num = String(currentListIndex.value + 1).padStart(2, ' ')
  const dur = t.duration_s ? ` (${fmtTime(t.duration_s)})` : ''
  return `${num}. ${t.artist || 'Unknown'} - ${t.title}${dur}`
})

/** Source label fills the kbps slot (SMTC has no bitrate); kHz shows the
 *  pipeline's real 48 kHz capture rate. */
const kbpsLabel = computed(() => {
  const t = track.value
  if (!t) return ''
  const site = (t.site || '').toUpperCase()
  if (site) return site.slice(0, 7)
  return (t.source_app || '').replace(/\.exe$/i, '').slice(0, 7).toUpperCase()
})

// --- Mini spectrum analyzer — segmented bars + peak caps ----------------

const analyzerCanvas = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let resizeObs: ResizeObserver | null = null
const disp = new Array<number>(20).fill(0)
const peaks = new Array<number>(20).fill(0)

/** EQ mask: 10 sliders over the 20 display bands, ±12 dB → 0.25..4 gain. */
const eqOn = ref(true)
const preampDb = ref(0)
const eqDb = ref<number[]>(new Array(10).fill(0))
const eqGain = (i: number) => {
  if (!eqOn.value) return 1
  const db = preampDb.value + eqDb.value[i >> 1]
  return Math.pow(10, Math.max(-12, Math.min(12, db)) / 20)
}

function drawAnalyzer() {
  const canvas = analyzerCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const dpr = Math.min(2, window.devicePixelRatio || 1)
  const w = canvas.clientWidth, h = canvas.clientHeight
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr; canvas.height = h * dpr
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  const now = performance.now()
  const dt = Math.min(0.1, (now - lastFrame) / 1000)
  lastFrame = now
  const idle = !spectrum.live

  const COLS = 20
  const colW = w / COLS
  const SEG = 5, GAP = 1
  const rows = Math.max(4, Math.floor(h / (SEG + GAP)))
  const maxH = rows * (SEG + GAP)

  for (let c = 0; c < COLS; c++) {
    const target = Math.min(1, (spectrum.bands[c] / 100) * eqGain(c))
    const rise = Math.exp(-dt * 22), fall = Math.exp(-dt * 7)
    disp[c] = target > disp[c]
      ? target + (disp[c] - target) * rise
      : target + (disp[c] - target) * fall
    if (idle) disp[c] *= Math.exp(-dt * 4)
    if (disp[c] > peaks[c]) peaks[c] = disp[c]
    else peaks[c] = Math.max(disp[c], peaks[c] - dt * 0.55)

    const lit = Math.round(disp[c] * rows)
    for (let r = 0; r < rows; r++) {
      const y = h - (r + 1) * (SEG + GAP)
      const frac = r / rows
      const hue = frac < 0.55 ? 140 : frac < 0.8 ? 75 : 24
      if (r < lit) {
        ctx.fillStyle = `hsla(${hue}, 90%, 55%, 0.95)`
      } else {
        ctx.fillStyle = `hsla(${hue}, 60%, 22%, 0.28)`
      }
      ctx.fillRect(c * colW + 1, y, colW - 2, SEG)
    }
    const pr = Math.floor(peaks[c] * rows)
    if (pr > 0) {
      ctx.fillStyle = '#ffb13d'
      ctx.fillRect(c * colW + 1, h - pr * (SEG + GAP), colW - 2, SEG)
    }
  }
  rafId = requestAnimationFrame(drawAnalyzer)
}
let lastFrame = performance.now()

onMounted(() => {
  const canvas = analyzerCanvas.value
  if (canvas && typeof ResizeObserver !== 'undefined') {
    resizeObs = new ResizeObserver(() => { /* resize handled per-frame via clientWidth */ })
    resizeObs.observe(canvas)
  }
  rafId = requestAnimationFrame(drawAnalyzer)
})
onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObs?.disconnect()
})

// --- Volume slider: real via volume_get/volume_set + system_volume ------

const volume = ref(50)
const volDragging = ref(false)
const volTrack = ref<HTMLElement | null>(null)
let volThrottle: ReturnType<typeof setTimeout> | null = null

function setVolume(v: number, force = false): void {
  const rounded = Math.round(Math.max(0, Math.min(100, v)))
  volume.value = rounded
  if (volThrottle) clearTimeout(volThrottle)
  const fire = () => void socketClient.executeAction({
    type: 'cross_platform',
    config: { action: 'volume_set', value: rounded },
  }).catch(() => {})
  if (force) fire()
  else volThrottle = setTimeout(fire, 120)
}

function volFromPointer(clientX: number): number {
  const rect = volTrack.value?.getBoundingClientRect()
  if (!rect || !rect.width) return volume.value
  return Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100))
}

function onVolDown(e: PointerEvent): void {
  volDragging.value = true
  volTrack.value?.setPointerCapture?.(e.pointerId)
  setVolume(volFromPointer(e.clientX), true)
  window.addEventListener('pointermove', onVolMove)
  window.addEventListener('pointerup', onVolUp, { once: true })
}
function onVolMove(e: PointerEvent): void {
  if (volDragging.value) setVolume(volFromPointer(e.clientX))
}
function onVolUp(e: PointerEvent): void {
  volDragging.value = false
  window.removeEventListener('pointermove', onVolMove)
  setVolume(volFromPointer(e.clientX), true)
}

function onSystemVolume(data: { value?: number }): void {
  if (typeof data?.value === 'number' && !volDragging.value) {
    volume.value = Math.max(0, Math.min(100, data.value))
  }
}

onMounted(() => {
  socketClient.on('system_volume', onSystemVolume)
  void socketClient.executeAction({
    type: 'cross_platform', config: { action: 'volume_get' },
  }).then((res) => {
    if (res?.success && typeof res.data?.value === 'number') volume.value = res.data.value
  }).catch(() => {})
})
onUnmounted(() => {
  socketClient.off('system_volume', onSystemVolume)
  if (volThrottle) clearTimeout(volThrottle)
})

// --- Balance: cosmetic — springs back to center on release --------------

const balance = ref(50)
const balTrack = ref<HTMLElement | null>(null)
let balDragging = false

function balFromPointer(clientX: number): number {
  const rect = balTrack.value?.getBoundingClientRect()
  if (!rect || !rect.width) return 50
  return Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100))
}
function onBalDown(e: PointerEvent): void {
  balDragging = true
  balTrack.value?.setPointerCapture?.(e.pointerId)
  balance.value = balFromPointer(e.clientX)
  window.addEventListener('pointermove', onBalMove)
  window.addEventListener('pointerup', onBalUp, { once: true })
}
function onBalMove(e: PointerEvent): void {
  if (balDragging) balance.value = balFromPointer(e.clientX)
}
function onBalUp(e: PointerEvent): void {
  balDragging = false
  balance.value = balFromPointer(e.clientX)
  window.removeEventListener('pointermove', onBalMove)
  // No backend balance action exists — the thumb eases back to center.
  const settle = () => {
    balance.value += (50 - balance.value) * 0.3
    if (Math.abs(balance.value - 50) > 0.5) requestAnimationFrame(settle)
    else balance.value = 50
  }
  requestAnimationFrame(settle)
}

// --- Local LED toggles (SMTC can't report/set shuffle/repeat) -----------

const shuffleOn = ref(false)
const repeatOn = ref(false)

// --- Collapsible equalizer ----------------------------------------------

const eqOpen = ref(false)
function eqFlat(): void { preampDb.value = 0; eqDb.value.fill(0) }
const recentTracks = computed(() => nowPlaying.recent.value)
const currentListIndex = computed(() => {
  const t = track.value
  if (!t) return -1
  return recentTracks.value.findIndex(
    r => r.title === t.title && r.artist === t.artist)
})

// EQ slider rows — 10 sliders + preamp, vertical.
const EQ_BANDS = ['70', '180', '320', '600', '1K', '3K', '6K', '12K', '14K', '16K']
function onEqInput(i: number, e: Event): void {
  eqDb.value[i] = Number((e.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="winamp-root">
    <div class="winamp-frame">
      <!-- ── Main window ── -->
      <section class="winamp-window winamp-main" aria-label="Winamp player">
        <header class="win-titlebar">
          <span class="win-title-grip" aria-hidden="true"></span>
          <span class="win-title-text">WINAMP</span>
          <span class="win-title-btns">
            <button type="button" class="win-tb" :class="{ lit: eqOpen }" title="Equalizer — expand / collapse" @click="eqOpen = !eqOpen">EQ</button>
            <button type="button" class="win-tb win-tb-close" title="Back to deck" aria-label="Back to deck" @click="emit('exit')">×</button>
          </span>
        </header>

        <div class="win-display">
          <div class="win-display-left">
            <span class="win-lcd-time">{{ lcdTime }}</span>
            <canvas ref="analyzerCanvas" class="win-analyzer" aria-hidden="true"></canvas>
          </div>
          <div class="win-display-right">
            <div class="win-marquee"><span class="win-marquee-text">{{ marqueeText }}</span></div>
            <div class="win-readouts">
              <span class="win-readout"><b>{{ kbpsLabel || '———' }}</b><i>kbps</i></span>
              <span class="win-readout"><b>48</b><i>kHz</i></span>
              <span class="win-stereo"><i class="mono">mono</i><i class="stereo lit">stereo</i></span>
            </div>
          </div>
        </div>

        <div class="win-sliders">
          <div class="win-slider">
            <span class="win-slider-label">Volume</span>
            <div ref="volTrack" class="win-slider-track" role="slider" aria-label="Volume"
                 :aria-valuenow="volume" aria-valuemin="0" aria-valuemax="100"
                 @pointerdown="onVolDown">
              <span class="win-slider-fill" :style="{ width: volume + '%' }"></span>
              <span class="win-slider-thumb" :style="{ left: volume + '%' }"></span>
            </div>
          </div>
          <div class="win-slider">
            <span class="win-slider-label">Balance</span>
            <div ref="balTrack" class="win-slider-track is-cosmetic" role="presentation"
                 @pointerdown="onBalDown">
              <span class="win-slider-thumb" :style="{ left: balance + '%' }"></span>
            </div>
          </div>
        </div>

        <div class="win-transport">
          <button type="button" class="win-btn" title="Previous" aria-label="Previous track" @click="media('media_previous')">
            <FontAwesomeIcon :icon="['fas', 'backward-step']" />
          </button>
          <button type="button" class="win-btn win-btn-play" :title="playing ? 'Pause' : 'Play'"
                  :aria-label="playing ? 'Pause' : 'Play'" @click="media('media_play_pause')">
            <FontAwesomeIcon :icon="['fas', playing ? 'pause' : 'play']" />
          </button>
          <button type="button" class="win-btn" title="Stop" aria-label="Stop" @click="media('media_stop')">
            <FontAwesomeIcon :icon="['fas', 'stop']" />
          </button>
          <button type="button" class="win-btn" title="Next" aria-label="Next track" @click="media('media_next')">
            <FontAwesomeIcon :icon="['fas', 'forward-step']" />
          </button>
          <button type="button" class="win-btn win-btn-eject" title="Eject — back to deck" aria-label="Eject — back to deck" @click="emit('exit')">
            <FontAwesomeIcon :icon="['fas', 'eject']" />
          </button>
        </div>

        <div class="win-toggles">
          <button type="button" class="win-toggle" :class="{ lit: shuffleOn }" title="Shuffle (visual only)" @click="shuffleOn = !shuffleOn">SHUFFLE</button>
          <button type="button" class="win-toggle" :class="{ lit: repeatOn }" title="Repeat (visual only)" @click="repeatOn = !repeatOn">REPEAT</button>
          <span class="win-wordmark" aria-hidden="true">VDock</span>
        </div>
      </section>

      <!-- ── Equalizer window ── -->
      <section v-if="eqOpen" class="winamp-window winamp-eq" aria-label="Equalizer">
        <header class="win-titlebar">
          <span class="win-title-grip" aria-hidden="true"></span>
          <span class="win-title-text">WINAMP EQUALIZER</span>
          <span class="win-title-btns">
            <button type="button" class="win-tb" title="Collapse" aria-label="Collapse equalizer" @click="eqOpen = false">×</button>
          </span>
        </header>
        <div class="win-eq-switches">
          <button type="button" class="win-tb" :class="{ lit: eqOn }" title="EQ on/off" @click="eqOn = !eqOn">ON</button>
          <button type="button" class="win-tb" title="Reset all bands to flat" @click="eqFlat">PRESETS</button>
        </div>
        <div class="win-eq-body">
          <div class="win-eq-col">
            <span class="win-eq-cap">+12db</span>
            <input type="range" class="win-eq-slider" min="-12" max="12" step="1"
                   v-model.number="preampDb" aria-label="Preamp" />
            <span class="win-eq-cap">−12db</span>
            <span class="win-eq-name">PREAMP</span>
          </div>
          <div v-for="(label, i) in EQ_BANDS" :key="label" class="win-eq-col">
            <span class="win-eq-cap">+12</span>
            <input type="range" class="win-eq-slider" min="-12" max="12" step="1"
                   :value="eqDb[i]" :aria-label="`EQ ${label}`" @input="onEqInput(i, $event)" />
            <span class="win-eq-cap">−12</span>
            <span class="win-eq-name">{{ label }}</span>
          </div>
        </div>
        <p class="win-eq-note">Shapes the analyzer display — the audio path is untouched.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* Classic 2.x chrome: dark navy-violet shells, black LCD wells, green
   phosphor text, orange peak accents. */
.winamp-root {
  position: absolute;
  inset: 0;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(8px, 2vmin, 24px);
  background:
    radial-gradient(120% 90% at 50% 0%, #181830 0%, #0b0b16 70%);
  font-family: 'Lucida Console', 'Consolas', ui-monospace, monospace;
  -webkit-font-smoothing: none;
}

.winamp-frame {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: min(460px, 96vw);
  max-height: 100%;
}

.winamp-window {
  background: linear-gradient(180deg, #2b2b45 0%, #232338 55%, #1c1c2e 100%);
  border: 1px solid #000;
  border-radius: 3px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.6),
    0 10px 30px rgba(0, 0, 0, 0.55);
  overflow: hidden;
}

.win-titlebar {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 18px;
  padding: 0 5px;
  background: linear-gradient(90deg, #11111f, #2e2e4e 30%, #2e2e4e 70%, #11111f);
  border-bottom: 1px solid #000;
  color: #9aa0c0;
  font-size: clamp(9px, 1.6vmin, 11px);
  letter-spacing: 2px;
  user-select: none;
}
.win-title-grip {
  width: 22px; height: 8px;
  border-top: 1px solid #585878; border-bottom: 1px solid #585878;
  box-shadow: 0 2px 0 #585878 inset, 0 -2px 0 #585878 inset;
}
.win-title-text { flex: 1; font-weight: 700; text-shadow: 0 1px 0 #000; }
.win-title-btns { display: flex; gap: 3px; }
.win-tb {
  min-width: 18px; height: 12px;
  padding: 0 4px;
  background: linear-gradient(180deg, #4a4a6e, #34344f);
  border: 1px solid #0a0a12;
  border-radius: 1px;
  color: #c8cce0; font-size: clamp(7px, 1.3vmin, 9px); font-family: inherit;
  line-height: 1; cursor: pointer;
}
.win-tb:active { background: #1a1a2a; color: #fff; }
.win-tb.lit { color: #7dff9a; box-shadow: inset 0 0 4px rgba(125, 255, 154, 0.4); }
.win-tb-close:hover { color: #ff6b6b; }

/* Display block */
.win-display {
  display: flex;
  gap: 8px;
  margin: 8px;
  padding: 8px;
  background: #05070a;
  border: 1px solid #000;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03), inset 0 4px 12px rgba(0,0,0,0.8);
}
.win-display-left { display: flex; flex-direction: column; gap: 4px; width: 46%; }
.win-lcd-time {
  align-self: flex-end;
  color: #8dffa8;
  font-size: clamp(18px, 3.4vmin, 26px);
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 0 6px rgba(125, 255, 154, 0.55);
  font-variant-numeric: tabular-nums;
}
.win-analyzer {
  width: 100%;
  height: clamp(44px, 9vmin, 72px);
  display: block;
}
.win-display-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.win-marquee {
  overflow: hidden;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 2px;
}
.win-marquee-text {
  display: inline-block;
  padding-left: 100%;
  color: #8dffa8;
  font-size: clamp(11px, 2vmin, 14px);
  letter-spacing: 1px;
  text-shadow: 0 0 5px rgba(125, 255, 154, 0.4);
  animation: win-marquee 14s linear infinite;
}
@keyframes win-marquee {
  to { transform: translateX(-100%); }
}
.win-readouts {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #8dffa8;
  font-size: clamp(10px, 1.8vmin, 13px);
}
.win-readout b { font-weight: 700; }
.win-readout i { font-style: normal; color: #4a8a58; margin-left: 3px; font-size: clamp(8px, 1.5vmin, 10px); }
.win-stereo { margin-left: auto; font-size: clamp(8px, 1.5vmin, 10px); letter-spacing: 1px; }
.win-stereo i { font-style: normal; margin-left: 6px; color: #3a3a55; }
.win-stereo i.lit { color: #8dffa8; text-shadow: 0 0 5px rgba(125,255,154,.5); }

/* Sliders */
.win-sliders {
  display: flex;
  gap: 12px;
  margin: 0 8px 8px;
}
.win-slider { flex: 1; display: flex; align-items: center; gap: 8px; }
.win-slider-label {
  color: #7a7ea0; font-size: clamp(8px, 1.5vmin, 10px); letter-spacing: 1px; text-transform: uppercase;
  min-width: 44px;
}
.win-slider-track {
  position: relative;
  flex: 1;
  height: 14px;
  background: linear-gradient(180deg, #0a0a14, #16162a);
  border: 1px solid #000;
  box-shadow: inset 0 1px 3px rgba(0,0,0,.8);
  cursor: pointer;
  touch-action: none;
}
.win-slider-fill {
  position: absolute; inset: 0 auto 0 0;
  background: linear-gradient(90deg, #1d5c33, #2fa04f);
  opacity: .55;
}
.win-slider-thumb {
  position: absolute; top: -3px;
  width: 12px; height: 18px;
  transform: translateX(-50%);
  background: linear-gradient(180deg, #5a5a80, #3c3c5c 55%, #2c2c46);
  border: 1px solid #0a0a12;
  border-radius: 1px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 1px 2px rgba(0,0,0,.6);
  pointer-events: none;
}
.is-cosmetic { opacity: .75; }

/* Transport */
.win-transport {
  display: flex;
  gap: 6px;
  margin: 0 8px 8px;
}
.win-btn {
  flex: 1;
  height: clamp(30px, 5.4vmin, 40px);
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(180deg, #4a4a6e, #34344f 60%, #2a2a44);
  border: 1px solid #0a0a12;
  border-radius: 2px;
  color: #cdd2ea;
  font-size: clamp(11px, 1.9vmin, 14px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
  cursor: pointer;
}
.win-btn:active { transform: translateY(1px); box-shadow: none; color: #fff; }
.win-btn-play { color: #8dffa8; }
.win-btn-eject { flex: 0 0 2.2em; }

/* Toggles row */
.win-toggles {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 8px 8px;
}
.win-toggle {
  padding: 4px 10px;
  background: linear-gradient(180deg, #3a3a58, #28283e);
  border: 1px solid #0a0a12;
  border-radius: 2px;
  color: #6a6e90; font-size: clamp(8px, 1.5vmin, 10px); letter-spacing: 1px; font-family: inherit;
  cursor: pointer;
}
.win-toggle.lit {
  color: #8dffa8;
  box-shadow: inset 0 0 6px rgba(125, 255, 154, 0.35);
}
.win-wordmark {
  margin-left: auto;
  color: #565a78; font-size: clamp(9px, 1.6vmin, 11px); font-style: italic; letter-spacing: 1px;
}

/* Equalizer */
.win-eq-switches {
  display: flex;
  gap: 4px;
  margin: 6px 8px 0;
}
.win-eq-switches .win-tb {
  height: 14px;
  min-width: 30px;
  letter-spacing: 1px;
}
.win-eq-body {
  display: flex;
  gap: 4px;
  margin: 8px;
  padding: 8px 4px;
  background: #05070a;
  border: 1px solid #000;
}
.win-eq-col {
  flex: 1;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  min-width: 0;
}
.win-eq-cap { color: #4a8a58; font-size: clamp(7px, 1.3vmin, 9px); }
.win-eq-name { color: #7a7ea0; font-size: clamp(7px, 1.3vmin, 9px); margin-top: 2px; }
.win-eq-slider {
  writing-mode: vertical-lr;
  direction: rtl;
  width: 16px;
  height: clamp(64px, 12vmin, 96px);
  appearance: none;
  background: transparent;
  cursor: pointer;
}
.win-eq-slider::-webkit-slider-runnable-track {
  width: 6px;
  background: linear-gradient(90deg, #0a0a14, #16162a);
  border: 1px solid #000;
}
.win-eq-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px; height: 10px;
  background: linear-gradient(90deg, #d9c34a, #a8932f 60%, #7a6a22);
  border: 1px solid #2a2008;
  border-radius: 1px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.35);
}
.win-eq-note {
  margin: 0 8px 8px;
  color: #565a78; font-size: clamp(8px, 1.5vmin, 10px);
}

/* Portrait phones (and narrow panels): player fills the width. */
@media (max-width: 899px), (max-aspect-ratio: 1/1) {
  .winamp-root { align-items: stretch; }
  .winamp-frame { width: 100%; height: 100%; justify-content: center; }
}

@media (prefers-reduced-motion: reduce) {
  .win-marquee-text { animation: none; padding-left: 0; }
}
</style>
