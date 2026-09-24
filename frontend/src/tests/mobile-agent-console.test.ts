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
  sendPrompt.mockReset()
  runAction.mockReset()
  executeButtonAction.mockReset()
  notifyError.mockReset()
})

describe('MobileAgentConsole', () => {
  it('shows the last prompt and reply as plain text', () => {
    sessionState.stateEntry.value = { prompt: 'Fix it', reply: '<b>done</b>', project: 'VDock2', message: '' }
    const wrapper = mountConsole()
    const messages = wrapper.findAll('.mac-message-text').map(node => node.text())
    expect(messages).toEqual(['Fix it', '<b>done</b>'])
    expect(wrapper.find('.mac-message b').exists()).toBe(false)
    expect(wrapper.find('.mac-project').text()).toContain('VDock2')
  })

  it('offers the scene buttons as shortcuts, without page navigation', () => {
    const labels = mountConsole().findAll('.mac-shortcut').map(node => node.text())
    expect(labels).toEqual(['Open Claude', 'Review'])
  })

  it('shows a permission request in the conversation', async () => {
    sessionState.currentState.value = 'permission'
    sessionState.stateEntry.value = { message: 'Claude needs your permission to use Bash', prompt: '', reply: '' }
    const wrapper = mountConsole()
    expect(wrapper.find('.is-permission').text()).toContain('permission to use Bash')
  })

  it('never renders a text composer — actions and shortcuts are the only controls', () => {
    expect(mountConsole().find('form').exists()).toBe(false)
    expect(mountConsole().find('textarea').exists()).toBe(false)
  })

  it('renders no conversation card at all when there is nothing to show', () => {
    sessionState.stateEntry.value = { prompt: '', reply: '', project: '', message: '' }
    expect(mountConsole().find('.mac-conversation').exists()).toBe(false)
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
})
