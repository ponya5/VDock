// DL-153 — every art id has drawable elements; sequences reference only real ids.
import { describe, it, expect } from 'vitest'
import { EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES, artTransform, propEnvelope } from '@/services/robot/robotArt'
import { SEQUENCES, SequencePlayer, type SeqStep } from '@/services/robot/sequences'
import { EXPRESSION_IDS } from '@/services/robot/expressions'

describe('robot art', () => {
  it('ships the spec catalogs', () => {
    expect(Object.keys(ICONS).sort()).toEqual(['battery', 'bubble', 'check', 'dots', 'download', 'envelope',
      'equalizer', 'exclaim', 'question', 'spinner', 'warning'])
    expect(Object.keys(PROPS)).toHaveLength(19)
    expect(Object.keys(ACCESSORIES).sort()).toEqual(['chef-hat', 'headphones', 'nightcap', 'party-hat', 'scarf', 'sunglasses', 'wizard-hat'])
    expect(Object.keys(EYE_GLYPHS).sort()).toEqual(['dot', 'gt', 'heart', 'lt', 'spiral', 'star', 'x'])
    expect(Object.keys(MOUTH_GLYPHS).sort()).toEqual(['pout', 'teeth'])
  })

  it('every art def has at least one element with geometry', () => {
    for (const set of [EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES]) {
      for (const [id, def] of Object.entries(set)) {
        expect(def.els.length, id).toBeGreaterThan(0)
        for (const el of def.els) expect(Object.keys(el.attrs).length, id).toBeGreaterThan(0)
      }
    }
  })

  it('uses only white + the accent tokens', () => {
    const allowed = new Set(['#fff', '#ffd84d', '#ff6fa8', '#ff4d4d', '#6cc7ff', '#ff9a4d', 'none', '#000', 'currentColor'])
    for (const set of [EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES]) {
      for (const def of Object.values(set)) for (const el of def.els) {
        for (const k of ['fill', 'stroke']) if (el.attrs[k] !== undefined) expect(allowed.has(String(el.attrs[k]))).toBe(true)
      }
    }
  })

  it('artTransform is finite for every anim and moment', () => {
    for (const a of ['none', 'bounce', 'spin', 'wave', 'twinkle', 'float', 'drip', 'pulse', 'pop', 'fall', 'scan', 'steam', 'sway', 'eq'] as const) {
      for (const t of [0, 123, 999, 5000]) expect(artTransform(a, t, 1, 0.5)).not.toMatch(/NaN|Infinity/)
    }
  })

  it('propEnvelope pops in, holds, fades out', () => {
    expect(propEnvelope(0, 2000).scale).toBeLessThan(0.6)
    expect(propEnvelope(1000, 2000).opacity).toBeCloseTo(1, 2)
    expect(propEnvelope(2000, 2000).opacity).toBeCloseTo(0, 2)
  })

  it('propEnvelope overshoots then settles to 1', () => {
    let max = 0
    for (let a = 0; a <= 260; a += 5) max = Math.max(max, propEnvelope(a, 2000).scale)
    expect(max).toBeGreaterThan(1.05)
    expect(propEnvelope(300, 2000).scale).toBe(1)
  })
})

describe('sequences', () => {
  it('ships the spec sequences', () => {
    for (const id of ['wink', 'look-around', 'eye-roll', 'double-take', 'nod', 'head-shake', 'yawn-sleep', 'wake-up',
      'sneeze', 'hiccup', 'giggle', 'shiver', 'sweat-wipe', 'whistle-away', 'peek-a-boo', 'startle', 'shrug',
      'celebrate', 'sigh']) {
      expect(Object.keys(SEQUENCES)).toContain(id)
    }
  })

  it('reference only known expressions/props/icons/accessories and are time-ordered', () => {
    for (const [id, seq] of Object.entries(SEQUENCES)) {
      let last = -1
      for (const s of seq.steps as readonly SeqStep[]) {
        expect(s.at, id).toBeGreaterThanOrEqual(last)
        last = s.at
        if (s.expr) expect(EXPRESSION_IDS).toContain(s.expr)
        if (s.prop) expect(Object.keys(PROPS)).toContain(s.prop)
        if (s.icon) expect(Object.keys(ICONS)).toContain(s.icon)
        if (s.accessory) expect(Object.keys(ACCESSORIES)).toContain(s.accessory)
      }
      expect(seq.duration, id).toBeGreaterThanOrEqual(last)
    }
  })

  it('SequencePlayer emits each step exactly once, in order', () => {
    const p = new SequencePlayer()
    p.start('wink', 1000)
    const all = [...p.due(1000), ...p.due(1100), ...p.due(5000)]
    expect(all.map(s => s.at)).toEqual(SEQUENCES.wink.steps.map(s => s.at))
    expect(p.active(1000 + SEQUENCES.wink.duration + 1)).toBe(false)
  })
})
