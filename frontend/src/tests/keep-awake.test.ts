// DL-147 Task 3.4 - keep the screen on while a phone/tablet is acting as a deck
// (fullscreen or installed), using the Screen Wake Lock API where it exists.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import type { DeviceClass } from '@/composables/useDeviceClass'

const deviceClass = ref<DeviceClass>('tablet')
const isStandalone = ref(false)
vi.mock('@/composables/useDeviceClass', () => ({
  useDeviceClass: () => ({ deviceClass, isStandalone }),
}))

import { startKeepAwake, wantsKeepAwake } from '@/services/keepAwake'
import { useDevicePrefs } from '@/services/devicePrefs'

const base = { deviceClass: 'tablet' as DeviceClass, fullscreen: true, standalone: false, visible: true, enabled: true }

describe('wantsKeepAwake', () => {
  it('wants the lock on a fullscreen tablet or phone', () => {
    expect(wantsKeepAwake(base)).toBe(true)
    expect(wantsKeepAwake({ ...base, deviceClass: 'phone' })).toBe(true)
  })

  it('accepts an installed (standalone) deck without fullscreen', () => {
    expect(wantsKeepAwake({ ...base, fullscreen: false, standalone: true })).toBe(true)
  })

  it('stays off in a plain browser tab, when hidden, or when switched off', () => {
    expect(wantsKeepAwake({ ...base, fullscreen: false })).toBe(false)
    expect(wantsKeepAwake({ ...base, visible: false })).toBe(false)
    expect(wantsKeepAwake({ ...base, enabled: false })).toBe(false)
  })

  it('never keeps a desktop or the 7" panel awake', () => {
    expect(wantsKeepAwake({ ...base, deviceClass: 'desktop' })).toBe(false)
    expect(wantsKeepAwake({ ...base, deviceClass: 'panel' })).toBe(false)
  })
})

describe('startKeepAwake', () => {
  let fullscreenElement: Element | null
  let visibility: DocumentVisibilityState
  let secure: boolean
  let sentinel: { release: ReturnType<typeof vi.fn>; listeners: Array<() => void>; addEventListener: (t: string, cb: () => void) => void }
  let request: ReturnType<typeof vi.fn>
  const stops: Array<() => void> = []

  const flush = async () => {
    await nextTick()
    await Promise.resolve()
    await Promise.resolve()
  }
  const start = () => {
    const stop = startKeepAwake()
    stops.push(stop)
    return stop
  }

  beforeEach(() => {
    localStorage.clear()
    deviceClass.value = 'tablet'
    isStandalone.value = false
    useDevicePrefs().keepAwake = true
    fullscreenElement = document.documentElement
    visibility = 'visible'
    secure = true
    sentinel = {
      release: vi.fn(async () => {}),
      listeners: [],
      addEventListener(_type, cb) { this.listeners.push(cb) },
    }
    request = vi.fn(async () => sentinel)
    Object.defineProperty(document, 'fullscreenElement', { configurable: true, get: () => fullscreenElement })
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility })
    Object.defineProperty(window, 'isSecureContext', { configurable: true, get: () => secure })
    Object.defineProperty(navigator, 'wakeLock', { configurable: true, value: { request } })
  })

  afterEach(() => {
    while (stops.length) stops.pop()!()
    Reflect.deleteProperty(document, 'fullscreenElement')
    Reflect.deleteProperty(document, 'visibilityState')
    Reflect.deleteProperty(window, 'isSecureContext')
    Reflect.deleteProperty(navigator, 'wakeLock')
  })

  it('requests a screen wake lock once when fullscreen on a secure origin', async () => {
    start()
    await flush()
    document.dispatchEvent(new Event('fullscreenchange'))
    await flush()
    expect(request).toHaveBeenCalledTimes(1)
    expect(request).toHaveBeenCalledWith('screen')
  })

  it('does nothing over plain HTTP, where the Wake Lock API is unavailable', async () => {
    secure = false
    start()
    await flush()
    expect(request).not.toHaveBeenCalled()
  })

  it('releases when fullscreen is left and re-acquires on re-entry', async () => {
    start()
    await flush()
    fullscreenElement = null
    document.dispatchEvent(new Event('fullscreenchange'))
    await flush()
    expect(sentinel.release).toHaveBeenCalledTimes(1)

    fullscreenElement = document.documentElement
    document.dispatchEvent(new Event('fullscreenchange'))
    await flush()
    expect(request).toHaveBeenCalledTimes(2)
  })

  it('re-acquires when the page becomes visible again after the browser dropped the lock', async () => {
    start()
    await flush()
    visibility = 'hidden'
    sentinel.listeners.forEach((cb) => cb())
    document.dispatchEvent(new Event('visibilitychange'))
    await flush()
    visibility = 'visible'
    document.dispatchEvent(new Event('visibilitychange'))
    await flush()
    expect(request).toHaveBeenCalledTimes(2)
  })

  it('follows the device preference and the device class', async () => {
    start()
    await flush()
    useDevicePrefs().keepAwake = false
    await flush()
    expect(sentinel.release).toHaveBeenCalledTimes(1)

    useDevicePrefs().keepAwake = true
    deviceClass.value = 'desktop'
    await flush()
    expect(request).toHaveBeenCalledTimes(1)
  })

  it('stops listening and releases when the returned stop function runs', async () => {
    const stop = start()
    await flush()
    stop()
    await flush()
    expect(sentinel.release).toHaveBeenCalledTimes(1)
    document.dispatchEvent(new Event('fullscreenchange'))
    await flush()
    expect(request).toHaveBeenCalledTimes(1)
  })
})
