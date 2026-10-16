// DL-011: when the PC goes away the reconnect banner owns the message; a
// failed request in that state must not add a contradictory "Network Error"
// toast on top of it.
import { afterEach, describe, expect, it, vi } from 'vitest'
import apiClient from '@/api/client'
import { markConnected, markDisconnected } from '@/services/connection'

function failNetwork() {
  // No response object = the request never reached the backend.
  ;(apiClient as any).client.defaults.adapter = () => Promise.reject(Object.assign(new Error('Network Error'), {
    isAxiosError: true, config: { url: '/x', method: 'get' }, response: undefined,
  }))
}

afterEach(() => { markConnected(); vi.useRealTimers() })

describe('network error toast', () => {
  it('stays quiet while the connection is down (the banner says it)', async () => {
    const store = { error: vi.fn() }
    apiClient.setNotificationsStore(store)
    failNetwork()
    markDisconnected()
    await apiClient.post('/x').catch(() => {})
    expect(store.error).not.toHaveBeenCalled()
  })

  it('explains itself in VDock terms when the socket is up', async () => {
    const store = { error: vi.fn() }
    apiClient.setNotificationsStore(store)
    failNetwork()
    ;(apiClient as any).lastErrorTime = 0
    await apiClient.post('/x').catch(() => {})
    expect(store.error).toHaveBeenCalledOnce()
    expect(store.error.mock.calls[0][0]).toBe("Couldn't reach VDock")
    expect(store.error.mock.calls[0][1]).not.toContain('internet')
  })
})
