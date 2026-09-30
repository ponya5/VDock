<template>
  <div
    class="timer-face"
    :class="{
      compact,
      'is-running': timer?.running,
      'is-paused': timer && !timer.running && hasProgress && !timer.expired,
      'is-expired': timer?.expired,
      'is-flashing': timer?.flashing,
      'is-idle': !timer || (!timer.running && !hasProgress && !timer.expired),
    }"
    :style="fontStyle"
  >
    <div class="timer-head">
      <FontAwesomeIcon :icon="modeIcon" class="timer-mode-icon" />
      <span v-if="button.label" class="timer-label">{{ button.label }}</span>
      <FontAwesomeIcon :icon="stateIcon" class="timer-state-icon" />
    </div>

    <div class="timer-time">{{ display }}</div>

    <div class="timer-sub">{{ statusText }}</div>

    <!-- Countdown progress: empties as time runs out. Stopwatch shows a
         per-minute fill so the face still visibly moves while running. -->
    <div v-if="timer" class="timer-progress" aria-hidden="true">
      <div class="timer-progress-fill" :style="{ width: `${progressPct}%` }" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Face for `time_timer` / `time_stopwatch` buttons (DL-122).
 *
 * Display-only: the tap goes through DeckButton's normal press path into
 * `dashboardStore.executeButtonAction` → `timerButtons.toggle`, so this
 * component never owns a click handler and can never eat the press. All
 * state lives in the shared engine — remounting (scene switch, page
 * flip) re-reads the same timer rather than starting over.
 */
import { computed, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Button } from '@/types'
import timerButtons from '@/services/timerButtons'

const props = withDefaults(defineProps<{
  button: Button
  compact?: boolean
  fontSize?: number
}>(), { compact: false, fontSize: 1.0 })

const timer = computed(() => timerButtons.getTimer(props.button.id))
const config = computed(() => props.button.action?.config ?? {})
const isCountdown = computed(() => (timer.value?.mode ?? 'countdown') === 'countdown')

const hasProgress = computed(() => {
  const t = timer.value
  if (!t) return false
  return isCountdown.value ? t.remainingS < t.durationS : t.elapsedS > 0
})

function fmt(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const mm = String(m).padStart(2, '0')
  const ss = String(sec).padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}

const display = computed(() => {
  const t = timer.value
  if (!t) {
    // Never started: show the armed duration (or 00:00 for a stopwatch).
    const cfg = timerButtons.normalizeConfig(config.value, props.button.action?.type)
    return fmt(cfg.mode === 'countdown' ? Number(cfg.duration_s ?? 0) : 0)
  }
  return fmt(isCountdown.value ? t.remainingS : t.elapsedS)
})

const progressPct = computed(() => {
  const t = timer.value
  if (!t) return 0
  if (isCountdown.value) {
    return t.durationS > 0 ? Math.min(100, (t.remainingS / t.durationS) * 100) : 0
  }
  return (t.elapsedS % 60) / 60 * 100
})

const modeIcon = computed(() =>
  isCountdown.value ? ['fas', 'hourglass-half'] : ['fas', 'stopwatch']
)

const stateIcon = computed(() => {
  const t = timer.value
  if (!t) return ['fas', 'play']
  if (t.expired) return ['fas', 'bell']
  return t.running ? ['fas', 'pause'] : ['fas', 'play']
})

const statusText = computed(() => {
  const t = timer.value
  if (!t) return 'Ready'
  if (t.expired) return 'Done — tap to re-arm'
  if (t.running) return isCountdown.value ? 'remaining' : 'elapsed'
  return hasProgress.value ? 'Paused' : 'Ready'
})

const fontStyle = computed(() => ({
  '--font-size-multiplier': props.fontSize || 1
}))

onMounted(() => {
  timerButtons.ensureMounted(
    props.button.id,
    config.value,
    props.button.action?.type
  )
})
</script>

<style scoped>
.timer-face {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  height: 100%;
  padding: 6px 8px;
  box-sizing: border-box;
  color: #eef2fa;
}

.timer-head {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  font-size: calc(0.72rem * var(--font-size-multiplier, 1));
  opacity: 0.85;
}

.timer-mode-icon {
  font-size: 0.9em;
  flex-shrink: 0;
}

.timer-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  text-align: left;
}

.timer-state-icon {
  flex-shrink: 0;
  font-size: 0.9em;
}

.is-running .timer-state-icon {
  color: #4ade80;
}

.is-paused .timer-state-icon {
  color: #fbbf24;
}

.timer-time {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  line-height: 1;
  font-size: calc(1.9rem * var(--font-size-multiplier, 1));
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.compact .timer-time {
  font-size: calc(1.25rem * var(--font-size-multiplier, 1));
}

.timer-sub {
  font-size: calc(0.62rem * var(--font-size-multiplier, 1));
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.timer-progress {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.14);
  overflow: hidden;
}

.timer-progress-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--btn-brand, var(--color-primary, #5b8cff));
  transition: width 0.25s linear;
}

.is-expired .timer-progress-fill {
  background: #f87171;
}

/* Expiry alarm: pulses the whole face until the flash window closes.
   `expired` alone keeps a red progress bar + "Done" sublabel. */
.is-flashing {
  animation: timer-alarm-flash 0.8s ease-in-out infinite;
}

@keyframes timer-alarm-flash {
  0%, 100% { background-color: transparent; }
  50% { background-color: rgba(220, 38, 38, 0.45); }
}

@media (prefers-reduced-motion: reduce) {
  .is-flashing {
    animation: none;
    background-color: rgba(220, 38, 38, 0.3);
  }
}
</style>
