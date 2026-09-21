// DL-036: Weather location moved to screensaver Widgets; Logs viewer
// redesigned as a full-height split layout with toolbar + status bar.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const view = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

describe('weather location move', () => {
  it('tab is renamed to Integrations and header drops widget copy', () => {
    expect(view).toContain("name: 'Integrations'")
    expect(view).not.toContain('Widgets & Integration')
  })

  it('location controls live inside the weather widget detail (DL-054)', () => {
    // DL-054 merged the widgets/settings/backgrounds sub-tabs into one
    // screensaver page; the location select sits inside the weather widget's
    // expanding detail row, gated on the widgets panel of that page.
    const idx = view.indexOf('weatherLocationMode')
    expect(idx).toBeGreaterThan(-1)
    // the field lives in the weather widget's expanding detail row, which is
    // inside the ss-widgets panel
    const panelIdx = view.indexOf('id="ss-widgets"')
    expect(panelIdx).toBeGreaterThan(-1)
    expect(panelIdx).toBeLessThan(idx)
    const before = view.slice(Math.max(0, idx - 400), idx)
    expect(before).toContain("w.id === 'weather'")
    // And the old integration-tab section is gone
    expect(view).not.toContain('<h2>Weather Widget Location</h2>')
  })

  it('search routes Weather Widget Location to appearance→screensaver→widgets', () => {
    const idx = view.indexOf("'Weather Widget Location'")
    const entry = view.slice(idx, idx + 260)
    expect(entry).toContain("tabId: 'appearance'")
    expect(entry).toContain("subTab: 'screensaver'")
    expect(entry).toContain("deepTab: 'widgets'")
  })
})

describe('logs viewer layout', () => {
  it('uses the split layout with a full-height viewer', () => {
    expect(view).toContain('logs-layout')
    expect(view).toContain('logs-files-card')
    expect(view).toContain('logs-viewer-card')
    // viewer fills remaining height, not a fixed cap
    expect(view).not.toContain('max-height: 340px')
    expect(view).toContain('flex: 1')
  })

  it('actions live in a viewer toolbar with tail select', () => {
    expect(view).toContain('log-toolbar')
    expect(view).toContain('refreshAll')
    expect(view).toContain('log-tail-select')
    expect(view).toContain('file-export')
  })

  it('has a status bar with line count and update time', () => {
    expect(view).toContain('log-statusbar')
    expect(view).toContain('logsUpdatedAt')
    expect(view).toContain('lines shown')
  })
})
