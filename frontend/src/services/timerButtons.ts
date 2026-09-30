/**
 * Deck-button timer engine (DL-122).
 *
 * The old `time_timer` face kept a per-mount `setInterval` — every scene
 * switch reset it and the widget could never be pressed (it was
 * `display_only`). Timers now live here, keyed by button id in a
 * module-level map, so a countdown keeps running while the user browses
 * other scenes and its face simply re-reads the shared state on mount.
 *
 * One 250 ms interval is shared by all live timers; elapsed time is
 * derived from `Date.now()` deltas rather than tick counting, which
 * doesn't drift and costs nothing between ticks. Everything is a plain
 * reactive object so `TimerButtonFace` and rule evaluation re-render on
 * field writes with no extra plumbing.
 */
import { reactive } from 'vue'
import { getActivePinia } from 'pinia'
import socketClient from '@/api/socket'
import { useNotificationsStore } from '@/stores/notifications'
import type { ActionResult } from '@/types'

export type TimerMode = 'countdown' | 'stopwatch'

export interface TimerConfig {
  /** 'countdown' (needs duration_s) or 'stopwatch' (counts up). */
  mode?: string
  /** Countdown length in seconds. */
  duration_s?: number
  /** Start automatically when the face first mounts. */
  auto_start?: boolean
  /** Flash the face and toast when the countdown hits 0. */
  alarm?: boolean
  /** Optional nested action dispatched over the socket on expiry. */
  on_finish?: { type: string; config?: Record<string, any> }
  /** Legacy config key from the widget era: >0 meant a countdown. */
  timer_duration?: number
  /** Legacy `time_countdown` widget key: ISO/datetime target. */
  countdown_target?: string
  /** Button label, stashed at start so the expiry toast can name it. */
  label?: string
}

export interface TimerState {
  mode: TimerMode
  /** Configured countdown length (0 for stopwatch). */
  durationS: number
  running: boolean
  /** Seconds banked while paused — elapsed = accumulated + live segment. */
  accumulatedS: number
  /** Date.now() when the current running segment began. */
  resumedAt: number
  /** Seconds elapsed (stopwatch) — refreshed each tick for reactivity. */
  elapsedS: number
  /** Seconds remaining (countdown) — refreshed each tick. */
  remainingS: number
  /** True once start() has run — auto_start fires only on first mount. */
  hasBeenStarted: boolean
  /** Countdown reached zero; stays until the next tap re-arms it. */
  expired: boolean
  /** Alarm flash window is open (clears ~10 s after expiry). */
  flashing: boolean
  /** Set when on_finish fired so a boundary tick can't double-dispatch. */
  finishDispatched: boolean
  /** The action type that created this timer ('time_timer' | …). */
  actionType?: string
  config: Required<Pick<TimerConfig, 'auto_start' | 'alarm'>> & TimerConfig
}

const TICK_MS = 250
const FLASH_MS = 10_000

/** buttonId → timer. Module scope: survives scene switches + unmounts. */
const timers = reactive(new Map<string, TimerState>())
let intervalId: ReturnType<typeof setInterval> | null = null
const flashTimers = new Map<string, ReturnType<typeof setTimeout>>()

function liveElapsed(t: TimerState, now: number): number {
  return t.accumulatedS + (t.running ? (now - t.resumedAt) / 1000 : 0)
}

/** Normalise old + new config shapes into engine config. */
export function normalizeConfig(
  raw: TimerConfig | undefined,
  actionType?: string
): TimerConfig {
  const cfg = { ...(raw ?? {}) }

  let durationS = Number(cfg.duration_s ?? NaN)
  if (!Number.isFinite(durationS) || durationS < 0) {
    durationS = Number(cfg.timer_duration ?? 0)
  }

  // The date-countdown widget pressed programmatically becomes a duration
  // countdown ending at its target.
  if (actionType === 'time_countdown' && !(durationS > 0) && cfg.countdown_target) {
    const target = new Date(cfg.countdown_target).getTime()
    if (Number.isFinite(target)) {
      durationS = Math.max(0, Math.round((target - Date.now()) / 1000))
    }
  }

  let mode: TimerMode = cfg.mode === 'stopwatch' ? 'stopwatch' : 'countdown'
  if (cfg.mode !== 'countdown' && cfg.mode !== 'stopwatch') {
    // Legacy `timer_duration` semantics: 0 meant "stopwatch".
    mode = durationS > 0 || actionType === 'time_countdown' ? 'countdown' : 'stopwatch'
  }
  if (actionType === 'time_stopwatch') mode = 'stopwatch'

  return {
    ...cfg,
    mode,
    duration_s: Math.max(0, durationS),
    auto_start: cfg.auto_start === true,
    alarm: cfg.alarm !== false,
  }
}

function ensureInterval() {
  if (intervalId === null && timers.size > 0) {
    intervalId = setInterval(tick, TICK_MS)
  }
}

function maybeStopInterval() {
  if (intervalId !== null && timers.size === 0) {
    clearInterval(intervalId)
    intervalId = null
  }
}

function ensure(buttonId: string, config: TimerConfig, actionType?: string): TimerState {
  let t = timers.get(buttonId)
  if (!t) {
    const cfg = normalizeConfig(config, actionType)
    t = reactive<TimerState>({
      mode: cfg.mode as TimerMode,
      durationS: Number(cfg.duration_s ?? 0),
      running: false,
      accumulatedS: 0,
      resumedAt: 0,
      elapsedS: 0,
      remainingS: Number(cfg.duration_s ?? 0),
      hasBeenStarted: false,
      expired: false,
      flashing: false,
      finishDispatched: false,
      actionType,
      config: cfg as TimerState['config'],
    })
    timers.set(buttonId, t)
  }
  return t
}

