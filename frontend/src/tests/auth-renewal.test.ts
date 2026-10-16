// DL-008: a device that is used never hits the sign-in expiry, and a 200 at
// boot means "accepted" - including the trusted host with no token at all.
import { beforeEach, describe, expect, it, vi } from 'vitest'

const axios = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }))
vi.mock('axios', () => ({ default: axios }))

beforeEach(() => {
  vi.resetModules()
  axios.get.mockReset()
  axios.post.mockReset()
  localStorage.clear()
})

describe('sign-in renewal', () => {
  it('unlocks the computer VDock runs on without a token', async () => {
    axios.get.mockResolvedValue({ data: { config: { require_auth: true } } })
    const auth = await import('@/services/auth')
    await auth.probeAuth()
    expect(auth.authState.required).toBe(true)
    expect(auth.authState.unlocked).toBe(true)
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('renews a held token at boot without reconnecting the socket', async () => {
    localStorage.setItem('vdock.authToken', 'old')
    axios.get.mockResolvedValue({ data: { config: { require_auth: true } } })
    axios.post.mockResolvedValue({ data: { token: 'fresh' } })
    const auth = await import('@/services/auth')
    const listener = vi.fn()
    auth.onAuthTokenChanged(listener)
    await auth.probeAuth()
    await vi.waitFor(() => expect(auth.getAuthToken()).toBe('fresh'))
    expect(axios.post).toHaveBeenCalledWith('/api/auth/refresh', null,
      expect.objectContaining({ headers: { Authorization: 'Bearer old' } }))
    expect(listener).not.toHaveBeenCalled()
  })

  it('keeps the old token when renewal fails', async () => {
    localStorage.setItem('vdock.authToken', 'old')
    axios.post.mockRejectedValue(new Error('offline'))
    const auth = await import('@/services/auth')
    expect(await auth.renewAuthToken()).toBe(false)
    expect(auth.getAuthToken()).toBe('old')
  })
})
