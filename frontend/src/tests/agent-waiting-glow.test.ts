// DL-080: waiting-agent edge glow + idle-session highlight in the bar.
// Session composable/targets are stubbed so each test pins the state.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { computed, ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { AgentStateName, AppProfileDto } from '@/api/appProfiles'
import type { Scene } from '@/types'
import AgentWaitingGlow from '@/components/AgentWaitingGlow.vue'
import AgentActionBar from '@/components/AgentActionBar.vue'
import GlassPillSceneSelector from '@/components/GlassPillSceneSelector.vue'
import { SETTINGS_DEFAULTS } from '@/stores/settings'

const sessionState = {
  currentState: ref<AgentStateName>('ready'),
  isAgentPossiblyRunning: ref(true),
}
const settingsState = {
  agentWaitingGlowEnabled: ref<boolean | undefined>(true),
  agentWaitingGlowStyle: ref<'flash' | 'pulse' | 'orbit'>('flash'),
  animationsEnabled: ref(true),
}
const dashboardState = {
  isEditMode: ref(false),
  profileScenes: ref<Scene[]>([]),
}
const effectiveSession = ref<{ state: string | null } | null>(null)
const sessionRowsState = ref<Array<{ pid: number; label: string; state: string | null }>>([])

vi.mock('@/composables/useAgentSession', () => ({
  useAgentSession: () => ({
    profile: computed(() => ({
      id: 'claude-code',
      label: 'Claude Code',
      status_source: 'claude',
      commands: [{ id: 'cc_submit', label: 'Submit', icon: 'paper-plane', description: '', session_marker: 'claude' }],
      state_actions: { ready: [{ id: 'cc_submit' }], unknown: [{ id: 'cc_submit' }] },
    })),
    stateEntry: computed(() => undefined),
    currentState: computed(() => sessionState.currentState.value),
    stateLabel: computed(() => `label-${sessionState.currentState.value}`),
    isAgentDetected: computed(() => true),
    isAgentPossiblyRunning: computed(() => sessionState.isAgentPossiblyRunning.value),
    visibleActions: computed(() => [
      { id: 'cc_submit', label: 'Submit', icon: 'paper-plane', description: '', isPrimary: true },
    ]),
    runningActionId: ref(null),
    runAction: vi.fn(),
    sendPrompt: vi.fn(),
  }),
  trackAgentSurfaceVisibility: vi.fn(),
}))

vi.mock('@/composables/useAgentTargets', () => ({
  useAgentTargets: () => ({
    sessions: computed(() => sessionRowsState.value),
    sessionRows: computed(() => sessionRowsState.value),
    pinnedPid: ref(null),
    resolvedPid: ref<number | null>(null),
    effectiveSession: computed(() => effectiveSession.value),
    targetLabel: computed(() => 'Auto'),
    refresh: vi.fn(),
    setTarget: vi.fn(),
    identify: vi.fn(),
  }),
  profileSessionMarker: (p: AppProfileDto | null | undefined) =>
    p?.commands?.find(c => c.session_marker)?.session_marker ?? null,
}))

vi.mock('@/stores/settings', async importOriginal => {
  const mod = await importOriginal<typeof import('@/stores/settings')>()
  return {
    ...mod,
    useSettingsStore: () => ({
      agentWaitingGlowEnabled: settingsState.agentWaitingGlowEnabled.value,
      agentWaitingGlowStyle: settingsState.agentWaitingGlowStyle.value,
      animationsEnabled: settingsState.animationsEnabled.value,
    }),
  }
})

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    isEditMode: dashboardState.isEditMode.value,
    currentProfile: { scenes: dashboardState.profileScenes.value },
    executeAction: vi.fn(async () => ({ success: true })),
  }),
}))

vi.mock('@/stores/notifications', () => ({
  useNotificationsStore: () => ({ error: vi.fn() }),
}))

// DL-080 follow-up — the scene rail asks a dedicated service whether each
// scene's agent sits idle; the sets below control the answer per test.
// `dismissedSources` simulates the snooze path end-to-end through the seam.
const waitingSceneIds = ref<Set<string>>(new Set())
const dismissedSources = ref<Set<string>>(new Set())
const dismissCalls: string[] = []

