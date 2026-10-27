/**
 * DL-153 — FaceAnimator: owns every animated value of the robot face. One
 * call to step(dt, now) per animation frame advances springs, blinks, glyph /
 * icon / accessory cross-fades, props and sequences; frame() turns the state
 * into SVG path strings. Pure — no DOM — so it is unit-tested directly.
 */
import { createSpring, stepSpring, SPRINGS, type Spring, type SpringConfig } from './springs'
import {
  EYE_KEYS, FACE_KEYS, eyeCenter, eyePath, mouthCenter, mouthPath, tonguePath,
  type EyeKey, type EyeParams, type FaceKey, type FaceParams, type FaceScalars,
} from './faceRig'
import { resolveExpression, type ExpressionId, type EyeGlyph, type MouthGlyph } from './expressions'
import { PROPS, type AccessoryId, type IconId, type PropId } from './robotArt'
import { SequencePlayer, type SequenceId } from './sequences'

export interface GlyphFrame<T> { id: T | null; opacity: number; scale: number }
export interface PropFrame { key: number; id: PropId; age: number }
export interface FaceFrame {
  eyeL: string; eyeR: string; eyeLCenter: [number, number]; eyeRCenter: [number, number]
  eyeOpacityL: number; eyeOpacityR: number
  mouth: string; mouthCenter: [number, number]; mouthOpacity: number
  tongue: string; tongueOpacity: number; blush: number
  glyphL: GlyphFrame<EyeGlyph>; glyphR: GlyphFrame<EyeGlyph>; mouthGlyph: GlyphFrame<MouthGlyph>
  faceOpacity: number
  icon: GlyphFrame<IconId>
  accessory: GlyphFrame<AccessoryId> & { dy: number }
  props: PropFrame[]
  transform: string
  expression: ExpressionId
  t: number
}

/** A cross-fading slot: desired id vs shown id over one opacity spring. */
class Slot<T> {
  desired: T | null = null
  shown: T | null = null
  readonly spring: Spring
  constructor(config: SpringConfig = SPRINGS.fade) { this.spring = createSpring(0, config) }
  step(dt: number): void {
    if (this.desired !== this.shown) {
      this.spring.target = 0
      if (this.spring.value < 0.05) { this.shown = this.desired; this.spring.value = Math.max(0, this.spring.value) }
    } else {
      this.spring.target = this.shown === null ? 0 : 1
    }
    stepSpring(this.spring, dt)
  }
  get busy(): boolean { return this.desired !== null || this.shown !== null }
  frame(): GlyphFrame<T> {
    const o = Math.max(0, Math.min(1, this.spring.value))
    return { id: this.shown, opacity: o, scale: 0.4 + 0.6 * Math.max(0, this.spring.value) }
  }
}

const eyeConfig = (k: EyeKey): SpringConfig => (k.startsWith('lid') ? SPRINGS.snappy : k === 'x' || k === 'y' ? SPRINGS.look : k === 'opacity' ? SPRINGS.fade : SPRINGS.soft)
const faceConfig = (k: FaceKey): SpringConfig =>
  k === 'lookX' || k === 'lookY' || k === 'tilt' ? SPRINGS.look
    : k === 'bounce' || k === 'scale' ? SPRINGS.bouncy
      : k === 'mouthOpacity' || k === 'blush' || k === 'tongue' ? SPRINGS.fade : SPRINGS.soft

const smooth = (u: number) => u * u * (3 - 2 * u)
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))
const f2 = (n: number) => (Math.round(n * 100) / 100).toString()

export class FaceAnimator {
  private readonly rand: () => number
  private readonly eyeL: Record<EyeKey, Spring>
  private readonly eyeR: Record<EyeKey, Spring>
  private readonly face: Record<FaceKey, Spring>
  private readonly glyphL = new Slot<EyeGlyph>()
  private readonly glyphR = new Slot<EyeGlyph>()
  private readonly mouthGlyphSlot = new Slot<MouthGlyph>()
  private readonly iconSlot = new Slot<IconId>()
  private readonly accessorySlot = new Slot<AccessoryId>(SPRINGS.bouncy)
  private readonly faceVis = createSpring(1, SPRINGS.fade)
  private readonly mouthVis = createSpring(1, SPRINGS.fade)
  private readonly player = new SequencePlayer()
  private expr: ExpressionId = 'neutral'
  private base: FaceParams
  private nudge: Partial<FaceScalars> = {}
  private look: { x: number; y: number } | null = null
  private saccade = { x: 0, y: 0 }
  private nextSaccadeAt = 0
  private nextBlinkAt = 0
  private blinkStart = -1
  private blinkSecond = false
  private bob = 0
  private reduced = false
  private props: Array<{ key: number; id: PropId; born: number }> = []
  private propSeq = 0
  private now = 0

