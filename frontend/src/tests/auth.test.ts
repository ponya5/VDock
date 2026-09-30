// DL-126 — usable authentication: token storage, lock-screen state, the
// axios bearer interceptor, the socket handshake token, and AuthGate.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

// axios is fully mocked: auth.ts calls it directly, api/client.ts calls
// axios.create(). The captured interceptors let tests drive them by hand.
const axiosGet = vi.fn()
const axiosPost = vi.fn()
const requestInterceptors: Array<(c: any) => any> = []
const responseErrorHandlers: Array<(e: any) => any> = []
const innerClient = {
  interceptors: {
    request: { use: (fn: any) => requestInterceptors.push(fn) },
    response: { use: (_ok: any, err: any) => responseErrorHandlers.push(err) },
  },
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}

vi.mock('axios', () => ({
  default: {
    create: () => innerClient,
    get: (...args: unknown[]) => axiosGet(...args),
    post: (...args: unknown[]) => axiosPost(...args),
  },
}))

const socketInstances: Array<{ on: ReturnType<typeof vi.fn>; disconnect: ReturnType<typeof vi.fn> }> = []
const ioMock = vi.fn(() => {
  const inst = { on: vi.fn(), disconnect: vi.fn(), connected: false }
  socketInstances.push(inst)
  return inst
})
vi.mock('socket.io-client', () => ({ io: (...args: any[]) => ioMock(...args) }))

async function freshAuth() {
  vi.resetModules()
  const mod = await import('@/services/auth')
  // Dynamic import after reset returns the fresh module's own state object.
  return mod
}

beforeEach(() => {
  localStorage.clear()
  axiosGet.mockReset()
  axiosPost.mockReset()
  ioMock.mockClear()
  socketInstances.length = 0
  requestInterceptors.length = 0
  responseErrorHandlers.length = 0
})

describe('auth service', () => {
  it('probe marks an open server as not required and unlocked', async () => {
    axiosGet.mockResolvedValue({ data: { config: { require_auth: false } } })
    const auth = await freshAuth()
    await auth.probeAuth()
    expect(auth.authState.required).toBe(false)
    expect(auth.authState.unlocked).toBe(true)
    expect(auth.authState.checked).toBe(true)
  })

  it('probe on a locked server without a token raises the gate', async () => {
    axiosGet.mockRejectedValue({ response: { status: 401 } })
    const auth = await freshAuth()
    await auth.probeAuth()
    expect(auth.authState.required).toBe(true)
    expect(auth.authState.unlocked).toBe(false)
  })

  it('probe sends the stored token and treats a 200 as still valid', async () => {
    localStorage.setItem('vdock.authToken', 'stored-token')
    axiosGet.mockResolvedValue({ data: { config: { require_auth: true } } })
    const auth = await freshAuth()
    await auth.probeAuth()
    expect(axiosGet).toHaveBeenCalledWith('/api/config', expect.objectContaining({
      headers: { Authorization: 'Bearer stored-token' },
    }))
    expect(auth.authState.required).toBe(true)
    expect(auth.authState.unlocked).toBe(true)
  })

  it('a 401 probe clears a stale stored token', async () => {
    localStorage.setItem('vdock.authToken', 'stale')
    axiosGet.mockRejectedValue({ response: { status: 401 } })
    const auth = await freshAuth()
    await auth.probeAuth()
    expect(auth.getAuthToken()).toBeNull()
    expect(localStorage.getItem('vdock.authToken')).toBeNull()
  })

  it('login stores the token, unlocks, and notifies listeners', async () => {
    axiosPost.mockResolvedValue({ data: { token: 'fresh-token' } })
    const auth = await freshAuth()
    const listener = vi.fn()
    auth.onAuthTokenChanged(listener)

    const result = await auth.login('deck1234')
    expect(result.ok).toBe(true)
    expect(auth.getAuthToken()).toBe('fresh-token')
    expect(localStorage.getItem('vdock.authToken')).toBe('fresh-token')
    expect(auth.authState.unlocked).toBe(true)
    expect(listener).toHaveBeenCalled()
  })

  it('login maps a 401 to a wrong-password message without storing', async () => {
    axiosPost.mockRejectedValue({ response: { status: 401 } })
    const auth = await freshAuth()
    const result = await auth.login('nope')
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/wrong password/i)
    expect(auth.getAuthToken()).toBeNull()
  })

  it('login surfaces the 429 throttle message', async () => {
    axiosPost.mockRejectedValue({
      response: { status: 429, data: { error: 'Too many attempts' } },
    })
    const auth = await freshAuth()
    const result = await auth.login('nope')
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/too many/i)
  })

  it('markUnauthorized drops the token and raises the gate', async () => {
    const auth = await freshAuth()
    auth.setAuthToken('x')
    auth.authState.unlocked = true
    auth.markUnauthorized()
    expect(auth.getAuthToken()).toBeNull()
    expect(auth.authState.required).toBe(true)
    expect(auth.authState.unlocked).toBe(false)
  })
})

