// DL-145 - a press: 'menu' live button opens a sheet of the rows its status
// offered; choosing a row re-dispatches the action with that row as `op`.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { reactive } from 'vue'

const executeButtonAction = vi.fn()
const executeAction = vi.fn()
const confirmDialog = vi.fn()
const notify = { success: vi.fn(), error: vi.fn() }

const states: Record<string, any> = reactive({})
const buttonState = {
  states,
  markRunning: vi.fn(),
  markFinished: vi.fn((id: string, r: any) => {
    states[id] = {
      menu: r?.data?.menu,
      panelText: r?.data?.panel_text,
      sublabel: r?.data?.sublabel,
    }
  }),
}

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    executeButtonAction: (...a: unknown[]) => executeButtonAction(...a),
    executeAction: (...a: unknown[]) => executeAction(...a),
  }),
}))
vi.mock('@/stores/buttonState', () => ({ useButtonStateStore: () => buttonState }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => notify }))
vi.mock('@/stores/actionCatalog', () => ({
  useActionCatalogStore: () => ({
    byActionType: { agent_review_changes: { poll_config: { op: 'status' }, poll_seconds: 20 } },
  }),
}))
vi.mock('@/composables/useConfirm', () => ({ confirmDialog: (...a: unknown[]) => confirmDialog(...a) }))

import { chooseLiveMenuItem, closeLiveMenu, liveMenu, openLiveMenu } from '@/services/liveActionMenu'

const button = { id: 'b1', label: 'Review', action: { type: 'agent_review_changes', config: { agent: 'auto' } } } as any
const menu = [{ id: 'open:a.py', label: 'a.py' }, { id: 'push', label: 'Push', confirm: 'Push now?' }]

beforeEach(() => {
  for (const key of Object.keys(states)) delete states[key]
  executeButtonAction.mockReset()
  executeAction.mockReset()
  confirmDialog.mockReset().mockResolvedValue(true)
  notify.success.mockReset()
  notify.error.mockReset()
  buttonState.markRunning.mockClear()
  buttonState.markFinished.mockClear()
  closeLiveMenu()
})

describe('openLiveMenu', () => {
  it('opens with the cached menu and does not fetch', async () => {
    states.b1 = { menu, sublabel: '+3 −1' }
    await openLiveMenu(button)

    expect(executeButtonAction).not.toHaveBeenCalled()
    expect(liveMenu.value?.items).toEqual(menu)
  })

  it('fetches status first when nothing is cached', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'm', data: { badge: '1', menu } })
    await openLiveMenu(button)

    expect(executeButtonAction.mock.calls[0][0].action.config).toEqual({ agent: 'auto', op: 'status' })
    expect(buttonState.markFinished).toHaveBeenCalled()
    expect(liveMenu.value?.items).toEqual(menu)
  })

  it('shows the backend message when the menu is empty', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'No changes this turn', data: { badge: '0' } })
    await openLiveMenu(button)

    expect(liveMenu.value?.items).toEqual([])
    expect(liveMenu.value?.message).toBe('No changes this turn')
  })
})

describe('chooseLiveMenuItem', () => {
  beforeEach(async () => {
    states.b1 = { menu }
    await openLiveMenu(button)
  })

  it('aborts without dispatching when the confirmation is declined', async () => {
    confirmDialog.mockResolvedValue(false)
    await chooseLiveMenuItem(menu[1])

    expect(confirmDialog).toHaveBeenCalledWith({ message: 'Push now?' })
    expect(executeButtonAction).not.toHaveBeenCalled()
    expect(liveMenu.value).not.toBeNull()
  })

  it('dispatches the item id as op after a confirmed prompt, then closes', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'Pushed', data: {} })
    await chooseLiveMenuItem(menu[1])

    expect(executeButtonAction.mock.calls[0][0].action.config).toEqual({ agent: 'auto', op: 'push' })
    expect(notify.success).toHaveBeenCalledWith('Action Executed', 'Pushed')
    expect(liveMenu.value).toBeNull()
  })

  it('keeps the sheet open and shows panel_text from the result', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'Logs', data: { panel_text: 'line 1\nline 2' } })
    await chooseLiveMenuItem(menu[0])

    expect(liveMenu.value?.panelText).toBe('line 1\nline 2')
  })

  it('opens a returned url through the url action', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'ok', data: { url: 'https://example.test/pr/1' } })
    await chooseLiveMenuItem(menu[0])

    expect(executeAction).toHaveBeenCalledWith({ type: 'url', config: { url: 'https://example.test/pr/1' } }, 'b1')
  })

  it('toasts a failure and refreshes the face', async () => {
    executeButtonAction
      .mockResolvedValueOnce({ success: false, message: 'Not a git repository' })
      .mockResolvedValueOnce({ success: true, message: 'm', data: { badge: '0' } })
    await chooseLiveMenuItem(menu[0])

    expect(notify.error).toHaveBeenCalled()
    expect(executeButtonAction.mock.calls[1][0].action.config.op).toBe('status')
  })
})
