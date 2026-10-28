import { reactive, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import { TUTORIAL_APPS, findTemplate } from '@/data/tutorialApps'
import { addTemplateScene } from '@/composables/useTemplateScenes'
import { ensureSceneForApp } from '@/composables/useAppShortcutScenes'

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
  /** `apps` renders the app picker inside the card. */
  kind?: 'apps'
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
  /** Target lives inside DeckHeader — reveal it (and pin the autohide
      countdown) before measuring; restored when the tour leaves '/'. */
  needsHeader?: boolean
  /** Target is the agent action bar — it only mounts on an agent-backed
      scene, so switch to one first; restored when the tour leaves '/'. */
  needsAgentScene?: boolean
  /** Target may legitimately be absent (conditional UI like the agent
      bar, a hidden header, or the docked sidebar). When it is, the step
      shows as a centered card — it never skips itself. */
  optional?: boolean
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    route: '/',
    title: 'Welcome to VDock',
    text: 'Your computer\'s controls on a deck you can tap — on this screen or on your phone. A one-minute tour; skip it any time.',
  },
  {
    route: '/',
    kind: 'apps',
    title: 'What do you use?',
    text: 'Tick your apps and each gets a ready-made scene of buttons. Media controls are already included. You can add or remove scenes later.',
  },
  {
    route: '/',
    // Desktop scene pills; the mobile/touch chrome swaps in a rail. Both
    // live in the header chrome — reveal it first (autohide default-off).
    needsHeader: true,
    target: '.enhanced-scene-nav, .mc-scene-rail',
    title: 'Scenes',
    text: 'A scene is a page of buttons for one job — media, Claude Code, a website. Tap a pill to switch, or swipe left and right anywhere on the deck.',
    placement: 'bottom',
    optional: true,
  },
  {
    route: '/',
    target: '.deck-grid .deck-button',
    title: 'Your deck',
    text: 'Tap a button to run it. To change the layout, open the header and tap the pencil: add, drag and resize buttons.',
    placement: 'bottom',
    optional: true,
  },
  {
    route: '/settings',
    target: '[data-tour="nav-integration"]',
    title: 'Agents & automation',
    text: 'Get an alert when Claude, Cursor or Codex needs you, let scenes follow the app you are using, and set rules that run on their own.',
    placement: 'right',
    optional: true,
  },
  {
    route: '/settings',
    activate: '[data-tour="nav-server"]',
    target: '[data-tour="allow-lan"]',
    title: 'Use your phone or tablet',
    text: 'Phone access is off until you turn it on, so no other device can reach your deck. Flip "Allow phone & tablet access" here. If VDock asks for a restart, restart it once — then the QR code under Security is ready to scan with your phone\'s camera.',
    placement: 'bottom',
  },
  {
    route: '/',
    title: 'You\'re all set',
    text: 'The Guide in the Settings sidebar covers everything else, and you can replay this tour from Settings → About.',
  },
]

interface TutorialState {
  active: boolean
  stepIndex: number
  /** TUTORIAL_APPS ids ticked in the "What do you use?" step. */
  picked: string[]
}

const state = reactive<TutorialState>({ active: false, stepIndex: 0, picked: [] })

/** Adds a scene for each ticked app that has none yet; returns how many were added. */
async function applyPickedApps(): Promise<number> {
  const profile = useDashboardStore().currentProfile
  const picked = state.picked.splice(0)
  if (!profile || !picked.length) return 0
  let added = 0
  for (const id of picked) {
    const app = TUTORIAL_APPS.find(a => a.id === id)
    if (!app) continue
    const exists = profile.scenes.some(sc => sc.appId === app.id || sc.triggeredByApp === app.source.replace('starter:', ''))
    if (exists) continue
    if (app.source.startsWith('starter:')) {
      if (await ensureSceneForApp(app.source.slice(8), app.label)) added++
    } else {
      const template = findTemplate(app.source)
      if (template && addTemplateScene(template)) added++
    }
  }
  return added
}

export function useTutorial() {
  const currentStep = computed(() => TUTORIAL_STEPS[state.stepIndex])
  const isFirst = computed(() => state.stepIndex === 0)
  const isLast = computed(() => state.stepIndex === TUTORIAL_STEPS.length - 1)

  function start() {
    state.stepIndex = 0
    state.active = true
  }

  function next() {
    // Leaving the apps step adds the ticked apps' scenes.
    if (currentStep.value?.kind === 'apps') void applyPickedApps()
    if (isLast.value) finish()
    else state.stepIndex++
  }

  function togglePicked(id: string) {
    const i = state.picked.indexOf(id)
    if (i >= 0) state.picked.splice(i, 1)
    else state.picked.push(id)
  }

  function back() {
    if (!isFirst.value) state.stepIndex--
  }

  function finish() {
    state.active = false
    state.stepIndex = 0
    state.picked = [] // skipping adds nothing
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
    togglePicked,
    back,
    finish,
    requestLaunch,
    consumePendingOrFirstRun,
  }
}