const fakeWaiting = (scene: Scene) =>
  waitingSceneIds.value.has(scene.id) && !dismissedSources.value.has('claude')
    ? {
        profile: { id: 'claude-code', label: 'Claude Code', status_source: 'claude' },
        entry: { source: 'claude', state: 'ready', ts: 1 },
      }
    : null

vi.mock('@/services/agentWaiting', () => ({
  sceneAgentIsWaiting: (scene: Scene) => fakeWaiting(scene) !== null,
  sceneWaitingAgent: (scene: Scene) => fakeWaiting(scene),
  dismissAgentWaiting: (source: string) => {
    dismissCalls.push(source)
    dismissedSources.value.add(source)
  },
  isAgentWaitingDismissed: (source: string) => dismissedSources.value.has(source),
  sceneSnoozedAgent: (scene: Scene) =>
    waitingSceneIds.value.has(scene.id) && dismissedSources.value.has('claude')
      ? {
          profile: { id: 'claude-code', label: 'Claude Code', status_source: 'claude' },
          entry: { source: 'claude', state: 'ready', ts: 1 },
        }
      : null,
  resumeAgentWaiting: (source: string) => { dismissedSources.value.delete(source) },
  agentSnoozeRemainingMs: () => 150_000,
}))

vi.mock('@/services/agentState', async importOriginal => {
  const mod = await importOriginal<typeof import('@/services/agentState')>()
  return {
    ...mod,
    initAgentState: vi.fn(),
    agentStateEntry: () => undefined,
    agentStateFor: () => 'unknown' as const,
  }
})

vi.mock('@/services/appDetection', () => ({
  startAppDetection: vi.fn(),
  stopAppDetection: vi.fn(),
  sceneAppIsLive: () => false,
  loadProfileMaps: vi.fn(async () => {}),
  sceneAppProfile: () => null,
  sceneLogo: () => null,
}))

vi.mock('@/composables/useAppIntegrations', () => ({
  useAppIntegrations: () => ref([]),
}))

vi.mock('@/utils/haptics', () => ({ vibrate: vi.fn() }))

const CLAUDE_SCENE = { id: 's1', name: 'Claude Code', pages: [] } as unknown as Scene

beforeEach(() => {
  sessionState.currentState.value = 'ready'
  sessionState.isAgentPossiblyRunning.value = true
  settingsState.agentWaitingGlowEnabled.value = true
  settingsState.agentWaitingGlowStyle.value = 'flash'
  settingsState.animationsEnabled.value = true
  dashboardState.isEditMode.value = false
  dashboardState.profileScenes.value = [CLAUDE_SCENE]
  effectiveSession.value = null
  sessionRowsState.value = []
  waitingSceneIds.value = new Set(['s1'])
  dismissedSources.value = new Set()
  dismissCalls.length = 0
})

function mountGlow() {
  return mount(AgentWaitingGlow, {
    global: { stubs: { teleport: true, FontAwesomeIcon: true } },
  })
}

