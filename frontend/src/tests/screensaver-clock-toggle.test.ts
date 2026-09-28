import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// DL-098: the screensaver Clock widget becomes toggleable via a persisted
// `screensaverClockEnabled` flag (default true — a separate flag rather
// than a `screensaverWidgets` entry so existing users' saved lists can't
// silently hide the clock), and the fresh-install widget set slims to
// weather + news + market (sports/worldclock still available, off by
// default for new users).

const src = resolve(__dirname, '..')

function readSrc(rel: string) {
  return readFileSync(resolve(src, rel), 'utf-8')
}

const store = readSrc('stores/settings.ts')
const backend = readFileSync(resolve(src, '../../backend/routes/user_settings.py'), 'utf-8')
const screensaver = readSrc('components/ScreenSaver.vue')
const settingsView = readSrc('views/SettingsView.vue')

test('screensaverClockEnabled is a persisted setting end-to-end', () => {
  for (const marker of [
    'screensaverClockEnabled = ref(true)',
    'screensaverClockEnabled: true',
    'screensaverClockEnabled: boolean',
    'screensaverClockEnabled: screensaverClockEnabled.value',
    'screensaverClockEnabled.value = settings.screensaverClockEnabled',
  ]) {
    expect(store.includes(marker), `settings store should contain "${marker}"`).toBe(true)
  }
  expect(backend.includes("'screensaverClockEnabled'"), 'backend allowlist should accept screensaverClockEnabled').toBe(true)
})

test('new-user widget default is weather + news + market only', () => {
  expect(store.includes("screensaverWidgets: ['weather', 'news', 'market']"),
    'SETTINGS_DEFAULTS.screensaverWidgets should slim to weather/news/market').toBe(true)
  expect(store.includes("ref<string[]>([...SETTINGS_DEFAULTS.screensaverWidgets])"),
    'pre-load ref default should share SETTINGS_DEFAULTS').toBe(true)
  expect(store.includes("settings.screensaverWidgets ?? [...SETTINGS_DEFAULTS.screensaverWidgets]"),
    'load fallback should share SETTINGS_DEFAULTS').toBe(true)
  // sports/worldclock must not survive in the defaults — scope the check to
  // the SETTINGS_DEFAULTS block: LEGACY_SCREENSAVER_WIDGETS (DL-101) carries
  // the old five-widget list verbatim as a migration signature, not a default.
  const defaultsBlock = store.match(/SETTINGS_DEFAULTS\s*=\s*\{([\s\S]*?)\} as const/)?.[1] ?? ''
  expect(defaultsBlock.includes("'sports'"),
    'sports should be off the default list').toBe(false)
  expect(defaultsBlock.includes("'worldclock'"),
    'worldclock should be off the default list').toBe(false)
})

test('screensaver gates the clock on showClockWidget and excludes it from mountedWidgets when off', () => {
  expect(screensaver.includes('showClockWidget'), 'ScreenSaver should define showClockWidget').toBe(true)
  // Slice the exact tag containing ss-pos ss-body — a regex over attributes
  // trips on the `>` inside `:ref="el => setWidgetEl('clock', el)"`.
  const clockIdx = screensaver.indexOf('ss-pos ss-body')
  const clockBlock = clockIdx === -1 ? '' : screensaver.slice(
    screensaver.lastIndexOf('<div', clockIdx),
    screensaver.indexOf('>', clockIdx) + 1
  )
  expect(clockBlock.includes('v-if="showClockWidget"'), 'clock block should render conditionally').toBe(true)
  const mounted = screensaver.match(/mountedWidgets[\s\S]*?return ids/ )?.[0] ?? ''
  expect(/showClockWidget\.value[^\n]*push\('clock'\)|ids\.push\('clock'\)[^\n]*showClockWidget|if \(showClockWidget\.value\)/s.test(mounted)
    || /ids:\s*ScreensaverWidgetId\[\]\s*=\s*\[\]/.test(mounted),
    'mountedWidgets should include clock conditionally').toBe(true)
})

test('settings row toggles the clock (no longer forced on)', () => {
  const clockRow = settingsView.match(/<span class="label">Clock<\/span>[\s\S]*?<\/label>/)?.[0] ?? ''
  expect(clockRow.includes('disabled'), 'clock toggle must not be disabled').toBe(false)
  expect(clockRow.includes('screensaverClockEnabled'), 'clock toggle must bind the flag').toBe(true)
  expect(settingsView.includes('Always drawn'), '"Always drawn" copy is obsolete').toBe(false)
})
