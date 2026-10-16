// DL-011: a waiting permission prompt can be answered from the alert card on
// any scene/device - but only when exactly one session of that agent waits.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { computed, ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const alertList = ref<any[]>([])
const dismiss = vi.fn()
vi.mock('@/services/agentAlerts', () => ({
  useAgentAlerts: () => ({ alerts: computed(() => alertList.value), dismiss, sourceLabelFor: () => 'Claude Code' }),
}))
vi.mock('@/services/agentState', () => ({ isAgentBarVisible: () => false }))
vi.mock('@/services/agentWaiting', () => ({ waitingChipSources: () => new Set() }))
vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => ({ currentProfile: { scenes: [] } }) }))
vi.mock('@/composables/useAppIntegrations', () => ({ useAppIntegrations: () => ref([]) }))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => ({ agentAlertsEnabled: true, agentWaitingGlowEnabled: false }) }))
const notifyError = vi.fn()
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => ({ error: notifyError }) }))
const mission = vi.hoisted(() => ({ fetchMission: vi.fn(), decideMissionSession: vi.fn() }))
vi.mock('@/services/missionControl', () => mission)

import AgentAlertOverlay from '@/components/AgentAlertOverlay.vue'

function mountOverlay() {
  return mount(AgentAlertOverlay, {
    global: { stubs: { FontAwesomeIcon: true, AgentWaitingDock: true, Teleport: true } },
  })
}

const waiting = (id: string) => ({ source: 'claude', session_id: id, can_decide: true })

beforeEach(() => {
  setActivePinia(createPinia())
  alertList.value = [{ source: 'claude', message: 'Run: git push', project: 'VDock', cwd: '', ts: 1 }]
  dismiss.mockReset()
  mission.decideMissionSession.mockReset().mockResolvedValue(undefined)
})

describe('alert card Approve / Deny', () => {
  it('approves the one waiting session and clears the card', async () => {
    mission.fetchMission.mockResolvedValue({ sessions: [waiting('s1')] })
    const w = mountOverlay()
    await flushPromises()
    expect(w.text()).toContain('Run: git push')
    await w.find('.alert-approve').trigger('click')
    await flushPromises()
    expect(mission.decideMissionSession).toHaveBeenCalledWith('claude', 's1', 'approve')
    expect(dismiss).toHaveBeenCalledWith('claude')
  })

  it('keeps "Got it" when two sessions of the agent wait (ambiguous)', async () => {
    mission.fetchMission.mockResolvedValue({ sessions: [waiting('s1'), waiting('s2')] })
    const w = mountOverlay()
    await flushPromises()
    expect(w.find('[data-testid="alert-decide"]').exists()).toBe(false)
    expect(w.text()).toContain('Got it')
  })

  it('reports a failed deny instead of hiding it', async () => {
    mission.fetchMission.mockResolvedValue({ sessions: [waiting('s1')] })
    mission.decideMissionSession.mockRejectedValue({ response: { data: { error: 'That session is no longer waiting for approval' } } })
    const w = mountOverlay()
    await flushPromises()
    await w.find('.alert-deny').trigger('click')
    await flushPromises()
    expect(notifyError).toHaveBeenCalledWith('Could not deny', 'That session is no longer waiting for approval')
    expect(dismiss).not.toHaveBeenCalled()
  })
})