describe('api client interceptor', () => {
  it('attaches the bearer token to outgoing requests', async () => {
    const auth = await freshAuth()
    auth.setAuthToken('tok-123')
    await import('@/api/client')
    const config: any = { headers: {}, data: {} }
    for (const fn of requestInterceptors) fn(config)
    expect(config.headers.Authorization).toBe('Bearer tok-123')
  })

  it('sends no header when there is no token', async () => {
    await freshAuth()
    await import('@/api/client')
    const config: any = { headers: {}, data: {} }
    for (const fn of requestInterceptors) fn(config)
    expect(config.headers.Authorization).toBeUndefined()
  })

  it('a 401 response locks the app — except the login call itself', async () => {
    const auth = await freshAuth()
    auth.setAuthToken('expired')
    auth.authState.unlocked = true
    await import('@/api/client')

    const err401 = { response: { status: 401 }, config: { url: '/config' } }
    for (const fn of responseErrorHandlers) {
      await expect(fn(err401)).rejects.toBe(err401)
    }
    expect(auth.authState.required).toBe(true)
    expect(auth.authState.unlocked).toBe(false)

    // Login's own 401 must NOT reset the state — it's a wrong password.
    auth.authState.required = false
    auth.authState.unlocked = true
    auth.setAuthToken('still-valid')
    const loginErr = { response: { status: 401 }, config: { url: '/auth/login' } }
    for (const fn of responseErrorHandlers) {
      await expect(fn(loginErr)).rejects.toBe(loginErr)
    }
    expect(auth.authState.unlocked).toBe(true)
    expect(auth.getAuthToken()).toBe('still-valid')
  })
})

describe('socket auth', () => {
  it('hands the token to the Socket.IO handshake', async () => {
    const auth = await freshAuth()
    auth.setAuthToken('tok-abc')
    const socket = (await import('@/api/socket')).default
    socket.connect()
    expect(ioMock).toHaveBeenCalledTimes(1)
    const options = ioMock.mock.calls[0][1]
    const cb = vi.fn()
    options.auth(cb)
    expect(cb).toHaveBeenCalledWith({ token: 'tok-abc' })
  })

  it('reconnects when the token changes so the handshake picks it up', async () => {
    const auth = await freshAuth()
    const socket = (await import('@/api/socket')).default
    socket.connect()
    expect(ioMock).toHaveBeenCalledTimes(1)

    auth.setAuthToken('new-token')
    expect(socketInstances[0].disconnect).toHaveBeenCalled()
    expect(ioMock).toHaveBeenCalledTimes(2)
  })
})

describe('AuthGate', () => {
  it('renders nothing while unlocked, and a form while locked', async () => {
    const auth = await freshAuth()
    const { default: AuthGate } = await import('@/components/AuthGate.vue')
    const wrapper = mount(AuthGate, { attachTo: document.body })
    await flushPromises()
    expect(document.body.querySelector('.auth-gate')).toBeNull()

    auth.authState.required = true
    auth.authState.unlocked = false
    await flushPromises()
    expect(document.body.querySelector('.auth-gate')).not.toBeNull()
    expect(document.body.querySelector('.gate-input')).not.toBeNull()
    wrapper.unmount()
  })

  it('shows the server error when login fails', async () => {
    axiosPost.mockRejectedValue({ response: { status: 401 } })
    const auth = await freshAuth()
    auth.authState.required = true
    auth.authState.unlocked = false
    const { default: AuthGate } = await import('@/components/AuthGate.vue')
    const wrapper = mount(AuthGate, { attachTo: document.body })
    await flushPromises()

    const input = document.body.querySelector<HTMLInputElement>('.gate-input')!
    input.value = 'bad'
    input.dispatchEvent(new Event('input'))
    // jsdom doesn't auto-submit on button.click() — dispatch the form event.
    document.body.querySelector('form.gate-form')!
      .dispatchEvent(new Event('submit', { cancelable: true }))
    await flushPromises()

    expect(document.body.querySelector('.gate-error')?.textContent).toMatch(/wrong password/i)
    expect(auth.authState.unlocked).toBe(false)
    wrapper.unmount()
  })
})
