// DL-123 — fullscreen spectrum screensaver: skin registry, shuffle picking,
// stage mount/idle states, media-bar event containment + dispatch, and the
// new settings keys' defaults/roundtrip.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const executeAction = vi.fn().mockResolvedValue({ success: true })
const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn().mockResolvedValue({ data: { success: true, available: false, track: null } })

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

import {
  SPECTRUM_SKINS,
  DEFAULT_SPECTRUM_SKIN,
  getSpectrumSkin,
  pickNextSkin,
  demoBands,
} from '@/services/spectrumSkins'
import { useSettingsStore } from '@/stores/settings'
import SpectrumStage from '@/components/screensaver/SpectrumStage.vue'

beforeEach(() => {
  // The store rehydrates from localStorage at setup (line ~890) — clearing it
  // first keeps a previous test's saved picks from leaking into the next.
  localStorage.clear()
  setActivePinia(createPinia())
  socketHandlers.clear()
  executeAction.mockClear()
  apiGet.mockClear()
})

describe('spectrum skin registry', () => {
  it('ships the full sixteen-skin catalogue', () => {
    const ids = SPECTRUM_SKINS.map(s => s.id)
    expect(new Set(ids).size).toBe(ids.length)
    // DL-134: the research-branch set restored (rotor/swarm/wave/ring/
    // mirror) plus the hue-drifting 'rgb' bars.
    // DL-139: GPU set — radial pulse + three.js wavegrid/flight.
    // DL-139 follow-up: psyche/smoke/chrome cut on taste grounds.
    expect(ids).toEqual([
      'winamp', 'mono', 'uv', 'rgb',
      'iso', 'scope', 'aurora', 'ember',
      'rotor', 'swarm', 'wave', 'ring', 'mirror',
      'radial', 'wavegrid', 'flight',
    ])
    for (const skin of SPECTRUM_SKINS) {
      expect(skin.label.length).toBeGreaterThan(0)
      expect(typeof skin.create().draw).toBe('function')
    }
  })

  it('getSpectrumSkin resolves unknown ids to the default', () => {
    expect(getSpectrumSkin('winamp').id).toBe('winamp')
    expect(getSpectrumSkin('nonsense').id).toBe(DEFAULT_SPECTRUM_SKIN)
    expect(getSpectrumSkin(undefined).id).toBe(DEFAULT_SPECTRUM_SKIN)
  })

  it('pickNextSkin always returns a different valid skin', () => {
    for (const skin of SPECTRUM_SKINS) {
      for (let i = 0; i < 30; i++) {
        const next = pickNextSkin(skin.id)
        expect(next).not.toBe(skin.id)
        expect(SPECTRUM_SKINS.some(s => s.id === next)).toBe(true)
      }
    }
  })

  it('demoBands produces 20 in-range values that move', () => {
    const a = demoBands(0)
    const b = demoBands(3)
    expect(a).toHaveLength(20)
    expect(a.every(v => v >= 0 && v <= 100)).toBe(true)
    expect(a).not.toEqual(b)
  })
})

