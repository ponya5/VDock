// DL-119 — the multi-agent "who needs you" surface: per-source alert list in
// agentAlerts.ts, stacked/rollup cards in AgentAlertOverlay.vue, the
// persistent AgentWaitingDock chips, and `panel_notification` fan-out into
// the notification-center store.
//
// Modules are re-imported after `vi.resetModules()` so each test gets a
// fresh agentAlerts singleton — the same instance the freshly-imported SFCs
// will read.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import type { AgentAlert } from '@/services/agentAlerts'

const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
    isConnected: () => true,
    connect: vi.fn(),
  },
}))

vi.mock('@/api/client', () => ({
  default: {
    get: (...args: unknown[]) => apiGet(...args),
    delete: (...args: unknown[]) => apiDelete(...args),
    post: vi.fn(),
  },
}))

vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ agentAlertsEnabled: true, toastLevel: 'all' }),
}))

// The overlay stands down per-source while that agent's action bar is on
// screen — pinned to "never covered" here; the bar interplay is covered by
// the agent-waiting tests.
vi.mock('@/services/agentState', () => ({
  isAgentBarVisible: () => false,
  initAgentState: vi.fn(),
  agentStateEntry: () => undefined,
}))

function alert(source: string, ts: number, project = ''): AgentAlert {
  return { source, message: `${source} is waiting`, project, cwd: `/w/${project}`, ts }
}

/** Fresh service instance wired to the mocked socket + api. */
async function freshService() {
  const mod = await import('@/services/agentAlerts')
  const svc = mod.useAgentAlerts()
  svc.init()
  await flushPromises() // let the /current re-sync resolve
  return { svc, mod }
}

function fireAgentAlert(alertValue: AgentAlert | null, alerts?: AgentAlert[]) {
  socketHandlers.get('agent_alert')?.({ alert: alertValue, alerts })
}

beforeEach(() => {
  setActivePinia(createPinia())
  socketHandlers.clear()
  apiGet.mockReset().mockResolvedValue({ data: { alert: null, alerts: [] } })
  apiDelete.mockReset().mockResolvedValue({ data: { success: true } })
  vi.resetModules()
})

describe('agentAlerts service (DL-119)', () => {
  it('keeps every source alert, newest first, with alert = newest', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2, 'app'), [alert('cursor', 2, 'app'), alert('claude', 1, 'vdock')])
    await nextTick()

    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor', 'claude'])
    expect(svc.alert.value?.source).toBe('cursor')
  })

  it('re-sorts a misordered payload so the list is always newest-first', async () => {
    const { svc } = await freshService()
    fireAgentAlert(null, [alert('claude', 1), alert('cursor', 5)])
    await nextTick()

    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor', 'claude'])
    // `alert` absent → falls back to the list's newest entry.
    expect(svc.alert.value?.source).toBe('cursor')
  })

  it('maps a legacy {alert} payload to a one-item list', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('devin', 3))
    await nextTick()

    expect(svc.alerts.value.map((a) => a.source)).toEqual(['devin'])
    expect(svc.alert.value?.source).toBe('devin')
  })

  it('restores the alert list from GET /current on init', async () => {
    apiGet.mockResolvedValue({
      data: { alert: alert('cursor', 9), alerts: [alert('cursor', 9), alert('claude', 8)] },
    })
    const { svc } = await freshService()

    expect(apiGet).toHaveBeenCalledWith('/agent-events/current')
    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor', 'claude'])
  })

  it('dismisses one source without touching the others', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2), [alert('cursor', 2), alert('claude', 1)])
    await nextTick()

    await svc.dismiss('claude')

    expect(apiDelete).toHaveBeenCalledWith('/agent-events/current?source=claude')
    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor'])
    expect(svc.alert.value?.source).toBe('cursor')
  })

  it('clears the whole list when dismiss is called without a source', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2), [alert('cursor', 2), alert('claude', 1)])
    await nextTick()

    await svc.dismiss()

    expect(apiDelete).toHaveBeenCalledWith('/agent-events/current')
    expect(svc.alerts.value).toEqual([])
    expect(svc.alert.value).toBeNull()
  })

  it('labels known, unknown and empty sources', async () => {
    const { mod } = await freshService()
    expect(mod.sourceLabelFor('claude')).toBe('Claude Code')
    expect(mod.sourceLabelFor('antigravity')).toBe('Antigravity')
    expect(mod.sourceLabelFor('generic')).toBe('Agent')
    expect(mod.sourceLabelFor('mystery-ide')).toBe('Mystery-ide')
    expect(mod.sourceLabelFor('')).toBe('Agent')
  })

  it('routes panel_notification events into the notification store', async () => {
    await freshService()
    const { useNotificationsStore } = await import('@/stores/notifications')

    socketHandlers.get('panel_notification')?.({
      source: 'mcp', title: 'Build done', message: 'All green', ts: 1,
    })
    await nextTick()

    const entries = useNotificationsStore().notifications
    expect(entries).toHaveLength(1)
    expect(entries[0].type).toBe('warning')
    expect(entries[0].title).toBe('Build done')
    expect(entries[0].message).toBe('All green')
    expect(entries[0].details).toBe('Source: MCP')
    // Not marked important — an errors-only toast level must silence it.
    expect(entries[0].important).toBeUndefined()
  })

  it('falls back to a generic title for empty panel notifications', async () => {
    await freshService()
    const { useNotificationsStore } = await import('@/stores/notifications')

    socketHandlers.get('panel_notification')?.({ source: 'trigger' })
    await nextTick()

    const entries = useNotificationsStore().notifications
    expect(entries[0].title).toBe('Notification')
    expect(entries[0].details).toBe('Source: Trigger')
  })
})

