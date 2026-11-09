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
  // DL-163: expanded event sequences (getting bored, typing a lot, nodding when AI agent is idle, etc.)
  'bored-drum': {
    duration: 3800,
    steps: [
      { at: 0, expr: 'bored-sigh', scene: 'bored-desk' },
      { at: 900, nudge: { lookX: 0.5, lookY: -0.3 } },
      { at: 1800, expr: 'yawn', nudge: { scale: 1.04 } },
      { at: 2700, expr: 'bored-sigh', nudge: { scale: 1, lookX: -0.4 } },
      { at: 3500, expr: 'bored', scene: null },
    ],
  },
  'typing-frenzy': {
    duration: 4400,
    steps: [
      { at: 0, expr: 'hyper-typing', scene: 'typing-frenzy', nudge: { lookX: -0.45, bounce: -2 } },
      { at: 600, nudge: { lookX: 0.45, bounce: 1 } },
      { at: 1200, prop: 'sweat', nudge: { lookX: -0.4, bounce: -3 } },
      { at: 1900, nudge: { lookX: 0.5, bounce: 1 } },
      { at: 2600, expr: 'determined', prop: 'bulb', nudge: { lookX: 0, bounce: -4 } },
      { at: 3500, expr: 'proud', prop: 'sparkles', nudge: { bounce: 0 } },
      { at: 4100, scene: null },
    ],
  },
  'idle-nod': {
    duration: 4000,
    steps: [
      { at: 0, expr: 'nodding', scene: 'nodding-off', nudge: { bounce: 2, tilt: 2 } },
      { at: 650, expr: 'dozing', nudge: { bounce: 7, tilt: 6 } },
      { at: 1200, expr: 'nodding', nudge: { bounce: 1, tilt: 1 } },
      { at: 1850, expr: 'dozing', prop: 'zzz', nudge: { bounce: 9, tilt: 8 } },
      { at: 2750, expr: 'jolt-awake', nudge: { bounce: -8, tilt: -3 } },
      { at: 3350, expr: 'relieved', nudge: { bounce: 0, tilt: 0 } },
      { at: 3750, scene: null },
    ],
  },
  'agent-idle-nod': {
    duration: 2800,
    steps: [
      { at: 0, expr: 'zen', scene: 'chin', nudge: { lookY: 0.5, bounce: 3 } },
      { at: 450, nudge: { lookY: -0.1, bounce: -1 } },
      { at: 900, nudge: { lookY: 0.5, bounce: 3 } },
      { at: 1400, expr: 'content', nudge: { lookY: 0, bounce: 0 } },
      { at: 2400, scene: null },
    ],
  },
  'coffee-sip': {
    duration: 3400,
    steps: [
      { at: 0, expr: 'content', scene: 'coffee-break' },
      { at: 900, expr: 'zen', nudge: { lookY: 0.3, scale: 1.03 } },
      { at: 2100, expr: 'relieved', prop: 'heart', nudge: { scale: 1 } },
      { at: 3100, expr: 'happy', scene: null },
    ],
  },
  'facepalm-sigh': {
    duration: 2800,
    steps: [
      { at: 0, expr: 'exasperated', scene: 'facepalm', nudge: { bounce: 3, tilt: -6 } },
      { at: 800, nudge: { lookX: -0.5, tilt: -8 } },
      { at: 1500, nudge: { lookX: 0.5, tilt: -4 } },
      { at: 2400, expr: 'unimpressed', scene: null, nudge: { bounce: 0, tilt: 0 } },
    ],
  },
  'thumbs-up-pop': {
    duration: 2800,
    steps: [
      { at: 0, expr: 'excited', scene: 'thumbs-up', prop: 'sparkles', nudge: { bounce: -6 } },
      { at: 600, expr: 'wink-l', nudge: { bounce: 0 } },
      { at: 1500, expr: 'proud' },
      { at: 2500, expr: 'happy', scene: null },
    ],
  },
  'big-stretch': {
    duration: 3000,
    steps: [
      { at: 0, expr: 'yawn', scene: 'stretch', nudge: { bounce: -6, scale: 1.05 } },
      { at: 1100, expr: 'relieved', nudge: { bounce: 2, scale: 0.98 } },
      { at: 2000, expr: 'happy', prop: 'sparkles', nudge: { bounce: 0, scale: 1 } },
      { at: 2700, scene: null },
    ],
  },
  // DL-164: chat typing, DJ deck, karaoke, reading
  'chat-typing': {
    duration: 5200,
    steps: [
      { at: 0, expr: 'focused', scene: 'texting', icon: 'dots' },
      { at: 900, expr: 'typing', icon: null, nudge: { lookY: 0.5 } },
      { at: 2200, expr: 'chatty', nudge: { lookY: 0.3 } },
      { at: 3400, expr: 'joy', prop: 'heart', nudge: { lookY: 0 } },
      { at: 4800, expr: 'happy', scene: null },
    ],
  },
  'dj-scratch': {
    duration: 4200,
    steps: [
      { at: 0, expr: 'grooving', scene: 'dj', prop: 'notes', nudge: { bounce: -4, tilt: -5 } },
      { at: 450, nudge: { bounce: 1, tilt: 5 } },
      { at: 900, nudge: { bounce: -4, tilt: -5 } },
      { at: 1350, nudge: { bounce: 1, tilt: 5 } },
      { at: 2400, expr: 'joy', prop: 'sparkles', nudge: { bounce: -3, tilt: 0 } },
      { at: 3900, expr: 'happy', scene: null, nudge: { bounce: 0 } },
    ],
  },
  'sing-along': {
    duration: 4400,
    steps: [
      { at: 0, expr: 'chatty', scene: 'karaoke', prop: 'notes' },
      { at: 600, nudge: { mouthOpen: 0.9, tilt: -3 } },
      { at: 1100, nudge: { mouthOpen: 0.2, tilt: 3 } },
      { at: 1700, nudge: { mouthOpen: 0.9, tilt: -3 } },
      { at: 2300, nudge: { mouthOpen: 0.3, tilt: 3 } },
      { at: 2900, expr: 'joy', nudge: { mouthOpen: 0.8, tilt: 0 } },
      { at: 4100, expr: 'proud', scene: null, nudge: { mouthOpen: 0 } },
    ],
  },
  'reading-book': {
    duration: 5200,
    steps: [
      { at: 0, expr: 'focused', scene: 'reading', nudge: { lookY: 0.7 } },
      { at: 1500, nudge: { lookX: 0.5, lookY: 0.7 } },
      { at: 2400, nudge: { lookX: -0.5, lookY: 0.7 } },
      { at: 3300, expr: 'surprised', nudge: { lookX: 0, lookY: 0.6 } },
      { at: 3900, expr: 'content', nudge: { lookY: 0.7 } },
      { at: 4900, expr: 'happy', scene: null, nudge: { lookY: 0 } },
    ],
  },
  'music-jam': {
    duration: 3400,
    steps: [
      { at: 0, expr: 'grooving', scene: 'jamming', prop: 'notes', nudge: { bounce: -5, tilt: -5 } },
      { at: 500, nudge: { bounce: 1, tilt: 5 } },
      { at: 1000, nudge: { bounce: -5, tilt: -5 } },
      { at: 1500, nudge: { bounce: 1, tilt: 5 } },
      { at: 2200, expr: 'joy', prop: 'sparkles', nudge: { bounce: -4, tilt: 0 } },
      { at: 3100, expr: 'happy', scene: null, nudge: { bounce: 0 } },
    ],
  },
  'rainy-day': {
    duration: 3800,
    steps: [
      { at: 0, expr: 'surprised', scene: 'weather-rain', nudge: { lookY: -0.7 } },
      { at: 900, expr: 'worried', nudge: { lookY: -0.4, lookX: 0.3 } },
      { at: 1900, expr: 'cozy', nudge: { lookY: 0, lookX: 0 } },
      { at: 3400, expr: 'content', scene: null },
    ],
  },
  'snowy-day': {
    duration: 3600,
    steps: [
      { at: 0, expr: 'shivering', scene: 'weather-snow', accessory: 'scarf', prop: 'snowflake', nudge: { tilt: -3 } },
      { at: 400, nudge: { tilt: 3 } },
      { at: 800, nudge: { tilt: -3 } },
      { at: 1300, expr: 'cozy', nudge: { tilt: 0 } },
      { at: 3200, expr: 'happy', scene: null },
    ],
  },
  'sunny-day': {
    duration: 3400,
    steps: [
      { at: 0, expr: 'relaxed', scene: 'weather-sunny', accessory: 'sunglasses', prop: 'sun' },
      { at: 1400, expr: 'happy', nudge: { bounce: -3 } },
      { at: 2900, expr: 'content', scene: null, nudge: { bounce: 0 } },
    ],
  },
  'heavy-lift': {
    duration: 3800,
    steps: [
      { at: 0, expr: 'straining', scene: 'heavy-load', nudge: { bounce: 3, scale: 0.97 } },
      { at: 800, prop: 'sweat', nudge: { bounce: -4, scale: 1.04 } },
      { at: 1700, expr: 'straining', nudge: { bounce: 3, scale: 0.98 } },
      { at: 2600, expr: 'determined', prop: 'thermometer', nudge: { bounce: -2, scale: 1 } },
      { at: 3400, expr: 'relieved', scene: null, nudge: { bounce: 0 } },
    ],
  },
  'memory-full': {
    duration: 3600,
    steps: [
      { at: 0, expr: 'overloaded', scene: 'brain-overload', nudge: { tilt: -4, bounce: -2 } },
      { at: 700, prop: 'sweat', nudge: { tilt: 4, bounce: 2 } },
      { at: 1500, expr: 'dizzy', nudge: { tilt: -3 } },
      { at: 2400, expr: 'exasperated', nudge: { tilt: 0, bounce: 0 } },
      { at: 3200, expr: 'relieved', scene: null },
    ],
  },
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
