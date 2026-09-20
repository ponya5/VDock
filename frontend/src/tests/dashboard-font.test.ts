// DL-032: dashboard font styles (screensaver typography reusable on the
// dashboard) + Screen Saver pane split into Widgets/Settings/Backgrounds
// sub-tabs.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const settings = readFileSync(resolve(__dirname, '../stores/settings.ts'), 'utf-8')
const appVue = readFileSync(resolve(__dirname, '../App.vue'), 'utf-8')
const mainCss = readFileSync(resolve(__dirname, '../assets/styles/main.css'), 'utf-8')
const settingsView = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

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

describe('screensaver sub-tabs', () => {
  it('declares the three sub-tabs with widgets default', () => {
    expect(settingsView).toContain("screensaverSubTab = ref<'widgets' | 'settings' | 'backgrounds'>('widgets')")
  })

  it('gates every screensaver section on a sub-tab', () => {
    for (const gate of [
      "screensaverSubTab === 'settings'",
      "screensaverSubTab === 'backgrounds'",
      "screensaverSubTab === 'widgets'",
    ]) {
      expect(settingsView).toContain(gate)
    }
  })
})
