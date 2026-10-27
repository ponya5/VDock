/**
 * DL-153 — named animation sequences: short timelines of expressions,
 * nudges (extra param overrides on top of the expression), props, icons and
 * accessories. The SequencePlayer only hands out due steps; the animator
 * applies them, so all motion still goes through the springs.
 */
import type { ExpressionId } from './expressions'
import type { FaceScalars } from './faceRig'
import type { AccessoryId, IconId, PropId } from './robotArt'

export interface SeqStep {
  at: number
  expr?: ExpressionId
  nudge?: Partial<FaceScalars>
  prop?: PropId
  icon?: IconId | null
  accessory?: AccessoryId | null
}
export interface SequenceDef { readonly steps: readonly SeqStep[]; duration: number }

export const SEQUENCES = {
  wink: { duration: 900, steps: [{ at: 0, expr: 'wink-l' }, { at: 700, expr: 'happy' }] },
  'look-around': { duration: 2400, steps: [{ at: 0, expr: 'look-l' }, { at: 700, expr: 'look-r' }, { at: 1400, expr: 'look-up' }, { at: 2000, expr: 'neutral' }] },
  'eye-roll': { duration: 1600, steps: [{ at: 0, expr: 'unimpressed', nudge: { lookX: -0.8, lookY: -0.2 } }, { at: 250, nudge: { lookX: -0.4, lookY: -1 } }, { at: 500, nudge: { lookX: 0.5, lookY: -1 } }, { at: 750, nudge: { lookX: 0.9, lookY: -0.3 } }, { at: 1050, expr: 'unimpressed' }] },
  'double-take': { duration: 1500, steps: [{ at: 0, expr: 'look-r' }, { at: 350, expr: 'neutral' }, { at: 600, expr: 'surprised', nudge: { lookX: 1, bounce: -6 } }, { at: 1200, expr: 'surprised' }] },
  nod: { duration: 1200, steps: [{ at: 0, expr: 'happy', nudge: { lookY: 0.6 } }, { at: 250, nudge: { lookY: -0.2 } }, { at: 500, nudge: { lookY: 0.6 } }, { at: 750, nudge: { lookY: 0 } }] },
  'head-shake': { duration: 1300, steps: [{ at: 0, expr: 'unimpressed', nudge: { lookX: -0.7, tilt: -4 } }, { at: 250, nudge: { lookX: 0.7, tilt: 4 } }, { at: 500, nudge: { lookX: -0.7, tilt: -4 } }, { at: 750, nudge: { lookX: 0, tilt: 0 } }] },
  'yawn-sleep': { duration: 4200, steps: [{ at: 0, expr: 'sleepy' }, { at: 700, expr: 'yawn' }, { at: 2200, expr: 'sleepy' }, { at: 3200, expr: 'asleep', prop: 'zzz' }] },
  'wake-up': { duration: 2200, steps: [{ at: 0, expr: 'sleepy' }, { at: 600, expr: 'yawn' }, { at: 1500, expr: 'neutral', nudge: { scale: 1.06 } }, { at: 1900, nudge: { scale: 1 } }] },
  sneeze: { duration: 2000, steps: [{ at: 0, expr: 'squint', nudge: { lookY: -0.4 } }, { at: 500, expr: 'squint', nudge: { lookY: -0.8, mouthOpen: 0.4 } }, { at: 900, expr: 'squint', nudge: { lookY: 0.8, bounce: 6, mouthOpen: 0.8 } }, { at: 1200, expr: 'dizzy' }, { at: 1800, expr: 'neutral' }] },
  hiccup: { duration: 2200, steps: [{ at: 0, expr: 'surprised', nudge: { bounce: -8 } }, { at: 200, nudge: { bounce: 0 } }, { at: 900, nudge: { bounce: -8 } }, { at: 1100, nudge: { bounce: 0 } }, { at: 1600, expr: 'pout' }] },
  giggle: { duration: 1600, steps: [{ at: 0, expr: 'laughing', nudge: { bounce: -3 } }, { at: 200, nudge: { bounce: 1 } }, { at: 400, nudge: { bounce: -3 } }, { at: 600, nudge: { bounce: 1 } }, { at: 900, expr: 'happy' }] },
  shiver: { duration: 1800, steps: [{ at: 0, expr: 'worried', nudge: { tilt: -3 } }, { at: 90, nudge: { tilt: 3 } }, { at: 180, nudge: { tilt: -3 } }, { at: 270, nudge: { tilt: 3 } }, { at: 360, nudge: { tilt: -3 } }, { at: 450, nudge: { tilt: 0 } }, { at: 1200, expr: 'worried' }] },
  'sweat-wipe': { duration: 1800, steps: [{ at: 0, expr: 'worried', prop: 'sweat' }, { at: 900, expr: 'content' }] },
  'whistle-away': { duration: 2600, steps: [{ at: 0, expr: 'whistle', prop: 'notes' }, { at: 1800, expr: 'side-eye' }] },
  'peek-a-boo': { duration: 2400, steps: [{ at: 0, expr: 'neutral', nudge: { scale: 0.2, lookY: 1 } }, { at: 1000, expr: 'joy', nudge: { scale: 1.08 } }, { at: 1500, nudge: { scale: 1 } }] },
  startle: { duration: 1400, steps: [{ at: 0, expr: 'shocked', nudge: { bounce: -10, scale: 1.08 } }, { at: 400, expr: 'surprised', nudge: { bounce: 0, scale: 1 } }, { at: 900, expr: 'happy', prop: 'wave' }] },
  shrug: { duration: 1600, steps: [{ at: 0, expr: 'bored', nudge: { tilt: -6, bounce: -4 } }, { at: 600, nudge: { tilt: 0, bounce: 0 } }] },
  celebrate: { duration: 2600, steps: [{ at: 0, expr: 'joy', prop: 'confetti', nudge: { bounce: -8 } }, { at: 300, nudge: { bounce: 0 } }, { at: 600, nudge: { bounce: -8 } }, { at: 900, nudge: { bounce: 0 } }, { at: 1500, expr: 'happy', prop: 'sparkles' }] },
  sigh: { duration: 2000, steps: [{ at: 0, expr: 'bored', nudge: { scale: 1.04, lookY: -0.3 } }, { at: 800, nudge: { scale: 0.97, lookY: 0.4 } }, { at: 1500, nudge: { scale: 1, lookY: 0 } }] },
} as const satisfies Record<string, SequenceDef>
export type SequenceId = keyof typeof SEQUENCES

export class SequencePlayer {
  private id: SequenceId | null = null
  private startedAt = 0
  private next = 0

  get current(): SequenceId | null { return this.id }

  start(id: SequenceId, now: number): void {
    this.id = id
    this.startedAt = now
    this.next = 0
  }

  stop(): void { this.id = null }

  due(now: number): SeqStep[] {
    if (!this.id) return []
    const seq: SequenceDef = SEQUENCES[this.id]
    const out: SeqStep[] = []
    while (this.next < seq.steps.length && seq.steps[this.next].at <= now - this.startedAt) {
      out.push(seq.steps[this.next++])
    }
    return out
  }

  active(now: number): boolean {
    return this.id !== null && now - this.startedAt <= SEQUENCES[this.id].duration
  }
}
