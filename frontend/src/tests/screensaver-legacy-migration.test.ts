import { test, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '../stores/settings'
import apiClient from '@/api/client'
import { defaultScreensaverLayout } from '@/utils/screensaverLayout'

// DL-101: settings files written before the clock flag existed store the
// pre-DL-098 all-five widget list. When the file is provably untouched
// (flag absent + legacy list + default layout), applySettingsFromRemote
// swaps it for the current slim default — once, by construction, since the
// flag exists on every payload a current build writes.

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn()
  }
}))

const LEGACY_WIDGETS = ['weather', 'news', 'sports', 'market', 'worldclock']
const NEW_DEFAULT = ['weather', 'news', 'market']

function serverReturns(settings: Record<string, unknown>) {
  vi.mocked(apiClient.get).mockResolvedValue({ data: { success: true, settings } } as any)
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

test('untouched legacy screensaver settings migrate to the slim default', async () => {
  const store = useSettingsStore()
  // Diverge local state so the migration has something to apply over.
  store.screensaverWidgets = ['sports']

  serverReturns({ screensaverWidgets: [...LEGACY_WIDGETS] }) // no clock flag
  await store.loadSettingsFromServer()

  expect(store.screensaverWidgets).toEqual(NEW_DEFAULT)
  expect(store.screensaverClockEnabled).toBe(true)
})

test('a file carrying the clock flag is never migrated, even with the legacy widget list', async () => {
  const store = useSettingsStore()
  store.screensaverWidgets = ['sports']

  // Flag present => written by a current build => the all-five list was a
  // deliberate choice and must survive.
  serverReturns({
    screensaverWidgets: [...LEGACY_WIDGETS],
    screensaverClockEnabled: false,
  })
  await store.loadSettingsFromServer()

  expect(store.screensaverWidgets).toEqual(LEGACY_WIDGETS)
  expect(store.screensaverClockEnabled).toBe(false)
})

test('a dragged-widget layout fails the untouched check', async () => {
  const store = useSettingsStore()
  store.screensaverWidgets = ['sports']

  const movedLayout = defaultScreensaverLayout()
  movedLayout.weather = { x: 40, y: 40, scale: 1.5 }
  serverReturns({
    screensaverWidgets: [...LEGACY_WIDGETS],
    screensaverLayout: movedLayout,
  })
  await store.loadSettingsFromServer()

  // List survives intact — the user customized the saver, so no migration.
  expect(store.screensaverWidgets).toEqual(LEGACY_WIDGETS)
  expect(store.screensaverLayout.weather).toEqual({ x: 40, y: 40, scale: 1.5 })
})
