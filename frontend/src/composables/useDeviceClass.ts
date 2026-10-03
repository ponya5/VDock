import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { useElectron } from '@/composables/useElectron'
import { isRunningStandalone } from '@/utils/fullscreenSupport'

/**
 * DL-147 — one model of "what device is this" instead of six ad-hoc rules.
 *
 * `deviceClass` is hardware-stable (derived from the physical screen, so an
 * on-screen keyboard or a resized window cannot flip it). `layoutClass` is
 * what the layout should follow: a tablet squeezed into a split-view pane
 * lays out as a phone.
 */
export type DeviceClass = 'phone' | 'tablet' | 'panel' | 'desktop'
export type Orientation = 'portrait' | 'landscape'

export interface DeviceProbe {
  screenW: number
  screenH: number
  coarse: boolean
  touchPoints: number
  electron: boolean
}

const PHONE_MAX_SHORT = 700
const PHONE_MAX_LONG_EXCLUSIVE = 960
/** Narrower than this a tablet window is a split-view / slide-over pane. */
const TABLET_SPLIT_WIDTH = 600

/** Pure classifier (first matching rule wins); unit-tested as a table. */
export function classifyDevice(probe: DeviceProbe): DeviceClass {
  const touch = probe.coarse || probe.touchPoints > 0
  const short = Math.min(probe.screenW, probe.screenH)
  const long = Math.max(probe.screenW, probe.screenH)

  if (probe.electron) return touch && short <= PHONE_MAX_SHORT ? 'panel' : 'desktop'
  if (!touch) return 'desktop'
  if (short <= PHONE_MAX_SHORT && long < PHONE_MAX_LONG_EXCLUSIVE) return 'phone'
  if (short <= PHONE_MAX_SHORT) return 'panel'
  if (probe.coarse) return 'tablet'
  return 'desktop'
}

/** Layout follows the window: a narrow tablet window reflows as a phone. */
export function resolveLayoutClass(deviceClass: DeviceClass, innerWidth: number): DeviceClass {
  return deviceClass === 'tablet' && innerWidth < TABLET_SPLIT_WIDTH ? 'phone' : deviceClass
}

const vw = ref(0)
const vh = ref(0)
const deviceClass = ref<DeviceClass>('desktop')
const isTouch = ref(false)
const isCompactTouch = ref(false)
const isStandalone = ref(false)

const orientation = computed<Orientation>(() => (vh.value > vw.value ? 'portrait' : 'landscape'))
const layoutClass = computed<DeviceClass>(() => resolveLayoutClass(deviceClass.value, vw.value))

function update() {
  vw.value = window.innerWidth
  vh.value = window.innerHeight
  const coarse =
    typeof window.matchMedia === 'function' && window.matchMedia('(pointer: coarse)').matches
  const touchPoints = navigator.maxTouchPoints || 0
  const electron = useElectron().isElectron()

  isTouch.value = coarse || touchPoints > 0
  // Legacy rule, kept bit-for-bit for every pre-DL-147 `useMobileViewport` caller.
  isCompactTouch.value = Math.min(vw.value, vh.value) <= PHONE_MAX_SHORT && isTouch.value
  isStandalone.value = isRunningStandalone()
  deviceClass.value = classifyDevice({
    // The Electron window is the panel itself; `screen` may describe another monitor.
    screenW: electron ? vw.value : window.screen.width,
    screenH: electron ? vh.value : window.screen.height,
    coarse,
    touchPoints,
    electron,
  })
}

let installed = false

export interface DeviceInfo {
  deviceClass: Ref<DeviceClass>
  layoutClass: ComputedRef<DeviceClass>
  orientation: ComputedRef<Orientation>
  viewportWidth: Ref<number>
  isTouch: Ref<boolean>
  isCompactTouch: Ref<boolean>
  isStandalone: Ref<boolean>
}

export function useDeviceClass(): DeviceInfo {
  if (!installed && typeof window !== 'undefined') {
    installed = true
    update()
    window.addEventListener('resize', update)
    window.addEventListener('orientationchange', update)
    if (typeof window.matchMedia === 'function') {
      window.matchMedia('(pointer: coarse)').addEventListener?.('change', update)
    }
  }
  return { deviceClass, layoutClass, orientation, viewportWidth: vw, isTouch, isCompactTouch, isStandalone }
}
