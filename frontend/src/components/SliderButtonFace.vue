<template>
  <div
    class="slider-face"
    :class="{ compact }"
    :style="faceStyle"
    @wheel.prevent="onWheel"
  >
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
    <div v-if="showPresets" class="slider-presets">
      <button
        v-for="preset in presets"
        :key="preset.value"
        type="button"
        class="slider-preset"
        :class="{ active: preset.isActive }"
        @pointerdown.stop
        @click="applyPreset(preset.value)"
      >
        <FontAwesomeIcon v-if="preset.icon" :icon="preset.icon" />
        <span v-else>{{ preset.label }}</span>
      </button>
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
 *   app_volume    → per-app session volume (config.process)
 *
 * Dispatches are throttled while dragging (the backend applies real volume —
 * 60 events/sec of nircmd calls is how sliders get laggy), with a final set on
 * release so the resting value always lands.
 *
 * A row of quick-jump chips (0/25/50/75/100% of the configured range) sits
 * under the track — `config.show_presets` (default true) turns it off for
 * buttons too small to fit it.
 */
import { computed, onMounted, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useButtonStateStore } from '@/stores/buttonState'
import { useSettingsStore } from '@/stores/settings'
import { vibrate } from '@/utils/haptics'

const props = defineProps<{ button: Button; compact?: boolean; buttonSize?: number }>()

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
let wheelTimer: number | undefined
const THROTTLE_MS = 120

const fillPct = computed(() =>
  max.value === min.value ? 0 : ((value.value - min.value) / (max.value - min.value)) * 100
)

// Match the regular button label sizing (DeckButton labelStyle): the button's
// fontSize scaled by the global button-size/touch-mode multiplier. Track and
// thumb scale too, but capped so big scales don't turn the track into a bar.
const faceScale = computed(() => props.buttonSize ?? 1)
const faceStyle = computed(() => {
  const base = props.button.style?.fontSize || 14
  const trackScale = Math.min(faceScale.value, 1.5)
  return {
    '--slider-text': `${Math.max(10, Math.round(base * faceScale.value))}px`,
    '--slider-track-h': `${Math.round(28 * trackScale)}px`,
    '--slider-thumb': `${Math.round(24 * trackScale)}px`
  }
})

const targetIcon = computed(() => {
  if (target.value === 'volume') {
    return value.value <= 0 ? ['fas', 'volume-mute'] : value.value < 50 ? ['fas', 'volume-down'] : ['fas', 'volume-up']
  }
  if (target.value === 'brightness') return ['fas', 'sun']
  if (target.value === 'app_volume') return ['fas', 'headphones']
  return ['fas', 'adjust']
})

// Quick-jump chips under the track: the bottom of the range, three even
// steps across it, and the top — the same "0/25/50/75/100" shape regardless
// of a custom min/max. Volume's bottom chip reads as mute (an icon, not a
// number) since that's what tapping it does.
const showPresets = computed(() => cfg.value.show_presets !== false)

const presets = computed(() => {
  const range = max.value - min.value
  const fractions = [0, 0.25, 0.5, 0.75, 1]
  return fractions.map((fraction) => {
    const presetValue = clamp(min.value + fraction * range)
    const isMuteChip = target.value === 'volume' && fraction === 0
    return {
      value: presetValue,
      label: `${Math.round(presetValue)}`,
      icon: isMuteChip ? ['fas', 'volume-mute'] : null,
      isActive: Math.round(value.value) === Math.round(presetValue)
    }
  })
})

function applyPreset(presetValue: number) {
  apply(presetValue, true)
  vibrate(20)
}

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
    : target.value === 'app_volume'
      ? { type: 'cross_platform', config: { action: 'app_volume_set', process: cfg.value.process ?? '', value: rounded } }
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
  // In edit mode the press belongs to the parent's drag-grab — applying a value
  // would fire a real volume_set/brightness_set while rearranging, and pointer
  // capture would steal the gesture.
  if (props.button.enabled === false || dashboardStore.isEditMode) return
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

// A wheel notch should be audible, not sub-perceptible — floor at 5%
// even when the configured step is finer.
const wheelStep = computed(() => Math.max(step.value, 5))

function onWheel(e: WheelEvent) {
  if (props.button.enabled === false || dashboardStore.isEditMode) return
  const dir = e.deltaY < 0 ? 1 : -1
  apply(value.value + dir * wheelStep.value)
  vibrate(8)
  // The 120ms dispatch throttle can swallow the final tick, leaving the
  // system level short of what the face shows — force it once the wheel
  // stops moving.
  window.clearTimeout(wheelTimer)
  wheelTimer = window.setTimeout(() => apply(value.value, true), 160)
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
  } else if (target.value === 'app_volume' && cfg.value.process) {
    dashboardStore.executeAction(
      { type: 'cross_platform', config: { action: 'app_volume_get', process: cfg.value.process } },
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
  font-size: calc(var(--slider-text, 13px) * 1.15);
  opacity: 0.9;
}
.slider-label {
  flex: 1;
  min-width: 0;
  font-size: var(--slider-text, 0.8rem);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.slider-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: calc(var(--slider-text, 14px) * 1.08);
}
.slider-value small {
  font-size: calc(var(--slider-text, 14px) * 0.72);
  opacity: 0.7;
}
.slider-track {
  position: relative;
  height: var(--slider-track-h, 28px); /* touch: the whole band is grabbable, not just the thumb */
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
  width: var(--slider-thumb, 24px);
  height: var(--slider-thumb, 24px);
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
}
.compact .slider-track { height: calc(var(--slider-track-h, 28px) * 0.78); }
.compact .slider-thumb { width: calc(var(--slider-thumb, 24px) * 0.75); height: calc(var(--slider-thumb, 24px) * 0.75); }

.slider-presets {
  display: flex;
  gap: 4px;
}
.slider-preset {
  flex: 1;
  min-width: 0;
  height: 20px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  font-size: calc(var(--slider-text, 13px) * 0.62);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  touch-action: manipulation;
}
.slider-preset:hover {
  background: rgba(255, 255, 255, 0.16);
}
.slider-preset.active {
  background: var(--color-primary, #5b8cff);
  border-color: transparent;
}
.compact .slider-preset { height: 16px; font-size: calc(var(--slider-text, 13px) * 0.55); }
</style>
