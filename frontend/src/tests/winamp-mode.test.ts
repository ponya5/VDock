// DL-136 — Winamp player mode: persisted playerMode key, DashboardView swap
// wiring + portrait exemption, and the WinampPlayer component contract
// (transport dispatch, collapsible EQ, marquee from the now-playing feed).
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const executeAction = vi.fn().mockResolvedValue({ success: true })
const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn().mockResolvedValue({ data: { success: true, available: true, track: null } })

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
    isConnected: () => false,
    connect: vi.fn(),
    executeAction: (...args: unknown[]) => executeAction(...args),
    broadcastSettingsChange: vi.fn(),
  },
}))

vi.mock('@/api/client', () => ({
  default: { get: (...args: unknown[]) => apiGet(...args) },
}))

import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import WinampPlayer from '@/components/WinampPlayer.vue'

const dashboardView = readFileSync(
  resolve(__dirname, '../views/DashboardView.vue'), 'utf-8')
const backendAllowlist = readFileSync(
  resolve(__dirname, '../../../backend/routes/user_settings.py'), 'utf-8')

function mountPlayer() {
  return mount(WinampPlayer, {
    global: { stubs: { FontAwesomeIcon: true } },
  })
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  // NB: socketHandlers is NOT cleared — services register their socket
  // listeners once per module lifetime (init guards), so clearing the map
  // would orphan them while the guard says "already subscribed".
  executeAction.mockClear()
  apiGet.mockClear()
})

describe('playerMode setting', () => {
  it('defaults to deck and round-trips through the payload', () => {
    const settings = useSettingsStore()
    expect(SETTINGS_DEFAULTS.playerMode).toBe('deck')
    expect(settings.playerMode).toBe('deck')
    settings.playerMode = 'winamp'
    settings.playerMode = 'deck'
  })

  it('is allowlisted server-side so the panel follows the desktop', () => {
    expect(backendAllowlist).toContain("'playerMode'")
  })
})

describe('dashboard wiring', () => {
  it('renders WinampPlayer instead of the deck chrome in winamp mode', () => {
    expect(dashboardView).toContain("playerMode === 'winamp'")
    expect(dashboardView).toContain('<WinampPlayer')
    expect(dashboardView).toContain('@exit="exitWinampMode"')
    expect(dashboardView).toContain("settingsStore.playerMode = 'deck'")
  })

  it('exempts winamp mode from the portrait rotate gate', () => {
    expect(dashboardView).toContain('portrait-allowed=')
    expect(dashboardView).toMatch(/portrait-allowed="[^"]*winampMode/)
  })
})

describe('WinampPlayer', () => {
  it('mounts the classic chrome: titlebar, LCD, transport, toggles', () => {
    const w = mountPlayer()
    expect(w.find('.win-title-text').text()).toBe('WINAMP')
    expect(w.find('.win-lcd-time').exists()).toBe(true)
    expect(w.find('.win-analyzer').exists()).toBe(true)
    expect(w.find('.win-marquee-text').exists()).toBe(true)
    expect(w.findAll('.win-transport .win-btn').length).toBe(5)
    w.unmount()
  })

  it('dispatches real media actions from the transport row', async () => {
    const w = mountPlayer()
    const btns = w.findAll('.win-transport .win-btn')
    await btns[0].trigger('click') // prev
    await btns[1].trigger('click') // play/pause
    await btns[2].trigger('click') // stop
    await btns[3].trigger('click') // next
    const actions = executeAction.mock.calls
      .map(c => c[0].config.action)
      .filter((a: string) => a.startsWith('media_'))
    expect(actions).toEqual([
      'media_previous', 'media_play_pause', 'media_stop', 'media_next',
    ])
    w.unmount()
  })

  it('emits exit from the close and eject controls', async () => {
    const w = mountPlayer()
    await w.find('.win-tb-close').trigger('click')
    await w.find('.win-btn-eject').trigger('click')
    expect(w.emitted('exit')!.length).toBe(2)
    w.unmount()
  })

  it('the EQ button expands/collapses the equalizer', async () => {
    const w = mountPlayer()
    expect(w.find('.winamp-playlist').exists()).toBe(false)
    expect(w.find('.winamp-eq').exists()).toBe(false)
    const eqBtn = w.findAll('.win-title-btns .win-tb')[0]
    await eqBtn.trigger('click') // EQ
    expect(w.find('.winamp-eq').exists()).toBe(true)
    expect(w.findAll('.win-eq-slider').length).toBe(11) // preamp + 10 bands
    expect(w.find('.win-eq-switches .win-tb.lit').exists()).toBe(true) // ON lit
    await eqBtn.trigger('click') // collapse
    expect(w.find('.winamp-eq').exists()).toBe(false)
    w.unmount()
  })

  it('the marquee lists the now-playing track, LCD ticks', async () => {
    const w = mountPlayer()
    const emit = socketHandlers.get('now_playing')
    expect(emit).toBeDefined()
    emit!({ playing: true, title: 'Echo', artist: 'Crusher-P', source_app: 'spotify.exe', site: 'spotify', duration_s: 230, position_s: 51, has_art: false, ts: 1 })
    await w.vm.$nextTick()
    expect(w.find('.win-marquee-text').text()).toContain('Crusher-P - Echo')
    expect(w.find('.win-marquee-text').text()).toContain('(3:50)')
    expect(w.find('.win-lcd-time').text()).toMatch(/\d+:\d{2}/)
    w.unmount()
  })
})
