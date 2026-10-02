// DL-144 - pressing a GitHub widget runs it once and then opens the page its
// data points at (latest CI run, PR list). Other buttons are untouched.
import { describe, it, expect, beforeEach, vi } from 'vitest'

const executeButtonAction = vi.fn()
const executeAction = vi.fn()
const markRunning = vi.fn()
const markFinished = vi.fn()
const notify = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    currentProfile: null, currentScene: null, currentPage: null,
    executeButtonAction: (...a: unknown[]) => executeButtonAction(...a),
    executeAction: (...a: unknown[]) => executeAction(...a),
  }),
}))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => ({}) }))
vi.mock('@/stores/profiles', () => ({ useProfilesStore: () => ({}) }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => notify }))
vi.mock('@/stores/actionCatalog', () => ({ useActionCatalogStore: () => ({ displayOnlyTypes: new Set<string>() }) }))
vi.mock('@/stores/buttonState', () => ({
  useButtonStateStore: () => ({ markRunning, markFinished, states: {} }),
}))
vi.mock('@/composables/useConfirm', () => ({ confirmDialog: vi.fn() }))

import { useButtonActions } from '@/composables/useButtonActions'
import { missionControlOpen, closeMissionControl } from '@/services/missionControl'

const button = (type: string, config: Record<string, unknown> = {}) =>
  ({ id: 'b1', action: { type, config } }) as any

beforeEach(() => {
  executeButtonAction.mockReset()
  executeAction.mockReset()
  markRunning.mockReset()
  markFinished.mockReset()
  Object.values(notify).forEach((fn) => fn.mockReset())
  closeMissionControl()
})

async function press(b: any) {
  useButtonActions().handleButtonClick(b)
  await vi.waitFor(() => expect(markFinished).toHaveBeenCalled())
  await Promise.resolve()
}

describe('widget press', () => {
  it('opens the latest run after a CI widget refresh', async () => {
    executeButtonAction.mockResolvedValue({
      success: true, message: 'main: failure',
      data: { badge: 'x', status: 'critical', url: 'https://github.com/me/app/actions/runs/9' },
    })

    await press(button('gh_widget_ci'))

    expect(executeAction).toHaveBeenCalledWith(
      { type: 'url', config: { url: 'https://github.com/me/app/actions/runs/9' } }, 'b1')
  })

  it('opens the PR list for the PR widget', async () => {
    executeButtonAction.mockResolvedValue({
      success: true, message: '2 open', data: { badge: '2', url: 'https://github.com/me/app/pulls' },
    })

    await press(button('gh_widget_prs'))

    expect(executeAction).toHaveBeenCalledWith(
      { type: 'url', config: { url: 'https://github.com/me/app/pulls' } }, 'b1')
  })

  it('does not open anything when the widget failed (e.g. no token)', async () => {
    executeButtonAction.mockResolvedValue({
      success: false, message: 'GitHub token missing', data: { badge: '!', url: 'https://github.com/x' },
    })

    await press(button('gh_widget_ci'))

    expect(executeAction).not.toHaveBeenCalled()
  })

  it('leaves ordinary buttons alone even if their result carries a url', async () => {
    executeButtonAction.mockResolvedValue({ success: true, message: 'ok', data: { url: 'https://x.test' } })

    await press(button('gh_pr_list'))

    expect(executeAction).not.toHaveBeenCalled()
  })
})

describe('Mission Control deck action', () => {
  it('opens the modal without calling the backend', () => {
    useButtonActions().handleButtonClick(button('ui_control', { action: 'open_mission_control' }))

    expect(missionControlOpen.value).toBe(true)
    expect(executeButtonAction).not.toHaveBeenCalled()
  })
})