describe('AgentWaitingGlow', () => {
  it('flashes the whole frame while any scene in the profile waits', () => {
    const wrapper = mountGlow()
    const glow = wrapper.find('.agent-waiting-glow')
    expect(glow.exists()).toBe(true)
    expect(glow.classes()).toContain('style-flash')
    expect(glow.attributes('aria-label')).toContain('Claude Code')
  })

  it('alerts from any scene — the waiting scene does not have to be current', () => {
    // The profile has a non-agent scene too; the frame must fire on the
    // waiting one regardless of which scene the user is looking at.
    dashboardState.profileScenes.value = [
      { id: 's-media', name: 'Media', pages: [] },
      { id: 's1', name: 'Claude Code', pages: [] },
    ] as unknown as Scene[]
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(true)
  })

  it('stays dark when no scene has a waiting agent', () => {
    waitingSceneIds.value = new Set()
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
  })

  it('hides when the setting is off and shows when unset (default on)', () => {
    settingsState.agentWaitingGlowEnabled.value = false
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
    settingsState.agentWaitingGlowEnabled.value = undefined
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(true)
  })

  it('hides in edit mode', () => {
    dashboardState.isEditMode.value = true
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
  })

  it('drops the animation when animations are disabled', () => {
    settingsState.animationsEnabled.value = false
    expect(mountGlow().find('.agent-waiting-glow').classes()).toContain('no-anim')
  })

  it('defaults the setting to enabled and the style to flash', () => {
    expect(SETTINGS_DEFAULTS.agentWaitingGlowEnabled).toBe(true)
    expect(SETTINGS_DEFAULTS.agentWaitingGlowStyle).toBe('flash')
  })

  it('switches frame styles with the configured style', () => {
    settingsState.agentWaitingGlowStyle.value = 'pulse'
    const wrapper = mountGlow()
    const glow = wrapper.find('.agent-waiting-glow')
    expect(glow.classes()).toContain('style-pulse')
    expect(wrapper.find('.agent-waiting-orbit').exists()).toBe(false)
  })

  // --- DL-080 follow-up #2: snooze ----------------------------------------

  it('after snoozing, shows a Resume chip with time left; Resume re-arms the alert', async () => {
    const wrapper = mountGlow()
    await wrapper.find('.snooze-btn').trigger('click')

    const chip = wrapper.find('[data-testid="snoozed-chip"]')
    expect(chip.exists()).toBe(true)
    expect(chip.text()).toContain('Claude Code snoozed')
    expect(chip.text()).toContain('3m left') // 150 s rounds up to 3m
    expect(wrapper.find('.agent-waiting-glow').exists()).toBe(false)

    await wrapper.find('[data-testid="resume-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="snoozed-chip"]').exists()).toBe(false)
    expect(wrapper.find('.agent-waiting-glow').exists()).toBe(true)
  })

  it('offers a snooze chip naming the waiting agent', () => {
    const chip = mountGlow().find('.agent-waiting-snooze')
    expect(chip.exists()).toBe(true)
    expect(chip.text()).toContain('Claude Code is waiting for input')
  })

  it('snoozing dismisses the alert for this waiting episode', async () => {
    const wrapper = mountGlow()
    await wrapper.find('.snooze-btn').trigger('click')
    expect(dismissCalls).toEqual(['claude'])
    expect(wrapper.find('.agent-waiting-glow').exists()).toBe(false)
    expect(wrapper.find('.agent-waiting-snooze').exists()).toBe(false)
  })

  // --- Orbit style ---------------------------------------------------------

  it('runs the comet frame only for the orbit style', () => {
    settingsState.agentWaitingGlowStyle.value = 'orbit'
    expect(mountGlow().find('.agent-waiting-orbit').exists()).toBe(true)
  })

  it('drops the comet when animations are disabled but keeps the static glow', () => {
    settingsState.agentWaitingGlowStyle.value = 'orbit'
    settingsState.animationsEnabled.value = false
    const wrapper = mountGlow()
    expect(wrapper.find('.agent-waiting-glow').exists()).toBe(true)
    expect(wrapper.find('.agent-waiting-orbit').exists()).toBe(false)
  })

  it('animates a registered angle through a conic-gradient ring', () => {
    const source = readFileSync(resolve(__dirname, '../components/AgentWaitingGlow.vue'), 'utf-8')
    expect(source).toContain("@property --agent-orbit")
    expect(source).toContain("syntax: '<angle>'")
    expect(source).toContain('conic-gradient')
    expect(source).toContain('@keyframes agent-waiting-orbit')
    expect(source).toContain('mask-composite')
    expect(source).toContain('linear infinite')
  })

  it('flashes the whole frame with a heartbeat double-blink', () => {
    const source = readFileSync(resolve(__dirname, '../components/AgentWaitingGlow.vue'), 'utf-8')
    expect(source).toContain('@keyframes agent-waiting-flash')
    expect(source).toContain('style-flash')
    expect(source).toContain('style-pulse')
    expect(source).toContain('agent-waiting-snooze')
  })
})

