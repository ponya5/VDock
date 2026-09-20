import { reactive, computed } from 'vue'

/**
 * First-run bubble tutorial. A small reactive store so both DashboardView
 * (auto-start / pending launch) and SettingsView ("Launch Tutorial" button)
 * can drive the single <TutorialTour> mounted in DashboardView.
 *
 * Flags:
 *  - vdock_tutorial_done    — set when the tour completes or is skipped;
 *                           suppresses the first-run auto-start.
 *  - vdock_tutorial_pending — set by "Launch Tutorial" in Settings; consumed
 *                           by DashboardView on mount, so the tour always
 *                           runs against the live dashboard DOM.
 */

export const TUTORIAL_DONE_KEY = 'vdock_tutorial_done'
export const TUTORIAL_PENDING_KEY = 'vdock_tutorial_pending'

export interface TutorialStep {
  /** CSS selector to spotlight; null/undefined renders a centered card. */
  target?: string
  title: string
  text: string
  /** Preferred bubble side relative to the target. */
  placement?: 'top' | 'bottom' | 'left' | 'right'
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    title: 'Welcome to VDock',
    text: 'A quick tour of the main features — tap Next to walk through, or Skip to explore on your own.',
  },
  {
    target: '.enhanced-scene-nav',
    title: 'Scenes',
    text: 'Each scene is a page of buttons for a context — media, AI, tools. Tap a pill to switch, or swipe up/down on the deck.',
    placement: 'bottom',
  },
  {
    target: '.deck-grid',
    title: 'Your Deck',
    text: 'Tap a button to run its action — media controls, hotkeys, websites, system commands. Swipe left/right for more pages.',
    placement: 'top',
  },
  {
    target: '[aria-label="Toggle Edit Mode"]',
    title: 'Edit Mode',
    text: 'Tap the pencil to customize: add buttons to empty slots, drag to rearrange, resize, and pick actions from the sidebar.',
    placement: 'bottom',
  },
  {
    target: '.docked-sidebar',
    title: 'Docked Sidebar',
    text: 'Buttons here stay visible on every scene — perfect for volume, weather, or a clock. Toggle it in Settings → Appearance.',
    placement: 'right',
  },
  {
    target: '[aria-label="Settings"]',
    title: 'Settings',
    text: 'Backgrounds, screensaver widgets, touch mode, app integrations, templates — everything is configured here.',
    placement: 'bottom',
  },
  {
    title: 'You\'re all set',
    text: 'Leave the deck idle and the screensaver kicks in with weather, news, and market widgets. Re-run this tour anytime from Settings → About.',
  },
]

interface TutorialState {
  active: boolean
  stepIndex: number
}

const state = reactive<TutorialState>({ active: false, stepIndex: 0 })

export function useTutorial() {
  const currentStep = computed(() => TUTORIAL_STEPS[state.stepIndex])
  const isFirst = computed(() => state.stepIndex === 0)
  const isLast = computed(() => state.stepIndex === TUTORIAL_STEPS.length - 1)

  function start() {
    state.stepIndex = 0
    state.active = true
  }

  function next() {
    if (isLast.value) finish()
    else state.stepIndex++
  }

  function back() {
    if (!isFirst.value) state.stepIndex--
  }

  function finish() {
    state.active = false
    state.stepIndex = 0
    localStorage.setItem(TUTORIAL_DONE_KEY, '1')
  }

  /** Launch the tour regardless of the done flag (Settings → Launch Tutorial). */
  function requestLaunch() {
    localStorage.setItem(TUTORIAL_PENDING_KEY, '1')
  }

  /** Called by DashboardView on mount — starts a pending or first-run tour. */
  function consumePendingOrFirstRun() {
    if (localStorage.getItem(TUTORIAL_PENDING_KEY) === '1') {
      localStorage.removeItem(TUTORIAL_PENDING_KEY)
      start()
      return true
    }
    if (!localStorage.getItem(TUTORIAL_DONE_KEY)) {
      start()
      return true
    }
    return false
  }

  return {
    state,
    currentStep,
    isFirst,
    isLast,
    start,
    next,
    back,
    finish,
    requestLaunch,
    consumePendingOrFirstRun,
  }
}
