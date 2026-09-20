import { useSettingsStore } from '@/stores/settings'

/**
 * Press feedback — a WebAudio tick so the panel feels physical.
 *
 * One shared AudioContext, created lazily on the first press (browsers block
 * audio before a user gesture, and a pointerdown IS a gesture — so this is
 * always allowed). No audio files to ship or license; each style is a short
 * oscillator blip shaped by frequency + decay.
 */

let ctx: AudioContext | null = null

interface SoundSpec {
  freq: number
  endFreq?: number // pitch sweep target — gives 'pop' its pop
  duration: number
  type: OscillatorType
  gain: number
}

const SOUNDS: Record<'click' | 'blip' | 'pop', SoundSpec> = {
  click: { freq: 2400, duration: 0.035, type: 'square', gain: 0.05 },
  blip: { freq: 880, duration: 0.08, type: 'sine', gain: 0.08 },
  pop: { freq: 500, endFreq: 180, duration: 0.09, type: 'sine', gain: 0.12 },
}

export function usePressFeedback() {
  const settingsStore = useSettingsStore()

  function playPressSound() {
    if (!settingsStore.pressSoundEnabled) return
    const style = settingsStore.pressSoundStyle
    if (style === 'none') return

    try {
      ctx ??= new AudioContext()
      if (ctx.state === 'suspended') void ctx.resume()

      const spec = SOUNDS[style]
      const osc = ctx.createOscillator()
      const amp = ctx.createGain()
      const now = ctx.currentTime

      osc.type = spec.type
      osc.frequency.setValueAtTime(spec.freq, now)
      if (spec.endFreq) {
        osc.frequency.exponentialRampToValueAtTime(spec.endFreq, now + spec.duration)
      }
      amp.gain.setValueAtTime(spec.gain, now)
      amp.gain.exponentialRampToValueAtTime(0.0001, now + spec.duration)

      osc.connect(amp).connect(ctx.destination)
      osc.start(now)
      osc.stop(now + spec.duration)
    } catch {
      // No audio device / blocked context — feedback is optional, never fatal.
    }
  }

  return { playPressSound }
}