function bankElapsed(t: TimerState) {
  t.accumulatedS = liveElapsed(t, Date.now())
}

function start(buttonId: string, config?: TimerConfig, actionType?: string): TimerState {
  const t = ensure(buttonId, config ?? {}, actionType)
  clearFlash(buttonId)
  if (!t.running) {
    // Reconfiguring a stopped timer adopts the new duration/mode so an
    // edited button doesn't keep running its old parameters.
    const cfg = normalizeConfig(config ?? t.config, actionType ?? t.actionType)
    t.mode = cfg.mode as TimerMode
    t.durationS = Number(cfg.duration_s ?? t.durationS)
    t.config = cfg as TimerState['config']
    t.actionType = actionType ?? t.actionType
    if (t.expired || t.accumulatedS === 0) {
      // Fresh arm or restart after expiry.
      t.accumulatedS = 0
      t.expired = false
      t.finishDispatched = false
    }
    t.resumedAt = Date.now()
    t.running = true
    t.hasBeenStarted = true
  }
  ensureInterval()
  refresh(t)
  return t
}

function pause(buttonId: string): TimerState | undefined {
  const t = timers.get(buttonId)
  if (!t?.running) return t
  bankElapsed(t)
  t.running = false
  refresh(t)
  return t
}

/** Stop and re-arm: countdown returns to its duration, stopwatch to 0. */
function reset(buttonId: string): TimerState | undefined {
  const t = timers.get(buttonId)
  if (!t) return undefined
  t.running = false
  t.accumulatedS = 0
  t.expired = false
  t.finishDispatched = false
  clearFlash(buttonId)
  refresh(t)
  return t
}

/** Drop the timer entirely — button deleted or config abandoned. */
function remove(buttonId: string) {
  clearFlash(buttonId)
  timers.delete(buttonId)
  maybeStopInterval()
}

/**
 * The press contract: tap toggles. A running timer pauses; a paused or
 * armed timer runs; an expired countdown is acknowledged and re-armed
 * (still stopped — a second tap starts the next round).
 */
function toggle(
  buttonId: string,
  config?: TimerConfig,
  label?: string,
  actionType?: string
): ActionResult {
  const t = ensure(buttonId, config ?? {}, actionType)
  if (t.expired) {
    reset(buttonId)
    return { success: true, message: `${label || 'Timer'} re-armed` }
  }
  if (t.running) {
    pause(buttonId)
    return { success: true, message: `${label || 'Timer'} paused` }
  }
  const wasPaused = t.accumulatedS > 0
  start(buttonId, label ? { ...(config ?? {}), label } : config, actionType)
  const verb = t.mode === 'stopwatch'
    ? (wasPaused ? 'Stopwatch resumed' : 'Stopwatch started')
    : (wasPaused ? 'Timer resumed' : 'Timer started')
  return { success: true, message: label ? `${label}: ${verb.toLowerCase()}` : verb }
}

/** Face mount hook: honour `auto_start` once per timer. */
function ensureMounted(buttonId: string, config: TimerConfig, actionType?: string) {
  const t = ensure(buttonId, config, actionType)
  if (!t.running && !t.hasBeenStarted && !t.expired && t.config.auto_start) {
    start(buttonId, t.config, actionType)
  }
}

function getTimer(buttonId: string): TimerState | undefined {
  return timers.get(buttonId)
}

function isRunning(buttonId: string): boolean {
  return timers.get(buttonId)?.running === true
}

function clearFlash(buttonId: string) {
  const t = timers.get(buttonId)
  if (t) t.flashing = false
  const pending = flashTimers.get(buttonId)
  if (pending) {
    clearTimeout(pending)
    flashTimers.delete(buttonId)
  }
}

function refresh(t: TimerState, now = Date.now()) {
  const elapsed = liveElapsed(t, now)
  t.elapsedS = elapsed
  t.remainingS = Math.max(0, t.durationS - elapsed)
}

function onExpiry(buttonId: string, t: TimerState) {
  t.running = false
  t.expired = true
  t.accumulatedS = t.durationS
  t.remainingS = 0

  if (t.config.alarm) {
    t.flashing = true
    flashTimers.set(buttonId, setTimeout(() => {
      const cur = timers.get(buttonId)
      if (cur) cur.flashing = false
      flashTimers.delete(buttonId)
    }, FLASH_MS))
    try {
      // Guarded: the engine must work in tests/previews with no pinia.
      if (getActivePinia()) {
        useNotificationsStore().warning(
          'Timer finished',
          `${t.config.label || 'Timer'} reached 0:00.`
        )
      }
    } catch { /* no pinia, no toast */ }
  }

  const finish = t.config.on_finish
  if (finish?.type && !t.finishDispatched) {
    t.finishDispatched = true
    // Socket dispatch — not the dashboard store — so the follow-up action
    // doesn't depend on which scene/view is mounted when time runs out.
    socketClient.executeAction({ type: finish.type, config: finish.config ?? {} })
      .catch((err: unknown) => {
        console.warn('Timer on_finish failed:', err)
      })
  }
}

function tick() {
  const now = Date.now()
  for (const [id, t] of timers) {
    if (t.running) {
      refresh(t, now)
      if (t.mode === 'countdown' && t.remainingS <= 0 && !t.expired) {
        onExpiry(id, t)
      }
    }
  }
}

/** Test/console escape hatch: clear every timer and stop the ticker. */
function _resetAll() {
  for (const id of [...timers.keys()]) remove(id)
}

export const timerButtons = {
  timers,
  normalizeConfig,
  ensure,
  ensureMounted,
  toggle,
  start,
  pause,
  reset,
  remove,
  getTimer,
  isRunning,
  _resetAll,
}

export default timerButtons
