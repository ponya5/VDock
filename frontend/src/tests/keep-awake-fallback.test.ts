// DL-011: over plain http (no Wake Lock) keep-awake falls back to a muted,
// inline, looping video; it stops with the preference.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

vi.mock('@/composables/useDeviceClass', async () => {
  const { ref } = await import('vue')
  return { useDeviceClass: () => ({ deviceClass: ref('phone'), isStandalone: ref(true) }) }
})

import { startKeepAwake, hasWakeLockApi } from '@/services/keepAwake'
import { useDevicePrefs } from '@/services/devicePrefs'

let stop: (() => void) | null = null

beforeEach(() => {
  Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true })
  ;(HTMLCanvasElement.prototype as any).captureStream = () => ({ getTracks: () => [] })
  HTMLCanvasElement.prototype.getContext = (() => ({ fillRect: () => {}, fillStyle: '' })) as any
  HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined)
  HTMLMediaElement.prototype.pause = vi.fn()
})
afterEach(() => { stop?.(); stop = null })

describe('keep-awake fallback', () => {
  it('has no Wake Lock API over plain http', () => {
    expect(hasWakeLockApi()).toBe(false)
  })

  it('plays a hidden muted inline video while wanted, removes it when turned off', async () => {
    useDevicePrefs().keepAwake = true
    stop = startKeepAwake()
    const video = document.querySelector('video') as HTMLVideoElement
    expect(video).not.toBeNull()
    expect(video.muted).toBe(true)
    expect(video.hasAttribute('playsinline')).toBe(true)
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()

    useDevicePrefs().keepAwake = false
    await nextTick()
    expect(document.querySelector('video')).toBeNull()
  })
})
