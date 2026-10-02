import { describe, it, expect, beforeEach, vi } from 'vitest'

// Auto-focus: when an agent newly starts waiting (idle after a prompt, or a
// permission dialog) the deck jumps to that agent's scene — once per
// waiting episode, never on page load, never while editing.

type Handler = (payload: unknown) => void
const handlers: Record<string, Handler> = {}

const setScene = vi.fn()
const dashboard = {
  isEditMode: false,
  currentProfile: { scenes: [{ name: 'Media' }, { name: 'Claude Code' }, { name: 'Cursor' }] },
  setScene,
}
const settings = { agentAlertsEnabled: true, agentAutoFocusScene: true }

vi.mock('@/api/socket', () => ({
  default: { on: (event: string, cb: Handler) => { handlers[event] = cb } },
}))
vi.mock('@/stores/dashboard', () => ({ useDashboardStore: () => dashboard }))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => settings }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => ({ info: vi.fn(), error: vi.fn() }) }))

import { initTriggerEvents } from '@/services/triggerEvents'

const ready = (prompted = true) => ({ state: 'ready', prompted })
const working = { state: 'working', prompted: true }

function broadcast(states: Record<string, unknown>) {
  handlers.agent_state({ states })
}

describe('agent auto-focus', () => {
  beforeEach(() => {
    setScene.mockClear()
    dashboard.isEditMode = false
    settings.agentAlertsEnabled = true
    settings.agentAutoFocusScene = true
  })

  it('records who is already waiting on the first broadcast without jumping', () => {
    initTriggerEvents()
    broadcast({ cursor: ready() })
    expect(setScene).not.toHaveBeenCalled()
  })

  it('jumps to the scene when an agent starts waiting', () => {
    broadcast({ cursor: working })
    broadcast({ cursor: ready() })
    expect(setScene).toHaveBeenCalledTimes(1)
    expect(setScene).toHaveBeenCalledWith(2)
  })

  it('does not jump again for the same waiting episode', () => {
    broadcast({ cursor: working })
    broadcast({ cursor: ready() })
    setScene.mockClear()
    broadcast({ cursor: ready(), claude: working })
    expect(setScene).not.toHaveBeenCalled()
  })

  it('jumps on a permission prompt', () => {
    broadcast({ claude: working })
    broadcast({ claude: { state: 'permission', prompted: true } })
    expect(setScene).toHaveBeenCalledWith(1)
  })

  it('ignores an idle session that was never prompted', () => {
    broadcast({ claude: working })
    broadcast({ claude: ready(false) })
    expect(setScene).not.toHaveBeenCalled()
  })

  it('stays put when the setting is off', () => {
    settings.agentAutoFocusScene = false
    broadcast({ cursor: working })
    broadcast({ cursor: ready() })
    expect(setScene).not.toHaveBeenCalled()
  })

  it('stays put while editing the deck', () => {
    dashboard.isEditMode = true
    broadcast({ cursor: working })
    broadcast({ cursor: ready() })
    expect(setScene).not.toHaveBeenCalled()
  })
})
