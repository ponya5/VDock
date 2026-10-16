// DL-011: a reused or expired QR explains itself on the lock screen.
import { beforeEach, describe, expect, it, vi } from 'vitest'

const exchange = vi.hoisted(() => vi.fn())
vi.mock('@/services/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/services/auth')>()),
  exchangePairToken: exchange,
}))

import { authState } from '@/services/auth'
import { consumePairQuery } from '@/services/pairing'

function routerWith(query: Record<string, string>) {
  return {
    isReady: () => Promise.resolve(),
    currentRoute: { value: { path: '/', query, hash: '' } },
    replace: vi.fn().mockResolvedValue(undefined),
  } as any
}

beforeEach(() => { authState.pairFailed = false })

describe('QR sign-in', () => {
  it('flags a used or expired code and still cleans the address bar', async () => {
    exchange.mockResolvedValue(false)
    const router = routerWith({ pair: 'old-code' })
    await consumePairQuery(router)
    expect(authState.pairFailed).toBe(true)
    expect(router.replace).toHaveBeenCalledWith({ path: '/', query: {}, hash: '' })
  })

  it('clears the flag on a good code', async () => {
    authState.pairFailed = true
    exchange.mockResolvedValue(true)
    await consumePairQuery(routerWith({ pair: 'fresh' }))
    expect(authState.pairFailed).toBe(false)
  })
})
