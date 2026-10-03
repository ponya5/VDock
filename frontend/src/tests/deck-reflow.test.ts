// DL-147 Task 2.2 - DeckGrid shows a portrait-folded copy of a landscape-authored
// page on phones, and the rotate gate retires for the phones that now have it.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { computed, ref, nextTick, type Component } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import type { Button, Page } from '@/types'
import type { DeviceClass, Orientation } from '@/composables/useDeviceClass'

const device = {
  deviceClass: ref<DeviceClass>('phone'),
  orientation: ref<Orientation>('portrait'),
  isCompactTouch: ref(true),
}

vi.mock('@/composables/useDeviceClass', () => ({
  useDeviceClass: () => ({
    deviceClass: device.deviceClass,
    layoutClass: computed(() => device.deviceClass.value),
    orientation: device.orientation,
    viewportWidth: ref(390),
    isTouch: ref(true),
    isCompactTouch: device.isCompactTouch,
    isStandalone: ref(false),
  }),
}))
vi.mock('@/composables/useParallax', () => ({ useParallax: () => ({ tiltX: ref(0), tiltY: ref(0) }) }))

import DeckGrid from '@/components/DeckGrid.vue'
import RotateToLandscape from '@/components/RotateToLandscape.vue'
import { useDevicePrefs } from '@/services/devicePrefs'

function btn(id: string, row: number, col: number, cols = 1): Button {
  return {
    id, label: id, shape: 'rounded', position: { row, col }, size: { rows: 1, cols }, enabled: true,
  } as Button
}

const MEDIA: Page = {
  id: 'media',
  name: 'Media',
  grid_config: { rows: 3, cols: 6 },
  buttons: [btn('a', 0, 0), btn('b', 0, 1), btn('c', 0, 5), btn('d', 1, 2), btn('e', 2, 0), btn('f', 2, 4)],
}

class FakeResizeObserver {
  static size = { width: 390, height: 780 }
  constructor(private cb: (entries: unknown[]) => void) {}
  observe() {
    const { width, height } = FakeResizeObserver.size
    this.cb([{ contentRect: { width, height } }])
  }
  disconnect() {}
}

const DeckButtonStub = {
  props: ['button'],
  template: '<div class="deck-button-stub" :data-id="button.id" :data-row="button.position.row" :data-col="button.position.col" />',
}

const mounted: VueWrapper[] = []

function mountGrid(props: Record<string, unknown> = {}) {
  const wrapper = mount(DeckGrid as Component, {
    props: { page: MEDIA, ...props },
    attachTo: document.body,
    global: { stubs: { DeckButton: DeckButtonStub, DeckOverlay: true, FontAwesomeIcon: true } },
  })
  mounted.push(wrapper)
  return wrapper
}

function cells(wrapper: VueWrapper) {
  return wrapper.findAll('.deck-button-stub').map((el) => `${el.attributes('data-id')}@${el.attributes('data-row')},${el.attributes('data-col')}`)
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.stubGlobal('ResizeObserver', FakeResizeObserver)
  FakeResizeObserver.size = { width: 390, height: 780 }
  device.deviceClass.value = 'phone'
  device.orientation.value = 'portrait'
  device.isCompactTouch.value = true
  useDevicePrefs().layout = 'fit'
})

afterEach(() => {
  while (mounted.length) mounted.pop()!.unmount()
  vi.unstubAllGlobals()
})