async function mountOverlay() {
  const { default: AgentAlertOverlay } = await import('@/components/AgentAlertOverlay.vue')
  return mount(AgentAlertOverlay, {
    global: { stubs: { teleport: true, FontAwesomeIcon: true } },
  })
}

describe('AgentAlertOverlay (DL-119)', () => {
  it('renders a stacked card per waiting agent, each dismissible alone', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2, 'app'), [alert('cursor', 2, 'app'), alert('claude', 1, 'vdock')])
    const wrapper = await mountOverlay()
    await nextTick()

    const cards = wrapper.findAll('.agent-alert')
    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Cursor needs you')
    expect(cards[0].text()).toContain('app')
    expect(cards[1].text()).toContain('Claude Code needs you')

    await cards[1].find('.alert-dismiss').trigger('click')
    expect(apiDelete).toHaveBeenCalledWith('/agent-events/current?source=claude')
    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor'])
  })

  it('collapses 3+ alerts into a single "N agents need you" card', async () => {
    await freshService()
    fireAgentAlert(alert('devin', 3), [
      alert('devin', 3), alert('cursor', 2), alert('claude', 1),
    ])
    const wrapper = await mountOverlay()
    await nextTick()

    const cards = wrapper.findAll('.agent-alert')
    expect(cards).toHaveLength(1)
    expect(cards[0].text()).toContain('3 agents need you')
    expect(cards[0].text()).toContain('Devin')
    expect(cards[0].text()).toContain('Cursor')
    expect(cards[0].text()).toContain('Claude Code')

    await cards[0].find('.alert-dismiss').trigger('click')
    expect(apiDelete).toHaveBeenCalledWith('/agent-events/current')
  })

  it('renders nothing when the alert list is empty', async () => {
    const wrapper = await mountOverlay()
    await nextTick()
    expect(wrapper.find('.agent-alert').exists()).toBe(false)
  })
})

describe('AgentWaitingDock (DL-119)', () => {
  it('shows one chip per waiting agent — persisted beyond the banner', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2, 'app'), [alert('cursor', 2, 'app'), alert('claude', 1, 'vdock')])
    const wrapper = await mountOverlay()
    await nextTick()

    const chips = wrapper.findAll('.dock-chip')
    expect(chips).toHaveLength(2)
    expect(chips[0].text()).toContain('Cursor')
    expect(chips[0].text()).toContain('app')
    expect(chips[1].text()).toContain('Claude Code')
    expect(svc.alerts.value).toHaveLength(2)
  })

  it('dispatches vdock:navigate-scene with the chip source on tap', async () => {
    await freshService()
    fireAgentAlert(alert('claude', 1), [alert('claude', 1)])
    const wrapper = await mountOverlay()
    await nextTick()

    const spy = vi.fn()
    window.addEventListener('vdock:navigate-scene', spy)
    await wrapper.find('.dock-chip').trigger('click')
    window.removeEventListener('vdock:navigate-scene', spy)

    expect(spy).toHaveBeenCalledOnce()
    expect((spy.mock.calls[0][0] as CustomEvent).detail).toEqual({ source: 'claude' })
  })

  it('per-chip × dismisses just that source', async () => {
    const { svc } = await freshService()
    fireAgentAlert(alert('cursor', 2), [alert('cursor', 2), alert('claude', 1)])
    const wrapper = await mountOverlay()
    await nextTick()

    await wrapper.findAll('.dock-chip')[1].find('.dock-dismiss').trigger('click')
    expect(apiDelete).toHaveBeenCalledWith('/agent-events/current?source=claude')
    expect(svc.alerts.value.map((a) => a.source)).toEqual(['cursor'])
    await nextTick()
    expect(wrapper.findAll('.dock-chip')).toHaveLength(1)
  })

  it('hides the dock when no alerts are pending', async () => {
    const wrapper = await mountOverlay()
    await nextTick()
    expect(wrapper.find('.agent-waiting-dock').exists()).toBe(false)
  })
})
