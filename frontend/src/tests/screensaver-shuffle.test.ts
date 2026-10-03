// DL-133 — Shuffle screensaver type: rotation picker, persisted cadence,
// ScreenSaver wiring and the Settings layout contract (type select first,
// named "Screensaver Type", widgets as the factory default).
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import {
  SAVER_TYPES,
  SHUFFLE_POOL,
  pickNextSaverType,
  saverTypeLabel,
} from '@/services/screensaverTypes'
import { useSettingsStore } from '@/stores/settings'
import { settingsSource } from './helpers/settingsSource'

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('screensaverTypes registry', () => {
  it('offers the four types — widgets first, shuffle last', () => {
    expect(SAVER_TYPES.map(t => t.id)).toEqual(
      ['widgets', 'spectrum', 'stats', 'shuffle'])
  })

  it('the shuffle pool holds real views only — never shuffle itself', () => {
    expect(SHUFFLE_POOL).toEqual(['widgets', 'spectrum', 'stats'])
    expect(SHUFFLE_POOL).not.toContain('shuffle')
  })

  it('pickNextSaverType always lands in the pool and never repeats', () => {
    for (const t of SHUFFLE_POOL) {
      for (let i = 0; i < 40; i++) {
        const next = pickNextSaverType(t)
        expect(next).not.toBe(t)
        expect(SHUFFLE_POOL).toContain(next)
      }
    }
    // A sentinel current ('' — pre-mount) leaves the whole pool open.
    expect(SHUFFLE_POOL).toContain(pickNextSaverType(''))
  })

  it('saverTypeLabel names every type and falls back to widgets', () => {
    expect(saverTypeLabel('widgets')).toBe('Widget dashboard')
    expect(saverTypeLabel('spectrum')).toBe('Spectrum visualizer')
    expect(saverTypeLabel('stats')).toBe('System stats')
    expect(saverTypeLabel('shuffle')).toBe('Shuffle')
    expect(saverTypeLabel('nonsense')).toBe('Widget dashboard')
  })
})

describe('settings: shuffle keys', () => {
  it('defaults to the Widget dashboard with a 5-minute rotation', () => {
    const settings = useSettingsStore()
    expect(settings.screensaverStyle).toBe('widgets')
    expect(settings.screensaverShuffleMinutes).toBe(5)
  })

  it('accepts shuffle as a style and persists the interval', async () => {
    const settings = useSettingsStore()
    settings.screensaverStyle = 'shuffle'
    settings.screensaverShuffleMinutes = 10
    await new Promise(r => setTimeout(r, 0))
    const saved = JSON.parse(localStorage.getItem('vdock_settings') || '{}')
    expect(saved.screensaverStyle).toBe('shuffle')
    expect(saved.screensaverShuffleMinutes).toBe(10)
  })

  it('roundtrips through loadSettings — including a saved shuffle pick', () => {
    const settings = useSettingsStore()
    settings.screensaverStyle = 'shuffle'
    settings.screensaverShuffleMinutes = 30
    settings.saveSettingsLocalOnly()

    setActivePinia(createPinia())
    const fresh = useSettingsStore()
    fresh.loadSettings()
    expect(fresh.screensaverStyle).toBe('shuffle')
    expect(fresh.screensaverShuffleMinutes).toBe(30)
  })

  it('a missing key falls back to the Widget dashboard', () => {
    // Blob written before the style key existed → factory default.
    localStorage.setItem('vdock_settings', JSON.stringify({ screensaverTimeout: 60 }))
    const settings = useSettingsStore()
    settings.loadSettings()
    expect(settings.screensaverStyle).toBe('widgets')
    expect(settings.screensaverShuffleMinutes).toBe(5)
  })
})

describe('ScreenSaver wiring (source contract)', () => {
  const src = readFileSync(
    resolve(__dirname, '../components/ScreenSaver.vue'), 'utf-8')

  it('routes stage selection through the effective (shuffled) style', () => {
    expect(src).toContain("screensaverStyle === 'shuffle'")
    expect(src).toContain('pickNextSaverType')
    expect(src).toContain('effectiveStyle.value === \'spectrum\'')
    expect(src).toContain('effectiveStyle.value === \'stats\'')
  })

  it('the rotation timer is interval-driven and cleared on unmount', () => {
    expect(src).toContain('screensaverShuffleMinutes')
    expect(src).toContain('clearInterval(shuffleTimer)')
  })
})

describe('SettingsView wiring (source contract)', () => {
  const src = settingsSource()

  it('the Screensaver Type select sits in the first, generic panel on the tab', () => {
    // DL-137: type + activation merged into one "General" panel — ss-type
    // and ss-activation are gone, idle delay + try-it moved in.
    const general = src.indexOf('id="ss-general"')
    const spectrum = src.indexOf('id="ss-spectrum"')
    expect(general).toBeGreaterThan(-1)
    expect(spectrum).toBeGreaterThan(-1)
    expect(general).toBeLessThan(spectrum)
    expect(src).not.toContain('id="ss-activation"')
    expect(src).toContain('>Screensaver Type<')
    expect(src).toContain('aria-label="Screensaver type"')
  })

  it('offers the Shuffle option with a rotation interval row', () => {
    expect(src).toContain('value="shuffle"')
    expect(src).toContain('screensaverStyle === \'shuffle\'')
    expect(src).toContain('v-model.number="settingsStore.screensaverShuffleMinutes"')
  })

  it('DL-135: offers "Widgets on the visualizer" for spectrum + shuffle', () => {
    expect(src).toContain('Widgets on the visualizer')
    expect(src).toContain('settingsStore.screensaverSpectrumWidgets')
    // Only offered where it can apply — spectrum directly, or shuffle
    // rotating through spectrum windows.
    expect(src).toContain(
      "settingsStore.screensaverStyle === 'spectrum' || settingsStore.screensaverStyle === 'shuffle'")
    // The widgets-panel note points at the toggle on spectrum, keeps the
    // "not in use" explanation on stats.
    expect(src).toContain("v-if=\"settingsStore.screensaverStyle === 'spectrum'\"")
    expect(src).toContain('overlay the <strong>Spectrum visualizer</strong>')
    expect(src).toContain("v-else-if=\"settingsStore.screensaverStyle === 'stats'\"")
  })
})

describe('SpectrumStage card sizing (source contract)', () => {
  const src = readFileSync(
    resolve(__dirname, '../components/screensaver/SpectrumStage.vue'), 'utf-8')

  it('the now-playing card is sized up but bounded', () => {
    expect(src).toContain('width: min(94vw, 560px)')
    // Art scaled up from the 104px DL-123 card.
    expect(src).toContain('clamp(88px, 15vh, 120px)')
  })
})