describe('AgentActionBar waiting highlight', () => {
  function mountBar() {
    return mount(AgentActionBar, {
      props: { scene: CLAUDE_SCENE },
      global: { stubs: { teleport: true, FontAwesomeIcon: true } },
    })
  }

  it('pulses the target chip while the effective session is idle', () => {
    effectiveSession.value = { state: 'ready', prompted: true }
    expect(mountBar().find('.agent-target-chip').classes()).toContain('waiting')
  })

  it('leaves the chip alone for working sessions and when the setting is off', () => {
    effectiveSession.value = { state: 'working' }
    expect(mountBar().find('.agent-target-chip').classes()).not.toContain('waiting')
    effectiveSession.value = { state: 'ready', prompted: true }
    settingsState.agentWaitingGlowEnabled.value = false
    expect(mountBar().find('.agent-target-chip').classes()).not.toContain('waiting')
  })

  it('leaves a just-launched (never prompted) session unflagged (DL-105)', () => {
    effectiveSession.value = { state: 'ready', prompted: false }
    const chip = mountBar().find('.agent-target-chip')
    expect(chip.classes()).not.toContain('waiting')
    expect(chip.find('.chip-tag').exists()).toBe(false)
  })

  it('flags idle rows in the session picker', async () => {
    sessionRowsState.value = [
      { pid: 100, label: 'projA', state: 'working' },
      { pid: 200, label: 'projB', state: 'ready', prompted: true },
      { pid: 300, label: 'projC', state: 'ready', prompted: false },
    ]
    const wrapper = mountBar()
    await wrapper.find('.agent-target-chip').trigger('click')
    await flushPromises()
    // Row 0 is the "Auto" pseudo-row; sessions follow.
    const rows = wrapper.findAll('.agent-target-row')
    expect(rows[1].classes()).not.toContain('waiting')
    expect(rows[2].classes()).toContain('waiting')
    expect(rows[2].text()).toContain('waiting')
    // DL-105: a ready-but-never-prompted session does not flag.
    expect(rows[3].classes()).not.toContain('waiting')
  })

  // --- DL-080 follow-up: chip tag + other-session nudge --------------------

  it('spells out "waiting" on the chip when the target session is idle', () => {
    effectiveSession.value = { state: 'ready', prompted: true }
    const chip = mountBar().find('.agent-target-chip')
    expect(chip.find('.chip-tag').exists()).toBe(true)
    expect(chip.find('.chip-tag').text()).toBe('waiting')
    expect(chip.find('.chip-waiting-nudge').exists()).toBe(false)
  })

  it('nudges the chip when a session other than the target sits idle', () => {
    effectiveSession.value = { state: 'working', pid: 100 }
    sessionRowsState.value = [
      { pid: 100, label: 'projA', state: 'working' },
      { pid: 200, label: 'projB', state: 'ready', prompted: true },
    ]
    const chip = mountBar().find('.agent-target-chip')
    expect(chip.classes()).not.toContain('waiting')
    expect(chip.find('.chip-waiting-nudge').exists()).toBe(true)
  })
})

// --- DL-080 follow-up: scene-level guidance ----------------------------------
// Off the agent scene, the rail rings the pill whose agent sits idle.

describe('GlassPillSceneSelector waiting highlight', () => {
  const SCENES = [
    { id: 's-media', name: 'Media', pages: [] },
    { id: 's-claude', name: 'Claude Code', pages: [] },
  ] as unknown as Scene[]

  function mountSelector(isEditMode = false) {
    return mount(GlassPillSceneSelector, {
      props: { scenes: SCENES, currentSceneIndex: 0, isEditMode },
      global: { stubs: { FontAwesomeIcon: true } },
    })
  }

  it('rings the scene pill whose agent is idle', () => {
    waitingSceneIds.value = new Set(['s-claude'])
    const segments = mountSelector().findAll('.segment')
    expect(segments[0].classes()).not.toContain('agent-waiting')
    expect(segments[1].classes()).toContain('agent-waiting')
    expect(segments[1].find('.app-live-dot').classes()).toContain('agent-waiting-dot')
  })

  it('shows the waiting dot even when the app-running dot is off', () => {
    // app scanning off → sceneAppIsLive false; a `ready` hook state still
    // proves the session is alive, so the waiting cue must not depend on it.
    waitingSceneIds.value = new Set(['s-claude'])
    const segments = mountSelector().findAll('.segment')
    expect(segments[1].find('.app-live-dot').exists()).toBe(true)
    expect(segments[0].find('.app-live-dot').exists()).toBe(false)
  })

  it('stays quiet when the setting is off and in edit mode', () => {
    waitingSceneIds.value = new Set(['s-claude'])
    settingsState.agentWaitingGlowEnabled.value = false
    expect(mountSelector().findAll('.segment')[1].classes()).not.toContain('agent-waiting')
    settingsState.agentWaitingGlowEnabled.value = true
    expect(mountSelector(true).findAll('.segment')[1].classes()).not.toContain('agent-waiting')
  })

  it('leaves non-agent scenes alone', () => {
    waitingSceneIds.value = new Set()
    expect(mountSelector().find('.segment.agent-waiting').exists()).toBe(false)
  })
})

