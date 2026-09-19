// frontend/src/tests/background-migration.test.ts
import { describe, test, expect } from 'vitest'
import { migrateBackground } from '../stores/settings'

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
