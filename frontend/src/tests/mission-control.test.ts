// DL-144 - Mission Control + approval inbox: grouping rules, the modal
// (list / approve / deny / open / live refresh) and the dock + deck-action
// entry points.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const handlers = new Map<string, () => void>()
const apiGet = vi.fn()
const apiPost = vi.fn()
const toast = { success: vi.fn(), error: vi.fn() }

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: () => void) => handlers.set(event, cb),
    off: (event: string) => handlers.delete(event),
  },
}))
vi.mock('@/api/client', () => ({
  default: { get: (...a: unknown[]) => apiGet(...a), post: (...a: unknown[]) => apiPost(...a), delete: vi.fn() },
}))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => toast }))
vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ agentAlertsEnabled: true, agentWaitingDockEnabled: true }),
}))

import AgentMissionControl from '@/components/AgentMissionControl.vue'
import {
  closeMissionControl,
  formatIdle,
  groupMission,
  missionControlOpen,
  openMissionControl,
  type MissionSession,
} from '@/services/missionControl'

function session(over: Partial<MissionSession>): MissionSession {
  return {
    source: 'claude', session_id: 's1', project: 'api', cwd: 'C:/repos/api',
    state: 'working', message: '', prompt: '', reply: '', prompted: true,
    ts: 1, idle_seconds: 10, needs_you: false, can_decide: false, can_focus: true, can_prompt: false,
    ...over,
  }
}

const SNAPSHOT_SESSIONS: MissionSession[] = [
  session({ session_id: 'p', project: 'web', state: 'permission', needs_you: true, can_decide: true,
            message: 'Claude needs your permission to use Bash' }),
  session({ source: 'cursor', session_id: 'r', project: 'app', state: 'ready', needs_you: true,
            prompt: 'add tests', reply: 'Done - 12 tests added.' }),
  session({ session_id: 'w', project: 'infra', state: 'working' }),
  session({ source: 'codex', session_id: 'i', project: 'docs', state: 'ready', prompted: false, can_focus: false }),
]

function snapshotResponse(sessions = SNAPSHOT_SESSIONS) {
  return {
    data: {
      success: true,
      sessions,
      presets: [{ id: 'continue', label: 'Continue' }, { id: 'write_tests', label: 'Write tests' }],
      needs_you: sessions.filter((s) => s.needs_you).length,
      pending_approvals: sessions.filter((s) => s.can_decide).length,
    },
  }
}

const mounted: Array<{ unmount: () => void }> = []

function mountPanel() {
  const wrapper = mount(AgentMissionControl, {
    global: { stubs: { Teleport: { template: '<div><slot /></div>' }, Transition: { template: '<div><slot /></div>' } } },
  })
  mounted.push(wrapper)
  return wrapper
}

async function mountOpen() {
  const wrapper = mountPanel()
  openMissionControl()
  await flushPromises()
  await nextTick()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  handlers.clear()
  apiGet.mockReset().mockResolvedValue(snapshotResponse())
  apiPost.mockReset().mockResolvedValue({ data: { success: true } })
  toast.success.mockReset()
  toast.error.mockReset()
  closeMissionControl()
})

afterEach(() => {
  closeMissionControl()
  mounted.splice(0).forEach((w) => w.unmount())
})

// ---------------------------------------------------------------------------

describe('groupMission', () => {
  it('splits into approval / waiting / working / idle and drops empty groups', () => {
    const groups = groupMission(SNAPSHOT_SESSIONS)

    expect(groups.map((g) => g.id)).toEqual(['approval', 'waiting', 'working', 'idle'])
    expect(groups.map((g) => g.sessions.map((s) => s.session_id))).toEqual([['p'], ['r'], ['w'], ['i']])
    expect(groupMission([session({ state: 'working' })]).map((g) => g.id)).toEqual(['working'])
    expect(groupMission([])).toEqual([])
  })
})

describe('formatIdle', () => {
  it.each([
    [0, 'now'], [4, 'now'], [5, '5s'], [59, '59s'], [60, '1m'],
    [4 * 60 + 30, '4m'], [3600, '1h'], [3600 + 5 * 60, '1h 5m'],
  ])('%is -> %s', (seconds, label) => {
    expect(formatIdle(seconds)).toBe(label)
  })
})

