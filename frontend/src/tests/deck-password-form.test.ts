// DL-146 3c: the deck-password form shared by Security and the prompt in Connect.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const updateServerConfig = vi.hoisted(() => vi.fn().mockResolvedValue(true))
vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ updateServerConfig }),
}))
import DeckPasswordForm from '@/components/settings/DeckPasswordForm.vue'

let wrapper: VueWrapper | undefined

beforeEach(() => {
  setActivePinia(createPinia())
  updateServerConfig.mockClear()
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
})

async function fill(w: VueWrapper, pw: string, confirm: string) {
  const [first, second] = w.findAll('input')
  await first.setValue(pw)
  await second.setValue(confirm)
  await w.find('button.primary').trigger('click')
  await flushPromises()
}

describe('DeckPasswordForm', () => {
  it('rejects a short password without calling the server', async () => {
    wrapper = mount(DeckPasswordForm)
    await fill(wrapper, 'abc', 'abc')
    expect(wrapper.text()).toContain('4–128 characters')
    expect(updateServerConfig).not.toHaveBeenCalled()
  })

  it('rejects a mismatch', async () => {
    wrapper = mount(DeckPasswordForm)
    await fill(wrapper, 'secret1', 'secret2')
    expect(wrapper.text()).toContain("don't match")
    expect(updateServerConfig).not.toHaveBeenCalled()
  })

  it('enable mode sets the password and turns authentication on in one request', async () => {
    wrapper = mount(DeckPasswordForm)
    await fill(wrapper, 'secret1', 'secret1')
    expect(updateServerConfig).toHaveBeenCalledWith({ require_auth: true, auth_password: 'secret1' })
    expect(wrapper.emitted('done')).toHaveLength(1)
  })

  it('change mode only replaces the password', async () => {
    wrapper = mount(DeckPasswordForm, { props: { mode: 'change' } })
    await fill(wrapper, 'secret1', 'secret1')
    expect(updateServerConfig).toHaveBeenCalledWith({ auth_password: 'secret1' })
    expect(wrapper.emitted('done')).toHaveLength(1)
  })
})
