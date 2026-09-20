import { test, expect } from 'vitest'
import { createDefaultProfile, createDefaultScene } from '../utils/defaultProfile'

test('createDefaultProfile seeds Home + AI Assistant + Tools scenes', () => {
  const profile = createDefaultProfile()

  const names = profile.scenes.map((s) => s.name)
  expect(names).toEqual(['Home', 'AI Assistant', 'Tools'])

  const home = profile.scenes[0]
  expect(home.isDefault).toBe(true)
  expect(home.isActive).toBe(true)
})

test('every seeded button has an action, position inside the grid, and a label', () => {
  const profile = createDefaultProfile()

  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      const { rows, cols } = page.grid_config
      for (const btn of page.buttons) {
        expect(btn.label).toBeTruthy()
        expect(btn.action?.type).toBeTruthy()
        expect(btn.position.row).toBeGreaterThanOrEqual(0)
        expect(btn.position.row).toBeLessThan(rows)
        expect(btn.position.col).toBeGreaterThanOrEqual(0)
        expect(btn.position.col).toBeLessThan(cols)
        expect(btn.enabled).toBe(true)
      }
    }
  }
})

test('seeded buttons use only no-key action types', () => {
  const profile = createDefaultProfile()
  const allowed = new Set(['url', 'hotkey', 'cross_platform', 'macro'])

  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      for (const btn of page.buttons) {
        expect(allowed.has(btn.action!.type)).toBe(true)
      }
    }
  }
})

test('button ids are unique across the profile', () => {
  const profile = createDefaultProfile()
  const ids = profile.scenes.flatMap((s) =>
    s.pages.flatMap((p) => p.buttons.map((b) => b.id))
  )
  expect(new Set(ids).size).toBe(ids.length)
})

test('createDefaultScene output is unchanged (reset parity)', () => {
  const scene = createDefaultScene()
  expect(scene.name).toBe('Home')
  expect(scene.isDefault).toBe(true)
  expect(scene.pages[0].buttons.length).toBeGreaterThan(0)
})
