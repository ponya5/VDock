// DL-008: one step from "I want my phone" to the QR - save LAN access plus the
// recommended password, restart, and land back on the code.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const serverConfig = ref<any>({ allow_lan: false, require_auth: false, auth_password_set: false, port: 5001, lan_ip: '192.168.0.14' })
const updateServerConfig = vi.hoisted(() => vi.fn())
const loadServerConfig = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ updateServerConfig, loadServerConfig, get serverConfig() { return serverConfig.value } }),
}))
vi.mock('@/composables/useServerConfig', () => ({
  useServerConfig: () => ({ serverConfig, lanUrl: ref(null), setAllowLan: vi.fn() }),
}))
const restart = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
vi.mock('@/composables/useBackendRestart', () => ({
  useBackendRestart: () => ({ restarting: ref(false), error: ref(null), restart }),
}))
vi.mock('@/composables/useHostOs', () => ({ useHostOs: () => ({ hostOs: ref('macos') }) }))
vi.mock('@/services/pairing', () => ({ PAIR_REFRESH_MS: 1e9, buildPairUrl: vi.fn(), requestPairToken: vi.fn() }))
vi.mock('@/api/client', () => ({ default: { get: vi.fn().mockResolvedValue({ data: {} }) } }))

import ConnectPanel from '@/components/settings/panels/ConnectPanel.vue'

function mountPanel() {
  return mount(ConnectPanel, { global: { stubs: { FontAwesomeIcon: true, DeckPasswordForm: true } } })
}

beforeEach(() => {
  setActivePinia(createPinia())
  updateServerConfig.mockReset().mockResolvedValue(true)
  restart.mockClear()
})

describe('one-step phone setup', () => {
  it('saves LAN access with the password, then restarts', async () => {
    const w = mountPanel()
    const [pw, confirm] = w.findAll('.phone-setup-pw input')
    await pw.setValue('deckpass')
    await confirm.setValue('deckpass')
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true, require_auth: true, auth_password: 'deckpass' })
    expect(restart).toHaveBeenCalledOnce()
  })

  it('can skip the password, but never silently', async () => {
    const w = mountPanel()
    await w.find('.phone-setup .btn.link').trigger('click')
    expect(w.text()).toContain('anyone on this Wi-Fi can press your keys')
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true })
  })

  it('refuses a mismatched password without restarting', async () => {
    const w = mountPanel()
    const [pw, confirm] = w.findAll('.phone-setup-pw input')
    await pw.setValue('deckpass')
    await confirm.setValue('other')
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(w.text()).toContain("Passwords don't match")
    expect(updateServerConfig).not.toHaveBeenCalled()
    expect(restart).not.toHaveBeenCalled()
  })
})
