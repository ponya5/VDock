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
  expect(restored.name).toBe('Media')
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

// DL-066 follow-up: profiles created before the Cursor scene fix must not
// stay stuck on the old layout forever — setProfile auto-upgrades an
// untouched legacy Cursor scene on every load, in place.
function legacyCursorScene() {
  const legacyActionTypes = [
    'cursor_composer', 'cursor_chat', 'cursor_inline_edit', 'cursor_command_palette',
    'cursor_accept', 'cursor_reject', 'cursor_toggle_terminal', 'cursor_quick_open'
  ]
  return {
    id: 'scene-legacy-cursor',
    name: 'Cursor',
    icon: 'i-cursor',
    color: '#1f6fd1',
    pages: [{
      id: 'page-legacy-cursor',
      name: 'Page 1',
      grid_config: { rows: 3, cols: 5 },
      buttons: legacyActionTypes.map((type, index) => ({
        id: `btn-${index}`,
        label: type,
        icon: ['fas', 'star'] as [string, string],
        icon_type: 'fontawesome' as const,
        shape: 'rounded' as const,
        size: { rows: 1, cols: 1 },
        enabled: true,
        position: { row: Math.floor(index / 4), col: index % 4 },
        action: { type, config: {} }
      }))
    }]
  }
}

test('setProfile auto-upgrades an untouched legacy Cursor scene to the current layout', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  const profile = makeProfile()
  profile.scenes = [...profile.scenes, legacyCursorScene() as any]

  store.setProfile(profile)

  const cursorScene = store.currentProfile!.scenes.find((s) => s.name === 'Cursor')!
  expect(cursorScene.id).toBe('scene-legacy-cursor') // id preserved
  expect(cursorScene.pages[0].grid_config).toEqual({ rows: 2, cols: 4 })
  const actionTypes = cursorScene.pages[0].buttons.map((b) => b.action?.type)
  expect(actionTypes).toContain('cursor_new_chat')
  expect(actionTypes).not.toContain('cursor_composer')
})

test('setProfile leaves a customised Cursor scene alone', () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  const profile = makeProfile()
  const customised = legacyCursorScene()
  // One extra/renamed button is enough to mark it as no longer untouched.
  customised.pages[0].buttons[0] = {
    ...customised.pages[0].buttons[0],
    action: { type: 'url', config: { url: 'https://example.com' } }
  }
  profile.scenes = [...profile.scenes, customised as any]

  store.setProfile(profile)

  const cursorScene = store.currentProfile!.scenes.find((s) => s.name === 'Cursor')!
  const actionTypes = cursorScene.pages[0].buttons.map((b) => b.action?.type)
  expect(actionTypes).toContain('url')
  expect(actionTypes).not.toContain('cursor_new_chat')
})
