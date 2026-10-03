// DL-147 Task 4.2 - a layout saved on another device reaches an open phone or
// tablet: one debounced re-fetch, same scene and page, never over an editor.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { Profile } from '@/types'

const handlers = new Map<string, (payload: unknown) => void>()
const getProfile = vi.fn()
const info = vi.fn()

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => handlers.set(event, cb),
    off: (event: string) => handlers.delete(event),
    emitProfileChanged: vi.fn(),
  },
}))
vi.mock('@/stores/profiles', () => ({ useProfilesStore: () => ({ getProfile }) }))
vi.mock('@/stores/notifications', () => ({ useNotificationsStore: () => ({ info }) }))
vi.mock('@/api/client', () => ({ default: { get: vi.fn(), put: vi.fn(), post: vi.fn(), delete: vi.fn() } }))

import { initProfileSync, PROFILE_REFETCH_DEBOUNCE_MS } from '@/services/profileSync'
import { useDashboardStore } from '@/stores/dashboard'

function profile(id: string, sceneNames: string[]): Profile {
  return {
    id,
    name: id,
    scenes: sceneNames.map(name => ({
      id: `scene-${name}`,
      name,
      isDefault: name === 'Media',
      pages: [
        { id: `${name}-p1`, name: 'P1', rows: 1, cols: 1, buttons: [] },
        { id: `${name}-p2`, name: 'P2', rows: 1, cols: 1, buttons: [] },
      ],
    })),
    factorySeedsApplied: ['claude-code', 'cursor'],
  } as unknown as Profile
}

let stop: () => void

beforeEach(() => {
  vi.useFakeTimers()
  setActivePinia(createPinia())
  handlers.clear()
  getProfile.mockReset()
  info.mockReset()
  localStorage.clear()
  stop = initProfileSync()
})

afterEach(() => {
  stop()
  vi.useRealTimers()
})

function relay(id: string) {
  handlers.get('profile_changed')?.({ id })
}

async function settle() {
  await vi.advanceTimersByTimeAsync(PROFILE_REFETCH_DEBOUNCE_MS)
}

describe('initProfileSync', () => {
  it('collapses a burst of three events into one re-fetch', async () => {
    const dashboard = useDashboardStore()
    dashboard.setProfile(profile('p1', ['Media']))
    getProfile.mockResolvedValue(profile('p1', ['Media']))

    relay('p1'); relay('p1'); relay('p1')
    await settle()

    expect(getProfile).toHaveBeenCalledTimes(1)
    expect(getProfile).toHaveBeenCalledWith('p1')
  })

  it('keeps the viewer on their scene and page', async () => {
    const dashboard = useDashboardStore()
    dashboard.setProfile(profile('p1', ['Media', 'Notes']))
    const target = dashboard.currentProfile!.scenes.findIndex(s => s.name === 'Notes')
    dashboard.setScene(target)
    dashboard.setPage(1)
    getProfile.mockResolvedValue(profile('p1', ['Media', 'Notes']))

    relay('p1')
    await settle()

    expect(dashboard.currentScene?.name).toBe('Notes')
    expect(dashboard.currentPageIndex).toBe(1)
  })

  it('ignores another profile id', async () => {
    useDashboardStore().setProfile(profile('p1', ['Media']))
    relay('someone-else')
    await settle()
    expect(getProfile).not.toHaveBeenCalled()
  })

  it('does not overwrite an open editor and says so instead', async () => {
    const dashboard = useDashboardStore()
    dashboard.setProfile(profile('p1', ['Media']))
    dashboard.isEditMode = true

    relay('p1'); relay('p1')
    await settle()

    expect(getProfile).not.toHaveBeenCalled()
    expect(info).toHaveBeenCalledTimes(1)
    expect(info.mock.calls[0][0]).toContain('Profile changed on another device')
  })

  it('stops listening when stopped', () => {
    stop()
    expect(handlers.has('profile_changed')).toBe(false)
  })
})
