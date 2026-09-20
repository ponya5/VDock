<template>
  <div class="slider-face" :class="{ compact }">
    <div class="slider-head">
      <FontAwesomeIcon :icon="targetIcon" class="slider-icon" />
      <span v-if="button.label" class="slider-label">{{ button.label }}</span>
      <span class="slider-value">{{ Math.round(value) }}<small>%</small></span>
    </div>
    <div
      ref="trackRef"
      class="slider-track"
      role="slider"
      :aria-valuenow="Math.round(value)"
      :aria-valuemin="min"
      :aria-valuemax="max"
      :aria-label="button.label || 'Slider'"
      tabindex="0"
      @pointerdown="onPointerDown"
      @keydown.left.prevent="nudge(-step)"
      @keydown.down.prevent="nudge(-step)"
      @keydown.right.prevent="nudge(step)"
      @keydown.up.prevent="nudge(step)"
    >
      <div class="slider-fill" :style="{ width: `${fillPct}%` }" />
      <div class="slider-thumb" :style="{ left: `${fillPct}%` }" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Drag face for `action.type === 'slider'`. The button becomes a track: drag
 * horizontally to set a level, or tap near an edge to nudge one step.
 *
 * Targets:
 *   volume        → cross_platform volume_set (absolute, 0-100)
 *   brightness    → cross_platform brightness_set
 *   ui_brightness → local VDock dimmer, no backend round-trip
 *
 * Dispatches are throttled while dragging (the backend applies real volume —
 * 60 events/sec of nircmd calls is how sliders get laggy), with a final set on
 * release so the resting value always lands.
 */
import { computed, onMounted, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useButtonStateStore } from '@/stores/buttonState'
import { useSettingsStore } from '@/stores/settings'
import { vibrate } from '@/utils/haptics'

const props = defineProps<{ button: Button; compact?: boolean }>()

const dashboardStore = useDashboardStore()
const buttonStateStore = useButtonStateStore()
const settingsStore = useSettingsStore()

const cfg = computed(() => props.button.action?.config ?? {})
const target = computed(() => cfg.value.target ?? 'volume')
const min = computed(() => Number(cfg.value.min ?? 0))
const max = computed(() => Number(cfg.value.max ?? 100))
const step = computed(() => Math.max(1, Number(cfg.value.step ?? 1)))

const value = ref<number>(Number(cfg.value.value ?? min.value))
const dragging = ref(false)
const trackRef = ref<HTMLElement | null>(null)
let lastDispatch = 0
const THROTTLE_MS = 120

const fillPct = computed(() =>
  max.value === min.value ? 0 : ((value.value - min.value) / (max.value - min.value)) * 100
)

const targetIcon = computed(() => {
  if (target.value === 'volume') {
    return value.value <= 0 ? ['fas', 'volume-mute'] : value.value < 50 ? ['fas', 'volume-down'] : ['fas', 'volume-up']
  }
  if (target.value === 'brightness') return ['fas', 'sun']
  return ['fas', 'adjust']
})

function clamp(v: number): number {
  return Math.min(max.value, Math.max(min.value, Math.round(v / step.value) * step.value))
}

function apply(v: number, force = false) {
  value.value = clamp(v)
  const now = Date.now()
  if (!force && now - lastDispatch < THROTTLE_MS) return
  lastDispatch = now

  if (target.value === 'ui_brightness') {
    settingsStore.uiBrightness = Math.round(value.value)
    buttonStateStore.set(props.button.id, { badge: `${Math.round(value.value)}%` })
    return
  }

  const rounded = Math.round(value.value)
  const action = target.value === 'brightness'
    ? { type: 'cross_platform', config: { action: 'brightness_set', brightness: rounded } }
    : { type: 'cross_platform', config: { action: 'volume_set', value: rounded } }
  dashboardStore.executeAction(action, props.button.id).then((result) => {
    if (result?.success) {
      buttonStateStore.set(props.button.id, { badge: result.data?.badge ?? `${rounded}%` })
    }
  }).catch(() => { /* throttled dispatch — failures ride the next move */ })
}

function valueFromPointer(clientX: number): number {
  const rect = trackRef.value?.getBoundingClientRect()
  if (!rect || rect.width === 0) return value.value
  const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  return min.value + ratio * (max.value - min.value)
}

function onPointerDown(e: PointerEvent) {
  if (props.button.enabled === false) return
  dragging.value = true
  try {
    trackRef.value?.setPointerCapture(e.pointerId)
  } catch { /* fine — move/up may just be missed */ }
  apply(valueFromPointer(e.clientX), true)
  vibrate(20)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp, { once: true })
  window.addEventListener('pointercancel', onPointerUp, { once: true })
}

function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return
  apply(valueFromPointer(e.clientX))
}

function onPointerUp(e: PointerEvent) {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('pointermove', onPointerMove)
  apply(valueFromPointer(e.clientX), true)
}

function nudge(delta: number) {
  apply(value.value + delta, true)
}

onMounted(() => {
  // Show the REAL level, not the last-saved config — the OS may have moved
  // since this button was made. Best effort: stay silent on failure.
  if (target.value === 'volume') {
    dashboardStore.executeAction(
      { type: 'cross_platform', config: { action: 'volume_get' } },
      props.button.id
    ).then((result) => {
      if (result?.success && typeof result.data?.value === 'number') {
        value.value = clamp(result.data.value)
      }
    }).catch(() => {})
  } else if (target.value === 'ui_brightness') {
    value.value = clamp(settingsStore.uiBrightness)
  }
})
</script>

<style scoped>
.slider-face {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  padding: 4px 8px;
}
.slider-head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.slider-icon {
  font-size: 1rem;
  opacity: 0.9;
}
.slider-label {
  flex: 1;
  min-width: 0;
  font-size: 0.8rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.slider-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 0.9rem;
}
.slider-value small {
  font-size: 0.65rem;
  opacity: 0.7;
}
.slider-track {
  position: relative;
  height: 28px; /* touch: the whole band is grabbable, not just the thumb */
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  touch-action: none; /* drag must not scroll/pinch the page */
  cursor: pointer;
  outline-offset: 2px;
}
.slider-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--color-primary, #5b8cff), #8ab4ff);
  transition: none; /* follows the finger — laggy transitions feel broken */
}
.slider-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
}
.compact .slider-track { height: 22px; }
.compact .slider-thumb { width: 18px; height: 18px; }
</style>
