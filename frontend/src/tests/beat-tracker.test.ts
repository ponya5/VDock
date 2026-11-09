// DL-165 — beat tracker estimates BPM from bass onsets and exposes a beat pulse.
import { describe, it, expect } from 'vitest'
import { BeatTracker, foldBpm } from '@/services/robot/beatTracker'

function drive(bpm: number, seconds: number, level = 50, t = new BeatTracker(), start = 1000) {
  const period = 60000 / bpm
  let now = start
  const end = start + seconds * 1000
  while (now < end) {
    const phase = ((now - start) % period) / period
    const kick = phase < 0.18 ? 70 - phase * 150 : 10
    const bands = new Array(20).fill(8)
    for (let i = 0; i < 4; i++) bands[i] = kick
    t.feed(bands, level, now)
    now += 45
  }
  return { t, now }
}

describe('beat tracker', () => {
  it('folds out-of-range tempos by octaves', () => {
    expect(foldBpm(240)).toBe(120)
    expect(foldBpm(40)).toBe(80)
  })

  it.each([90, 120, 140])('locks onto %i BPM', (bpm) => {
    const { t, now } = drive(bpm, 14)
    const info = t.read(now)
    expect(info.bpm).not.toBeNull()
    expect(Math.abs(info.bpm! - bpm)).toBeLessThanOrEqual(6)
    expect(info.confidence).toBeGreaterThan(0.5)
  })

  it('buckets tempo and loudness', () => {
    expect(drive(80, 14, 20).t.read(15000).tempo).toBe('slow')
    expect(drive(120, 14, 50).t.read(15000).tempo).toBe('mid')
    const fast = drive(150, 14, 85)
    expect(fast.t.read(fast.now).tempo).toBe('fast')
    expect(fast.t.read(fast.now).vibe).toBe('hype')
  })

  it('pulses on the beat and decays between beats', () => {
    const { t, now } = drive(120, 12)
    const samples: number[] = []
    for (let d = 0; d < 500; d += 20) samples.push(t.read(now + d).pulse)
    expect(Math.max(...samples)).toBeGreaterThan(0.8)
    expect(Math.min(...samples)).toBeLessThan(0.3)
  })

  it('keeps beating through a missed hit, then forgets the tempo after silence', () => {
    const { t, now } = drive(120, 12)
    const idx = t.read(now).beatIndex
    expect(t.read(now + 1300).beatIndex).toBeGreaterThan(idx + 1)
    const gone = t.read(now + 10000)
    expect(gone.bpm).toBeNull()
    expect(gone.pulse).toBe(0)
  })

  it('stays quiet (no pulse) on steady noise with no beat', () => {
    const t = new BeatTracker()
    for (let now = 0; now < 8000; now += 45) t.feed(new Array(20).fill(30), 40, now)
    const info = t.read(8000)
    expect(info.bpm).toBeNull()
    expect(info.pulse).toBe(0)
  })
})

import { FaceAnimator } from '@/services/robot/animator'

describe('beat-driven robot (DL-165)', () => {
  it('head bounces on the beat only when a tempo is locked', () => {
    const a = new FaceAnimator(() => 0.5)
    const y = (pulse: number) => { a.setBeat({ pulse, beatIndex: 1, confidence: 0.9, energy: 0.8 }); a.step(16, 1000); return a.frame().transform }
    expect(y(1)).not.toBe(y(0))
    a.setBeat({ pulse: 1, beatIndex: 1, confidence: 0.1, energy: 0.8 })
    a.step(16, 2000)
    const t1 = a.frame().transform
    a.setBeat({ pulse: 0, beatIndex: 1, confidence: 0.1, energy: 0.8 })
    expect(a.frame().transform).toBe(t1) // untrusted beat is ignored
  })
})

import { hasIdleAgent } from '@/services/robot/signals'
import { MoodEngine as Engine, type RobotSignals as Sig } from '@/services/robot/moodEngine'

describe('baselines for music and an idle agent (DL-165)', () => {
  const base = (o: Partial<Sig> = {}): Sig => ({
    agent: 'idle', musicPlaying: false, cpuPercent: 10, batteryPercent: 80, batteryCharging: null,
    notificationCount: 0, updateAvailable: false, weather: null, isDay: true, hour: 14, day: '2026-11-09', ...o,
  })
  const reactTo = { music: true, agent: true, system: true, ambient: true, notifications: true } as never
  const settle = (mood: 'funny' | 'grumpy' | 'sarcastic' | 'sweet', s: Sig) => {
    const e = new Engine({ mood, quips: false, reactTo, storage: null, rand: () => 0.5 })
    e.step(base(), [], 0, 0)
    return [...e.step(s, [], 0, 5_000), ...e.step(s, [], 0, 12_000)]
  }

  it('detects an idle agent session', () => {
    expect(hasIdleAgent([])).toBe(false)
    expect(hasIdleAgent([{ state: 'ready' }])).toBe(true)
    expect(hasIdleAgent([{ state: 'idle' }, { state: 'working' }])).toBe(false)
  })

  it.each(['funny', 'grumpy', 'sarcastic', 'sweet'] as const)('%s: music shows the listening look', (mood) => {
    const out = settle(mood, base({ musicPlaying: true }))
    expect(out).toContainEqual({ type: 'expr', id: 'grooving' })
    expect(out).toContainEqual({ type: 'scene', id: 'jamming' })
    expect(out.some(c => c.type === 'accessory' && c.id === 'headphones')).toBe(true)
  })

  it('an idle agent gets its own face and scene; music still wins over it', () => {
    const idle = settle('funny', base({ agentIdle: true }))
    expect(idle).toContainEqual({ type: 'expr', id: 'whistle' })
    expect(idle).toContainEqual({ type: 'scene', id: 'coffee-break' })
    const both = settle('funny', base({ agentIdle: true, musicPlaying: true }))
    expect(both).toContainEqual({ type: 'expr', id: 'grooving' })
  })
})
