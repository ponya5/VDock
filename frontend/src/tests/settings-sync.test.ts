import { test, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '../stores/settings'
import apiClient from '@/api/client'
import socketClient from '@/api/socket'

/**
 * DL-138 — field-level settings sync. A phone booting fresh must not be
 * able to push factory defaults over the shared server file (the boot
 * stomp that flipped the saver back to the widget dashboard), and a stale
 * client's save must only propagate the keys it actually changed.
 */

const putMock = vi.fn(() => Promise.resolve({ data: { success: true } }))
const getMock = vi.fn()

vi.mock('@/api/client', () => ({
  default: {
    get: (...args: unknown[]) => getMock(...args),
    post: vi.fn(),
    put: (...args: unknown[]) => putMock(...args),
    delete: vi.fn(),
  },
}))

const broadcastMock = vi.fn()
const socketHandlers = new Map<string, (...args: unknown[]) => void>()

vi.mock('@/api/socket', () => ({
  default: {
    on: vi.fn((event: string, cb: (...args: unknown[]) => void) => {
      socketHandlers.set(event, cb)
    }),
    off: vi.fn(),
    broadcastSettingsChange: (...args: unknown[]) => broadcastMock(...args),
    sendUiCommand: vi.fn(),
  },
}))

function serverReturns(settings: Record<string, unknown>) {
  getMock.mockResolvedValue({ data: { success: true, settings } })
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  socketHandlers.clear()
  // Desktop-sized viewport so detectSmallScreenDefaults() stays out of the
  // way — on jsdom's default 1024×768 it would queue touchMode saves.
  Object.defineProperty(window, 'innerWidth', { value: 1400, configurable: true })
  Object.defineProperty(window, 'innerHeight', { value: 900, configurable: true })
  setActivePinia(createPinia())
})

test('pre-sync saves never reach the server or peers — the boot stomp fix', async () => {
  const store = useSettingsStore()
  store.uiBrightness = 55
  await new Promise(r => setTimeout(r, 0))
  await store.flushSettingsToServer()

  expect(putMock).not.toHaveBeenCalled()
  expect(broadcastMock).not.toHaveBeenCalled()
  // …but the local cache still recorded the edit for next boot.
  expect(localStorage.getItem('vdock_settings')).toContain('"uiBrightness":55')
})

test('after the first sync, saves PUT only the keys that changed', async () => {
  serverReturns({ uiBrightness: 100, screensaverStyle: 'spectrum' })
  const store = useSettingsStore()
  await store.loadSettingsFromServer()

  putMock.mockClear() // the post-sync registration flush isn't the edit
  store.uiBrightness = 61
  await new Promise(r => setTimeout(r, 0))
  await store.flushSettingsToServer()

  const bodies = putMock.mock.calls.map(c => (c[1] as { settings: Record<string, unknown> }).settings)
  const sent = bodies.find(b => b.uiBrightness === 61)
  expect(sent).toEqual({ uiBrightness: 61 })
  // …and no call ever drags untouched keys along.
  for (const body of bodies) {
    expect(body).not.toHaveProperty('screensaverStyle')
  }
})

test('untouched stale keys never travel — the stomp vector is gone', async () => {
  // This client's localStorage is stale: it says widgets while the server
  // says spectrum. A save must not resurrect 'widgets' anywhere.
  localStorage.setItem('vdock_settings', JSON.stringify({ screensaverStyle: 'widgets', uiBrightness: 90 }))
  serverReturns({ screensaverStyle: 'spectrum', uiBrightness: 90 })
  const store = useSettingsStore()
  await store.loadSettingsFromServer()
  expect(store.screensaverStyle).toBe('spectrum') // healed, not stomped

  store.uiBrightness = 70
  await new Promise(r => setTimeout(r, 0))
  await store.flushSettingsToServer()

  for (const call of putMock.mock.calls) {
    const sent = (call[1] as { settings: Record<string, unknown> }).settings
    expect(sent).not.toHaveProperty('screensaverStyle')
  }
})

test('a remote apply does not echo back out as a broadcast', async () => {
  serverReturns({ screensaverStyle: 'spectrum' })
  const store = useSettingsStore()
  await store.loadSettingsFromServer()
  store.initLiveSync()

  broadcastMock.mockClear()
  socketHandlers.get('user_settings_updated')?.({ settings: { spectrumSkin: 'aurora' } })
  await new Promise(r => setTimeout(r, 0))

  expect(store.spectrumSkin).toBe('aurora')
  expect(broadcastMock).not.toHaveBeenCalled()
})

test('broadcasts carry only the changed subset', async () => {
  serverReturns({ uiBrightness: 100 })
  const store = useSettingsStore()
  await store.loadSettingsFromServer()
  store.initLiveSync()

  store.uiBrightness = 40
  await new Promise(r => setTimeout(r, 0))

  expect(broadcastMock).toHaveBeenCalledTimes(1)
  expect(broadcastMock.mock.calls[0][0]).toEqual({ uiBrightness: 40 })
})
