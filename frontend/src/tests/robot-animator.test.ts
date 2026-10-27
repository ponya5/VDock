// DL-153 — FaceAnimator: smooth expression changes, glyph swaps, blinks, icons, props.
import { describe, it, expect } from 'vitest'
import { FaceAnimator } from '@/services/robot/animator'

function seeded(seed = 1) {
  return () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646 }
}
function run(a: FaceAnimator, ms: number, start = 0, dt = 16.7) {
  let t = start
  for (; t < start + ms; t += dt) a.step(dt, t)
  return t
}
const nums = (d: string) => [...d.matchAll(/-?\d+\.?\d*/g)].map(m => Number(m[0]))

describe('FaceAnimator', () => {
  it('moves smoothly toward a new expression (no single-frame jump)', () => {
    const a = new FaceAnimator(seeded())
    let t = run(a, 500)
    const before = nums(a.frame().mouth)
    a.setExpression('grin')
    a.step(16.7, (t += 16.7))
    const oneFrame = nums(a.frame().mouth)
    t = run(a, 1500, t)
    const settled = nums(a.frame().mouth)
    const jump = Math.max(...oneFrame.map((v, i) => Math.abs(v - before[i])))
    const total = Math.max(...settled.map((v, i) => Math.abs(v - before[i])))
    expect(total).toBeGreaterThan(2)
    expect(jump).toBeLessThan(total * 0.35)
    expect(a.frame().expression).toBe('grin')
  })

  it('swaps glyph → different glyph by fading out first', () => {
    const a = new FaceAnimator(seeded())
    a.setExpression('love')
    let t = run(a, 800)
    expect(a.frame().glyphL.id).toBe('heart')
    expect(a.frame().glyphL.opacity).toBeGreaterThan(0.9)
    a.setExpression('dizzy')
    a.step(16.7, (t += 16.7))
    expect(a.frame().glyphL.id).toBe('heart') // still the old glyph, fading
    let sawLow = false
    for (let i = 0; i < 60; i++) {
      a.step(16.7, (t += 16.7))
      const g = a.frame().glyphL
      if (g.id === 'spiral' && g.opacity > 0.9) break
      if (g.opacity < 0.1) sawLow = true
    }
    expect(sawLow).toBe(true)
    expect(a.frame().glyphL.id).toBe('spiral')
  })

  it('blinks on its own within 8 s', () => {
    const a = new FaceAnimator(seeded(7))
    let minH = Infinity
    let t = 0
    for (; t < 8000; t += 16.7) {
      a.step(16.7, t)
      const ys = nums(a.frame().eyeL).filter((_, i) => i % 2 === 1)
      minH = Math.min(minH, Math.max(...ys) - Math.min(...ys))
    }
    expect(minH).toBeLessThan(12)
  })

  it('an icon hides the face and shows the icon; clearing restores the face', () => {
    const a = new FaceAnimator(seeded())
    a.setIcon('exclaim')
    let t = run(a, 800)
    expect(a.frame().icon.id).toBe('exclaim')
    expect(a.frame().icon.opacity).toBeGreaterThan(0.9)
    expect(a.frame().faceOpacity).toBeLessThan(0.1)
    a.setIcon(null)
    run(a, 800, t)
    expect(a.frame().faceOpacity).toBeGreaterThan(0.9)
  })

  it('props live for their life span then disappear', () => {
    const a = new FaceAnimator(seeded())
    let t = run(a, 100)
    a.addProp('heart')
    t = run(a, 200, t)
    expect(a.frame().props.map(p => p.id)).toEqual(['heart'])
    run(a, 3000, t)
    expect(a.frame().props).toEqual([])
  })

  it('pointer look override moves the eyes toward the pointer', () => {
    const a = new FaceAnimator(seeded())
    let t = run(a, 300)
    const x0 = a.frame().eyeLCenter[0]
    a.setLook({ x: 1, y: 0 })
    run(a, 1000, t)
    expect(a.frame().eyeLCenter[0]).toBeGreaterThan(x0 + 8)
  })

  it('plays a sequence end to end and returns to its last expression', () => {
    const a = new FaceAnimator(seeded())
    a.playSequence('wink')
    run(a, 1500)
    expect(a.frame().expression).toBe('happy')
  })

  it('a huge dt (hidden tab) produces finite paths', () => {
    const a = new FaceAnimator(seeded())
    a.setExpression('joy')
    a.step(60_000, 60_000)
    expect(a.frame().eyeL + a.frame().mouth + a.frame().transform).not.toMatch(/NaN|Infinity/)
  })

  it('fades the drawn mouth when a mouth glyph takes over (no single-frame pop)', () => {
    const a = new FaceAnimator(seeded())
    let t = run(a, 500)
    expect(a.frame().mouthOpacity).toBeGreaterThan(0.9)
    a.setExpression('pout')
    let prev = a.frame().mouthOpacity
    for (let i = 0; i < 120; i++) {
      a.step(16.7, (t += 16.7))
      const o = a.frame().mouthOpacity
      expect(prev - o).toBeLessThan(0.8)
      prev = o
    }
    expect(prev).toBeLessThan(0.1)
    a.setExpression('neutral')
    for (let i = 0; i < 240; i++) {
      a.step(16.7, (t += 16.7))
      const o = a.frame().mouthOpacity
      expect(o - prev).toBeLessThan(0.8)
      prev = o
    }
    expect(prev).toBeGreaterThan(0.9)
  })

  it('stopSequence lets an external expression survive a running gag', () => {
    const a = new FaceAnimator(seeded())
    a.playSequence('hiccup')
    let t = run(a, 300)
    a.stopSequence()
    a.setExpression('glare')
    run(a, 3000, t)
    expect(a.frame().expression).toBe('glare')
  })
})
