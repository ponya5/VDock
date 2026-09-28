// frontend/src/tests/background-migration.test.ts
import { describe, test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { migrateBackground, useSettingsStore } from '../stores/settings'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('migrateBackground', () => {
  test('an explicit background wins over both legacy keys', () => {
    expect(migrateBackground({
      background: 'silk',
      backgroundPreference: 'aurora',
      dashboardBackground: 'starfield',
    })).toBe('silk')
  })

  test('backgroundPreference wins when it is a real selection', () => {
    expect(migrateBackground({
      backgroundPreference: 'aurora',
      dashboardBackground: 'default',
    })).toBe('aurora')
  })

  test("backgroundPreference of 'none' is not a selection", () => {
    expect(migrateBackground({
      backgroundPreference: 'none',
      dashboardBackground: 'starfield',
    })).toBe('starfield')
  })

  test('falls back to dashboardBackground', () => {
    expect(migrateBackground({ dashboardBackground: 'ocean-breeze' }))
      .toBe('ocean-breeze')
  })

  test('both absent yields default', () => {
    expect(migrateBackground({})).toBe('default')
  })

  test('an uploaded image in dashboardBackground survives migration', () => {
    expect(migrateBackground({ dashboardBackground: '/api/uploads/bg.png' }))
      .toBe('/api/uploads/bg.png')
  })
})

describe('factory default (DL-106)', () => {
  test('a fresh install seeds Floating Bubbles; the "default" sentinel stays the migration fallback', () => {
    setActivePinia(createPinia())
    expect(useSettingsStore().background).toBe('bubble-float')
    // Existing users whose stored file lacks a background key keep the
    // classic gradient — the new default is out-of-box only.
    expect(migrateBackground({})).toBe('default')
  })
})

describe('loadSettingsFromServer migration', () => {
  test('a legacy-only server response migrates into store.background', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { dashboardBackground: 'starfield' } },
    })

    await store.loadSettingsFromServer()

    expect(store.background).toBe('starfield')
  })
})
