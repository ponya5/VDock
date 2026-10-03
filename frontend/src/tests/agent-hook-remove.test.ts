// Agent alerts: remove a hook (DL-146 follow-up). Removal needs an explicit
// inline confirmation and must refresh both the chip and the shared setup status.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const state = vi.hoisted(() => ({ installed: true }))
const post = vi.hoisted(() => vi.fn())
const refresh = vi.hoisted(() => vi.fn())
const success = vi.hoisted(() => vi.fn())
const error = vi.hoisted(() => vi.fn())

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({
      data: { agents: { claude: { installed: state.installed, partial: false }, cursor: { installed: false, partial: false } } },
    })),
    post,
  },
}))
vi.mock('@/composables/useSetupStatus', () => ({ useSetupStatus: () => ({ refresh }) }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => ({ success, error }) }))
import AgentAlertsPanel from '@/components/settings/panels/AgentAlertsPanel.vue'

let wrapper: VueWrapper | null = null
const mountPanel = async () => {
  setActivePinia(createPinia())
  wrapper = mount(AgentAlertsPanel, { global: { stubs: { FontAwesomeIcon: true } } })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  state.installed = true
  post.mockReset().mockImplementation(() => { state.installed = false; return Promise.resolve({ data: { success: true, removed: true } }) })
  refresh.mockReset()
  success.mockReset()
  error.mockReset()
})
afterEach(() => { wrapper?.unmount(); wrapper = null })

describe('AgentAlertsPanel remove hook', () => {
  it('asks before removing, then removes, toasts and refreshes status', async () => {
    const w = await mountPanel()
    expect(w.text()).toContain('1 of 4 agents hooked')
    await w.find('[data-action="remove-hook"]').trigger('click')
    expect(post).not.toHaveBeenCalled()
    expect(w.text()).toContain('Remove?')

    await w.find('[data-action="confirm-remove-hook"]').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/agent-events/uninstall-hook', null, { params: { agent: 'claude' } })
    expect(success).toHaveBeenCalledWith('Hook removed', expect.any(String))
    expect(refresh).toHaveBeenCalled()
    expect(w.find('[data-action="remove-hook"]').exists()).toBe(false)
    expect(w.text()).toContain('0 of 4 agents hooked')
  })

  it('cancel leaves the hook alone', async () => {
    const w = await mountPanel()
    await w.find('[data-action="remove-hook"]').trigger('click')
    await w.find('[data-action="cancel-remove-hook"]').trigger('click')
    expect(post).not.toHaveBeenCalled()
    expect(w.find('[data-action="remove-hook"]').exists()).toBe(true)
  })

  it('shows the server error and keeps the hook marked installed', async () => {
    post.mockRejectedValueOnce({ response: { data: { error: 'settings.json is not valid JSON' } } })
    const w = await mountPanel()
    await w.find('[data-action="remove-hook"]').trigger('click')
    await w.find('[data-action="confirm-remove-hook"]').trigger('click')
    await flushPromises()
    expect(error).toHaveBeenCalledWith('Hook removal failed', 'settings.json is not valid JSON')
    expect(w.text()).toContain('1 of 4 agents hooked')
    expect(w.find('[data-action="remove-hook"]').exists()).toBe(true)
  })

  it('offers no remove button for an agent that is not installed', async () => {
    const w = await mountPanel()
    await w.find('select[aria-label="Agent to hook"]').setValue('cursor')
    expect(w.find('[data-action="remove-hook"]').exists()).toBe(false)
  })
})
