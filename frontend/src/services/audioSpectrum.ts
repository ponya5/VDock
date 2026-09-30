import { reactive, readonly } from 'vue'
import socketClient from '@/api/socket'

/**
 * Live output-audio spectrum (DL-117): 20 log-spaced bands, pushed by the
 * backend's WASAPI loopback monitor at up to ~14 Hz.
 *
 * `live` flips false on a ~2 s heartbeat when nothing is playing, so the
 * widget can relax to a flat baseline; `lastSeenAt` staying null means the
 * backend never emitted at all (deps missing / not Windows / capture off)
 * — the honest "unavailable" state.
 */

export interface AudioSpectrumFrame {
  bands: number[]
  level: number
  live: boolean
  lastSeenAt: number | null
}

interface AudioSpectrumPayload {
  bands?: number[]
  level?: number
  live?: boolean
  ts?: number
}

const BAND_COUNT = 20

const state = reactive<AudioSpectrumFrame>({
  bands: new Array<number>(BAND_COUNT).fill(0),
  level: 0,
  live: false,
  lastSeenAt: null
})

let subscribed = false

export function initAudioSpectrum(): void {
  if (subscribed) return
  subscribed = true
  socketClient.on('audio_spectrum', (payload: AudioSpectrumPayload) => {
    const bands = Array.isArray(payload?.bands) ? payload.bands : []
    for (let i = 0; i < BAND_COUNT; i++) {
      const v = Number(bands[i])
      state.bands[i] = Number.isFinite(v) ? Math.max(0, Math.min(100, v)) : 0
    }
    state.level = Math.max(0, Math.min(100, Number(payload?.level) || 0))
    state.live = payload?.live === true
    state.lastSeenAt = Date.now()
  })
}

/**
 * Reactive view of the spectrum stream. Attaches the socket listener once;
 * callers get a readonly frame — copy values out, don't mutate.
 */
export function useAudioSpectrum(): Readonly<AudioSpectrumFrame> {
  initAudioSpectrum()
  return readonly(state)
}
