// DL-065: the mobile agent console — a portrait phone surface for talking to
// a coding agent. The session composable is stubbed so each test pins one
// agent state and checks what the phone offers in it.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { computed, ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import type { AgentStateName, AppProfileDto } from '@/api/appProfiles'
import type { AgentStateEntry } from '@/services/agentState'
import type { Button, Scene } from '@/types'
import MobileAgentConsole from '@/components/MobileAgentConsole.vue'

const sessionState = {
  profile: ref<Partial<AppProfileDto> | null>(null),
  stateEntry: ref<Partial<AgentStateEntry> | undefined>(undefined),
  currentState: ref<AgentStateName>('ready'),
  isAgentPossiblyRunning: ref(true),
}
const sendPrompt = vi.fn()
const runAction = vi.fn()
const executeButtonAction = vi.fn()
const notifyError = vi.fn()

vi.mock('@/composables/useAgentSession', () => ({
  useAgentSession: () => ({
    profile: computed(() => sessionState.profile.value),
    stateEntry: computed(() => sessionState.stateEntry.value),
    currentState: computed(() => sessionState.currentState.value),
    stateLabel: computed(() => `label-${sessionState.currentState.value}`),
    isAgentDetected: computed(() => true),
    isAgentPossiblyRunning: computed(() => sessionState.isAgentPossiblyRunning.value),
    visibleActions: computed(() => [
      { id: 'cc_submit', label: 'Submit', icon: 'paper-plane', description: '', isPrimary: true },
      { id: 'cc_clear', label: 'Clear', icon: 'eraser', description: '', isPrimary: false },
    ]),
    runningActionId: ref(null),
    runAction,
    sendPrompt,
  }),
  trackAgentSurfaceVisibility: vi.fn(),
}))

// DL-071 session targeting — stubbed so each test controls the session list.
const targetState = {
  sessions: ref<{ pid: number; hwnd: number; title: string; cwd: string | null; project: string; state: string | null }[]>([]),
  pinnedPid: ref<number | null>(null),
  resolvedPid: ref<number | null>(null),
}
const setTargetMock = vi.fn()
const identifyMock = vi.fn()

vi.mock('@/composables/useAgentTargets', () => ({
  useAgentTargets: () => ({
    sessions: computed(() => targetState.sessions.value),
    sessionRows: computed(() =>
      targetState.sessions.value.map(s => ({
        ...s,
        label: s.project || s.title || `pid ${s.pid}`,
      }))
    ),
    pinnedPid: computed(() => targetState.pinnedPid.value),
    resolvedPid: computed(() => targetState.resolvedPid.value),
    effectiveSession: computed(() => null),
    targetLabel: computed(() => 'Auto'),
    refresh: vi.fn(),
    setTarget: setTargetMock,
    identify: identifyMock,
  }),
  profileSessionMarker: (p: any) =>
    p?.commands?.find((c: any) => c.session_marker)?.session_marker ?? null,
}))

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({ executeButtonAction }),
}))

vi.mock('@/stores/notifications', () => ({
  useNotificationsStore: () => ({ error: notifyError }),
}))

function makeButton(id: string, label: string, actionType: string): Button {
  return {
    id,
    label,
    icon: ['fas', 'terminal'],
    action: { type: actionType, config: {} } as Button['action'],
    shape: 'rounded',
    position: { row: 0, col: 0 },
    size: { rows: 1, cols: 1 },
    enabled: true,
  } as Button
}

const CLAUDE_SCENE = {
  id: 'scene-claude',
  name: 'Claude Code',
  pages: [{
    id: 'page-1',
    name: 'Main',
    grid_config: { rows: 2, cols: 4 },
    buttons: [
      makeButton('open', 'Open Claude', 'claude_continue'),
      makeButton('review', 'Review', 'cc_prompt'),
      makeButton('next', 'Next Page', 'next_page'),
    ],
  }],
} as Scene

function mountConsole() {
  return mount(MobileAgentConsole, {
    props: { scene: CLAUDE_SCENE },
    global: { stubs: { FontAwesomeIcon: true } },
  })
}

beforeEach(() => {
  sessionState.profile.value = { id: 'claude-code', label: 'Claude Code', prompt_command: 'cc_prompt', status_source: 'claude' }
  sessionState.stateEntry.value = { prompt: 'Fix the tests', reply: 'All 12 tests pass now.', project: 'VDock2', message: '' }
  sessionState.currentState.value = 'ready'
  sessionState.isAgentPossiblyRunning.value = true
  targetState.sessions.value = []
  targetState.pinnedPid.value = null
  targetState.resolvedPid.value = null
  setTargetMock.mockReset()
  identifyMock.mockReset()
  sendPrompt.mockReset()
  runAction.mockReset()
  executeButtonAction.mockReset()
  notifyError.mockReset()
})

