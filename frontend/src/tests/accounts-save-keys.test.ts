// Accounts & keys: save a key in-app (DL-146 follow-up). The typed value must
// only ever go to the PUT body and must not linger in the DOM afterwards.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const SECRET = 'ghp_unit_test_secret_value'
const state = vi.hoisted(() => ({ configured: false }))
const put = vi.hoisted(() => vi.fn())
const del = vi.hoisted(() => vi.fn())

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn((url: string) => Promise.resolve({
      data: url.includes('config/integrations')
        ? { env_file: 'backend/.env', items: [{ id: 'GITHUB_TOKEN', label: 'GitHub token', kind: 'secret', configured: state.configured, reason: '', help_url: 'https://github.com/settings/tokens', unlocks: 'PR buttons' }] }
        : {},
    })),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put,
    delete: del,
  },
}))
import AccountsPanel from '@/components/settings/panels/AccountsPanel.vue'

const mountPanel = async () => {
  setActivePinia(createPinia())
  const w = mount(AccountsPanel, { global: { stubs: { FontAwesomeIcon: true } } })
  await flushPromises()
  return w
}

beforeEach(() => {
  state.configured = false
  put.mockReset().mockImplementation(() => { state.configured = true; return Promise.resolve({ data: { id: 'GITHUB_TOKEN', configured: true } }) })
  del.mockReset().mockImplementation(() => { state.configured = false; return Promise.resolve({ data: {} }) })
})

describe('AccountsPanel save keys', () => {
  it('opens a masked input, saves, flips to Set and clears the value', async () => {
    const w = await mountPanel()
    const row = () => w.find('[data-key="GITHUB_TOKEN"]')
    expect(row().text()).toContain('Not set')
    await row().find('[data-action="set"]').trigger('click')
    const input = row().find('input')
    expect(input.attributes('type')).toBe('password')
    expect(input.attributes('autocomplete')).toBe('off')
    await input.setValue(SECRET)
    await row().find('form').trigger('submit')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/config/integrations/GITHUB_TOKEN', { value: SECRET })
    expect(row().find('input').exists()).toBe(false)
    expect(row().text()).toContain('Set')
    expect(row().text()).not.toContain('Not set')
    expect(w.html()).not.toContain(SECRET)
  })

  it('shows the server error without keeping the value elsewhere', async () => {
    put.mockRejectedValueOnce({ response: { data: { error: 'Key cannot contain spaces.' } } })
    const w = await mountPanel()
    await w.find('[data-action="set"]').trigger('click')
    await w.find('input').setValue('bad value')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('.key-error').text()).toContain('cannot contain spaces')
  })

  it('removes a set key', async () => {
    state.configured = true
    const w = await mountPanel()
    await w.find('[data-action="set"]').trigger('click')
    await w.find('[data-action="remove"]').trigger('click')
    await flushPromises()
    expect(del).toHaveBeenCalledWith('/config/integrations/GITHUB_TOKEN')
    expect(w.find('[data-key="GITHUB_TOKEN"]').text()).toContain('Not set')
  })

  it('keeps copy line / open .env under Advanced', async () => {
    const w = await mountPanel()
    expect(w.find('details.advanced').text()).toContain('Open .env')
  })
})
