// DL-153 — every art id has drawable elements; sequences reference only real ids.
import { describe, it, expect } from 'vitest'
import { EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES, GRADIENTS, artTransform, propEnvelope } from '@/services/robot/robotArt'
import { SCENES, SCENE_IDS, handPoses } from '@/services/robot/scenes'
import { SEQUENCES, SequencePlayer, type SeqStep } from '@/services/robot/sequences'
import { EXPRESSION_IDS } from '@/services/robot/expressions'

describe('robot art', () => {
  it('ships the spec catalogs', () => {
    expect(Object.keys(ICONS).sort()).toEqual(['battery', 'bubble', 'check', 'dots', 'download', 'envelope',
      'equalizer', 'exclaim', 'question', 'spinner', 'warning'])
    expect(Object.keys(PROPS)).toHaveLength(25)
    expect(Object.keys(PROPS)).toEqual(expect.arrayContaining(['rocket', 'trophy']))
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

  it('uses only white, the accent tokens and the shared gradients', () => {
    const allowed = new Set(['#fff', '#ffd84d', '#ff6fa8', '#ff4d4d', '#6cc7ff', '#ff9a4d', 'none', '#000', 'currentColor', '#e8a317', '#8a4f24'])
    const gradientIds = new Set(GRADIENTS.map(g => `url(#${g.id})`))
    for (const set of [EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES]) {
      for (const def of Object.values(set)) for (const el of def.els) {
        for (const k of ['fill', 'stroke']) {
          if (el.attrs[k] === undefined) continue
          const v = String(el.attrs[k])
          expect(allowed.has(v) || gradientIds.has(v), v).toBe(true)
        }
      }
    }
  })

  it('every gradient has at least two stops and a unique id', () => {
    expect(new Set(GRADIENTS.map(g => g.id)).size).toBe(GRADIENTS.length)
    for (const g of GRADIENTS) expect(g.stops.length, g.id).toBeGreaterThanOrEqual(2)
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
      'celebrate', 'sigh', 'type-session', 'cheer', 'clap', 'cover-eyes', 'hello-hand', 'cheeky-wink']) {
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
        if (s.scene) expect(SCENE_IDS).toContain(s.scene)
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

describe('scenes (DL-155)', () => {
  it('every scene yields finite poses for both hands at every moment', () => {
    for (const id of SCENE_IDS) for (const p of [0, 0.5, 1, 1.12]) for (const t of [0, 321, 5000]) {
      for (const h of handPoses(id, p, t)) {
        for (const n of [h.x, h.y, h.rot, h.thumb, ...h.curl]) expect(Number.isFinite(n), `${id} ${p} ${t}`).toBe(true)
      }
    }
  })

  it('hands start off-screen and arrive on the face box', () => {
    for (const id of ['typing', 'cheer', 'clap', 'cover'] as const) {
      const [l0, r0] = handPoses(id, 0, 0)
      const [l1, r1] = handPoses(id, 1, 0)
      expect(l0.x, id).toBeLessThan(0)
      expect(r0.x, id).toBeGreaterThan(200)
      expect(l1.x, id).toBeGreaterThan(0)
      expect(r1.x, id).toBeLessThan(200)
    }
  })

  it('typing curls the fingers over time and only that scene shows a laptop', () => {
    const a = handPoses('typing', 1, 0)[0].curl.join()
    const b = handPoses('typing', 1, 137)[0].curl.join()
    expect(a).not.toBe(b)
    expect(SCENE_IDS.filter(id => SCENES[id].laptop)).toEqual(['typing'])
  })
})

import { HELD, heldSlide, propTransform } from '@/services/robot/heldProps'

describe('held props (DL-155 follow-up A)', () => {
  it('only reference real props and keep motion bounded', () => {
    for (const [id, h] of Object.entries(HELD)) {
      expect(Object.keys(PROPS)).toContain(id)
      for (let s = 0; s < 6; s += 0.1) {
        const m = h!.motion(s)
        expect(Math.abs(m.dx)).toBeLessThan(80)
        expect(Math.abs(m.dy)).toBeLessThan(40)
        expect(Math.abs(m.rot)).toBeLessThan(45)
      }
    }
  })
  it('actually moves over time', () => {
    for (const h of Object.values(HELD)) {
      const a = JSON.stringify(h!.motion(0.4))
      const b = JSON.stringify(h!.motion(0.9))
      expect(a).not.toBe(b)
    }
  })
  it('arm slides in, holds, then slides out', () => {
    expect(heldSlide(0, 3000)).toBe(0)
    expect(heldSlide(1500, 3000)).toBe(1)
    expect(heldSlide(2990, 3000)).toBeLessThan(0.1)
  })
  it('pivots a held prop about its grip; unheld props are a plain translate', () => {
    expect(propTransform('magnifier', [100, 128], 1.2, 500)).toContain('rotate(')
    expect(propTransform('heart', [166, 36], 1.4, 500)).not.toContain('rotate')
  })
  it('internal animations (clock, shoes, pen) change with time', () => {
    expect(artTransform('clockMin', 0)).not.toBe(artTransform('clockMin', 500))
    expect(artTransform('step', 100, 0)).not.toBe(artTransform('step', 300, 0))
    expect(artTransform('write', 0)).not.toBe(artTransform('write', 120))
  })
})
