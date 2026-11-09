// DL-166: the desktop bar now shows on every AI coding scene (so "No session" is visible), while the
// alert overlay is only told the bar is visible when Approve/Deny style actions really are on screen.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { computed, ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import type { Scene } from '@/types'
import AgentActionBar from '@/components/AgentActionBar.vue'
import { resetAgentSceneViews } from '@/composables/useAgentSceneView'

const session = {
  running: ref(false),
  state: ref<'ready' | 'working' | 'permission' | 'unknown'>('unknown'),
  actions: ref<Array<{ id: string; label: string; icon: string; description: string; isPrimary: boolean }>>([]),
  stateActions: ref<object | undefined>({}),
  isEdit: ref(false),
}
const tracked = vi.hoisted(() => ({ visible: undefined as { value: boolean } | undefined }))

vi.mock('@/composables/useAgentSession', () => ({
  useAgentSession: () => ({
    profile: computed(() => ({ id: 'claude-code', label: 'Claude Code', status_source: 'claude', commands: [], state_actions: session.stateActions.value })),
    stateEntry: computed(() => undefined),
    currentState: computed(() => session.state.value),
    stateLabel: computed(() => 'label'),
    isAgentDetected: computed(() => session.running.value),
    isAgentPossiblyRunning: computed(() => session.running.value),
    visibleActions: computed(() => session.actions.value),
    runningActionId: ref(null), flashActionId: ref(null), runAction: vi.fn(), sendPrompt: vi.fn(),
  }),
  trackAgentSurfaceVisibility: (_source: unknown, visible: { value: boolean }) => { tracked.visible = visible },
}))
vi.mock('@/composables/useAgentTargets', () => ({
  useAgentTargets: () => ({
    sessions: computed(() => []), sessionRows: computed(() => []),
    pinnedPid: ref(null), resolvedPid: ref(null), effectiveSession: computed(() => null),
    targetLabel: computed(() => 'No session'), refresh: vi.fn(), setTarget: vi.fn(), identify: vi.fn(),
  }),
  profileSessionMarker: () => 'claude',
}))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => ({ agentWaitingGlowEnabled: false }) }))
vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => ({ get isEditMode() { return session.isEdit.value } }) }))

const mk = (id: string, type: string) => ({
  id, label: id, shape: 'rounded', position: { row: 0, col: 0 }, size: { rows: 1, cols: 1 }, enabled: true, action: { type, config: {} },
})
const SCENE = { id: 'bar-scene', name: 'Claude Code', pages: [{ id: 'p', name: 'P', grid_config: { rows: 2, cols: 4 }, buttons: [
  mk('a', 'cc_interrupt'), mk('b', 'cc_mode'),
] }] } as unknown as Scene

function mountBar() {
  return mount(AgentActionBar, { props: { scene: SCENE }, global: { stubs: { AgentSessionPicker: true, FontAwesomeIcon: true } } })
}

beforeEach(() => {
  resetAgentSceneViews()
  session.running.value = false
  session.state.value = 'unknown'
  session.actions.value = []
  session.stateActions.value = {}
  session.isEdit.value = false
})

describe('AgentActionBar status banner', () => {
  it('renders offline with no actions when no agent runs, and reports the actions as not visible', async () => {
    const w = mountBar()
    await flushPromises()
    expect(w.find('.agent-action-bar').exists()).toBe(true)
    expect(w.classes()).toContain('state-offline')
    expect(w.find('.asb-word').text()).toBe('No session')
    expect(w.find('.agent-actions').exists()).toBe(false)
    expect(tracked.visible?.value).toBe(false)
  })

  it('shows the actions and reports them visible once the agent runs', async () => {
    session.running.value = true
    session.state.value = 'permission'
    session.actions.value = [{ id: 'cc_approve', label: 'Approve', icon: 'check', description: '', isPrimary: true }]
    const w = mountBar()
    await flushPromises()
    expect(w.find('.asb-word').text()).toBe('Needs you')
    expect(w.findAll('.agent-action')).toHaveLength(1)
    expect(tracked.visible?.value).toBe(true)
  })

  it('shows the Groups / All toggle for a multi-category scene and switches it', async () => {
    const w = mountBar()
    const toggle = w.find('[data-testid="agent-view-toggle"]')
    expect(toggle.exists()).toBe(true)
    expect(toggle.find('[data-mode="groups"]').attributes('aria-checked')).toBe('true')
    await toggle.find('[data-mode="all"]').trigger('click')
    expect(w.find('[data-testid="agent-view-toggle"] [data-mode="all"]').attributes('aria-checked')).toBe('true')
  })

  it('is hidden in edit mode and on scenes without agent state actions', async () => {
    session.isEdit.value = true
    expect(mountBar().find('.agent-action-bar').exists()).toBe(false)
    session.isEdit.value = false
    session.stateActions.value = undefined
    expect(mountBar().find('.agent-action-bar').exists()).toBe(false)
  })
})
