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

  it('location controls live under the screensaver widgets sub-tab', () => {
    // The section is gated on screensaverSubTab === 'widgets'
    const idx = view.indexOf('Weather Location')
    expect(idx).toBeGreaterThan(-1)
    const before = view.slice(Math.max(0, idx - 400), idx)
    expect(before).toContain("screensaverSubTab === 'widgets'")
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
