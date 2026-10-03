// DL-147 Task 1.7 (X7) - a failed fetch, or a phone/tablet, must never create
// a profile on the server; only a reachable, empty backend on desktop/panel does.
import { describe, it, expect, vi } from 'vitest'
import { loadInitialProfile, type InitialProfileDeps } from '@/services/initialProfile'
import type { Profile } from '@/types'

const profile = (id: string) => ({ id, name: id, scenes: [] }) as unknown as Profile

function deps(over: Partial<InitialProfileDeps> & { list?: Array<{ id: string }> } = {}) {
  const list = over.list ?? []
  const calls = {
    setProfile: vi.fn(),
    createDefaultProfile: vi.fn(() => Promise.resolve()),
  }
  const value: InitialProfileDeps = {
    lastProfileId: null,
    canCreateProfile: true,
    getProfile: vi.fn(() => Promise.resolve(null)),
    loadProfiles: vi.fn(() => Promise.resolve(true)),
    profiles: () => list,
    setProfile: calls.setProfile,
    createDefaultProfile: calls.createDefaultProfile,
    ...over,
  }
  return { value, calls }
}

describe('loadInitialProfile', () => {
  it('loads the remembered profile without listing', async () => {
    const { value, calls } = deps({
      lastProfileId: 'p1',
      getProfile: vi.fn(() => Promise.resolve(profile('p1'))),
    })
    expect(await loadInitialProfile(value)).toBe('loaded')
    expect(calls.setProfile).toHaveBeenCalledWith(profile('p1'))
    expect(value.loadProfiles).not.toHaveBeenCalled()
  })

  it('falls back to the first listed profile', async () => {
    const { value, calls } = deps({
      list: [{ id: 'a' }],
      getProfile: vi.fn((id: string) => Promise.resolve(id === 'a' ? profile('a') : null)),
    })
    expect(await loadInitialProfile(value)).toBe('loaded')
    expect(calls.setProfile).toHaveBeenCalledWith(profile('a'))
  })

  it('list fetch failed (network blip): no profile is created, Retry state', async () => {
    const { value, calls } = deps({ loadProfiles: vi.fn(() => Promise.resolve(false)) })
    expect(await loadInitialProfile(value)).toBe('unreachable')
    expect(calls.createDefaultProfile).not.toHaveBeenCalled()
  })

  it('profiles exist but fetching one fails: Retry state, nothing created', async () => {
    const { value, calls } = deps({ list: [{ id: 'a' }] })
    expect(await loadInitialProfile(value)).toBe('unreachable')
    expect(calls.createDefaultProfile).not.toHaveBeenCalled()
  })

  it('reachable and empty on a phone/tablet: shows the desktop hint, creates nothing', async () => {
    const { value, calls } = deps({ canCreateProfile: false })
    expect(await loadInitialProfile(value)).toBe('needs-desktop-setup')
    expect(calls.createDefaultProfile).not.toHaveBeenCalled()
  })

  it('reachable and empty on desktop/panel: bootstraps as before', async () => {
    const { value, calls } = deps({ canCreateProfile: true })
    expect(await loadInitialProfile(value)).toBe('created')
    expect(calls.createDefaultProfile).toHaveBeenCalledTimes(1)
  })
})
