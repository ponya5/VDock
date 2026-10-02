// frontend/src/tests/settings-malformed-payload.test.ts
// DL-140: a malformed remote/persisted payload must never put a non-array or
// non-string into the composite settings refs — the Settings template calls
// .includes()/.some()/.length on screensaverWidgets and .startsWith() on the
// background ids via isImageBackground, so a bad value threw mid-patch and
// left the page half-rendered.
import { describe, test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { migrateBackground, useSettingsStore, SETTINGS_DEFAULTS } from '../stores/settings'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('malformed composite settings (DL-140)', () => {
  test.each([
    ['null', null],
    ['a string', 'weather'],
    ['a number', 42],
    ['an object', { 0: 'weather' }],
  ])('screensaverWidgets=%s keeps the store array', async (_label, bad) => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { screensaverWidgets: bad } },
    })

    await store.loadSettingsFromServer()

    expect(Array.isArray(store.screensaverWidgets)).toBe(true)
  })

  test('recentActions non-array is ignored', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { recentActions: 'media_play' } },
    })

    await store.loadSettingsFromServer()

    expect(Array.isArray(store.recentActions)).toBe(true)
  })

  test('screensaverBackground non-string is ignored', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { screensaverBackground: 123 } },
    })

    await store.loadSettingsFromServer()

    expect(typeof store.screensaverBackground).toBe('string')
  })

  test('a valid screensaverWidgets array still applies', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { screensaverWidgets: ['weather', 'nowplaying'] } },
    })

    await store.loadSettingsFromServer()

    expect(store.screensaverWidgets).toEqual(['weather', 'nowplaying'])
  })
})

describe('migrateBackground type guards', () => {
  test('a numeric background falls through to the default', () => {
    expect(migrateBackground({ background: 42 as unknown as string }))
      .toBe(SETTINGS_DEFAULTS.background === 'balatro' ? 'default' : 'default')
  })

  test('a numeric dashboardBackground yields default', () => {
    expect(migrateBackground({ dashboardBackground: 7 as unknown as string }))
      .toBe('default')
  })
})