describe('AgentMissionControl', () => {
  it('stays hidden until opened, then loads and lists every session', async () => {
    const wrapper = mountPanel()
    expect(wrapper.find('.mc-panel').exists()).toBe(false)
    expect(apiGet).not.toHaveBeenCalled()

    openMissionControl()
    await flushPromises()

    expect(apiGet).toHaveBeenCalledWith('/agent-mission')
    expect(wrapper.findAll('[data-testid="mc-row"]')).toHaveLength(4)
    expect(wrapper.find('[data-testid="mc-needs-count"]').text()).toBe('2 need you')
  })

  it('puts the approval inbox first and shows what the agent is asking', async () => {
    const wrapper = await mountOpen()

    const first = wrapper.find('.mc-group')
    expect(first.attributes('data-group')).toBe('approval')
    expect(first.text()).toContain('Claude Code')
    expect(first.text()).toContain('web')
    expect(first.text()).toContain('Claude needs your permission to use Bash')
    expect(first.find('[data-testid="mc-approve"]').exists()).toBe(true)
    expect(first.find('[data-testid="mc-deny"]').exists()).toBe(true)
  })

  it('offers Approve / Deny only where the server says the row can be decided', async () => {
    const wrapper = await mountOpen()

    expect(wrapper.findAll('[data-testid="mc-approve"]')).toHaveLength(1)
    expect(wrapper.findAll('[data-testid="mc-deny"]')).toHaveLength(1)
    // codex row: can_focus false -> no Open either
    const rows = wrapper.findAll('[data-testid="mc-row"]')
    expect(rows[3].find('[data-testid="mc-open"]').exists()).toBe(false)
  })

  it('Approve posts the decision for exactly that session and confirms', async () => {
    const wrapper = await mountOpen()

    await wrapper.find('[data-testid="mc-approve"]').trigger('click')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/agent-mission/decide', {
      source: 'claude', session_id: 'p', decision: 'approve',
    })
    expect(toast.success).toHaveBeenCalledWith('Approved', 'Claude Code - web')
    // list is refreshed afterwards so the answered row drops out
    expect(apiGet).toHaveBeenCalledTimes(2)
  })

  it('Deny posts a deny decision', async () => {
    const wrapper = await mountOpen()

    await wrapper.find('[data-testid="mc-deny"]').trigger('click')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/agent-mission/decide', {
      source: 'claude', session_id: 'p', decision: 'deny',
    })
    expect(toast.success).toHaveBeenCalledWith('Denied', 'Claude Code - web')
  })

  it('surfaces the server reason when a stale answer is refused', async () => {
    apiPost.mockRejectedValueOnce({
      response: { data: { error: 'That session is no longer waiting for approval' } },
    })
    const wrapper = await mountOpen()

    await wrapper.find('[data-testid="mc-approve"]').trigger('click')
    await flushPromises()

    expect(toast.error).toHaveBeenCalledWith(
      'Could not answer the prompt',
      'That session is no longer waiting for approval',
      undefined,
    )
    expect(toast.success).not.toHaveBeenCalled()
  })

  it('ignores a second tap while the first answer is in flight', async () => {
    let release: (v: unknown) => void = () => {}
    apiPost.mockReturnValueOnce(new Promise((resolve) => { release = resolve }))
    const wrapper = await mountOpen()
    const approve = wrapper.find('[data-testid="mc-approve"]')

    await approve.trigger('click')
    await approve.trigger('click')
    release({ data: { success: true } })
    await flushPromises()

    expect(apiPost).toHaveBeenCalledTimes(1)
  })

  it('Open focuses that session without answering it', async () => {
    const wrapper = await mountOpen()
    const rows = wrapper.findAll('[data-testid="mc-row"]')

    await rows[1].find('[data-testid="mc-open"]').trigger('click')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/agent-mission/focus', { source: 'cursor', session_id: 'r' })
    expect(apiPost).not.toHaveBeenCalledWith('/agent-mission/decide', expect.anything())
  })

  it('refreshes when an agent_state event arrives while open', async () => {
    vi.useFakeTimers()
    try {
      await mountOpen()
      apiGet.mockClear()

      handlers.get('agent_state')?.()
      await vi.advanceTimersByTimeAsync(200)

      expect(apiGet).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('shows a helpful empty state', async () => {
    apiGet.mockResolvedValue(snapshotResponse([]))
    const wrapper = await mountOpen()

    expect(wrapper.find('[data-testid="mc-empty"]').text()).toContain('No agent sessions')
  })

  it('shows an error when the list cannot be loaded', async () => {
    apiGet.mockRejectedValue(new Error('offline'))
    const wrapper = await mountOpen()

    expect(wrapper.find('.mc-error').text()).toContain('Could not load')
  })

  it('closes from the close button and from Escape, and unsubscribes', async () => {
    const wrapper = await mountOpen()
    expect(handlers.has('agent_state')).toBe(true)

    await wrapper.find('.mc-close').trigger('click')
    await nextTick()
    expect(missionControlOpen.value).toBe(false)
    expect(wrapper.find('.mc-panel').exists()).toBe(false)
    expect(handlers.has('agent_state')).toBe(false)

    openMissionControl()
    await flushPromises()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(missionControlOpen.value).toBe(false)
  })
})

// ---------------------------------------------------------------------------

describe('DL-145 prompt menu and turn changes', () => {
  const READY = session({ session_id: 'r1', project: 'api', state: 'ready', needs_you: true, can_prompt: true, ts: 5 })
  const CHANGES = {
    success: true,
    files: [
      { path: 'src/a.ts', added: 100, removed: 8, status: 'M' },
      { path: 'src/b.ts', added: 20, removed: 0, status: 'A' },
    ],
    totals: { files: 2, added: 120, removed: 8 },
  }

  function respond(changes: unknown = CHANGES) {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url === '/agent-mission/changes' ? { data: changes } : snapshotResponse([READY, ...SNAPSHOT_SESSIONS])))
  }

  it('offers Prompt only on rows the server marks can_prompt', async () => {
    respond()
    const wrapper = await mountOpen()

    expect(wrapper.findAll('[data-testid="mc-prompt"]')).toHaveLength(1)
  })

  it('Prompt opens the preset list and a preset posts for exactly that session', async () => {
    respond()
    const wrapper = await mountOpen()

    expect(wrapper.find('[data-testid="mc-presets"]').exists()).toBe(false)
    await wrapper.find('[data-testid="mc-prompt"]').trigger('click')
    const labels = wrapper.findAll('[data-testid="mc-preset"]').map((b) => b.text())
    expect(labels).toEqual(['Continue', 'Write tests'])

    await wrapper.findAll('[data-testid="mc-preset"]')[1].trigger('click')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/agent-mission/prompt', {
      source: 'claude', session_id: 'r1', preset: 'write_tests',
    })
    expect(toast.success).toHaveBeenCalledWith('Write tests', 'Claude Code - api')
    expect(wrapper.find('[data-testid="mc-presets"]').exists()).toBe(false)
  })

  it('shows the server refusal verbatim, including a 409', async () => {
    respond()
    apiPost.mockRejectedValueOnce({
      response: { status: 409, data: { error: 'That session is busy', details: 'Wait for it to finish' } },
    })
    const wrapper = await mountOpen()

    await wrapper.find('[data-testid="mc-prompt"]').trigger('click')
    await wrapper.find('[data-testid="mc-preset"]').trigger('click')
    await flushPromises()

    expect(toast.error).toHaveBeenCalledWith('Could not send the prompt', 'That session is busy', 'Wait for it to finish')
  })

  it('summarises what the turn changed and opens a file diff on tap', async () => {
    respond()
    const wrapper = await mountOpen()

    // apiClient.get takes the query object directly (it wraps it in `params`).
    expect(apiGet).toHaveBeenCalledWith('/agent-mission/changes', { source: 'claude', session_id: 'r1' })
    const chip = wrapper.find('[data-testid="mc-changes"]')
    expect(chip.text()).toBe('2 files +120 −8')
    expect(wrapper.find('[data-testid="mc-files"]').exists()).toBe(false)

    await chip.trigger('click')
    expect(wrapper.findAll('[data-testid="mc-file"]')).toHaveLength(2)

    await wrapper.findAll('[data-testid="mc-file"]')[0].trigger('click')
    expect(apiPost).toHaveBeenCalledWith('/agent-mission/open-diff', {
      source: 'claude', session_id: 'r1', path: 'src/a.ts',
    })
  })

  it('hides the changes chip when nothing changed', async () => {
    respond({ success: true, files: [], totals: { files: 0, added: 0, removed: 0 } })
    const wrapper = await mountOpen()

    expect(wrapper.find('[data-testid="mc-changes"]').exists()).toBe(false)
  })
})

