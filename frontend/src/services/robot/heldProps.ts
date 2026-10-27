/**
 * DL-155 follow-up A — held props. A glove grips the prop and moves it with a
 * purpose (magnifier sweeps, mug is sipped, phone is talked into, trophy is
 * pumped). Pure geometry: RobotFace draws the prop at anchor + motion, rotating
 * about the grip, and RobotHeldHand draws the arm and fist at the grip.
 */
import type { PropId } from './robotArt'

export interface HeldMotion { dx: number; dy: number; rot: number }
export interface HeldDef {
  /** Which edge the arm enters from: 1 = right, -1 = left. */
  side: 1 | -1
  /** Where the fist closes, in prop-local coordinates. */
  grip: readonly [number, number]
  /** Prop offset/tilt `s` seconds after it appeared. */
  motion: (s: number) => HeldMotion
}

const sin = Math.sin
const sip = (s: number) => 0.5 - 0.5 * Math.cos(s * 2.2) // 0 → 1 → 0 lift cycle

export const HELD: Partial<Record<PropId, HeldDef>> = {
  magnifier: { side: 1, grip: [15, 15], motion: s => ({ dx: sin(s * 1.6) * 28, dy: sin(s * 3.2) * 4, rot: sin(s * 1.6) * 12 }) },
  coffee: { side: -1, grip: [19, 3], motion: s => ({ dx: sip(s) * 52, dy: -sip(s) * 16, rot: sip(s) * 24 }) },
  thermometer: { side: 1, grip: [0, 16], motion: s => ({ dx: sin(s * 22) * 1.5, dy: 0, rot: sin(s * 22) * 8 }) },
  umbrella: { side: 1, grip: [0, 14], motion: s => ({ dx: 0, dy: sin(s * 2.4) * 2, rot: sin(s * 2.4) * 9 }) },
  trophy: { side: -1, grip: [0, 15], motion: s => ({ dx: 0, dy: -Math.abs(sin(s * 3)) * 11, rot: sin(s * 3) * 6 }) },
  phone: { side: 1, grip: [-2, 0], motion: s => ({ dx: sin(s * 8) * 1.2, dy: sin(s * 5) * 1.5, rot: -18 + sin(s * 8) * 4 }) },
  clipboard: { side: -1, grip: [-20, 6], motion: s => ({ dx: 0, dy: sin(s * 2) * 1.5, rot: -8 + sin(s * 2) * 2 }) },
}

/** 0 = arm off-screen, 1 = in place (overshoots slightly on the way in). */
export function heldSlide(ageMs: number, lifeMs: number): number {
  const IN = 380
  const OUT = 350
  if (ageMs <= 0) return 0
  if (ageMs < IN) {
    const v = ageMs / IN - 1
    return 1 + 2.2 * v * v * v + 1.2 * v * v
  }
  if (ageMs > lifeMs - OUT) return Math.max(0, (lifeMs - ageMs) / OUT)
  return 1
}

const r2 = (n: number) => Math.round(n * 100) / 100

/** Group transform for a prop: anchor + motion, scale, then tilt about the grip. */
export function propTransform(id: PropId, anchor: readonly [number, number], k: number, ageMs: number): string {
  const held = HELD[id]
  if (!held) return `translate(${anchor[0]} ${anchor[1]}) scale(${r2(k)})`
  const m = held.motion(Math.max(0, ageMs) / 1000)
  const [gx, gy] = held.grip
  return `translate(${r2(anchor[0] + m.dx)} ${r2(anchor[1] + m.dy)}) scale(${r2(k)}) translate(${gx} ${gy}) rotate(${r2(m.rot)}) translate(${-gx} ${-gy})`
}
