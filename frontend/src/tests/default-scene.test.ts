import { test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '../stores/dashboard'
import type { Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn()
  }
}))

function makeProfile(): Profile {
  return {
    id: 'profile-1',
    name: 'Test Profile',
    description: '',
    theme: 'default',
    scenes: [{
      id: 'scene-custom',
      name: 'Custom Scene',
      pages: [{
        id: 'page-1',
        name: 'Page 1',
        buttons: [],
        grid_config: { rows: 4, cols: 5 }
      }]
    }]
  } as Profile
}

test('setProfile appends a default scene, keeping the original scene at index 0', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()

  store.setProfile(makeProfile())

  const scenes = store.currentProfile!.scenes
  expect(scenes[0].id).toBe('scene-custom')
  expect(scenes.filter((s) => s.isDefault)).toHaveLength(1)
  expect(scenes[scenes.length - 1].isDefault).toBe(true)
})

test('setProfile does not insert a second default scene on reload', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()

  store.setProfile(makeProfile())
  const firstLoadSceneCount = store.currentProfile!.scenes.length

  // Reload the same (now-migrated) profile
  store.setProfile(JSON.parse(JSON.stringify(store.currentProfile)))

  expect(store.currentProfile!.scenes).toHaveLength(firstLoadSceneCount)
  expect(store.currentProfile!.scenes.filter((s) => s.isDefault)).toHaveLength(1)
})

test('resetScene restores a mutated default scene to the factory layout', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  store.setProfile(makeProfile())

  const defaultScene = store.currentProfile!.scenes.find((s) => s.isDefault)!
  const originalButtonCount = defaultScene.pages[0].buttons.length

  // Mutate it
  defaultScene.name = 'Wrecked'
  defaultScene.pages[0].buttons = []
  defaultScene.color = '#000000'

  store.resetScene(defaultScene.id)

  const restored = store.currentProfile!.scenes.find((s) => s.id === defaultScene.id)!
  expect(restored.name).toBe('Home')
  expect(restored.pages[0].buttons).toHaveLength(originalButtonCount)
  expect(restored.isDefault).toBe(true)
  expect(restored.id).toBe(defaultScene.id) // id preserved across reset
})

test('resetScene is a no-op for a non-default scene', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  store.setProfile(makeProfile())

  const customScene = store.currentProfile!.scenes.find((s) => s.id === 'scene-custom')!
  const before = JSON.parse(JSON.stringify(customScene))

  store.resetScene('scene-custom')

  const after = store.currentProfile!.scenes.find((s) => s.id === 'scene-custom')!
  expect(after).toEqual(before)
})
