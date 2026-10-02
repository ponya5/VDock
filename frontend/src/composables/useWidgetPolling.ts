import { onUnmounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useButtonStateStore } from '@/stores/buttonState'
import { useNotificationsStore } from '@/stores/notifications'
import type { Button } from '@/types'

/**
 * Keep live backend widgets fresh (DL-144).
 *
 * The GitHub widgets (`gh_widget_*`: CI colour, PR counts, notifications)
 * fetch on the backend and paint their result onto the button face - but
 * nothing ever re-ran them, so a face was only as fresh as its last press.
 * This polls every widget button that is *on screen* at the interval its
 * config declares (`refresh_interval`, floored so a typo can't hammer the
 * GitHub API), silently: no toast, no success flash, just the face updating.
 *
 * Polling pauses while the tab is hidden or the deck is in edit mode, and
 * catches up as soon as it becomes visible again.
 *
 * One side effect: a CI widget flipping to a failed run raises a single
 * notification, so a red build is noticed even when you are not looking at
 * the button.
 */

const WIDGET_PREFIX = 'gh_widget_'
export const MIN_POLL_SECONDS = 30
const DEFAULT_POLL_SECONDS = 120

export function isPolledWidget(button: Button): boolean {
  return !!button.action?.type?.startsWith(WIDGET_PREFIX)
}

export function pollSecondsFor(button: Button): number {
  const configured = Number(button.action?.config?.refresh_interval)
  const seconds = Number.isFinite(configured) && configured > 0
    ? configured
    : DEFAULT_POLL_SECONDS
  return Math.max(MIN_POLL_SECONDS, seconds)
}

/**
 * True when a CI widget just went from a known not-failed state to failed.
 * The first reading after load never counts - a build that was already red
 * when VDock started is not news.
 */
export function ciJustFailed(previous: string | undefined, hadPrevious: boolean, tone: string | undefined): boolean {
  return hadPrevious && previous !== 'critical' && tone === 'critical'
}

export function useWidgetPolling() {
  const dashboardStore = useDashboardStore()
  const buttonStateStore = useButtonStateStore()
  const notifications = useNotificationsStore()

  const timers = new Map<string, ReturnType<typeof setInterval>>()
  const lastTone = new Map<string, string | undefined>()

  function canPoll(): boolean {
    if (dashboardStore.isEditMode) return false
    return typeof document === 'undefined' || document.visibilityState !== 'hidden'
  }

  async function pollOne(button: Button): Promise<void> {
    if (!canPoll()) return
    try {
      const result = await dashboardStore.executeButtonAction(button)
      if (!result) return
      buttonStateStore.markFinished(button.id, result)

      const tone = buttonStateStore.states[button.id]?.tone
      const hadPrevious = lastTone.has(button.id)
      const previous = lastTone.get(button.id)
      lastTone.set(button.id, tone)

      if (button.action?.type === 'gh_widget_ci' && ciJustFailed(previous, hadPrevious, tone)) {
        notifications.error(
          'CI failed',
          `${result.data?.repo ?? 'Repository'} - ${result.data?.sublabel ?? 'branch'}`,
          result.data?.url,
        )
      }
    } catch {
      // A failed poll leaves the previous face in place; the next tick retries.
    }
  }

  function sync(buttons: Button[]): void {
    const wanted = new Map<string, Button>()
    for (const button of buttons) {
      if (isPolledWidget(button)) {
        wanted.set(`${button.id}:${pollSecondsFor(button)}`, button)
      }
    }

    for (const [key, timer] of timers) {
      if (!wanted.has(key)) {
        clearInterval(timer)
        timers.delete(key)
      }
    }

    for (const [key, button] of wanted) {
      if (timers.has(key)) continue
      void pollOne(button)
      timers.set(key, setInterval(() => { void pollOne(button) }, pollSecondsFor(button) * 1000))
    }
  }

  function refreshAll(): void {
    for (const button of dashboardStore.currentPage?.buttons ?? []) {
      if (isPolledWidget(button)) void pollOne(button)
    }
  }

  function onVisible(): void {
    if (document.visibilityState === 'visible') refreshAll()
  }

  watch(
    () => (dashboardStore.currentPage?.buttons ?? []).map(
      (b) => [
        b.id, b.action?.type, b.action?.config?.refresh_interval,
        b.action?.config?.cwd, b.action?.config?.only_mine,
      ].join('|'),
    ).join(','),
    () => sync(dashboardStore.currentPage?.buttons ?? []),
    { immediate: true },
  )

  // Leaving edit mode catches up on anything that went stale.
  watch(() => dashboardStore.isEditMode, (editing) => { if (!editing) refreshAll() })

  document.addEventListener('visibilitychange', onVisible)

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', onVisible)
    for (const timer of timers.values()) clearInterval(timer)
    timers.clear()
  })
}