describe('DL-145 usage chip and compact', () => {
  const usage = (status: string, pct: number, estimate = true) =>
    ({ cost_usd: 1.236, estimate, context_pct: pct, status }) as any
  const claude = (over: Partial<MissionSession>) =>
    session({ session_id: 'u1', project: 'api', state: 'ready', needs_you: true, can_prompt: true, ...over })

  function respond(rows: MissionSession[]) {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url === '/agent-mission/changes'
        ? { data: { success: true, files: [], totals: { files: 0, added: 0, removed: 0 } } }
        : snapshotResponse(rows)))
  }

  it('shows estimated cost and context on a Claude row', async () => {
    respond([claude({ usage: usage('normal', 72) })])
    const wrapper = await mountOpen()

    const chip = wrapper.find('[data-testid="mc-usage"]')
    expect(chip.text()).toBe('≈$1.24 · ctx 72%')
    expect(chip.classes()).not.toContain('mc-usage-warning')
    expect(chip.attributes('title')).toContain('Estimated')
  })

  it('drops the ≈ for a total Claude reported itself', async () => {
    respond([claude({ usage: usage('normal', 10, false) })])
    const wrapper = await mountOpen()

    expect(wrapper.find('[data-testid="mc-usage"]').text()).toBe('$1.24 · ctx 10%')
  })

  it('colours the chip amber and red from the server status', async () => {
    respond([
      claude({ session_id: 'w', usage: usage('warning', 85) }),
      claude({ session_id: 'c', usage: usage('critical', 97) }),
    ])
    const wrapper = await mountOpen()

    const chips = wrapper.findAll('[data-testid="mc-usage"]')
    expect(chips.map((c) => c.classes().find((k) => k.startsWith('mc-usage-')))).toEqual(
      ['mc-usage-warning', 'mc-usage-critical'])
  })

  it('shows no chip when the row has no usage (non-Claude or unreadable)', async () => {
    respond([claude({ usage: null }), claude({ session_id: 'x', source: 'cursor' })])
    const wrapper = await mountOpen()

    expect(wrapper.find('[data-testid="mc-usage"]').exists()).toBe(false)
  })

  it('offers Compact only when context is filling and posts it for that session', async () => {
    respond([
      claude({ session_id: 'ok', usage: usage('normal', 20) }),
      claude({ session_id: 'hot', usage: usage('warning', 88) }),
    ])
    const wrapper = await mountOpen()

    const buttons = wrapper.findAll('[data-testid="mc-compact"]')
    expect(buttons).toHaveLength(1)
    await buttons[0].trigger('click')
    await flushPromises()

    expect(apiPost).toHaveBeenCalledWith('/agent-mission/compact', { source: 'claude', session_id: 'hot' })
    expect(toast.success).toHaveBeenCalledWith('Compacting context', 'Claude Code - api')
  })

  it('shows the server refusal when compact is not allowed (busy session)', async () => {
    respond([claude({ usage: usage('critical', 96) })])
    apiPost.mockRejectedValueOnce({ response: { status: 409, data: { error: 'That session is busy' } } })
    const wrapper = await mountOpen()

    await wrapper.find('[data-testid="mc-compact"]').trigger('click')
    await flushPromises()

    expect(toast.error).toHaveBeenCalledWith('Could not compact the session', 'That session is busy', undefined)
  })
})

