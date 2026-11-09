// DL-147 Task 1.4 - device-local presentation prefs: persisted per browser,
// never part of the DL-138 synced settings, and the effective touch scale is
// per device class on phones/tablets while desktop/panel keep the shared value.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const putMock = vi.fn(() => Promise.resolve({ data: { success: true } }))
const broadcastMock = vi.fn()

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: { success: true, settings: {} } })),
    post: vi.fn(),
    put: (...args: unknown[]) => putMock(...args),
    delete: vi.fn(),
  },
}))

vi.mock('@/api/socket', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
    broadcastSettingsChange: (...args: unknown[]) => broadcastMock(...args),
    sendUiCommand: vi.fn(),
  },
}))

function setEnv(width: number, height: number, screenW: number, screenH: number, touch: boolean) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true })
  Object.defineProperty(window, 'innerHeight', { value: height, configurable: true })
  Object.defineProperty(window, 'screen', { value: { width: screenW, height: screenH }, configurable: true })
  Object.defineProperty(navigator, 'maxTouchPoints', { value: touch ? 5 : 0, configurable: true })
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: touch && query === '(pointer: coarse)',
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })) as unknown as typeof window.matchMedia
}

async function freshStore() {
  vi.resetModules()
  setActivePinia(createPinia())
  const { useSettingsStore } = await import('@/stores/settings')
  const { useDevicePrefs } = await import('@/services/devicePrefs')
  return { store: useSettingsStore(), prefs: useDevicePrefs() }
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  document.documentElement.removeAttribute('style')
})

describe('devicePrefs service', () => {
  it('defaults to auto touch, fit layout, keep-awake on', async () => {
    vi.resetModules()
    const { useDevicePrefs } = await import('@/services/devicePrefs')
    expect({ ...useDevicePrefs() }).toEqual({ touchMode: 'auto', layout: 'fit', keepAwake: true })
  })

  it('tolerates junk JSON and unknown values', async () => {
    localStorage.setItem('vdock_device_prefs', '{not json')
    vi.resetModules()
    let { useDevicePrefs } = await import('@/services/devicePrefs')
    expect(useDevicePrefs().touchMode).toBe('auto')

    localStorage.setItem('vdock_device_prefs', JSON.stringify({ touchMode: 'huge', layout: 7, keepAwake: 'yes' }))
    vi.resetModules()
    ;({ useDevicePrefs } = await import('@/services/devicePrefs'))
    expect({ ...useDevicePrefs() }).toEqual({ touchMode: 'auto', layout: 'fit', keepAwake: true })
  })

  it('persists changes to localStorage and restores them', async () => {
    vi.resetModules()
    let { useDevicePrefs } = await import('@/services/devicePrefs')
    useDevicePrefs().touchMode = 'tablet'
    useDevicePrefs().keepAwake = false
    await nextTick()
    expect(JSON.parse(localStorage.getItem('vdock_device_prefs')!)).toMatchObject({
      touchMode: 'tablet',
      keepAwake: false,
    })

    vi.resetModules()
    ;({ useDevicePrefs } = await import('@/services/devicePrefs'))
    expect(useDevicePrefs().touchMode).toBe('tablet')
    expect(useDevicePrefs().keepAwake).toBe(false)
  })
})

describe('effective touch scale', () => {
  it('phone auto = 1.0 and tablet auto = 1.5, whatever the shared value says', async () => {
    setEnv(390, 844, 390, 844, true)
    let { store } = await freshStore()
    store.touchMode = 'tablet'
    expect(store.touchModeMultiplier).toBe(1)

    setEnv(820, 1180, 820, 1180, true)
    ;({ store } = await freshStore())
    store.touchMode = 'normal'
    expect(store.touchModeMultiplier).toBe(1.5)
  })

  it('an explicit device choice overrides on phone/tablet only', async () => {
    setEnv(820, 1180, 820, 1180, true)
    const { store, prefs } = await freshStore()
    prefs.touchMode = 'tablet'
    expect(store.touchModeMultiplier).toBe(2)
  })

  it('desktop and panel keep using the shared touchMode, ignoring device prefs', async () => {
    setEnv(1400, 900, 1400, 900, false)
    let { store, prefs } = await freshStore()
    prefs.touchMode = 'normal'
    store.touchMode = 'tablet'
    expect(store.touchModeMultiplier).toBe(2)

    setEnv(1024, 600, 1024, 600, true)
    ;({ store, prefs } = await freshStore())
    prefs.touchMode = 'normal'
    store.touchMode = 'touch-friendly'
    expect(store.touchModeMultiplier).toBe(1.5)
  })

  it('regression: shared tablet mode on a desktop class still writes --touch-multiplier 2', async () => {
    setEnv(1400, 900, 1400, 900, false)
    const { store } = await freshStore()
    store.touchMode = 'tablet'
    store.applyTouchModeStyles()
    expect(document.documentElement.style.getPropertyValue('--touch-multiplier')).toBe('2')
  })

  it('updates the CSS multiplier when the device pref changes', async () => {
    setEnv(820, 1180, 820, 1180, true)
    const { prefs } = await freshStore()
    expect(document.documentElement.style.getPropertyValue('--touch-multiplier')).toBe('1.5')
    prefs.touchMode = 'normal'
    await nextTick()
    expect(document.documentElement.style.getPropertyValue('--touch-multiplier')).toBe('1')
  })
})

describe('sync isolation (DL-138)', () => {
  it('device prefs never reach the server, peers or the synced payload', async () => {
    setEnv(820, 1180, 820, 1180, true)
    const { store, prefs } = await freshStore()
    await store.loadSettingsFromServer()
    putMock.mockClear()
    broadcastMock.mockClear()

    prefs.touchMode = 'tablet'
    prefs.layout = 'designed'
    prefs.keepAwake = false
    await new Promise((r) => setTimeout(r, 0))
    await store.flushSettingsToServer()

    expect(putMock).not.toHaveBeenCalled()
    expect(broadcastMock).not.toHaveBeenCalled()
    expect(localStorage.getItem('vdock_settings') ?? '').not.toContain('keepAwake')
  })
})

describe('detectSmallScreenDefaults', () => {
  it('does not write the shared touchMode on phones or tablets', async () => {
    setEnv(390, 844, 390, 844, true)
    const phone = await freshStore()
    expect(phone.store.touchMode).toBe('normal')

    setEnv(820, 1180, 820, 1180, true)
    const tablet = await freshStore()
    expect(tablet.store.touchMode).toBe('normal')
  })

  it('still flips normal to tablet on the 7" panel class', async () => {
    setEnv(1024, 600, 1024, 600, true)
    const { store } = await freshStore()
    expect(store.touchMode).toBe('tablet')
  })
})
