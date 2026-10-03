// DL-032: dashboard font styles (screensaver typography reusable on the
// dashboard) + Screen Saver pane split into Widgets/Settings/Backgrounds
// sub-tabs.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { settingsSource } from './helpers/settingsSource'
import { SECTIONS } from '@/settings/registry'

const settings = readFileSync(resolve(__dirname, '../stores/settings.ts'), 'utf-8')
const appVue = readFileSync(resolve(__dirname, '../App.vue'), 'utf-8')
const mainCss = readFileSync(resolve(__dirname, '../assets/styles/main.css'), 'utf-8')
const settingsView = settingsSource()

describe('dashboard font option', () => {
  it('declares dashboardFont with default + persists it', () => {
    expect(settings).toContain("dashboardFont: 'default'")
    expect(settings).toContain("dashboardFont: 'default' | 'editorial' | 'mono'")
    expect(settings).toContain('dashboardFont.value')
  })

  it('applies the choice on the app root via data-ui-font', () => {
    expect(appVue).toContain(':data-ui-font="settingsStore.dashboardFont"')
  })

  it('styles editorial and mono against dashboard chrome', () => {
    for (const sel of [
      "[data-ui-font='editorial'] .button-label",
      "[data-ui-font='editorial'] .segment-label",
      "[data-ui-font='mono'] .deck-button",
    ]) {
      expect(mainCss).toContain(sel)
    }
    expect(mainCss).toContain("'Instrument Serif'")
    expect(mainCss).toContain("'JetBrains Mono'")
  })

  it('exposes a picker + reset in settings', () => {
    expect(settingsView).toContain('font-style-picker')
    expect(settingsView).toContain('dashboardFontOptions')
    expect(settingsView).toContain('label="Dashboard font"')
  })
})

describe('screensaver page (DL-054 merged panels)', () => {
  it('registers the screensaver page under Appearance', () => {
    const page = SECTIONS.find((s) => s.id === 'appearance')!.pages.find((p) => p.id === 'screensaver')
    expect(page?.panels).toEqual(['ScreensaverPanel'])
  })

  it('keeps widgets, timing and background as anchored panels', () => {
    for (const gate of [
      'id="ss-widgets"',
      'id="ss-general"',
      'id="ss-background"',
    ]) {
      expect(settingsView).toContain(gate)
    }
  })
})