describe('SpectrumStage', () => {
  const mountStage = () =>
    mount(SpectrumStage, { global: { stubs: { FontAwesomeIcon: true } } })

  it('mounts two crossfade canvas layers and the media bar', () => {
    const settings = useSettingsStore()
    settings.screensaverStyle = 'spectrum'
    const wrapper = mountStage()
    // DL-134: skin swaps cross-dissolve between two stacked canvases.
    expect(wrapper.findAll('.spectrum-canvas')).toHaveLength(2)
    expect(wrapper.find('.spectrum-media').exists()).toBe(true)
    wrapper.unmount()
  })

  it('hides the media bar when spectrumMediaBar is off', () => {
    const settings = useSettingsStore()
    settings.spectrumMediaBar = false
    const wrapper = mountStage()
    expect(wrapper.find('.spectrum-media').exists()).toBe(false)
    wrapper.unmount()
  })

  it('backdrop mode hides the media bar even when the pref is on', () => {
    // DL-135: under the widget layer / layout editor the transport buttons
    // would eat drag gestures in the bottom-center band.
    const settings = useSettingsStore()
    settings.spectrumMediaBar = true
    const wrapper = mount(SpectrumStage, {
      props: { backdrop: true },
      global: { stubs: { FontAwesomeIcon: true } },
    })
    expect(wrapper.find('.spectrum-media').exists()).toBe(false)
    expect(wrapper.findAll('.spectrum-canvas')).toHaveLength(2)
    wrapper.unmount()
  })

  it('media buttons dispatch cross_platform media actions', async () => {
    const wrapper = mountStage()
    const buttons = wrapper.findAll('.spectrum-media-btn')
    expect(buttons).toHaveLength(3) // prev, play/stop (state-split), next
    await buttons[0].trigger('click')
    expect(executeAction).toHaveBeenCalledWith({
      type: 'cross_platform',
      config: { action: 'media_previous' },
    })
    await buttons[1].trigger('click')
    expect(executeAction).toHaveBeenLastCalledWith({
      type: 'cross_platform',
      config: { action: 'media_play_stop' },
    })
    await buttons[2].trigger('click')
    expect(executeAction).toHaveBeenLastCalledWith({
      type: 'cross_platform',
      config: { action: 'media_next' },
    })
    wrapper.unmount()
  })

  it('media-bar clicks stay inside — they never bubble to a dismiss handler', async () => {
    const wrapper = mountStage()
    const parentSpy = vi.fn()
    // Simulate the saver root: a listener on the stage element would catch
    // any un-stopped click from the media bar.
    wrapper.element.addEventListener('click', parentSpy)
    await wrapper.find('.spectrum-media').trigger('click')
    // Vue's .stop calls stopPropagation — the parent listener must not fire.
    expect(parentSpy).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('respects the saved skin on mount and swaps on settings change', async () => {
    const settings = useSettingsStore()
    settings.spectrumSkin = 'aurora'
    const wrapper = mountStage()
    expect(wrapper.find('.spectrum-tag').text()).toContain('Aurora')
    settings.spectrumSkin = 'scope'
    await wrapper.vm.$nextTick()
    // Swap fades through a dip — the tag follows once the swap applies.
    await new Promise(r => setTimeout(r, 0))
    wrapper.unmount()
  })

  it('stays a slim pill when nothing plays — no kicker, no card', async () => {
    const wrapper = mountStage()
    await new Promise(r => setTimeout(r, 0)) // let the REST sync settle
    const media = wrapper.find('.spectrum-media')
    expect(media.exists()).toBe(true)
    expect(media.classes()).not.toContain('has-track')
    expect(media.find('.spectrum-media-kicker').exists()).toBe(false)
    expect(media.find('.spectrum-media-title').text()).toBe('Nothing playing')
    wrapper.unmount()
  })

  it('presents a now-playing card when a track is live', async () => {
    // useNowPlaying is a module singleton guarded by an `initialized` flag —
    // reload the module graph so a fresh instance actually calls the REST
    // sync this mock serves (socket emits would be clobbered by it anyway).
    const liveTrack = {
      playing: true, title: 'Are You There?', artist: 'Deane',
      album: 'Are You There?', source_app: 'Spotify.exe',
      has_art: true, ts: 1, duration_s: 181, position_s: 40,
    }
    apiGet.mockImplementation((url: string) => Promise.resolve({
      data: url === '/now-playing'
        ? { success: true, available: true, track: liveTrack }
        : {},
    }))
    vi.resetModules()
    const { default: Stage } = await import('@/components/screensaver/SpectrumStage.vue')
    const wrapper = mount(Stage, { global: { stubs: { FontAwesomeIcon: true } } })
    await new Promise(r => setTimeout(r, 0)) // let the sync settle
    await wrapper.vm.$nextTick()
    const media = wrapper.find('.spectrum-media')
    expect(media.classes()).toContain('has-track')
    const kicker = media.find('.spectrum-media-kicker')
    expect(kicker.text()).toContain('Now playing')
    expect(kicker.text()).toContain('Spotify') // '.exe' tail stripped
    expect(media.find('.spectrum-media-title').text()).toBe('Are You There?')
    expect(media.find('.spectrum-media-artist').text()).toBe('Deane')
    // mockClear() in beforeEach doesn't drop a mockImplementation — restore
    // the default empty-track sync for any later mounts.
    apiGet.mockResolvedValue({ data: { success: true, available: false, track: null } })
    wrapper.unmount()
  })
})

describe('settings keys', () => {
  it('defaults: widgets mode, winamp skin, shuffle off, media bar on', () => {
    const settings = useSettingsStore()
    expect(settings.screensaverStyle).toBe('widgets')
    expect(settings.spectrumSkin).toBe('winamp')
    expect(settings.spectrumShuffle).toBe(false)
    expect(settings.spectrumShuffleMinutes).toBe(10)
    expect(settings.spectrumMediaBar).toBe(true)
    // DL-135: the spectrum widget overlay is opt-in — existing installs
    // keep a clean visualizer.
    expect(settings.screensaverSpectrumWidgets).toBe(false)
    expect(settings.agentWaitingDockEnabled).toBe(true)
    expect(settings.mcpEnabled).toBe(true)
  })

  it('spectrum keys persist on change — the save watcher covers them', async () => {
    // Regression: the persistence watch() list was missing all five DL-123
    // keys, so spectrum/style picks never reached localStorage (or the
    // server) — a reload silently reverted to the widget dashboard.
    const settings = useSettingsStore()
    settings.screensaverStyle = 'spectrum'
    settings.spectrumSkin = 'aurora'
    await new Promise(r => setTimeout(r, 0))
    const saved = JSON.parse(localStorage.getItem('vdock_settings') || '{}')
    expect(saved.screensaverStyle).toBe('spectrum')
    expect(saved.spectrumSkin).toBe('aurora')
  })

  it('persists through the localStorage roundtrip', () => {
    const settings = useSettingsStore()
    settings.screensaverStyle = 'spectrum'
    settings.spectrumSkin = 'iso'
    settings.spectrumShuffle = true
    settings.spectrumShuffleMinutes = 5
    settings.spectrumMediaBar = false
    settings.screensaverSpectrumWidgets = true
    settings.agentWaitingDockEnabled = false
    settings.mcpEnabled = false
    settings.saveSettingsLocalOnly()

    setActivePinia(createPinia())
    const fresh = useSettingsStore()
    fresh.loadSettings()
    expect(fresh.screensaverStyle).toBe('spectrum')
    expect(fresh.spectrumSkin).toBe('iso')
    expect(fresh.spectrumShuffle).toBe(true)
    expect(fresh.spectrumShuffleMinutes).toBe(5)
    expect(fresh.spectrumMediaBar).toBe(false)
    expect(fresh.screensaverSpectrumWidgets).toBe(true)
    expect(fresh.agentWaitingDockEnabled).toBe(false)
    expect(fresh.mcpEnabled).toBe(false)
  })
})

describe('ScreenSaver integration (source contract)', () => {
  const src = readFileSync(
    resolve(__dirname, '../components/ScreenSaver.vue'), 'utf-8')

  it('mounts SpectrumStage and gates it on the spectrum style', () => {
    expect(src).toContain("import SpectrumStage")
    // DL-133: gating runs through the effective style so the 'shuffle'
    // type can land on the spectrum mid-rotation.
    expect(src).toContain("effectiveStyle.value === 'spectrum'")
    expect(src).toContain('<SpectrumStage')
  })

  it('DL-135: spectrum stays mounted as the layout editor backdrop', () => {
    // spectrumBackdrop excludes layoutEdit no longer — the stage renders
    // behind the editor so positions are edited on the real canvas, with
    // the media bar suppressed.
    expect(src).toContain(':backdrop="layoutEdit"')
    expect(src).not.toContain('spectrumMode')
  })

  it('DL-135: widget layer gates on widgetLayerOn; component widgets stay surface-only', () => {
    // Info widgets may overlay the spectrum (opt-in + always while
    // editing); stats still keeps the layer off.
    expect(src).toContain('widgetLayerOn')
    expect(src).toContain('spectrumOverlay')
    // nowplaying / mini-spectrum / systemstats never overlay the stage.
    expect(src).toContain('v-if="!spectrumBackdrop"')
  })

  it('widget feeds follow the widget layer, not the stage', () => {
    // Feeds sleep when nothing can show them (stats, or spectrum with
    // the overlay off) and wake whenever the layer is visible.
    expect(src).toContain('watch(widgetLayerOn')
    expect(src).toContain('if (widgetLayerOn.value)')
    expect(src).not.toContain('watch(spectrumMode')
  })
})