describe('MobileDeckChrome + MobileAgentConsole waiting wiring', () => {
  it('flags the waiting scene segment and live dot on the mobile rail', () => {
    const chrome = readFileSync(resolve(__dirname, '../components/MobileDeckChrome.vue'), 'utf-8')
    expect(chrome).toContain("'agent-waiting': sceneWaiting(scene)")
    expect(chrome).toContain('sceneAgentIsWaiting')
    expect(chrome).toContain('mc-seg.agent-waiting')
    expect(chrome).toContain('initAgentState()')
    expect(chrome).toContain('loadProfileMaps()')
  })

  it('rings idle session rows in the shared session picker', () => {
    // The waiting ring moved with the picker into AgentSessionPicker.vue
    // (DL-071 follow-up) — AgentActionBar and MobileAgentConsole share it.
    const picker = readFileSync(resolve(__dirname, '../components/AgentSessionPicker.vue'), 'utf-8')
    expect(picker).toContain("waiting: waitingGlowOn && s.state === 'ready' && s.prompted === true")
    expect(picker).toContain('.agent-target-row.waiting')
  })
})

describe('sceneAgentIsWaiting service', () => {
  it('reads the hook state through the scene profile', async () => {
    // The file-level mocks above stub these three services for the component
    // tests — undo that so this test exercises the real resolution chain.
    vi.resetModules()
    vi.doUnmock('@/services/agentWaiting')
    vi.doUnmock('@/services/agentState')
    vi.doUnmock('@/services/appDetection')
    vi.doMock('@/api/client', () => ({
      default: {
        get: vi.fn(async (url: string) => {
          if (url === '/app-profiles') {
            return {
              data: {
                profiles: [{
                  id: 'claude-code',
                  label: 'Claude Code',
                  exes: ['windowsterminal.exe'],
                  status_source: 'claude',
                  commands: [{ id: 'cc_prompt' }],
                  action_types: ['claude_prompt'],
                }],
              },
            }
          }
          if (url === '/agent-events/states') {
            return { data: { states: { claude: { source: 'claude', state: 'ready', message: '', cwd: '', project: 'VDock2', prompted: true, ts: 1 } } } }
          }
          return { data: {} }
        }),
      },
    }))
    vi.doMock('@/api/socket', () => ({ default: { on: vi.fn(), off: vi.fn() } }))

    const { initAgentState } = await import('@/services/agentState')
    const { loadProfileMaps } = await import('@/services/appDetection')
    const {
      sceneAgentIsWaiting,
      dismissAgentWaiting,
      isAgentWaitingDismissed,
    } = await import('@/services/agentWaiting')

    initAgentState()
    await loadProfileMaps()
    await new Promise(r => setTimeout(r, 0))

    const claudeScene = { id: 's1', appId: 'claude-code', pages: [] }
    const mediaScene = { id: 's2', name: 'Media', pages: [] }
    expect(sceneAgentIsWaiting(claudeScene as never)).toBe(true)
    expect(sceneAgentIsWaiting(mediaScene as never)).toBe(false)

    // --- snooze: silences this episode, re-arms on the next fresh event ---
    dismissAgentWaiting('claude')
    expect(sceneAgentIsWaiting(claudeScene as never)).toBe(false)
    expect(isAgentWaitingDismissed('claude')).toBe(true)

    // A new hook event stamps a fresh ts — the dismissal keyed on ts 1 no
    // longer matches, so the alert re-arms by itself.
    const socket = (await import('@/api/socket')).default as unknown as {
      on: ReturnType<typeof vi.fn>
    }
    const handler = socket.on.mock.calls.find(c => c[0] === 'agent_state')![1] as (
      payload: { states: Record<string, unknown> }
    ) => void
    handler({
      states: {
        claude: { source: 'claude', session_id: 'default', state: 'ready', message: '', cwd: '', project: 'VDock2', prompted: true, ts: 2 },
      },
    })
    expect(sceneAgentIsWaiting(claudeScene as never)).toBe(true)
    expect(isAgentWaitingDismissed('claude')).toBe(false)
  })
})
