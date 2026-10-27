// DL-153 — mood engine: edges, priorities, cooldowns, gating, baselines, quips.
import { describe, it, expect } from 'vitest'
import { MoodEngine, type RobotSignals, type RobotCommand } from '@/services/robot/moodEngine'
import { REACTIONS, BASELINES, IDLE_GAGS } from '@/services/robot/reactions'
import { QUIPS } from '@/services/robot/quips'
import { EXPRESSION_IDS } from '@/services/robot/expressions'
import { SEQUENCES } from '@/services/robot/sequences'

const ALL = { agent: true, music: true, system: true, ambient: true }
const sig = (o: Partial<RobotSignals> = {}): RobotSignals => ({
  agent: 'idle', musicPlaying: false, cpuPercent: 10, batteryPercent: null, batteryCharging: null,
  notificationCount: 0, updateAvailable: false, weather: null, isDay: true, hour: 15, day: '2026-10-27', ...o,
})
const fixed = () => 0.5
const types = (c: RobotCommand[]) => c.map(x => x.type + ':' + ('id' in x ? x.id : x.text))

describe('reaction data', () => {
  it('only references real expressions/sequences; every quip ≤ 40 chars', () => {
    for (const byMood of Object.values(REACTIONS)) for (const r of Object.values(byMood)) {
      if (!r) continue
      expect(EXPRESSION_IDS).toContain(r.expr)
      if (r.seq) expect(Object.keys(SEQUENCES)).toContain(r.seq)
    }
    for (const m of Object.values(BASELINES)) for (const e of Object.values(m)) expect(EXPRESSION_IDS).toContain(e)
    for (const g of Object.values(IDLE_GAGS)) for (const s of g) expect(Object.keys(SEQUENCES)).toContain(s)
    for (const m of Object.values(QUIPS)) for (const lines of Object.values(m)) for (const l of lines!) expect(l.length).toBeLessThanOrEqual(40)
  })
})

