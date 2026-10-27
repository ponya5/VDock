// DL-153 — parametric face rig: constant point counts → every shape morphs.
import { describe, it, expect } from 'vitest'
import { eyePath, mouthPath, eyeCenter, mouthCenter, defaultParams } from '@/services/robot/faceRig'
import { EXPRESSION_IDS, resolveExpression } from '@/services/robot/expressions'

const count = (d: string, ch: string) => d.split('').filter(c => c === ch).length

describe('face rig', () => {
  it('ships the spec expression catalog', () => {
    for (const id of ['neutral', 'happy', 'joy', 'grin', 'content', 'wink-l', 'wink-r', 'look-l', 'look-r',
      'look-up', 'look-down', 'side-eye', 'glare', 'angry', 'squint', 'focused', 'bored', 'unimpressed',
      'suspicious', 'sleepy', 'asleep', 'surprised', 'shocked', 'love', 'starstruck', 'dizzy', 'dead',
      'laughing', 'crying', 'sad', 'worried', 'shy', 'puppy', 'thinking', 'mischievous', 'smug', 'pout',
      'whistle', 'teeth-grit', 'yawn']) {
      expect(EXPRESSION_IDS).toContain(id)
    }
  })

  it('every expression yields an 8-cubic eye path and a 4-cubic mouth path', () => {
    for (const id of EXPRESSION_IDS) {
      const { params } = resolveExpression(id)
      for (const side of ['L', 'R'] as const) {
        const [cx, cy] = eyeCenter(side, params)
        const d = eyePath(side === 'L' ? params.eyeL : params.eyeR, cx, cy, side)
        expect(count(d, 'C'), `${id} eye ${side}`).toBe(8)
        expect(d).not.toMatch(/NaN|Infinity/)
      }
      const [mx, my] = mouthCenter(params)
      const m = mouthPath(params.face, mx, my)
      expect(count(m, 'C'), `${id} mouth`).toBe(4)
      expect(m).not.toMatch(/NaN|Infinity/)
    }
  })

  it('a fully closed eye still draws a visible line (min height)', () => {
    const p = defaultParams()
    const d = eyePath({ ...p.eyeL, lidTop: 0.7, lidBottom: 0.7 }, 72, 62, 'L')
    const ys = [...d.matchAll(/-?\d+\.?\d*/g)].map(m => Number(m[0])).filter((_, i) => i % 2 === 1)
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThanOrEqual(3)
  })

  it('looking right moves the eyes right', () => {
    const p = defaultParams()
    const [x0] = eyeCenter('L', p)
    p.face.lookX = 1
    const [x1] = eyeCenter('L', p)
    expect(x1).toBeGreaterThan(x0)
  })

  it('glyph expressions carry glyph ids', () => {
    expect(resolveExpression('love').glyphs).toEqual(['heart', 'heart'])
    expect(resolveExpression('laughing').glyphs).toEqual(['gt', 'lt'])
    expect(resolveExpression('neutral').glyphs).toEqual([null, null])
    expect(resolveExpression('teeth-grit').mouthGlyph).toBe('teeth')
  })

  it('curveUp pushes the eye ends down (^), curveDown pulls them up (‿)', () => {
    const e = { ...defaultParams().eyeL, lidBottom: 0.55 }
    const firstY = (d: string) => Number(d.match(/^M\S+ (\S+)/)![1])
    const flat = firstY(eyePath(e, 72, 62, 'L'))
    expect(firstY(eyePath({ ...e, curveUp: 1 }, 72, 62, 'L'))).toBeGreaterThan(flat)
    expect(firstY(eyePath({ ...e, curveDown: 1 }, 72, 62, 'L'))).toBeLessThan(flat)
  })
})