  constructor(rand: () => number = Math.random) {
    this.rand = rand
    const r = resolveExpression('neutral')
    this.base = r.params
    const mk = <K extends string>(keys: readonly K[], src: Record<K, number>, cfg: (k: K) => SpringConfig) =>
      Object.fromEntries(keys.map(k => [k, createSpring(src[k], cfg(k))])) as Record<K, Spring>
    this.eyeL = mk(EYE_KEYS, r.params.eyeL, eyeConfig)
    this.eyeR = mk(EYE_KEYS, r.params.eyeR, eyeConfig)
    this.face = mk(FACE_KEYS, r.params.face, faceConfig)
    this.nextBlinkAt = 2500 + rand() * 4500
    this.nextSaccadeAt = 1000 + rand() * 3000
  }

  get expression(): ExpressionId { return this.expr }

  setExpression(id: ExpressionId): void {
    const r = resolveExpression(id)
    this.expr = id
    this.base = r.params
    this.nudge = {}
    this.glyphL.desired = r.glyphs[0]
    this.glyphR.desired = r.glyphs[1]
    this.mouthGlyphSlot.desired = r.mouthGlyph
  }

  setNudge(n: Partial<FaceScalars>): void { this.nudge = { ...this.nudge, ...n } }
  setLook(look: { x: number; y: number } | null): void {
    this.look = look ? { x: clamp(look.x, -1, 1), y: clamp(look.y, -1, 1) } : null
  }
  setBob(level: number): void { this.bob = clamp(level, 0, 1) }
  setIcon(id: IconId | null): void { this.iconSlot.desired = id }
  setAccessory(id: AccessoryId | null): void { this.accessorySlot.desired = id }
  addProp(id: PropId): void { this.props.push({ key: ++this.propSeq, id, born: this.now }) }
  playSequence(id: SequenceId): void { this.player.start(id, this.now) }
  setReducedMotion(on: boolean): void { this.reduced = on }

  step(dtMs: number, now: number): void {
    this.now = now
    // sequences (steps are shared objects — never mutate them)
    for (const s of this.player.due(now)) {
      if (s.expr) this.setExpression(s.expr)
      if (s.nudge) this.setNudge(s.nudge)
      if (s.prop) this.addProp(s.prop)
      if (s.icon !== undefined) this.setIcon(s.icon)
      if (s.accessory !== undefined) this.setAccessory(s.accessory)
    }
    if (this.player.current && !this.player.active(now)) { this.player.stop(); this.nudge = {} }

    // idle saccades
    if (now >= this.nextSaccadeAt) {
      this.saccade = { x: (this.rand() - 0.5) * 0.5, y: (this.rand() - 0.5) * 0.3 }
      this.nextSaccadeAt = now + 1000 + this.rand() * 3000
    }
    // blinks
    if (now >= this.nextBlinkAt && this.blinkStart < 0) {
      this.blinkStart = now
      this.blinkSecond = this.rand() < 0.1
      this.nextBlinkAt = now + 2500 + this.rand() * 4500
    }

    // targets
    const glyphOn = (s: Slot<EyeGlyph>) => s.busy
    const tgtFace: FaceScalars = { ...this.base.face, ...this.nudge }
    if (this.look) { tgtFace.lookX = this.look.x; tgtFace.lookY = this.look.y }
    else { tgtFace.lookX = clamp(tgtFace.lookX + this.saccade.x, -1, 1); tgtFace.lookY = clamp(tgtFace.lookY + this.saccade.y, -1, 1) }
    if (this.reduced) { tgtFace.bounce = 0; tgtFace.tilt = 0 }
    for (const k of FACE_KEYS) { this.face[k].target = tgtFace[k]; stepSpring(this.face[k], dtMs) }
    const setEye = (springs: Record<EyeKey, Spring>, tgt: EyeParams, glyph: boolean) => {
      for (const k of EYE_KEYS) {
        springs[k].target = k === 'opacity' ? (glyph ? 0 : tgt.opacity) : glyph && (k === 'w' || k === 'h') ? tgt[k] * 0.4 : tgt[k]
        stepSpring(springs[k], dtMs)
      }
    }
    setEye(this.eyeL, this.base.eyeL, glyphOn(this.glyphL))
    setEye(this.eyeR, this.base.eyeR, glyphOn(this.glyphR))
    this.mouthVis.target = this.mouthGlyphSlot.busy ? 0 : 1
    stepSpring(this.mouthVis, dtMs)
    for (const s of [this.glyphL, this.glyphR, this.mouthGlyphSlot, this.iconSlot, this.accessorySlot]) s.step(dtMs)
    this.faceVis.target = this.iconSlot.busy ? 0 : 1
    stepSpring(this.faceVis, dtMs)

    this.props = this.props.filter(p => now - p.born < (PROPS[p.id].life ?? 2000))
  }