describe('entry points', () => {
  it('the waiting dock offers a Mission Control button that opens it', async () => {
    vi.resetModules()
    const alerts = [{ source: 'claude', message: 'x', project: 'p', cwd: '', ts: 1 }]
    vi.doMock('@/services/agentAlerts', () => ({
      useAgentAlerts: () => ({
        alerts: { value: alerts },
        sourceLabelFor: () => 'Claude Code',
        dismiss: vi.fn(),
      }),
    }))
    const { default: Dock } = await import('@/components/AgentWaitingDock.vue')
    const mission = await import('@/services/missionControl')
    mission.closeMissionControl()

    const wrapper = mount(Dock, { global: { stubs: { Teleport: { template: '<div><slot /></div>' }, Transition: { template: '<div><slot /></div>' } } } })
    await wrapper.find('[data-testid="dock-inbox"]').trigger('click')

    expect(mission.missionControlOpen.value).toBe(true)
    vi.doUnmock('@/services/agentAlerts')
  })

  it('the open_mission_control deck action is a known backend ui_control action', async () => {
    // Guards the contract between the catalog entry and the frontend branch.
    const { readFileSync } = await import('node:fs')
    const { resolve } = await import('node:path')
    const source = readFileSync(resolve(__dirname, '../composables/useButtonActions.ts'), 'utf-8')

    expect(source).toContain("action === 'open_mission_control'")
    expect(source).toContain('openMissionControl()')
  })
})
