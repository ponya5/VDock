// Feature: ai-dev-integration-packs, Property 3.2: scene and page navigation.
//
// Stream Deck's "Switch Profile" and direct page jumps. These are frontend-only
// actions -- they must never reach POST /api/actions/execute, which would fail
// with "Unknown action type" since the backend has no handler for them.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const post = vi.fn()
const get = vi.fn()

vi.mock('@/api/client', () => ({
  default: { post: (...a: any[]) => post(...a), get: (...a: any[]) => get(...a) }
}))
vi.mock('@/api/socket', () => ({
  default: { on: vi.fn(), off: vi.fn(), isConnected: () => false }
}))
vi.mock('@/stores/settings', () => ({ useSettingsStore: () => ({}) }))

let useDashboardStore: any

function profile() {
  const page = (id: string) => ({
    id, name: id, grid_config: { rows: 2, cols: 3 }, buttons: []
  })
  return {
    id: 'p1',
    name: 'Test',
    description: '',
    theme: 'default',
    scenes: [
      { id: 's1', name: 'Home', pages: [page('h1'), page('h2'), page('h3')] },
      { id: 's2', name: 'Cursor', pages: [page('c1')] },
      { id: 's3', name: 'Claude Code', pages: [page('cc1')] }
    ]
  }
}

function button(type: string, config: Record<string, unknown> = {}) {
  return {
    id: 'btn', label: type, shape: 'rounded',
    position: { row: 0, col: 0 }, size: { rows: 1, cols: 1 },
    enabled: true, action: { type, config }
  }
}

beforeEach(async () => {
  setActivePinia(createPinia())
  post.mockReset()
  get.mockReset()
  vi.resetModules()
  useDashboardStore = (await import('@/stores/dashboard')).useDashboardStore
})

describe('scene and page navigation', () => {
  it('jumps to a page by its 1-based number', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    const result = await store.executeButtonAction(button('goto_page', { page: 3 }))

    expect(result).toMatchObject({ success: true })
    expect(store.currentPageIndex).toBe(2)
    expect(post).not.toHaveBeenCalled()
  })

  it('refuses a page that does not exist instead of going blank', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    const result = await store.executeButtonAction(button('goto_page', { page: 99 }))

    expect(result.success).toBe(false)
    expect(result.message).toContain('does not exist')
    expect(store.currentPageIndex).toBe(0)
  })

  it('refuses page zero, since pages are 1-based in the UI', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    expect((await store.executeButtonAction(button('goto_page', { page: 0 }))).success)
      .toBe(false)
  })

  it('switches scene by name, case-insensitively', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    const result = await store.executeButtonAction(
      button('switch_scene', { scene: 'claude code' })
    )

    expect(result).toMatchObject({ success: true })
    expect(store.currentSceneIndex).toBe(2)
    expect(post).not.toHaveBeenCalled()
  })

  it('reports a scene name that does not match', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    const result = await store.executeButtonAction(
      button('switch_scene', { scene: 'Nope' })
    )

    expect(result.success).toBe(false)
    expect(result.message).toContain('Nope')
    expect(store.currentSceneIndex).toBe(0)
  })

  it('reports an unconfigured switch_scene button', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    const result = await store.executeButtonAction(button('switch_scene', {}))

    expect(result.success).toBe(false)
    expect(result.message).toContain('No scene configured')
  })

  it('moves to the next and previous scene', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    await store.executeButtonAction(button('next_scene'))
    expect(store.currentSceneIndex).toBe(1)

    await store.executeButtonAction(button('previous_scene'))
    expect(store.currentSceneIndex).toBe(0)
  })

  it('never dispatches a frontend-only navigation action to the backend', async () => {
    const store = useDashboardStore()
    store.setProfile(profile())

    for (const type of [
      'next_page', 'previous_page', 'home_page',
      'goto_page', 'switch_scene', 'next_scene', 'previous_scene'
    ]) {
      await store.executeButtonAction(button(type, { page: 1, scene: 'Home' }))
    }

    expect(post).not.toHaveBeenCalled()
  })
})
