import { reactive, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/**
 * First-run bubble tutorial. A small reactive store so DashboardView
 * (auto-start / pending launch), SettingsView ("Launch Tutorial" button)
 * and the single <TutorialTour> mounted in App.vue can drive the tour.
 *
 * Steps can declare `route` (navigate first), `activate` (click a
 * selector — e.g. open a sub-tab) and `advanceOnPath` (auto-advance when
 * the app lands on that path — used so loading a profile moves the tour
 * from the Profiles screen onto the dashboard).
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
  /** Route the step needs before measuring ('/' dashboard, '/settings'). */
  route?: string
  /** Selector clicked before measuring — e.g. to open a settings sub-tab. */
  activate?: string
  /** Auto-advance when the app navigates to this path (e.g. user loads a
      profile and lands on '/'). */
  advanceOnPath?: string
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    route: '/profiles',
    title: 'Welcome to VDock',
    text: 'A quick tour of the main features — tap Next to walk through, or Skip to explore on your own.',
  },
  {
    route: '/profiles',
    target: '.profiles-grid',
    title: 'Your First Profile',
    text: 'Profiles hold your scenes and buttons. Tap ▶ on "My VDock" to load the starter profile — or "+ New Profile" to create your own. The tour continues on your dashboard.',
    placement: 'bottom',
    advanceOnPath: '/',
  },
  {
    target: '.enhanced-scene-nav',
    title: 'Scenes',
    text: 'Each scene is a page of buttons for a context — media, Claude Code, Cursor, websites. Tap a pill to switch, or swipe up/down on the deck.',
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
    text: 'Everything is configured here — backgrounds, widgets, touch mode, integrations. Let\'s take a look inside.',
    placement: 'bottom',
  },
  {
    route: '/settings',
    target: '.settings-nav-rail',
    title: 'Settings Sections',
    text: 'Appearance, Templates, Server, Integrations, Logs, About — each rail item opens a group of related options.',
    placement: 'right',
  },
  {
    route: '/settings',
    target: '.settings-search',
    title: 'Find a Setting',
    text: 'Not sure where something lives? Type it — "screensaver", "touch", "port" — and jump straight to the right card.',
    placement: 'bottom',
  },
  {
    route: '/settings',
    target: '[data-tour="appearance-tabs"]',
    title: 'Appearance Tabs',
    text: 'Button Behaviour, Layout & Behavior, Background and Screen Saver — the deck\'s look and feel is tuned across these tabs.',
    placement: 'bottom',
  },
  {
    route: '/settings',
    activate: '[data-tour="subtab-screensaver"]',
    target: '[data-tour="screensaver-picker"]',
    title: 'Screensaver Widgets',
    text: 'Free widgets — weather, news, sports, markets, world clock. Toggle them on, then tap a card below to configure it.',
    placement: 'bottom',
  },
  {
    route: '/settings',
    activate: '[data-tour="nav-about"]',
    target: '[data-tour="about-help"]',
    title: 'Help & Tutorial',
    text: 'Re-open the Help & Guide or re-run this tour anytime from the About section.',
    placement: 'left',
  },
  {
    route: '/',
    title: 'You\'re all set',
    text: 'Leave the deck idle and the screensaver kicks in with weather, news, and market widgets. Enjoy your deck!',
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
