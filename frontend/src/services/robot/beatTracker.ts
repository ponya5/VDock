/**
 * DL-165 — beat/tempo tracker for the robot buddy. Fed the live spectrum frames
 * (20 log bands, 0..100, ~22 Hz); detects bass onsets, estimates BPM from the
 * inter-onset intervals (folded into 70..175 BPM), and exposes a per-frame
 * `pulse` (1 on a beat, decaying) so the head can move on the beat. When the
 * onset detector misses a beat but the tempo is stable, the beat is predicted.
 * Pure; time is passed in.
 */
export type Tempo = 'slow' | 'mid' | 'fast'
export type Vibe = 'calm' | 'groove' | 'hype'

export interface BeatInfo {
  bpm: number | null
  /** 0..1 — how steady the detected tempo is. Below ~0.5 callers should not trust `pulse`. */
  confidence: number
  /** 1 right on a beat, decaying to 0 over ~60% of the beat period. */
  pulse: number
  /** Increments on every beat (real or predicted) — use parity to alternate sway sides. */
  beatIndex: number
  /** Smoothed loudness 0..1. */
  energy: number
  tempo: Tempo | null
  vibe: Vibe
}

const BASS_BANDS = 4
const MIN_GAP_MS = 280          // refractory period (≈214 BPM ceiling)
const WINDOW = 18               // onsets kept
const BPM_MIN = 70
const BPM_MAX = 175
const STALE_MS = 3500           // no onset this long → tempo forgotten

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export function foldBpm(bpm: number): number {
  let b = bpm
  while (b < BPM_MIN) b *= 2
  while (b > BPM_MAX) b /= 2
  return b
}

export class BeatTracker {
  private slow = 0              // slow bass average (the adaptive threshold base)
  private prevBass = 0
  private above = false
  private onsets: number[] = []
  private bpm: number | null = null
  private confidence = 0
  private lastBeatAt = -Infinity
  private beatIndex = 0
  private energy = 0
  private tempo: Tempo | null = null
  private vibe: Vibe = 'calm'
  private lastFeedAt = -Infinity

  reset(): void {
    this.slow = 0; this.prevBass = 0; this.above = false; this.onsets = []
    this.bpm = null; this.confidence = 0; this.lastBeatAt = -Infinity
    this.energy = 0; this.tempo = null; this.vibe = 'calm'
  }

  feed(bands: readonly number[], level: number, now: number): void {
    const dt = Number.isFinite(this.lastFeedAt) ? now - this.lastFeedAt : 45
    this.lastFeedAt = now
    let bass = 0
    for (let i = 0; i < BASS_BANDS; i++) bass += bands[i] ?? 0
    bass /= BASS_BANDS

    // loudness, ~1.5 s smoothing
    const a = 1 - Math.exp(-Math.max(1, dt) / 1500)
    this.energy += (clamp(level / 100, 0, 1) - this.energy) * a
    this.updateVibe()

    // adaptive threshold: bass must rise clearly above its own recent average
    this.slow += (bass - this.slow) * (1 - Math.exp(-Math.max(1, dt) / 900))
    const thr = this.slow * 1.22 + 4
    const rising = bass > thr && bass > this.prevBass - 0.5
    if (rising && !this.above && bass > 12) {
      const gap = now - this.lastBeatAt
      if (gap >= MIN_GAP_MS) this.onset(now)
      else if (this.bpm !== null && gap < (60000 / this.bpm) * 0.3) { this.above = true; this.lastBeatAt = now } // re-align a predicted beat to the real hit
    }
    if (bass < thr * 0.92) this.above = false
    this.prevBass = bass
  }

  private onset(now: number): void {
    this.above = true
    // keep the predicted phase glued to real hits
    this.lastBeatAt = now
    this.beatIndex++
    this.onsets.push(now)
    if (this.onsets.length > WINDOW) this.onsets.shift()
    this.estimate()
  }

  private estimate(): void {
    const o = this.onsets
    if (o.length < 5) return
    const bins = new Map<number, number[]>()
    let total = 0
    for (let i = 1; i < o.length; i++) {
      const ioi = o[i] - o[i - 1]
      if (ioi < 150 || ioi > 3000) continue
      const bpm = foldBpm(60000 / ioi)
      const bin = Math.round(bpm / 6)
      const arr = bins.get(bin) ?? []
      arr.push(bpm); bins.set(bin, arr); total++
    }
    if (!total) return
    let best: number[] = []
    for (const [bin, arr] of bins) {
      const merged = [...arr, ...(bins.get(bin - 1) ?? []), ...(bins.get(bin + 1) ?? [])]
      if (merged.length > best.length) best = merged
    }
    const est = best.reduce((s, v) => s + v, 0) / best.length
    this.confidence = clamp(best.length / total, 0, 1) * clamp(best.length / 6, 0, 1)
    if (this.confidence < 0.35) return
    this.bpm = this.bpm === null ? est : this.bpm + (est - this.bpm) * 0.25
    this.updateTempo()
  }

  private updateTempo(): void {
    if (this.bpm === null) { this.tempo = null; return }
    const b = this.bpm
    const prev = this.tempo
    // hysteresis ±4 BPM so a hovering tempo does not flip the scene
    const slowMax = prev === 'slow' ? 99 : 94
    const fastMin = prev === 'fast' ? 123 : 128
    this.tempo = b < slowMax ? 'slow' : b >= fastMin ? 'fast' : 'mid'
  }

  private updateVibe(): void {
    const e = this.energy
    const v = this.vibe
    if (e > (v === 'hype' ? 0.5 : 0.62)) this.vibe = 'hype'
    else if (e < (v === 'calm' ? 0.3 : 0.2)) this.vibe = 'calm'
    else this.vibe = 'groove'
  }

  read(now: number): BeatInfo {
    if (now - this.lastBeatAt > STALE_MS && this.bpm !== null) {
      this.bpm = null; this.confidence = 0; this.tempo = null; this.onsets = []
    }
    // predicted beats while the tempo is stable but the detector missed a hit
    if (this.bpm !== null && this.confidence >= 0.5) {
      const period = 60000 / this.bpm
      while (now - this.lastBeatAt > period && now - this.lastBeatAt < STALE_MS) {
        this.lastBeatAt += period
        this.beatIndex++
      }
    }
    const period = this.bpm ? 60000 / this.bpm : 450
    const since = Math.max(0, now - this.lastBeatAt)
    const pulse = this.bpm !== null && this.confidence >= 0.5
      ? Math.exp(-since / (period * 0.28))
      : 0
    return {
      bpm: this.bpm === null ? null : Math.round(this.bpm),
      confidence: this.confidence, pulse, beatIndex: this.beatIndex,
      energy: this.energy, tempo: this.tempo, vibe: this.vibe,
    }
  }
}
