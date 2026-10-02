<template>
  <!-- DL-141 F/U2: sensor-panel dial — a 270° arc of ticks (unlit ticks are
       the track), a sweeping needle, and a tweened center readout. All
       motion is CSS transitions / one rAF counter, so the panel GPU stays
       idle between the 2.5 s polls. -->
  <div class="gd" :class="{ 'gd-empty': value == null }">
    <svg class="gd-svg" viewBox="0 0 100 100" aria-hidden="true">
      <line
        v-for="(tk, i) in ticks"
        :key="i"
        class="gd-tick"
        :class="{ 'gd-tick-on': tk.on }"
        x1="50" y1="8" x2="50" y2="16"
        :transform="`rotate(${tk.angle} 50 50)`"
        :style="{ color: tk.color, transitionDelay: tk.delay }"
      />
      <line
        v-if="value != null"
        class="gd-needle"
        x1="50" y1="50" x2="50" y2="13"
        :style="needleStyle"
      />
      <circle v-if="value != null" class="gd-hub" cx="50" cy="50" r="3.2" />
    </svg>
    <div class="gd-center">
      <span :key="popKey" class="gd-num">{{ centerText }}</span>
      <span v-if="unit" class="gd-unit">{{ unit }}</span>
      <span v-if="label" class="gd-label">{{ label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  /** 0–100 position on the dial; null = no reading (ticks all dim). */
  value: number | null
  /** Center text override (e.g. a formatted rate) — skips the tween. */
  display?: string | null
  unit?: string
  label?: string
  /** 'load' = green→red by position; 'cool' = cyan for network-style dials. */
  scheme?: 'load' | 'cool'
  tickCount?: number
}>(), { unit: '', label: '', scheme: 'load', tickCount: 33 })

const SPAN = 270
const START = -SPAN / 2

const reducedMotion =
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

const clamped = computed(() =>
  props.value == null ? null : Math.min(100, Math.max(0, props.value)),
)

/** Position-graded hue: green at empty through yellow to red at full —
 *  the arc color tells the severity before the number is even read. */
function tickColor(pos: number): string {
  if (props.scheme === 'cool') return `hsl(196, 92%, ${56 + pos * 10}%)`
  const hue = pos <= 0.5 ? 140 - 180 * pos : 50 - 100 * (pos - 0.5)
  return `hsl(${hue}, 88%, 56%)`
}

const ticks = computed(() => {
  const n = Math.max(9, props.tickCount)
  const v = clamped.value
  return Array.from({ length: n }, (_, i) => {
    const pos = n > 1 ? i / (n - 1) : 0
    return {
      angle: START + pos * SPAN,
      on: v != null && ((i + 0.5) / n) * 100 <= v,
      color: tickColor(pos),
      delay: `${i * 9}ms`,
    }
  })
})

const needleAngle = computed(() =>
  clamped.value == null ? START : START + (clamped.value / 100) * SPAN,
)

const needleStyle = computed(() => ({
  transform: `rotate(${needleAngle.value}deg)`,
  transformOrigin: '50px 50px',
  transition: reducedMotion ? 'none' : 'transform 0.7s cubic-bezier(0.3, 1.35, 0.45, 1)',
}))

/* Center number tween — digits count between polls instead of snapping.
   First real value lands instantly so a fresh mount reads correctly. */
const shown = ref<number | null>(null)
let primed = false
let raf = 0

watch(clamped, (v) => {
  cancelAnimationFrame(raf)
  if (v == null) { shown.value = null; return }
  if (!primed || reducedMotion) { shown.value = v; primed = true; return }
  const from = shown.value ?? 0
  const t0 = performance.now()
  const step = (now: number) => {
    const k = Math.min(1, (now - t0) / 650)
    shown.value = from + (v - from) * (1 - Math.pow(1 - k, 3))
    if (k < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}, { immediate: true })

onUnmounted(() => cancelAnimationFrame(raf))

const centerText = computed(() =>
  props.display ?? (shown.value == null ? '—' : String(Math.round(shown.value))),
)
/* String displays (rates) get a pop on change; tweened numbers shouldn't
   remount every frame — they key to a stable value. */
const popKey = computed(() => (props.display != null ? centerText.value : 'num'))
</script>

<style scoped>
.gd {
  position: relative;
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 100%;
  aspect-ratio: 1;
  margin: 0 auto;
}

.gd-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.gd-tick {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 2.4;
  stroke-linecap: round;
  transition: stroke 0.4s ease, opacity 0.4s ease;
}

.gd-tick-on {
  stroke: currentColor;
  filter: drop-shadow(0 0 2.5px currentColor);
}

.gd-needle {
  stroke: rgba(255, 255, 255, 0.92);
  stroke-width: 1.8;
  stroke-linecap: round;
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.55));
}

.gd-hub {
  fill: #0a0e18;
  stroke: rgba(255, 255, 255, 0.55);
  stroke-width: 1;
}

.gd-empty .gd-needle,
.gd-empty .gd-hub {
  opacity: 0.15;
}

.gd-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  pointer-events: none;
}

.gd-num {
  font-family: 'Instrument Serif', Georgia, 'Times New Roman', serif;
  font-size: clamp(1.5rem, 4.6vh, 2.9rem);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  animation: gd-num-in 0.35s ease;
}

.gd-unit {
  font-size: clamp(0.55rem, 1vw, 0.72rem);
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.5);
}

.gd-label {
  margin-top: 4px;
  font-size: clamp(0.5rem, 0.9vw, 0.62rem);
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.38);
}

@keyframes gd-num-in {
  from { transform: scale(1.12); opacity: 0.4; }
  to { transform: scale(1); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .gd-tick, .gd-needle { transition: none; }
  .gd-num { animation: none; }
}
</style>
