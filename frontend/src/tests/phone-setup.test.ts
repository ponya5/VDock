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
const lanUrl = ref<string | null>(null)
vi.mock('@/composables/useServerConfig', () => ({
  useServerConfig: () => ({ serverConfig, lanUrl, setAllowLan: vi.fn() }),
}))
const copyText = vi.hoisted(() => vi.fn().mockResolvedValue(true))
vi.mock('@/utils/copyText', () => ({ copyText }))
const restart = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
vi.mock('@/composables/useBackendRestart', () => ({
  useBackendRestart: () => ({ restarting: ref(false), error: ref(null), restart }),
}))
vi.mock('@/composables/useHostOs', () => ({ useHostOs: () => ({ hostOs: ref('macos') }) }))
const fetchDevices = vi.hoisted(() => vi.fn().mockResolvedValue([]))
const revokeDevice = vi.hoisted(() => vi.fn().mockResolvedValue(true))
const requestPairToken = vi.hoisted(() => vi.fn().mockResolvedValue('tok'))
vi.mock('@/services/pairing', () => ({
  PAIR_REFRESH_MS: 1e9,
  buildPairUrl: (base: string, token: string) => `${base}/?pair=${token}`,
  requestPairToken,
  fetchDevices,
  revokeDevice,
  revokeAllDevices: vi.fn().mockResolvedValue(true),
  timeAgo: () => 'just now',
}))
vi.mock('@/api/client', () => ({ default: { get: vi.fn().mockResolvedValue({ data: {} }) } }))

import ConnectPanel from '@/components/settings/panels/ConnectPanel.vue'
import SecurityPanel from '@/components/settings/panels/SecurityPanel.vue'

function mountPanel() {
  return mount(ConnectPanel, { global: { stubs: { FontAwesomeIcon: true, DeckPasswordForm: true } } })
}

beforeEach(() => {
  setActivePinia(createPinia())
  updateServerConfig.mockReset().mockResolvedValue(true)
  restart.mockClear()
  copyText.mockClear()
  fetchDevices.mockReset().mockResolvedValue([])
  requestPairToken.mockClear()
  lanUrl.value = null
  serverConfig.value = { allow_lan: false, require_auth: false, auth_password_set: false, port: 5001, lan_ip: '192.168.0.14' }
})

const LIVE = { allow_lan: true, require_auth: true, auth_password_set: true, pair_only: true, port: 5001, lan_ip: '192.168.0.14', restart_required: false }

describe('one-step phone setup', () => {
  it('defaults to pair-only: no password to type, then restarts', async () => {
    const w = mountPanel()
    expect(w.find('.phone-setup-pw').exists()).toBe(false)
    expect(w.find('[data-testid="pair-only-note"]').exists()).toBe(true)
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true, pair_only: true })
    expect(restart).toHaveBeenCalledOnce()
  })

  it('saves LAN access with a chosen password, then restarts', async () => {
    const w = mountPanel()
    await w.find('[data-action="toggle-password"]').trigger('click')
    const [pw, confirm] = w.findAll('.phone-setup-pw input')
    await pw.setValue('deckpass')
    await confirm.setValue('deckpass')
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true, require_auth: true, auth_password: 'deckpass' })
    expect(restart).toHaveBeenCalledOnce()
  })

  it('refuses a mismatched password without restarting', async () => {
    const w = mountPanel()
    await w.find('[data-action="toggle-password"]').trigger('click')
    const [pw, confirm] = w.findAll('.phone-setup-pw input')
    await pw.setValue('deckpass')
    await confirm.setValue('other')
    await w.find('[data-action="enable-phone-access"]').trigger('click')
    await flushPromises()
    expect(w.text()).toContain("Passwords don't match")
    expect(updateServerConfig).not.toHaveBeenCalled()
    expect(restart).not.toHaveBeenCalled()
  })

  it('warns before enabling on a Public Windows network', async () => {
    serverConfig.value = { ...serverConfig.value, network_profile: 'public' }
    const w = mountPanel()
    expect(w.find('[data-testid="public-network-setup"]').text()).toContain('Public network')
  })
})

describe('connected phone access (DL-154)', () => {
  it('lists paired devices and revokes one', async () => {
    serverConfig.value = LIVE
    lanUrl.value = 'http://192.168.0.14:5001'
    fetchDevices.mockResolvedValue([{ id: 'd1', label: 'iPhone', paired_at: 1, last_seen: 2, ip: '192.168.0.52' }])
    const w = mountPanel()
    await flushPromises()
    expect(w.find('[data-testid="devices"]').text()).toContain('iPhone')
    await w.find('[data-revoke="d1"]').trigger('click')
    await flushPromises()
    expect(revokeDevice).toHaveBeenCalledWith('d1')
  })

  it('copies a pairing link with its own fresh token', async () => {
    serverConfig.value = LIVE
    lanUrl.value = 'http://192.168.0.14:5001'
    const w = mountPanel()
    await flushPromises()
    requestPairToken.mockClear()
    await w.find('[data-action="copy-link"]').trigger('click')
    await flushPromises()
    expect(requestPairToken).toHaveBeenCalledOnce()
    expect(copyText).toHaveBeenCalledWith('http://192.168.0.14:5001/?pair=tok')
  })

  it('shows the Public-network warning once phone access is live', async () => {
    serverConfig.value = { ...LIVE, network_profile: 'public' }
    lanUrl.value = 'http://192.168.0.14:5001'
    const w = mountPanel()
    await flushPromises()
    expect(w.find('[data-testid="public-network-warning"]').text()).toContain('Tailscale')
  })

  it('offers "Require pairing" on a legacy unprotected deck, under Security (not Connect)', async () => {
    serverConfig.value = { ...LIVE, require_auth: false, auth_password_set: false, pair_only: false }
    expect(mountPanel().find('[data-testid="unprotected-row"]').exists()).toBe(false)
    const w = mount(SecurityPanel, { global: { stubs: { FontAwesomeIcon: true, DeckPasswordForm: true } } })
    await w.find('[data-action="require-pairing"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ pair_only: true })
  })
})
