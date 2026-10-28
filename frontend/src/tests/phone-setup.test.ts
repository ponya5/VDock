// One switch for phone access, no automatic restart, QR + devices under Security.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const serverConfig = ref<any>({})
const updateServerConfig = vi.hoisted(() => vi.fn())
const loadServerConfig = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ updateServerConfig, loadServerConfig, get serverConfig() { return serverConfig.value } }),
}))
const lanUrl = ref<string | null>(null)
vi.mock('@/composables/useServerConfig', async (orig) => {
  const real: any = await orig()
  return {
    useServerConfig: () => ({ ...real.useServerConfig(), serverConfig, lanUrl }),
  }
})
const copyText = vi.hoisted(() => vi.fn().mockResolvedValue(true))
vi.mock('@/utils/copyText', () => ({ copyText }))
const restart = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))
vi.mock('@/composables/useBackendRestart', () => ({
  useBackendRestart: () => ({ restarting: ref(false), error: ref(null), restart }),
}))
vi.mock('@/composables/useHostOs', () => ({ useHostOs: () => ({ hostOs: ref('macos') }) }))
const fetchDevices = vi.hoisted(() => vi.fn().mockResolvedValue([]))
const revokeDevice = vi.hoisted(() => vi.fn().mockResolvedValue(true))
const renameDevice = vi.hoisted(() => vi.fn().mockResolvedValue(true))
const requestPairToken = vi.hoisted(() => vi.fn().mockResolvedValue('tok'))
vi.mock('@/services/pairing', () => ({
  PAIR_REFRESH_MS: 1e9,
  buildPairUrl: (base: string, token: string) => `${base}/?pair=${token}`,
  requestPairToken,
  fetchDevices,
  renameDevice,
  revokeDevice,
  revokeAllDevices: vi.fn().mockResolvedValue(true),
  timeAgo: () => 'just now',
}))
vi.mock('@/api/client', () => ({ default: { get: vi.fn().mockResolvedValue({ data: {} }) } }))

import PortsPanel from '@/components/settings/panels/PortsPanel.vue'
import SecurityPanel from '@/components/settings/panels/SecurityPanel.vue'

const stubs = { FontAwesomeIcon: true, DeckPasswordForm: true }
const mountPorts = () => mount(PortsPanel, { global: { stubs } })
const mountSecurity = () => mount(SecurityPanel, { global: { stubs } })

const OFF = { allow_lan: false, require_auth: false, auth_password_set: false, port: 5001, lan_ip: '192.168.0.14', restart_required: false }
const LIVE = { ...OFF, allow_lan: true, require_auth: true, auth_password_set: true, pair_only: true }

beforeEach(() => {
  setActivePinia(createPinia())
  updateServerConfig.mockReset().mockResolvedValue(true)
  restart.mockClear()
  copyText.mockClear()
  fetchDevices.mockReset().mockResolvedValue([])
  renameDevice.mockClear()
  requestPairToken.mockClear()
  lanUrl.value = null
  serverConfig.value = OFF
})

describe('phone access switch (Network & ports)', () => {
  it('turns on with pairing as the default protection and does NOT restart by itself', async () => {
    const w = mountPorts()
    await w.find('.switch input').setValue(true)
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true, pair_only: true })
    expect(restart).not.toHaveBeenCalled()
  })

  it('re-enables auth instead of pair-only when a password already exists', async () => {
    serverConfig.value = { ...OFF, auth_password_set: true }
    await mountPorts().find('.switch input').setValue(true)
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ allow_lan: true, require_auth: true })
  })

  it('shows the restart prompt only when the bind is out of date', async () => {
    expect(mountPorts().find('[data-testid="restart-required"]').exists()).toBe(false)
    serverConfig.value = { ...LIVE, restart_required: true }
    const w = mountPorts()
    expect(w.find('[data-testid="restart-required"]').text()).toContain('Restart VDock now')
    await w.find('[data-testid="restart-required"] button').trigger('click')
    expect(restart).toHaveBeenCalledOnce()
  })

  it('saves the host without a restart', async () => {
    const w = mountPorts()
    await w.find('input[aria-label="Host address"]').setValue('deck.local')
    await w.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ deck_host: 'deck.local' })
    expect(restart).not.toHaveBeenCalled()
  })

  it('warns on a Public Windows network once phone access is on', async () => {
    serverConfig.value = { ...LIVE, network_profile: 'public' }
    lanUrl.value = 'http://192.168.0.14:5001'
    const w = mountPorts()
    await flushPromises()
    expect(w.find('[data-testid="public-network-warning"]').text()).toContain('Tailscale')
  })
})

describe('Security & pairing', () => {
  it('points to the switch while phone access is off', () => {
    expect(mountSecurity().find('[data-testid="phone-off"]').exists()).toBe(true)
  })

  it('lists paired devices, renames one and revokes one', async () => {
    serverConfig.value = LIVE
    lanUrl.value = 'http://192.168.0.14:5001'
    fetchDevices.mockResolvedValue([{ id: 'd1', label: 'iPhone', paired_at: 1, last_seen: 2, ip: '192.168.0.52' }])
    const w = mountSecurity()
    await flushPromises()
    expect(w.find('[data-testid="devices"]').text()).toContain('iPhone')
    await w.find('[data-rename="d1"]').trigger('click')
    await w.find('.device-item input').setValue('Dan phone')
    await w.find('.device-item .btn.primary').trigger('click')
    await flushPromises()
    expect(renameDevice).toHaveBeenCalledWith('d1', 'Dan phone')
    await w.find('[data-revoke="d1"]').trigger('click')
    await flushPromises()
    expect(revokeDevice).toHaveBeenCalledWith('d1')
  })

  it('copies a pairing link with its own fresh token', async () => {
    serverConfig.value = LIVE
    lanUrl.value = 'http://192.168.0.14:5001'
    const w = mountSecurity()
    await flushPromises()
    requestPairToken.mockClear()
    await w.find('[data-action="copy-link"]').trigger('click')
    await flushPromises()
    expect(requestPairToken).toHaveBeenCalledOnce()
    expect(copyText).toHaveBeenCalledWith('http://192.168.0.14:5001/?pair=tok')
  })

  it('offers "Require pairing" on a legacy unprotected deck', async () => {
    serverConfig.value = { ...LIVE, require_auth: false, auth_password_set: false, pair_only: false }
    const w = mountSecurity()
    await w.find('[data-action="require-pairing"]').trigger('click')
    await flushPromises()
    expect(updateServerConfig).toHaveBeenCalledWith({ pair_only: true })
  })
})
