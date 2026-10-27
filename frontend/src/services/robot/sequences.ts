/**
 * DL-153 — named animation sequences: short timelines of expressions,
 * nudges (extra param overrides on top of the expression), props, icons and
 * accessories. The SequencePlayer only hands out due steps; the animator
 * applies them, so all motion still goes through the springs.
 */
import type { ExpressionId } from './expressions'
import type { FaceScalars } from './faceRig'
import type { AccessoryId, IconId, PropId } from './robotArt'
import type { SceneId } from './scenes'

export interface SeqStep {
  at: number
  expr?: ExpressionId
  nudge?: Partial<FaceScalars>
  prop?: PropId
  icon?: IconId | null
  accessory?: AccessoryId | null
  scene?: SceneId | null
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
  // DL-155: Wingy's hands
  'type-session': { duration: 5200, steps: [{ at: 0, expr: 'determined', scene: 'typing' }, { at: 1800, expr: 'focused' }, { at: 3600, expr: 'proud', prop: 'sparkles' }, { at: 4600, scene: null }] },
  cheer: { duration: 3200, steps: [{ at: 0, expr: 'excited', scene: 'cheer', prop: 'confetti', nudge: { bounce: -8 } }, { at: 400, nudge: { bounce: 0 } }, { at: 800, nudge: { bounce: -8 } }, { at: 1200, nudge: { bounce: 0 } }, { at: 2600, expr: 'happy', scene: null }] },
  clap: { duration: 2800, steps: [{ at: 0, expr: 'joy', scene: 'clap' }, { at: 2200, expr: 'happy', scene: null }] },
  'cover-eyes': { duration: 2600, steps: [{ at: 0, expr: 'shy', scene: 'cover' }, { at: 1900, expr: 'cheeky', scene: null }] },
  'hello-hand': { duration: 2600, steps: [{ at: 0, expr: 'happy', scene: 'hello' }, { at: 2000, scene: null }] },
  'cheeky-wink': { duration: 1400, steps: [{ at: 0, expr: 'cheeky' }, { at: 1100, expr: 'happy' }] },
  // DL-156: storyboard scenes (from the reference clips)
  inspect: { duration: 3300, steps: [{ at: 0, expr: 'inspecting', scene: 'inspect', nudge: { lookX: 0.2 } }, { at: 1200, nudge: { lookX: 0.6 } }, { at: 2200, nudge: { lookX: 0.2 } }, { at: 3000, expr: 'smug', scene: null }] },
  'phone-call': { duration: 3400, steps: [{ at: 0, expr: 'chatty', scene: 'call' }, { at: 500, nudge: { mouthOpen: 0.1 } }, { at: 800, nudge: { mouthOpen: 0.8 } }, { at: 1100, nudge: { mouthOpen: 0.1 } }, { at: 1400, nudge: { mouthOpen: 0.7 } }, { at: 1900, expr: 'bored', nudge: { mouthOpen: 0 } }, { at: 2300, expr: 'chatty', nudge: { mouthOpen: 0.8 } }, { at: 3200, expr: 'happy', scene: null }] },
  'take-notes': { duration: 3400, steps: [{ at: 0, expr: 'focused', scene: 'notes' }, { at: 1200, expr: 'content' }, { at: 2200, expr: 'focused', nudge: { lookY: 0.6 } }, { at: 3100, expr: 'proud', scene: null }] },
  relax: { duration: 3500, steps: [{ at: 0, expr: 'relaxed', scene: 'relax' }, { at: 3100, expr: 'happy', scene: null }] },
  'sneaker-walk': { duration: 2300, steps: [{ at: 0, scene: 'sneakers' }, { at: 2000, scene: null }] },
  'hand-on-chin': { duration: 2600, steps: [{ at: 0, expr: 'thinking', scene: 'chin' }, { at: 1400, expr: 'suspicious' }, { at: 2300, expr: 'happy', scene: null }] },
  'rage-fit': { duration: 2400, steps: [{ at: 0, expr: 'rage', nudge: { bounce: -4 } }, { at: 600, nudge: { bounce: 0 } }, { at: 1000, nudge: { bounce: -4 } }, { at: 1500, nudge: { bounce: 0 } }, { at: 2100, expr: 'unimpressed' }] },
  'sad-moment': { duration: 3000, steps: [{ at: 0, expr: 'sad-tear' }, { at: 2600, expr: 'content' }] },
  'what-now': { duration: 2600, steps: [{ at: 0, expr: 'confused' }, { at: 2200, expr: 'neutral' }] },
  'gasp-wink': { duration: 2200, steps: [{ at: 0, expr: 'gasp', nudge: { bounce: -8 } }, { at: 500, nudge: { bounce: 0 } }, { at: 1100, expr: 'startled' }, { at: 1700, expr: 'wink' }] },
  'evil-plan': { duration: 2400, steps: [{ at: 0, expr: 'smirk' }, { at: 900, expr: 'evil-grin' }, { at: 2000, expr: 'smirk' }] },
  // the whole reference storyboard, in order
  storyboard: {
    duration: 25500,
    steps: [
      { at: 0, expr: 'typing', scene: 'typing' },
      { at: 2400, expr: 'inspecting', scene: 'inspect' },
      { at: 5700, expr: 'chatty', scene: 'call' },
      { at: 6500, nudge: { mouthOpen: 0.8 } }, { at: 7000, nudge: { mouthOpen: 0.1 } }, { at: 7500, nudge: { mouthOpen: 0.8 } }, { at: 8300, nudge: { mouthOpen: 0.1 } },
      { at: 9100, expr: 'focused', scene: 'notes', nudge: { mouthOpen: 0 } },
      { at: 12500, expr: 'relaxed', scene: 'relax' },
      { at: 16000, expr: 'neutral', scene: 'sneakers' },
      { at: 18300, expr: 'thinking', scene: 'chin' },
      { at: 19300, expr: 'typing', scene: 'typing' },
      { at: 22800, expr: 'inspecting', scene: 'inspect' },
      { at: 24400, expr: 'smug' },
      { at: 25000, scene: null },
    ],
  },
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
