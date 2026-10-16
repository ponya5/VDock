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

/** Whether the real Screen Wake Lock is available (secure context + API). */
export function hasWakeLockApi(): boolean {
  return wakeLock() !== null
}

/**
 * Fallback for plain http on the LAN, where Wake Lock does not exist (DL-011):
 * a muted, inline, looping 2 px video fed by a canvas stream - the "NoSleep"
 * technique; browsers keep the screen on while a video plays. Best effort:
 * some OS versions ignore it, and the menu says so.
 */
class VideoKeepAwake {
  private video: HTMLVideoElement | null = null
  private timer: ReturnType<typeof setInterval> | null = null

  start(): void {
    if (this.video) { void this.video.play().catch(() => {}); return }
    const canvas = document.createElement('canvas')
    canvas.width = 2
    canvas.height = 2
    const paint = canvas.getContext('2d')
    const capture = (canvas as HTMLCanvasElement & { captureStream?: (fps: number) => MediaStream }).captureStream
    if (!paint || !capture) return
    const video = document.createElement('video')
    video.muted = true
    video.loop = true
    video.setAttribute('playsinline', '')
    video.setAttribute('aria-hidden', 'true')
    video.style.cssText = 'position:fixed;left:0;bottom:0;width:2px;height:2px;opacity:0.01;pointer-events:none;'
    video.srcObject = capture.call(canvas, 1)
    let tick = 0
    // A stream only produces frames when the canvas changes.
    this.timer = setInterval(() => {
      tick ^= 1
      paint.fillStyle = tick ? '#000' : '#010101'
      paint.fillRect(0, 0, 2, 2)
    }, 1000)
    document.body.appendChild(video)
    this.video = video
    void video.play().catch(() => {})
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer)
    this.timer = null
    this.video?.pause()
    this.video?.remove()
    this.video = null
  }
}

/** Starts following fullscreen / visibility / prefs; returns a stop function. */
export function startKeepAwake(): () => void {
  const { deviceClass, isStandalone } = useDeviceClass()
  const prefs = useDevicePrefs()
  let sentinel: WakeLockSentinelLike | null = null
  let requesting = false
  const fallback = new VideoKeepAwake()

  async function acquire() {
    const api = wakeLock()
    if (!api) { fallback.start(); return }
    if (sentinel || requesting) return
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
    fallback.stop()
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
  // Video playback may need a user gesture: retry on every tap (cheap no-op
  // once it plays).
  document.addEventListener('pointerdown', sync, { passive: true })
  sync()

  return () => {
    stopWatch()
    document.removeEventListener('fullscreenchange', sync)
    document.removeEventListener('visibilitychange', sync)
    document.removeEventListener('pointerdown', sync)
    release()
  }
}
