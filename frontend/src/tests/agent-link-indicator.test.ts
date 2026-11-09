// DL-165 — the bar shows which session its buttons are linked to, and the buttons follow THAT session's state.
import { describe, it, expect, vi } from 'vitest'
import { computed, ref, type Ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import AgentActionBar from '@/components/AgentActionBar.vue'

const captured: { override: Ref<string | null> | undefined } = { override: undefined }
const rows = ref([
  { pid: 1, hwnd: 1, title: 'a', cwd: 'C:/p/backend', project: 'backend', state: 'ready', prompted: true, detail: '', host: 'Cursor', started: 1, label: 'backend · Cursor', accent: '#7aa2ff', badge: 'CU' },
  { pid: 2, hwnd: 2, title: 'b', cwd: 'C:/p/frontend', project: 'frontend', state: 'working', prompted: true, detail: '', host: 'Windows Terminal', started: 2, label: 'frontend · Windows Terminal', accent: '#63d0a3', badge: 'WT' },
])
const effective = ref<(typeof rows.value)[number] | null>(rows.value[1])

vi.mock('@/composables/useAgentSession', () => ({
  useAgentSession: (_scene: unknown, override?: Ref<string | null>) => {
    captured.override = override
    return {
      profile: computed(() => ({ id: 'claude-code', label: 'Claude Code', status_source: 'claude',
        commands: [{ id: 'cc_interrupt', label: 'Interrupt', icon: 'hand', description: '', session_marker: 'claude' }], state_actions: {} })),
      stateEntry: computed(() => undefined),
      currentState: computed(() => (override?.value as never) ?? 'ready'),
      stateLabel: computed(() => 'label'),
      isAgentDetected: computed(() => true),
      isAgentPossiblyRunning: computed(() => true),
      visibleActions: computed(() => [{ id: 'cc_interrupt', label: 'Interrupt', icon: 'hand', description: '', isPrimary: true }]),
      runningActionId: ref(null), flashActionId: ref(null), runAction: vi.fn(), sendPrompt: vi.fn(),
    }
  },
  trackAgentSurfaceVisibility: vi.fn(),
}))
vi.mock('@/composables/useAgentTargets', () => ({
  useAgentTargets: () => ({
    sessions: computed(() => rows.value), sessionRows: computed(() => rows.value),
    pinnedPid: ref(null), resolvedPid: ref(2), effectiveSession: computed(() => effective.value),
    targetLabel: computed(() => 'Auto'), refresh: vi.fn(), setTarget: vi.fn(), identify: vi.fn(),
  }),
  profileSessionMarker: () => 'claude',
}))
vi.mock('@/stores/settings', async (orig) => ({ ...(await orig<typeof import('@/stores/settings')>()), useSettingsStore: () => ({ agentWaitingGlowEnabled: false }) }))
vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => ({ isEditMode: false }) }))

describe('agent bar link indicator', () => {
  it('names the linked session, summarises the others and drives the buttons by the linked state', async () => {
    const w = mount(AgentActionBar, { props: { scene: null }, global: { stubs: { AgentSessionPicker: true, FontAwesomeIcon: true } } })
    await flushPromises()
    expect(captured.override?.value).toBe('working')                       // buttons follow session 2, not session 1
    expect(w.find('.agent-link-badge').text()).toBe('WT')
    expect(w.find('[data-testid="actions-for"]').text()).toContain('frontend · Windows Terminal')
    expect(w.find('[data-testid="others-summary"]').text()).toBe('1 other: 1 ready')
    expect(w.classes()).toContain('state-working')
    expect(w.attributes('style')).toContain('--link-accent: #63d0a3')
  })
})