  private blinkAmount(): number {
    if (this.blinkStart < 0) return 0
    const t = this.now - this.blinkStart
    const one = (u: number) => (u < 90 ? smooth(u / 90) : u < 250 ? smooth(1 - (u - 90) / 160) : 0)
    if (t < 250) return one(t)
    if (this.blinkSecond && t < 520) return one(t - 270)
    this.blinkStart = -1
    return 0
  }

  frame(): FaceFrame {
    const val = <K extends string>(r: Record<K, Spring>) =>
      Object.fromEntries(Object.entries(r).map(([k, s]) => [k, (s as Spring).value])) as Record<K, number>
    const eyeL = val(this.eyeL) as EyeParams
    const eyeR = val(this.eyeR) as EyeParams
    const face = val(this.face) as FaceScalars
    const b = this.glyphL.busy || this.glyphR.busy ? 0 : this.blinkAmount()
    for (const e of [eyeL, eyeR]) {
      e.lidTop = Math.max(e.lidTop, 0.55 * b)
      e.lidBottom = Math.max(e.lidBottom, 0.45 * b)
    }
    const p: FaceParams = { eyeL, eyeR, face }
    const [lx, ly] = eyeCenter('L', p)
    const [rx, ry] = eyeCenter('R', p)
    const [mx, my] = mouthCenter(p)
    const t = this.now
    const breathe = (this.reduced ? 0.005 : 0.015) * Math.sin((2 * Math.PI * t) / 4000)
    const dx = this.reduced ? 0 : 3 * Math.sin((2 * Math.PI * t) / 7000)
    const dy = this.reduced ? 0 : 2 * Math.sin((2 * Math.PI * t) / 9000)
    const bob = this.reduced ? 0 : -6 * this.bob * Math.abs(Math.sin((2 * Math.PI * t) / 450))
    const scale = face.scale * (1 + breathe)
    const acc = this.accessorySlot.frame()
    return {
      eyeL: eyePath(eyeL, lx, ly, 'L'),
      eyeR: eyePath(eyeR, rx, ry, 'R'),
      eyeLCenter: [lx, ly],
      eyeRCenter: [rx, ry],
      eyeOpacityL: clamp(eyeL.opacity, 0, 1),
      eyeOpacityR: clamp(eyeR.opacity, 0, 1),
      mouth: mouthPath(face, mx, my),
      mouthCenter: [mx, my],
      mouthOpacity: clamp(face.mouthOpacity, 0, 1) * clamp(this.mouthVis.value, 0, 1),
      tongue: tonguePath(face, mx, my),
      tongueOpacity: clamp(face.tongue, 0, 1) * clamp(face.mouthOpen * 2, 0, 1),
      blush: clamp(face.blush, 0, 1),
      glyphL: this.glyphL.frame(),
      glyphR: this.glyphR.frame(),
      mouthGlyph: this.mouthGlyphSlot.frame(),
      faceOpacity: clamp(this.faceVis.value, 0, 1),
      icon: this.iconSlot.frame(),
      accessory: { ...acc, dy: (1 - Math.max(0, Math.min(1.2, this.accessorySlot.spring.value))) * -30 },
      props: this.props.map(pr => ({ key: pr.key, id: pr.id, age: t - pr.born })),
      transform: `translate(${f2(100 + dx)} ${f2(70 + dy + face.bounce + bob)}) rotate(${f2(face.tilt)}) scale(${f2(scale)}) translate(-100 -70)`,
      expression: this.expr,
      t,
    }
  }
}
