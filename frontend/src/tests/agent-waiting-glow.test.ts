// DL-080: waiting-agent edge glow + idle-session highlight in the bar.
// Session composable/targets are stubbed so each test pins the state.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { computed, ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import type { AgentStateName, AppProfileDto } from '@/api/appProfiles'
import type { Scene } from '@/types'
import AgentWaitingGlow from '@/components/AgentWaitingGlow.vue'
import AgentActionBar from '@/components/AgentActionBar.vue'
import { SETTINGS_DEFAULTS } from '@/stores/settings'

const sessionState = {
  currentState: ref<AgentStateName>('ready'),
  isAgentPossiblyRunning: ref(true),
}
const settingsState = {
  agentWaitingGlowEnabled: ref<boolean | undefined>(true),
  animationsEnabled: ref(true),
}
const dashboardState = {
  isEditMode: ref(false),
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
      animationsEnabled: settingsState.animationsEnabled.value,
    }),
  }
})

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    isEditMode: dashboardState.isEditMode.value,
    executeAction: vi.fn(async () => ({ success: true })),
  }),
}))

vi.mock('@/stores/notifications', () => ({
  useNotificationsStore: () => ({ error: vi.fn() }),
}))

const CLAUDE_SCENE = { id: 's1', name: 'Claude Code', pages: [] } as unknown as Scene

beforeEach(() => {
  sessionState.currentState.value = 'ready'
  sessionState.isAgentPossiblyRunning.value = true
  settingsState.agentWaitingGlowEnabled.value = true
  settingsState.animationsEnabled.value = true
  dashboardState.isEditMode.value = false
  effectiveSession.value = null
  sessionRowsState.value = []
})

function mountGlow() {
  return mount(AgentWaitingGlow, {
    props: { scene: CLAUDE_SCENE },
    global: { stubs: { teleport: true, FontAwesomeIcon: true } },
  })
}

describe('AgentWaitingGlow', () => {
  it('renders the edge glow while the agent waits for input', () => {
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(true)
  })

  it('stays dark for working/permission/unknown states', () => {
    for (const state of ['working', 'permission', 'unknown'] as const) {
      sessionState.currentState.value = state
      expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
    }
  })

  it('hides when the setting is off and shows when unset (default on)', () => {
    settingsState.agentWaitingGlowEnabled.value = false
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
    settingsState.agentWaitingGlowEnabled.value = undefined
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(true)
  })

  it('hides in edit mode and when no agent is possibly running', () => {
    dashboardState.isEditMode.value = true
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
    dashboardState.isEditMode.value = false
    sessionState.isAgentPossiblyRunning.value = false
    expect(mountGlow().find('.agent-waiting-glow').exists()).toBe(false)
  })

  it('drops the pulse animation when animations are disabled', () => {
    settingsState.animationsEnabled.value = false
    expect(mountGlow().find('.agent-waiting-glow').classes()).toContain('no-anim')
  })

  it('defaults the setting to enabled', () => {
    expect(SETTINGS_DEFAULTS.agentWaitingGlowEnabled).toBe(true)
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
    effectiveSession.value = { state: 'ready' }
    expect(mountBar().find('.agent-target-chip').classes()).toContain('waiting')
  })

  it('leaves the chip alone for working sessions and when the setting is off', () => {
    effectiveSession.value = { state: 'working' }
    expect(mountBar().find('.agent-target-chip').classes()).not.toContain('waiting')
    effectiveSession.value = { state: 'ready' }
    settingsState.agentWaitingGlowEnabled.value = false
    expect(mountBar().find('.agent-target-chip').classes()).not.toContain('waiting')
  })

  it('flags idle rows in the session picker', async () => {
    sessionRowsState.value = [
      { pid: 100, label: 'projA', state: 'working' },
      { pid: 200, label: 'projB', state: 'ready' },
    ]
    const wrapper = mountBar()
    await wrapper.find('.agent-target-chip').trigger('click')
    await flushPromises()
    // Row 0 is the "Auto" pseudo-row; sessions follow.
    const rows = wrapper.findAll('.agent-target-row')
    expect(rows[1].classes()).not.toContain('waiting')
    expect(rows[2].classes()).toContain('waiting')
    expect(rows[2].text()).toContain('waiting')
  })
})
