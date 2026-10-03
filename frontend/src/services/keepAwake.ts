import { watch } from 'vue'
import { useDeviceClass, type DeviceClass } from '@/composables/useDeviceClass'
import { useDevicePrefs } from '@/services/devicePrefs'

/**
 * DL-147 - a phone or tablet on a stand is a deck, not a browser tab: keep
 * its screen on while it runs fullscreen or installed. Uses the Screen Wake
 * Lock API, which browsers only expose on secure origins - over plain
 * `http://192.168.x.x` there is no lock to take and the OS timeout applies.
 */
export interface KeepAwakeState {
  deviceClass: DeviceClass
  fullscreen: boolean
  standalone: boolean
  visible: boolean
  enabled: boolean
}

export function wantsKeepAwake(state: KeepAwakeState): boolean {
  const handheld = state.deviceClass === 'phone' || state.deviceClass === 'tablet'
  return handheld && state.enabled && state.visible && (state.fullscreen || state.standalone)
}

interface WakeLockSentinelLike {
  release(): Promise<void>
  addEventListener(type: 'release', listener: () => void): void
}

function wakeLock(): { request(type: 'screen'): Promise<WakeLockSentinelLike> } | null {
  if (typeof navigator === 'undefined' || !window.isSecureContext) return null
  return (navigator as Navigator & { wakeLock?: { request(type: 'screen'): Promise<WakeLockSentinelLike> } }).wakeLock ?? null
}

/** Starts following fullscreen / visibility / prefs; returns a stop function. */
export function startKeepAwake(): () => void {
  const { deviceClass, isStandalone } = useDeviceClass()
  const prefs = useDevicePrefs()
  let sentinel: WakeLockSentinelLike | null = null
  let requesting = false

  async function acquire() {
    const api = wakeLock()
    if (!api || sentinel || requesting) return
    requesting = true
    try {
      const lock = await api.request('screen')
      // The browser also drops the lock on its own (tab hidden, low battery).
      lock.addEventListener('release', () => { if (sentinel === lock) sentinel = null })
      sentinel = lock
    } catch {
      // Denied (battery saver, no user activation yet): the next sync retries.
    } finally {
      requesting = false
    }
  }

  function release() {
    const lock = sentinel
    sentinel = null
    void lock?.release().catch(() => {})
  }

  function sync() {
    const want = wantsKeepAwake({
      deviceClass: deviceClass.value,
      fullscreen: !!document.fullscreenElement,
      standalone: isStandalone.value,
      visible: document.visibilityState === 'visible',
      enabled: prefs.keepAwake,
    })
    if (want) void acquire()
    else release()
  }

  const stopWatch = watch([deviceClass, isStandalone, () => prefs.keepAwake], sync)
  document.addEventListener('fullscreenchange', sync)
  document.addEventListener('visibilitychange', sync)
  sync()

  return () => {
    stopWatch()
    document.removeEventListener('fullscreenchange', sync)
    document.removeEventListener('visibilitychange', sync)
    release()
  }
}
