// DL-147 Task 4.3 - scanning the QR signs the phone in when a deck password is
// set: the token is traded once on boot, stripped from the address bar, and the
// Connect page puts a fresh one in the QR.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

const post = vi.fn()
vi.mock('axios', () => ({ default: { post: (...a: unknown[]) => post(...a), get: vi.fn() } }))

const clientPost = vi.fn()
vi.mock('@/api/client', () => ({ default: { post: (...a: unknown[]) => clientPost(...a) } }))

import { authState, getAuthToken, clearAuthToken } from '@/services/auth'
import { buildPairUrl, consumePairQuery, requestPairToken } from '@/services/pairing'
import { settingsSource } from './helpers/settingsSource'

function routerAt(url: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  })
  void router.push(url)
  return router
}

beforeEach(() => {
  post.mockReset()
  clientPost.mockReset()
  clearAuthToken()
  authState.required = false
  authState.unlocked = false
})

describe('consumePairQuery', () => {
  it('trades ?pair= for a login and strips it from the address', async () => {
    post.mockResolvedValue({ data: { token: 'jwt-1' } })
    const router = routerAt('/?pair=abc&keep=1')

    await consumePairQuery(router)

    expect(post).toHaveBeenCalledWith('/api/auth/pair', { token: 'abc' }, expect.anything())
    expect(getAuthToken()).toBe('jwt-1')
    expect(authState.unlocked).toBe(true)
    expect(router.currentRoute.value.query).toEqual({ keep: '1' })
  })

  it('strips the query even when the token is refused, leaving the lock screen', async () => {
    post.mockRejectedValue({ response: { status: 401 } })
    const router = routerAt('/?pair=stale')

    await consumePairQuery(router)

    expect(getAuthToken()).toBeNull()
    expect(authState.unlocked).toBe(false)
    expect(router.currentRoute.value.query).toEqual({})
  })

  it('does nothing without ?pair', async () => {
    await consumePairQuery(routerAt('/'))
    expect(post).not.toHaveBeenCalled()
  })
})

describe('boot order', () => {
  it('mounts the app only after the pairing exchange, so no early 401 can clear the new token', () => {
    const main = readFileSync(resolve(__dirname, '..', 'main.ts'), 'utf-8')
    expect(main).toContain("consumePairQuery(router).finally(() => app.mount('#app'))")
    expect(main).not.toMatch(/^app\.mount\('#app'\)/m)
  })
})

describe('QR helpers', () => {
  it('builds the pairing address from the deck url', () => {
    expect(buildPairUrl('http://192.168.1.5:5000', 'a-b_c')).toBe('http://192.168.1.5:5000/?pair=a-b_c')
  })

  it('returns the token from the server, or null when none could be minted', async () => {
    clientPost.mockResolvedValueOnce({ data: { token: 'tok' } })
    expect(await requestPairToken()).toBe('tok')
    clientPost.mockRejectedValueOnce(new Error('409'))
    expect(await requestPairToken()).toBeNull()
  })
})

describe('Connect page wiring', () => {
  const panel = settingsSource()

  it('encodes the pairing url only when a deck password is on, and refreshes it every 9 minutes', () => {
    expect(panel).toContain('buildPairUrl(lanUrl.value, pairToken.value)')
    expect(panel).toContain('serverConfig.value?.require_auth')
    expect(panel).toContain('setInterval(refreshPairToken, PAIR_REFRESH_MS)')
    expect(panel).toContain('clearInterval(pairTimer)')
  })

  it('warns that the code signs a device in, and offers the Home Screen step', () => {
    expect(panel).toContain("don't share screenshots of it")
    expect(panel).toContain('CONNECT_INSTALL_STEP')
  })
})
