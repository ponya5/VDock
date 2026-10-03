// DL-147 Task 1.3 - the device-class model: a pure classifier pinned as a
// table, the legacy phone flag kept bit-for-bit, and the runtime refs that
// follow resize / orientation changes.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { classifyDevice, resolveLayoutClass, type DeviceClass } from '@/composables/useDeviceClass'

const probe = (
  screenW: number,
  screenH: number,
  over: Partial<{ coarse: boolean; touchPoints: number; electron: boolean }> = {},
) => ({ screenW, screenH, coarse: true, touchPoints: 5, electron: false, ...over })

describe('classifyDevice', () => {
  const cases: Array<[string, ReturnType<typeof probe>, DeviceClass]> = [
    ['iPhone 390x844', probe(390, 844), 'phone'],
    ['iPhone landscape 844x390', probe(844, 390), 'phone'],
    ['iPhone Pro Max 430x932', probe(430, 932), 'phone'],
    ['800x480 kiosk browser', probe(800, 480), 'phone'],
    ['1024x600 touch display in a browser', probe(1024, 600), 'panel'],
    ['1024x600 Electron touch panel', probe(1024, 600, { electron: true }), 'panel'],
    ['1920x1080 Electron no touch', probe(1920, 1080, { electron: true, coarse: false, touchPoints: 0 }), 'desktop'],
    ['iPad mini 744x1133', probe(744, 1133), 'tablet'],
    ['iPad 768x1024', probe(768, 1024), 'tablet'],
    ['iPad 820x1180', probe(820, 1180), 'tablet'],
    ['tablet landscape 1024x768', probe(1024, 768), 'tablet'],
    ['Galaxy Tab 1280x800', probe(1280, 800), 'tablet'],
    ['iPad Pro 1366x1024', probe(1366, 1024), 'tablet'],
    ['touch laptop, fine primary pointer', probe(1920, 1080, { coarse: false, touchPoints: 10 }), 'desktop'],
    ['mouse-only 390x844 window', probe(390, 844, { coarse: false, touchPoints: 0 }), 'desktop'],
    ['mouse-only 1440x900', probe(1440, 900, { coarse: false, touchPoints: 0 }), 'desktop'],
  ]

  it.each(cases)('%s', (_name, input, expected) => {
    expect(classifyDevice(input)).toBe(expected)
  })
})

describe('resolveLayoutClass', () => {
  it('reflows a narrow tablet window (split view) as a phone', () => {
    expect(resolveLayoutClass('tablet', 405)).toBe('phone')
    expect(resolveLayoutClass('tablet', 590)).toBe('phone')
    expect(resolveLayoutClass('tablet', 820)).toBe('tablet')
  })

  it('never changes other classes', () => {
    expect(resolveLayoutClass('phone', 300)).toBe('phone')
    expect(resolveLayoutClass('panel', 500)).toBe('panel')
    expect(resolveLayoutClass('desktop', 500)).toBe('desktop')
  })
})

interface Env {
  innerWidth: number
  innerHeight: number
  screenW: number
  screenH: number
  coarse: boolean
  touchPoints: number
}

function setEnv(env: Env) {
  Object.defineProperty(window, 'innerWidth', { value: env.innerWidth, configurable: true })
  Object.defineProperty(window, 'innerHeight', { value: env.innerHeight, configurable: true })
  Object.defineProperty(window, 'screen', {
    value: { width: env.screenW, height: env.screenH },
    configurable: true,
  })
  Object.defineProperty(navigator, 'maxTouchPoints', { value: env.touchPoints, configurable: true })
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query === '(pointer: coarse)' ? env.coarse : false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })) as unknown as typeof window.matchMedia
}

async function freshDeviceClass() {
  vi.resetModules()
  return (await import('@/composables/useDeviceClass')).useDeviceClass()
}

describe('useDeviceClass runtime', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reports orientation from the window and follows resize', async () => {
    setEnv({ innerWidth: 820, innerHeight: 1180, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    const info = await freshDeviceClass()
    expect(info.deviceClass.value).toBe('tablet')
    expect(info.orientation.value).toBe('portrait')

    setEnv({ innerWidth: 1180, innerHeight: 820, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    window.dispatchEvent(new Event('resize'))
    expect(info.orientation.value).toBe('landscape')
    expect(info.deviceClass.value).toBe('tablet')
  })

  it('a split-view window lays out as phone while the hardware class stays tablet', async () => {
    setEnv({ innerWidth: 405, innerHeight: 1180, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    const info = await freshDeviceClass()
    expect(info.deviceClass.value).toBe('tablet')
    expect(info.layoutClass.value).toBe('phone')

    setEnv({ innerWidth: 820, innerHeight: 1180, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    window.dispatchEvent(new Event('orientationchange'))
    expect(info.layoutClass.value).toBe('tablet')
  })

  it('an on-screen keyboard shrinking the viewport does not flip the class', async () => {
    setEnv({ innerWidth: 820, innerHeight: 1180, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    const info = await freshDeviceClass()
    setEnv({ innerWidth: 820, innerHeight: 500, screenW: 820, screenH: 1180, coarse: true, touchPoints: 5 })
    window.dispatchEvent(new Event('resize'))
    expect(info.deviceClass.value).toBe('tablet')
  })
})

describe('isCompactTouch keeps the legacy mobile-viewport rule exactly', () => {
  const legacy = (w: number, h: number, coarse: boolean, touchPoints: number) =>
    Math.min(w, h) <= 700 && (coarse || touchPoints > 0)

  const sizes: Array<[number, number]> = [
    [390, 844], [844, 390], [700, 1200], [701, 1200], [768, 1024], [1024, 600],
    [1024, 768], [1400, 900], [320, 480], [1280, 700],
  ]
  const combos = sizes.flatMap(([w, h]) =>
    [[true, 0], [false, 5], [false, 0], [true, 5]].map(([c, t]) => [w, h, c, t] as [number, number, boolean, number]),
  )

  beforeEach(() => vi.resetModules())

  it.each(combos)('%dx%d coarse=%s touchPoints=%d', async (w, h, coarse, touchPoints) => {
    setEnv({ innerWidth: w, innerHeight: h, screenW: w, screenH: h, coarse, touchPoints })
    const { useMobileViewport } = await import('@/utils/mobileViewport')
    expect(useMobileViewport().isMobileViewport.value).toBe(legacy(w, h, coarse, touchPoints))
  })
})
