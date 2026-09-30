import { reactive, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/**
 * First-run bubble tutorial. A small reactive store so DashboardView
 * (auto-start / pending launch), SettingsView ("Launch Tutorial" button)
 * and the single <TutorialTour> mounted in App.vue can drive the tour.
 *
 * Steps can declare `route` (navigate first) and `activate` (click a
 * selector — e.g. open a sub-tab). Steps NEVER auto-advance: only the
 * user's Next/Back/Skip moves the tour — a step whose target is absent
 * renders as a centered card instead of skipping itself.
 *
 * Completion lives in the server-persisted `tutorialCompleted` setting —
 * a real boolean shared by every window — not localStorage. The legacy
 * `vdock_tutorial_done` key is migrated on first read so existing users
 * don't get re-toured.
 *  - vdock_tutorial_pending — set by "Launch Tutorial" in Settings; consumed
 *                           by DashboardView on mount, so the tour always
 *                           starts against the live dashboard DOM.
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
  /** Route the step needs before measuring ('/' dashboard, '/settings').
      Always set this when the step's target lives on a specific view —
      otherwise a Next/Back click (or the user navigating away mid-tour)
      leaves the bubble floating over the wrong screen. */
  route?: string
  /** Selector clicked before measuring — e.g. to open a settings sub-tab. */
  activate?: string
  /** Target may legitimately be absent (conditional UI like the agent
      bar, a hidden header, or the docked sidebar). When it is, the step
      shows as a centered card — it never skips itself. */
  optional?: boolean
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    route: '/profiles',
    title: 'Welcome to VDock',
    text: 'A quick tour — tap Next to walk through the essentials, or Skip to explore on your own.',
  },
  {
    route: '/profiles',
    target: '.profiles-grid',
    title: 'Pick a Profile',
    text: 'A profile is a full deck: scenes, pages, buttons. Tap ▶ on "My VDock" to load the starter — or "+ New Profile" to start blank and customize later.',
    placement: 'bottom',
  },
  {
    route: '/',
    // Desktop scene pills; the mobile/touch chrome swaps in a rail.
    target: '.enhanced-scene-nav, .mc-scene-rail',
    title: 'Scenes & Pages',
    text: 'Each scene is a page of buttons for a context — media, Claude Code, websites. Tap a pill to switch — or swipe right/left anywhere on the dashboard to move between scenes.',
    placement: 'bottom',
    optional: true,
  },
  {
    route: '/',
    target: '.deck-grid',
    title: 'Your Deck',
    text: 'Tap a button to run its action — media controls, hotkeys, websites, agent commands. Scenes with more buttons get extra pages — flip them with the dots or ‹ › below.',
    placement: 'top',
    optional: true,
  },
  {
    route: '/',
    // Phones render the deck read-only — no edit affordance there.
    target: '[aria-label="Toggle Edit Mode"]',
    title: 'Edit Mode',
    text: 'Tap the pencil to customize: add buttons to empty slots, drag to rearrange, resize, and pick actions from the sidebar.',
    placement: 'bottom',
    optional: true,
  },
  {
    route: '/',
    target: '.agent-action-bar',
    title: 'Agent Sessions',
    text: 'Running Claude Code or other agents? This bar shows their state — and with multiple sessions open, the chip lets you pick exactly which terminal your button taps control.',
    placement: 'top',
    optional: true,
  },
  {
    route: '/settings',
    target: '.nav',
    title: 'Settings',
    text: 'Everything is configured from this rail — appearance & key design, templates, server, integrations, connect a device, logs.',
    placement: 'right',
  },
  {
    route: '/settings',
    target: '.nav-search',
    title: 'Find a Setting',
    text: 'Not sure where something lives? Type it — "screensaver", "touch", "port" — and jump straight to the right card.',
    placement: 'right',
  },
  {
    route: '/',
    title: 'You\'re all set',
    text: 'Leave the deck idle and the screensaver kicks in with weather, news, and market widgets. The full Guide lives in Settings → Guide — re-run this tour anytime from Settings → About.',
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
    // Persisted server-side boolean + legacy localStorage marker.
    useSettingsStore().tutorialCompleted = true
    localStorage.setItem(TUTORIAL_DONE_KEY, '1')
  }

  /** Launch the tour regardless of the done flag (Settings → Launch Tutorial). */
  function requestLaunch() {
    localStorage.setItem(TUTORIAL_PENDING_KEY, '1')
  }

  /** Called by DashboardView on mount — starts a pending or first-run tour. */
  function consumePendingOrFirstRun() {
    // The tour navigates between dashboard and settings — when it returns
    // to '/', DashboardView remounts and would otherwise restart at step 0.
    if (state.active) return false
    if (localStorage.getItem(TUTORIAL_PENDING_KEY) === '1') {
      localStorage.removeItem(TUTORIAL_PENDING_KEY)
      start()
      return true
    }
    // Migrate the pre-settings flag so existing users don't get re-toured.
    if (localStorage.getItem(TUTORIAL_DONE_KEY) === '1'
        && !useSettingsStore().tutorialCompleted) {
      useSettingsStore().tutorialCompleted = true
    }
    if (!useSettingsStore().tutorialCompleted) {
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
