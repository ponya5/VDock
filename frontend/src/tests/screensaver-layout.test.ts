// DL-013: the screensaver layout is a persisted per-widget {x, y, scale}
// record (viewport-percent centers), the screensaver has its own background
// setting, and a live drag/resize editor is mounted inside the settings
// window (the deck-window ui_command path also remains).
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  DEFAULT_SCREENSAVER_LAYOUT,
  defaultScreensaverLayout,
  normalizeScreensaverLayout,
  SCREENSAVER_WIDGET_IDS,
} from '@/utils/screensaverLayout'

const screensaver = readFileSync(
  resolve(__dirname, '../components/ScreenSaver.vue'),
  'utf-8'
)
const store = readFileSync(
  resolve(__dirname, '../stores/settings.ts'),
  'utf-8'
)
const dashboard = readFileSync(
  resolve(__dirname, '../views/DashboardView.vue'),
  'utf-8'
)
const settingsView = readFileSync(
  resolve(__dirname, '../views/SettingsView.vue'),
  'utf-8'
)

describe('normalizeScreensaverLayout', () => {
  it('returns the default layout for missing or malformed input', () => {
    for (const raw of [undefined, null, 42, 'x', [], { news: 'nope' }]) {
      expect(normalizeScreensaverLayout(raw)).toEqual(DEFAULT_SCREENSAVER_LAYOUT)
    }
  })

  it('keeps valid entries and fills missing widgets from defaults', () => {
    const out = normalizeScreensaverLayout({ news: { x: 30, y: 60, scale: 1.5 } })
    expect(out.news).toEqual({ x: 30, y: 60, scale: 1.5 })
    expect(out.clock).toEqual(DEFAULT_SCREENSAVER_LAYOUT.clock)
    expect(SCREENSAVER_WIDGET_IDS.every(id => id in out)).toBe(true)
  })

  it('clamps positions and scale, and repairs non-numeric fields', () => {
    const out = normalizeScreensaverLayout({
      clock: { x: 500, y: -10, scale: 'big' },
      market: { x: 'left', y: 50, scale: 99 },
    })
    expect(out.clock).toEqual({ x: 100, y: 0, scale: DEFAULT_SCREENSAVER_LAYOUT.clock.scale })
    expect(out.market.x).toBe(DEFAULT_SCREENSAVER_LAYOUT.market.x)
    expect(out.market.scale).toBe(3)
  })

  it('drops unknown widget ids', () => {
    const out = normalizeScreensaverLayout({ ghost: { x: 1, y: 1, scale: 1 } })
    expect('ghost' in out).toBe(false)
  })

  it('defaultScreensaverLayout returns a fresh copy', () => {
    const a = defaultScreensaverLayout()
    a.clock.x = 1
    expect(defaultScreensaverLayout().clock.x).toBe(DEFAULT_SCREENSAVER_LAYOUT.clock.x)
  })
})

describe('screensaver layout wiring', () => {
  it('persists both settings through the payload and remote apply', () => {
    expect(store).toContain('screensaverBackground: screensaverBackground.value')
    expect(store).toContain('screensaverBackground.value = settings.screensaverBackground')
    expect(store).toContain('screensaverLayout: JSON.parse(JSON.stringify(screensaverLayout.value))')
    expect(store).toContain('normalizeScreensaverLayout(settings.screensaverLayout)')
    expect(store).toContain('screensaverBackground = ref<string>(DEFAULT_BACKGROUND_ID)')
  })

  it('is allowlisted for server persistence', () => {
    const backend = readFileSync(
      resolve(__dirname, '../../../backend/routes/user_settings.py'),
      'utf-8'
    )
    expect(backend).toContain("'screensaverBackground'")
    expect(backend).toContain("'screensaverLayout'")
  })

  it('routes the layout-edit ui_command through the backend allowlist', () => {
    const app = readFileSync(
      resolve(__dirname, '../../../backend/app.py'),
      'utf-8'
    )
    expect(app).toContain("'screensaver_layout_edit'")
    expect(dashboard).toContain("command === 'screensaver_layout_edit'")
    expect(dashboard).toContain('screensaverLayoutEdit')
    expect(dashboard).toContain('@save-layout="saveScreensaverLayout"')
    expect(dashboard).toContain('settingsStore.screensaverLayout = layout')
  })

  it('exposes the editor + background picker in Screensaver settings', () => {
    expect(settingsView).toContain('handleCustomizeScreensaverLayout')
    // The editor mounts directly inside the settings window — it no longer
    // depends on a deck window being reachable via ui_command.
    expect(settingsView).toContain('screensaverLayoutEditOpen')
    expect(settingsView).toContain("import ScreenSaver from '@/components/ScreenSaver.vue'")
    expect(settingsView).toContain('@save-layout="onSaveScreensaverLayout"')
    expect(settingsView).toContain('settingsStore.screensaverLayout = layout')
    expect(settingsView).toContain('settings.screensaverBackground')
    expect(settingsView).toContain('screensaverPickerGroups')
    expect(settingsView).toContain('handleScreensaverBackgroundUpload')
  })

  it('paints the custom background on a dedicated layer with a scrim', () => {
    expect(screensaver).toContain('ss-bg')
    expect(screensaver).toContain('ssBgComponent')
    expect(screensaver).toContain('ss-dim')
    // Default keeps the classic dark look instead of a dashboard gradient.
    expect(screensaver).toContain("ssBgId.value !== DEFAULT_BACKGROUND_ID")
  })
})