describe('MobileAgentConsole', () => {
  it('never renders a conversation card — the deck is control-only', () => {
    sessionState.stateEntry.value = { prompt: 'Fix it', reply: '<b>done</b>', project: 'VDock2', message: '' }
    const wrapper = mountConsole()
    expect(wrapper.find('.mac-conversation').exists()).toBe(false)
    expect(wrapper.find('.mac-message').exists()).toBe(false)
    expect(wrapper.find('.mac-project').text()).toContain('VDock2')
  })

  it('offers the scene buttons as shortcuts, without page navigation', () => {
    const labels = mountConsole().findAll('.mac-shortcut').map(node => node.text())
    expect(labels).toEqual(['Open Claude', 'Review'])
  })

  it('shows the hook detail message in the status line on a permission prompt', () => {
    sessionState.currentState.value = 'permission'
    sessionState.stateEntry.value = { message: 'Claude needs your permission to use Bash', prompt: '', reply: '' }
    const wrapper = mountConsole()
    expect(wrapper.find('.mac-state-label').text()).toContain('permission to use Bash')
  })

  it('never renders a text composer — actions and shortcuts are the only controls', () => {
    expect(mountConsole().find('form').exists()).toBe(false)
    expect(mountConsole().find('textarea').exists()).toBe(false)
  })

  it('points at the launch shortcut when the agent is not running, with no filler card', () => {
    sessionState.isAgentPossiblyRunning.value = false
    sessionState.stateEntry.value = undefined
    const wrapper = mountConsole()
    expect(wrapper.find('.mac-conversation').exists()).toBe(false)
    expect(wrapper.find('.mac-actions').exists()).toBe(false)
    expect(wrapper.find('.mac-shortcut.highlighted').text()).toBe('Open Claude')
  })

  it('runs a state action and a shortcut', async () => {
    executeButtonAction.mockResolvedValue({ success: true })
    const wrapper = mountConsole()
    await wrapper.find('.mac-action.primary').trigger('click')
    expect(runAction).toHaveBeenCalledWith(expect.objectContaining({ id: 'cc_submit' }))
    await wrapper.findAll('.mac-shortcut')[1].trigger('click')
    await flushPromises()
    expect(executeButtonAction).toHaveBeenCalledWith(expect.objectContaining({ id: 'review' }))
  })

  // --- DL-071: session target strip ---------------------------------------

  const TWO_SESSIONS = [
    { pid: 100, hwnd: 9001, title: 'wt A', cwd: 'C:\\repos\\projA', project: 'projA', state: 'working' },
    { pid: 200, hwnd: 9002, title: 'wt B', cwd: 'C:\\repos\\projB', project: 'projB', state: 'ready' },
  ]

  it('hides the session strip only when no sessions exist', () => {
    sessionState.profile.value = {
      id: 'claude-code', label: 'Claude Code', prompt_command: 'cc_prompt',
      status_source: 'claude', commands: [{ session_marker: 'claude' }],
    } as AppProfileDto
    // Zero sessions → hidden; one session → strip shows the current target.
    expect(mountConsole().find('.mac-sessions').exists()).toBe(false)
    targetState.sessions.value = [TWO_SESSIONS[0]]
    expect(mountConsole().find('.mac-sessions').exists()).toBe(true)
  })

  it('lists sessions and pins the tapped one', async () => {
    sessionState.profile.value = {
      id: 'claude-code', label: 'Claude Code', prompt_command: 'cc_prompt',
      status_source: 'claude', commands: [{ session_marker: 'claude' }],
    } as AppProfileDto
    targetState.sessions.value = TWO_SESSIONS
    targetState.resolvedPid.value = 200

    const wrapper = mountConsole()
    const chips = wrapper.findAll('.mac-session')
    expect(chips).toHaveLength(3) // Auto + 2 sessions
    expect(chips[0].text()).toContain('Auto')
    expect(chips[1].text()).toContain('projA')
    expect(chips[2].text()).toContain('projB')

    await chips[2].trigger('click')
    expect(setTargetMock).toHaveBeenCalledWith(200)
    // Pinning flashes the real window — "this one" made visible.
    expect(identifyMock).toHaveBeenCalledWith(200)
  })

  it('tapping the pinned session releases back to Auto', async () => {
    sessionState.profile.value = {
      id: 'claude-code', label: 'Claude Code', prompt_command: 'cc_prompt',
      status_source: 'claude', commands: [{ session_marker: 'claude' }],
    } as AppProfileDto
    targetState.sessions.value = TWO_SESSIONS
    targetState.pinnedPid.value = 100

    const wrapper = mountConsole()
    const pinned = wrapper.findAll('.mac-session')[1]
    expect(pinned.classes()).toContain('active')

    await pinned.trigger('click')
    expect(setTargetMock).toHaveBeenCalledWith(null)
    // Releasing to Auto doesn't flash anything — nothing was armed.
    expect(identifyMock).not.toHaveBeenCalled()
  })

  it('tapping Auto unpins without flashing', async () => {
    sessionState.profile.value = {
      id: 'claude-code', label: 'Claude Code', prompt_command: 'cc_prompt',
      status_source: 'claude', commands: [{ session_marker: 'claude' }],
    } as AppProfileDto
    targetState.sessions.value = TWO_SESSIONS
    targetState.pinnedPid.value = 100

    const wrapper = mountConsole()
    await wrapper.findAll('.mac-session')[0].trigger('click')
    expect(setTargetMock).toHaveBeenCalledWith(null)
    expect(identifyMock).not.toHaveBeenCalled()
  })
})
