// DL-153 — spring integrator: convergence, frame-rate independence, dt clamp.
import { describe, it, expect } from 'vitest'
import { createSpring, stepSpring, isSettled, SPRINGS, MAX_DT_MS } from '@/services/robot/springs'

function run(hz: number, ms: number, config = SPRINGS.soft) {
  const s = createSpring(0, config)
  s.target = 1
  const dt = 1000 / hz
  // integer frame count: accumulating `t += dt` runs 13 frames (216 ms) at 60 Hz vs 200 ms at 30/120 Hz
  const frames = Math.round(ms / dt)
  for (let i = 0; i < frames; i++) stepSpring(s, dt)
  return s
}

describe('springs', () => {
  it('converges to the target', () => {
    const s = run(60, 3000)
    expect(s.value).toBeCloseTo(1, 3)
    expect(isSettled(s)).toBe(true)
  })

  it('is frame-rate independent (30/60/120 Hz agree mid-flight)', () => {
    const a = run(30, 200).value
    const b = run(60, 200).value
    const c = run(120, 200).value
    expect(Math.abs(a - b)).toBeLessThan(0.03)
    expect(Math.abs(b - c)).toBeLessThan(0.03)
  })

  it('bouncy overshoots, snappy does not', () => {
    let peak = 0
    const s = createSpring(0, SPRINGS.bouncy); s.target = 1
    for (let i = 0; i < 120; i++) { stepSpring(s, 16.7); peak = Math.max(peak, s.value) }
    expect(peak).toBeGreaterThan(1.02)
    let peak2 = 0
    const q = createSpring(0, SPRINGS.snappy); q.target = 1
    for (let i = 0; i < 120; i++) { stepSpring(q, 16.7); peak2 = Math.max(peak2, q.value) }
    expect(peak2).toBeLessThan(1.01)
  })

  it('clamps a huge dt (tab was hidden) so nothing is flung', () => {
    const s = createSpring(0, SPRINGS.bouncy); s.target = 1
    stepSpring(s, 10_000)
    const t = createSpring(0, SPRINGS.bouncy); t.target = 1
    stepSpring(t, MAX_DT_MS)
    expect(s.value).toBeCloseTo(t.value, 6)
    expect(Number.isFinite(s.velocity)).toBe(true)
  })

  it('retargeting mid-motion keeps velocity (no snap)', () => {
    const s = createSpring(0, SPRINGS.soft); s.target = 1
    for (let i = 0; i < 6; i++) stepSpring(s, 16.7)
    const v = s.velocity
    s.target = -1
    stepSpring(s, 1)
    expect(Math.sign(s.velocity)).toBe(Math.sign(v))
  })
})