describe('MoodEngine', () => {
  it('greets on the first step but fires no edge for states already on (Review Focus 2)', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    const c = e.step(sig({ agent: 'working', musicPlaying: true }), [], 0, 0)
    expect(e.state.reaction).toBe('greet')
    expect(e.state.baseline).toBe('working')
    expect(types(c)).not.toContain('icon:dots')
  })

  it('agent working → needs you → working → done drives icons in order', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    expect(types(e.step(sig({ agent: 'working' }), [], 0, 10_000))).toContain('icon:dots')
    expect(types(e.step(sig({ agent: 'permission' }), [], 0, 20_000))).toContain('icon:exclaim')
    e.step(sig({ agent: 'working' }), [], 0, 30_000)
    expect(types(e.step(sig({ agent: 'ready' }), [], 0, 40_000))).toContain('icon:check')
  })

  it('a lower-priority event cannot interrupt needs-you', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    e.step(sig({ agent: 'permission' }), [], 0, 10_000)
    const c = e.step(sig({ agent: 'permission', musicPlaying: true }), [], 0, 10_500)
    expect(types(c)).not.toContain('icon:equalizer')
    expect(e.state.reaction).toBe('agentNeeds')
  })

  it('respects cooldowns', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    expect(types(e.step(sig({ notificationCount: 1 }), [], 0, 10_000))).toContain('icon:envelope')
    expect(types(e.step(sig({ notificationCount: 2 }), [], 0, 20_000))).not.toContain('icon:envelope')
    expect(types(e.step(sig({ notificationCount: 3 }), [], 0, 80_000))).toContain('icon:envelope')
  })

  it('drops events whose group is off', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: { ...ALL, music: false }, rand: fixed })
    e.step(sig(), [], 0, 0)
    expect(types(e.step(sig({ musicPlaying: true }), [], 0, 10_000))).not.toContain('icon:equalizer')
  })

  it('uses the mood variant', () => {
    const grumpy = new MoodEngine({ mood: 'grumpy', quips: false, reactTo: ALL, rand: fixed })
    grumpy.step(sig(), [], 0, 0)
    grumpy.step(sig({ agent: 'permission' }), [], 0, 10_000)
    const c = grumpy.step(sig({ agent: 'permission' }), [], 0, 11_300)
    expect(types(c)).toContain('expr:glare')
  })

  it('all-null signals idle without throwing (Review Focus 4)', () => {
    const e = new MoodEngine({ mood: 'sweet', quips: true, reactTo: ALL, rand: fixed })
    const s = sig({ cpuPercent: null, batteryPercent: null, batteryCharging: null, weather: null })
    expect(() => { for (let t = 0; t < 120_000; t += 500) e.step(s, [], 0, t) }).not.toThrow()
    expect(e.state.baseline).toBe('idle')
  })

  it('goes to sleep at night after 2 min without the pointer', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig({ hour: 23 }), [], 0, 0)
    let c: RobotCommand[] = []
    for (let t = 500; t <= 130_000; t += 500) c = c.concat(e.step(sig({ hour: 23 }), [], 0, t))
    expect(e.state.baseline).toBe('night')
    expect(types(c)).toContain('accessory:nightcap')
  })

  it('quips at most once per 20 s and never repeat back-to-back', () => {
    let i = 0
    const e = new MoodEngine({ mood: 'sarcastic', quips: true, reactTo: ALL, rand: () => (i++ % 7) / 7 })
    e.step(sig(), [], 0, 0)
    const quips: Array<[number, string]> = []
    let n = 0
    for (let t = 1000; t < 200_000; t += 1000) {
      for (const c of e.step(sig({ notificationCount: ++n }), [], 0, t)) if (c.type === 'quip') quips.push([t, c.text])
    }
    for (let k = 1; k < quips.length; k++) {
      expect(quips[k][0] - quips[k - 1][0]).toBeGreaterThanOrEqual(20_000)
      expect(quips[k][1]).not.toBe(quips[k - 1][1])
    }
  })

  it('pointer shake maps to a reaction', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    e.step(sig(), [], 0, 6000)
    const c = e.step(sig(), ['shake'], 6000, 6100)
    expect(e.state.reaction).toBe('pointerShake')
    expect(c.length).toBeGreaterThan(0)
  })

  it('baselines respect the reaction-group toggles', () => {
    const a = new MoodEngine({ mood: 'funny', quips: false, reactTo: { ...ALL, ambient: false }, rand: fixed })
    a.step(sig({ hour: 23 }), [], 0, 0)
    for (let t = 500; t <= 130_000; t += 500) a.step(sig({ hour: 23 }), [], 0, t)
    expect(a.state.baseline).toBe('idle')
    const b = new MoodEngine({ mood: 'funny', quips: false, reactTo: { ...ALL, agent: false }, rand: fixed })
    b.step(sig({ agent: 'working' }), [], 0, 0)
    expect(b.state.baseline).toBe('idle')
  })

  it('clears the status icon when a face-only reaction replaces an icon reaction', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    expect(types(e.step(sig({ agent: 'working' }), [], 0, 10_000))).toContain('icon:dots')
    const c = types(e.step(sig({ agent: 'working' }), ['shake'], 10_000, 10_300))
    expect(c).toContain('icon:null')
    expect(c).toContain('expr:joy')
  })

  it('re-emits the baseline expression once an idle gag has finished', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    let t = 500
    let gag: RobotCommand | undefined
    for (; t < 200_000 && !gag; t += 500) gag = e.step(sig(), [], 0, t).find(c => c.type === 'seq')
    expect(gag).toBeDefined()
    const gagAt = t - 500
    const dur = SEQUENCES[(gag as { id: keyof typeof SEQUENCES }).id].duration
    expect(types(e.step(sig(), [], 0, gagAt + 500))).not.toContain('expr:neutral')
    const after = types(e.step(sig(), [], 0, gagAt + dur + 500))
    expect(after).toContain('expr:neutral')
  })

  describe('morning / noon', () => {
    const mem = () => {
      const m = new Map<string, string>()
      return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v) }
    }
    const run = (e: MoodEngine, s: RobotSignals, from: number, to: number) => {
      let out: RobotCommand[] = []
      for (let t = from; t <= to; t += 500) out = out.concat(e.step(s, [], 0, t))
      return types(out)
    }
    it('greets first, then fires morning once the greet is over; once per day per device', () => {
      const storage = mem()
      const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed, storage })
      const first = types(e.step(sig({ hour: 8 }), [], 0, 0))
      expect(e.state.reaction).toBe('greet')
      expect(first).not.toContain('prop:coffee')
      expect(run(e, sig({ hour: 8 }), 500, 20_000)).toContain('prop:coffee')
      const e2 = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed, storage })
      e2.step(sig({ hour: 8 }), [], 0, 0)
      expect(run(e2, sig({ hour: 8 }), 500, 20_000)).not.toContain('prop:coffee')
    })
    it('fires noon at hour 12 with a chef hat', () => {
      const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed, storage: mem() })
      e.step(sig({ hour: 12 }), [], 0, 0)
      expect(run(e, sig({ hour: 12 }), 500, 20_000)).toContain('accessory:chef-hat')
    })
  })

  it('weather fires only on a known to different-known change', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    e.step(sig(), [], 0, 10_000)
    e.step(sig({ weather: 'sunny' }), [], 0, 20_000)
    expect(e.state.reaction).not.toBe('weather')
    e.step(sig({ weather: 'rain' }), [], 0, 30_000)
    expect(e.state.reaction).toBe('weather')
  })
})

describe('hands scenes (DL-155)', () => {
  it('funny/sweet sit at the laptop while the agent works, and put it away after', () => {
    const e = new MoodEngine({ mood: 'funny', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    const started = [
      ...types(e.step(sig({ agent: 'working' }), [], 0, 10_000)),
      ...types(e.step(sig({ agent: 'working' }), [], 0, 12_000)), // the icon clears, then the face commands land
    ]
    expect(started).toContain('scene:typing')
    // reaction (4 s) ends, the baseline keeps the laptop up
    const during = types(e.step(sig({ agent: 'working' }), [], 0, 30_000))
    expect(during.filter(c => c.startsWith('scene:')).every(c => c === 'scene:typing')).toBe(true)
    const after = types(e.step(sig({ agent: 'idle' }), [], 0, 60_000))
    expect(after.join()).not.toContain('scene:typing')
  })

  it('grumpy never pulls out a laptop', () => {
    const e = new MoodEngine({ mood: 'grumpy', quips: false, reactTo: ALL, rand: fixed })
    e.step(sig(), [], 0, 0)
    expect(types(e.step(sig({ agent: 'working' }), [], 0, 10_000))).not.toContain('scene:typing')
  })
})
