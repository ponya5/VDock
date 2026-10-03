import { reactive, watch } from 'vue'

/**
 * DL-147 — presentation preferences that belong to THIS browser/device only.
 *
 * Deliberately separate from the DL-138 synced user settings: they live in
 * localStorage, never enter `PersistedUserSettings`, and so are never PUT to
 * the server or broadcast to other devices. A phone's touch scale must not
 * rewrite the desktop's.
 */
export interface DevicePrefs {
  touchMode: 'auto' | 'normal' | 'touch-friendly' | 'tablet'
  layout: 'fit' | 'designed'
  keepAwake: boolean
}

export const DEVICE_PREFS_KEY = 'vdock_device_prefs'

const DEFAULTS: DevicePrefs = { touchMode: 'auto', layout: 'fit', keepAwake: true }

const TOUCH_MODES: readonly DevicePrefs['touchMode'][] = ['auto', 'normal', 'touch-friendly', 'tablet']
const LAYOUTS: readonly DevicePrefs['layout'][] = ['fit', 'designed']

function read(): DevicePrefs {
  try {
    const raw = JSON.parse(localStorage.getItem(DEVICE_PREFS_KEY) ?? 'null')
    if (!raw || typeof raw !== 'object') return { ...DEFAULTS }
    return {
      touchMode: TOUCH_MODES.includes(raw.touchMode) ? raw.touchMode : DEFAULTS.touchMode,
      layout: LAYOUTS.includes(raw.layout) ? raw.layout : DEFAULTS.layout,
      keepAwake: typeof raw.keepAwake === 'boolean' ? raw.keepAwake : DEFAULTS.keepAwake,
    }
  } catch {
    return { ...DEFAULTS }
  }
}

let prefs: DevicePrefs | null = null

/** Reactive, persisted-on-change device prefs (one shared instance). */
export function useDevicePrefs(): DevicePrefs {
  if (!prefs) {
    prefs = reactive(read())
    watch(prefs, (value) => {
      try {
        localStorage.setItem(DEVICE_PREFS_KEY, JSON.stringify(value))
      } catch {
        // Storage can be unavailable (private mode / quota); prefs stay in memory.
      }
    })
  }
  return prefs
}
