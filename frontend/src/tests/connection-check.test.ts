// DL-160: the "Why can't my phone connect?" panel shows the report and runs the one-click fixes.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const fetchCheck = vi.fn()
const updateServerConfig = vi.fn()
const loadServerConfig = vi.fn()
const notify = { success: vi.fn(), error: vi.fn() }

vi.mock('@/services/connectionCheck', async (orig) => ({
  ...(await orig<typeof import('@/services/connectionCheck')>()),
  fetchConnectionCheck: (...a: unknown[]) => fetchCheck(...a),
}))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => ({ updateServerConfig, loadServerConfig }) }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => notify }))

import ConnectionCheck from '@/components/settings/ConnectionCheck.vue'
import { fixPayload } from '@/services/connectionCheck'

const stale = [
  { id: 'lan', status: 'ok', title: 'Phone access is on', detail: 'ok' },
  { id: 'address', status: 'fail', title: 'Saved address 192.168.9.9 is not this computer', detail: 'x',
    fix: { action: 'clear_deck_host', label: 'Clear the override' } },
]
const healthy = [{ id: 'lan', status: 'ok', title: 'Phone access is on', detail: 'ok' }]

const stubs = { FontAwesomeIcon: true }

beforeEach(() => {
  fetchCheck.mockReset().mockResolvedValue(stale)
  updateServerConfig.mockReset().mockResolvedValue(true)
  loadServerConfig.mockReset().mockResolvedValue(undefined)
  notify.success.mockReset(); notify.error.mockReset()
})

describe('fixPayload', () => {
  it('clear → empty override; set → the suggested name', () => {
    expect(fixPayload({ action: 'clear_deck_host', label: '' })).toEqual({ deck_host: '' })
    expect(fixPayload({ action: 'set_deck_host', label: '', value: 'mac.local' })).toEqual({ deck_host: 'mac.local' })
  })
})

describe('ConnectionCheck', () => {
  it('shows nothing until asked, then lists each check with its status', async () => {
    const w = mount(ConnectionCheck, { global: { stubs } })
    expect(w.find('.check-list').exists()).toBe(false)
    await w.find('[data-action="run-check"]').trigger('click')
    await flushPromises()
    expect(w.findAll('.check-item')).toHaveLength(2)
    expect(w.find('[data-check="address"]').classes()).toContain('is-fail')
    expect(w.text()).toContain('192.168.9.9')
  })

  it('the fix saves the override, reloads config and re-runs the check', async () => {
    const w = mount(ConnectionCheck, { global: { stubs } })
    await w.find('[data-action="run-check"]').trigger('click')
    await flushPromises()
    fetchCheck.mockResolvedValue(healthy)
    await w.find('[data-fix="clear_deck_host"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ deck_host: '' })
    expect(loadServerConfig).toHaveBeenCalled()
    expect(notify.success).toHaveBeenCalled()
    expect(w.find('[data-fix]').exists()).toBe(false)
    expect(w.findAll('.check-item')).toHaveLength(1)
  })

  it('says so when the check cannot run', async () => {
    fetchCheck.mockResolvedValue(null)
    const w = mount(ConnectionCheck, { global: { stubs } })
    await w.find('[data-action="run-check"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-testid="check-error"]').exists()).toBe(true)
  })
})