describe('DeckGrid portrait reflow', () => {
  it('folds the 3x6 page into 3 columns in reading order on a portrait phone', async () => {
    const wrapper = mountGrid()
    await nextTick()
    expect(cells(wrapper)).toEqual(['a@0,0', 'b@0,1', 'c@0,2', 'd@1,0', 'e@1,1', 'f@1,2'])
    expect(wrapper.attributes('style')).toContain('repeat(3, minmax(0, 1fr))')
  })

  it('renders no placeholder tiles in the folded deck (they would become stray grid rows)', async () => {
    const wrapper = mountGrid()
    await nextTick()
    expect(wrapper.findAll('.button-placeholder')).toHaveLength(0)

    const editing = mountGrid({ isEditMode: true })
    await nextTick()
    expect(editing.findAll('.button-placeholder').length).toBeGreaterThan(0)
  })

  it('keeps the authored grid in edit mode', async () => {
    const wrapper = mountGrid({ isEditMode: true })
    await nextTick()
    expect(cells(wrapper)).toContain('c@0,5')
    expect(wrapper.attributes('style')).toContain('repeat(6, minmax(0, 1fr))')
  })

  it('keeps the authored grid when the device prefers "as designed"', async () => {
    useDevicePrefs().layout = 'designed'
    const wrapper = mountGrid()
    await nextTick()
    expect(cells(wrapper)).toContain('c@0,5')
  })

  it('keeps the authored grid in landscape', async () => {
    FakeResizeObserver.size = { width: 844, height: 300 }
    const wrapper = mountGrid()
    await nextTick()
    expect(cells(wrapper)).toContain('c@0,5')
    expect(wrapper.attributes('style')).toContain('repeat(6, minmax(0, 1fr))')
  })

  it.each<DeviceClass>(['panel', 'desktop'])('leaves the %s class on the authored grid', async (cls) => {
    device.deviceClass.value = cls
    const wrapper = mountGrid()
    await nextTick()
    expect(cells(wrapper)).toContain('c@0,5')
  })

  describe('tablet', () => {
    beforeEach(() => {
      device.deviceClass.value = 'tablet'
      FakeResizeObserver.size = { width: 820, height: 1100 }
    })

    it('folds the page in portrait, in reading order, like the phone', async () => {
      const wrapper = mountGrid()
      await nextTick()
      expect(cells(wrapper)).toEqual(['a@0,0', 'b@0,1', 'c@0,2', 'd@1,0', 'e@1,1', 'f@1,2'])
      expect(wrapper.attributes('style')).toContain('repeat(3, minmax(0, 1fr))')
    })

    it('keeps the authored grid in landscape and in edit mode', async () => {
      FakeResizeObserver.size = { width: 1180, height: 760 }
      const landscape = mountGrid()
      await nextTick()
      expect(cells(landscape)).toContain('c@0,5')

      FakeResizeObserver.size = { width: 820, height: 1100 }
      const editing = mountGrid({ isEditMode: true })
      await nextTick()
      expect(cells(editing)).toContain('c@0,5')
    })

    it('scrolls vertically below a 96px cell (a larger floor than the phone)', async () => {
      const many: Page = {
        ...MEDIA,
        buttons: Array.from({ length: 30 }, (_, i) => btn(`k${i}`, Math.floor(i / 6) % 3, i % 6)),
      }
      FakeResizeObserver.size = { width: 820, height: 900 }
      const wrapper = mountGrid({ page: many })
      await nextTick()
      const style = wrapper.attributes('style') ?? ''
      expect(style).toContain('repeat(10, 96px)')
      expect(style).toContain('overflow-x: hidden')
    })
  })

  it('scrolls vertically (never sideways) when the folded rows would be too short', async () => {
    const many: Page = {
      ...MEDIA,
      buttons: Array.from({ length: 30 }, (_, i) => btn(`k${i}`, Math.floor(i / 6) % 3, i % 6)),
    }
    FakeResizeObserver.size = { width: 390, height: 500 }
    const wrapper = mountGrid({ page: many })
    await nextTick()
    const style = wrapper.attributes('style') ?? ''
    expect(style).toContain('overflow-y: auto')
    expect(style).toContain('overflow-x: hidden')
    expect(style).toContain('repeat(10, 72px)')
  })

  it('never mutates the authored page', async () => {
    const snapshot = JSON.stringify(MEDIA)
    mountGrid()
    await nextTick()
    expect(JSON.stringify(MEDIA)).toBe(snapshot)
  })
})

describe('RotateToLandscape gate', () => {
  function gateShown(opts: {
    deviceClass: DeviceClass
    orientation: Orientation
    compactTouch: boolean
    layout: 'fit' | 'designed'
    portraitAllowed?: boolean
  }) {
    device.deviceClass.value = opts.deviceClass
    device.orientation.value = opts.orientation
    device.isCompactTouch.value = opts.compactTouch
    useDevicePrefs().layout = opts.layout
    const wrapper = mount(RotateToLandscape, {
      props: { portraitAllowed: opts.portraitAllowed },
      global: { stubs: { FontAwesomeIcon: true } },
    })
    mounted.push(wrapper)
    return wrapper.find('.rotate-gate').exists()
  }

  it('is retired for a portrait phone showing the fitted layout', () => {
    expect(gateShown({ deviceClass: 'phone', orientation: 'portrait', compactTouch: true, layout: 'fit' })).toBe(false)
  })

  it('comes back for a phone that asked for the layout "as designed"', () => {
    expect(gateShown({ deviceClass: 'phone', orientation: 'portrait', compactTouch: true, layout: 'designed' })).toBe(true)
  })

  it('never shows in landscape', () => {
    expect(gateShown({ deviceClass: 'phone', orientation: 'landscape', compactTouch: true, layout: 'designed' })).toBe(false)
  })

  it('keeps the 7" panel exactly as before: portrait still gates', () => {
    expect(gateShown({ deviceClass: 'panel', orientation: 'portrait', compactTouch: true, layout: 'fit' })).toBe(true)
  })

  it('keeps honouring the screensaver / agent console exemption', () => {
    expect(gateShown({
      deviceClass: 'phone', orientation: 'portrait', compactTouch: true, layout: 'designed', portraitAllowed: true,
    })).toBe(false)
  })

  it('never gates non-touch or large devices', () => {
    expect(gateShown({ deviceClass: 'desktop', orientation: 'portrait', compactTouch: false, layout: 'fit' })).toBe(false)
    expect(gateShown({ deviceClass: 'tablet', orientation: 'portrait', compactTouch: false, layout: 'designed' })).toBe(false)
  })
})
