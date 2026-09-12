import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Transient per-button state: what a button is doing right now.
 *
 * Buttons were fire-and-forget, which is fine for "volume up" and useless for
 * anything that takes time. Pressing "Ask Claude Code" looked identical to
 * pressing nothing at all until a toast appeared thirty seconds later, and a
 * GitHub widget had no way to show "3 PRs awaiting review" on its face.
 *
 * This is deliberately NOT persisted: it describes the current moment, not the
 * button's configuration. Nothing here is ever written to a profile.
 */

export type ButtonStatus = 'idle' | 'running' | 'success' | 'error'

export interface ButtonState {
  status: ButtonStatus
  /** Short text on the button face, e.g. a PR count. */
  badge?: string
  /** Replaces the secondary label while set. */
  sublabel?: string
  /** Semantic colour for the status ring: normal | warning | critical. */
  tone?: 'normal' | 'warning' | 'critical'
  /** Set on failure so the user can see why without hunting for the toast. */
  message?: string
  updatedAt: number
}

/** How long a success/error flash stays before fading back to idle. */
const FLASH_MS = 2200

export const useButtonStateStore = defineStore('buttonState', () => {
  const states = ref<Record<string, ButtonState>>({})
  const timers = new Map<string, ReturnType<typeof setTimeout>>()

  function clearTimer(buttonId: string) {
    const timer = timers.get(buttonId)
    if (timer) {
      clearTimeout(timer)
      timers.delete(buttonId)
    }
  }

  function set(buttonId: string, patch: Partial<ButtonState>) {
    if (!buttonId) return
    states.value = {
      ...states.value,
      [buttonId]: {
        ...(states.value[buttonId] ?? { status: 'idle' as ButtonStatus }),
        ...patch,
        updatedAt: Date.now()
      }
    }
  }

  function markRunning(buttonId: string) {
    clearTimer(buttonId)
    set(buttonId, { status: 'running', message: undefined })
  }

  /**
   * Record the outcome of a press.
   *
   * A widget result (one carrying a badge) stays on the face; a plain action
   * flashes success or error and then settles back to idle, so the deck does
   * not accumulate stale ticks.
   */
  function markFinished(buttonId: string, result: any) {
    if (!buttonId) return
    clearTimer(buttonId)

    const data = result?.data ?? {}
    const hasBadge = data.badge !== undefined && data.badge !== null

    set(buttonId, {
      status: result?.success ? 'success' : 'error',
      badge: hasBadge ? String(data.badge) : undefined,
      sublabel: data.sublabel,
      tone: data.status === 'warning' || data.status === 'critical'
        ? data.status
        : 'normal',
      message: result?.success ? undefined : result?.message
    })

    if (hasBadge) return // a live widget keeps its value

    timers.set(buttonId, setTimeout(() => {
      set(buttonId, { status: 'idle', message: undefined })
      timers.delete(buttonId)
    }, FLASH_MS))
  }

  function clear(buttonId: string) {
    clearTimer(buttonId)
    const next = { ...states.value }
    delete next[buttonId]
    states.value = next
  }

  function reset() {
    timers.forEach((t) => clearTimeout(t))
    timers.clear()
    states.value = {}
  }

  function get(buttonId: string): ButtonState | undefined {
    return states.value[buttonId]
  }

  const runningCount = computed(
    () => Object.values(states.value).filter((s) => s.status === 'running').length
  )

  return { states, get, set, markRunning, markFinished, clear, reset, runningCount }
})
