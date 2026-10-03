// DL-147 Task 4.1 - a visible, self-healing connection: the banner appears only
// after a real outage, Retry/wake dial at once, and a reconnect refreshes the
// deck without bouncing the viewer or interrupting an editor.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

type Handler = (...args: unknown[]) => void

const fakeSocket = {
  connected: false,
  handlers: new Map<string, Handler[]>(),
  on(event: string, cb: Handler) {
    this.handlers.set(event, [...(this.handlers.get(event) ?? []), cb])
  },
  off(event: string, cb?: Handler) {
    this.handlers.set(event, (this.handlers.get(event) ?? []).filter(h => cb && h !== cb))
  },
  emit: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  fire(event: string, ...args: unknown[]) {
    for (const h of this.handlers.get(event) ?? []) h(...args)
  },
}

vi.mock('socket.io-client', () => ({ io: vi.fn(() => fakeSocket) }))
const refreshVdock = vi.fn()
vi.mock('@/composables/useVdockRefresh', () => ({ refreshVdock: (...a: unknown[]) => refreshVdock(...a) }))
vi.mock('@/services/auth', () => ({
  getAuthToken: () => null,
  onAuthTokenChanged: vi.fn(),
  probeAuth: vi.fn(),
}))

import socketClient from '@/api/socket'
import ConnectionBanner from '@/components/ConnectionBanner.vue'
import { connection, markConnected, markDisconnected, OFFLINE_AFTER_MS, RECONNECTING_AFTER_MS } from '@/services/connection'
import { initConnectionResume } from '@/services/connectionResume'
import { useDashboardStore } from '@/stores/dashboard'

const mounted: VueWrapper[] = []

function drop() {
  fakeSocket.connected = false
  fakeSocket.fire('disconnect', 'transport close')
}

function join() {
  fakeSocket.connected = true
  fakeSocket.fire('connect')
}

beforeEach(() => {
  vi.useFakeTimers()
  setActivePinia(createPinia())
  fakeSocket.handlers.clear()
  fakeSocket.connected = false
  fakeSocket.connect.mockClear()
  refreshVdock.mockReset()
  markConnected()
  socketClient.disconnect()
  socketClient.connect()
})

afterEach(() => {
  mounted.splice(0).forEach(w => w.unmount())
  markConnected()
  vi.useRealTimers()
})

describe('connection status', () => {
  it('stays silent for a drop shorter than two seconds', () => {
    drop()
    vi.advanceTimersByTime(RECONNECTING_AFTER_MS - 1)
    expect(connection.status).toBe('connected')
    join()
    vi.advanceTimersByTime(OFFLINE_AFTER_MS)
    expect(connection.status).toBe('connected')
  })

  it('reports reconnecting after 2 s and offline after 15 s, without restarting the clock on repeat errors', () => {
    drop()
    vi.advanceTimersByTime(RECONNECTING_AFTER_MS)
    expect(connection.status).toBe('reconnecting')
    vi.advanceTimersByTime(5000)
    fakeSocket.fire('connect_error', new Error('nope'))
    vi.advanceTimersByTime(OFFLINE_AFTER_MS - RECONNECTING_AFTER_MS - 5000)
    expect(connection.status).toBe('offline')
  })

  it('clears as soon as the socket connects', () => {
    drop()
    vi.advanceTimersByTime(OFFLINE_AFTER_MS)
    join()
    expect(connection.status).toBe('connected')
  })

  it('does not treat a deliberate disconnect as an outage', () => {
    fakeSocket.fire('disconnect', 'io client disconnect')
    vi.advanceTimersByTime(OFFLINE_AFTER_MS)
    expect(connection.status).toBe('connected')
  })
})

describe('ConnectionBanner', () => {
  function mountBanner() {
    const wrapper = mount(ConnectionBanner)
    mounted.push(wrapper)
    return wrapper
  }

  it('is hidden while connected and for the first 2 s of a drop', async () => {
    const wrapper = mountBanner()
    expect(wrapper.find('[data-testid="connection-banner"]').exists()).toBe(false)
    markDisconnected()
    vi.advanceTimersByTime(RECONNECTING_AFTER_MS - 1)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="connection-banner"]').exists()).toBe(false)
  })

  it('says Reconnecting after 2 s, then names the host with a Retry after 15 s', async () => {
    const wrapper = mountBanner()
    markDisconnected()
    vi.advanceTimersByTime(RECONNECTING_AFTER_MS)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Reconnecting')
    expect(wrapper.find('button').exists()).toBe(false)

    vi.advanceTimersByTime(OFFLINE_AFTER_MS)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain(`Can't reach VDock at ${window.location.hostname}`)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('Retry dials the socket now', async () => {
    const wrapper = mountBanner()
    markDisconnected()
    vi.advanceTimersByTime(OFFLINE_AFTER_MS)
    await wrapper.vm.$nextTick()
    await wrapper.find('button').trigger('click')
    expect(fakeSocket.connect).toHaveBeenCalledTimes(1)
  })
})

describe('initConnectionResume', () => {
  let stop: () => void

  beforeEach(() => {
    stop = initConnectionResume()
  })
  afterEach(() => stop())

  function setVisibility(state: DocumentVisibilityState) {
    Object.defineProperty(document, 'visibilityState', { value: state, configurable: true })
    document.dispatchEvent(new Event('visibilitychange'))
  }

  it('dials once when the page returns to the foreground with a dead socket', () => {
    setVisibility('visible')
    expect(fakeSocket.connect).toHaveBeenCalledTimes(1)
  })

  it('leaves a live socket alone and ignores going to the background', () => {
    fakeSocket.connected = true
    setVisibility('visible')
    fakeSocket.connected = false
    setVisibility('hidden')
    expect(fakeSocket.connect).not.toHaveBeenCalled()
  })

  it('does not refresh on the first connect, but does on every later one, keeping the viewer in place', () => {
    join()
    expect(refreshVdock).not.toHaveBeenCalled()
    drop()
    join()
    expect(refreshVdock).toHaveBeenCalledTimes(1)
    expect(refreshVdock).toHaveBeenCalledWith({ keepPosition: true })
  })

  it('does not refresh under an open editor', () => {
    join()
    useDashboardStore().isEditMode = true
    drop()
    join()
    expect(refreshVdock).not.toHaveBeenCalled()
  })
})
