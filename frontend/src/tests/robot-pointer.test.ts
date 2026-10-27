// DL-153 — pointer gestures from synthetic tracks.
import { describe, it, expect } from 'vitest'
import { PointerSense } from '@/services/robot/pointerSense'

function feed(p: PointerSense, pts: Array<[number, number]>, t0: number, stepMs: number) {
  const out: string[] = []
  pts.forEach(([x, y], i) => out.push(...p.move(x, y, t0 + i * stepMs)))
  return out
}

describe('PointerSense', () => {
  it('enter, then eyes, then mouth', () => {
    const p = new PointerSense()
    expect(p.move(-0.2, 0.3, 0)).toEqual([])
    expect(p.move(0.1, 0.6, 100)).toContain('enter')
    expect(p.move(0.35, 0.3, 200)).toContain('eyes')
    expect(p.move(0.5, 0.5, 300)).toContain('mouth')
  })

  it('shake → dizzy after 2 s → annoyed after 4 s', () => {
    const p = new PointerSense()
    const track: Array<[number, number]> = []
    for (let i = 0; i < 300; i++) track.push([i % 2 ? 0.2 : 0.8, 0.35])
    const g = feed(p, track, 0, 16)
    expect(g).toContain('shake')
    expect(g).toContain('dizzy')
    expect(g).toContain('annoyed')
    expect(g.filter(x => x === 'dizzy')).toHaveLength(1)
  })

  it('circling the face', () => {
    const p = new PointerSense()
    const track: Array<[number, number]> = []
    for (let i = 0; i <= 40; i++) {
      const a = (i / 40) * Math.PI * 2.2
      track.push([0.5 + Math.cos(a) * 0.25, 0.35 + Math.sin(a) * 0.25])
    }
    expect(feed(p, track, 0, 30)).toContain('circle')
  })

  it('linger after 3 s still on the face', () => {
    const p = new PointerSense()
    p.move(0.5, 0.3, 0)
    expect(p.tick(2000)).toEqual([])
    expect(p.tick(3100)).toContain('linger')
    expect(p.tick(4000)).toEqual([])
  })

  it('linger re-arms after leave and re-enter', () => {
    const p = new PointerSense()
    p.move(0.5, 0.3, 0)
    expect(p.tick(3100)).toContain('linger')
    p.leave(3200)
    p.move(0.5, 0.3, 4000)
    expect(p.tick(7100)).toContain('linger')
  })

  it('slow approach toward the face', () => {
    const p = new PointerSense()
    const track: Array<[number, number]> = []
    for (let i = 0; i <= 40; i++) track.push([1.1 - i * 0.015, 0.35])
    expect(feed(p, track, 0, 60)).toContain('approach')
  })

  it('leave nulls the look; return after a minute away', () => {
    const p = new PointerSense()
    p.move(0.9, 0.35, 1000)
    expect(p.look()!.x).toBeGreaterThan(0.5)
    expect(p.leave(1100)).toContain('leave')
    expect(p.look()).toBeNull()
    expect(p.move(0.5, 0.35, 70_000)).toEqual(['return'])
  })
})
