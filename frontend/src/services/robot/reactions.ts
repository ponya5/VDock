/**
 * DL-153 — how each mood reacts to each event, steady-state faces, idle
 * gags, priorities and cooldowns. Pure data; MoodEngine interprets it.
 */
import type { ExpressionId } from './expressions'
import type { SequenceId } from './sequences'
import type { AccessoryId, IconId, PropId } from './robotArt'
import type { SceneId } from './scenes'
import type { RobotReactTo } from '@/stores/settings'

export type Mood = 'funny' | 'grumpy' | 'sarcastic' | 'sweet'
export type RobotEvent =
  | 'greet' | 'agentWorking' | 'agentLong' | 'agentNeeds' | 'agentDone' | 'musicStart' | 'musicStop'
  | 'cpuHigh' | 'batteryLow' | 'notification' | 'update' | 'morning' | 'noon' | 'night' | 'weather'
  | 'pointerEnter' | 'pointerEyes' | 'pointerMouth' | 'pointerShake' | 'pointerDizzy' | 'pointerAnnoyed'
  | 'pointerCircle' | 'pointerLinger' | 'pointerApproach' | 'pointerLeave' | 'pointerReturn'
export interface Reaction { icon?: IconId; expr: ExpressionId; seq?: SequenceId; prop?: PropId; accessory?: AccessoryId; scene?: SceneId; ms?: number }
export type BaselineState = 'idle' | 'working' | 'waiting' | 'music' | 'night'

export const ICON_MS = 1200

const all = (r: Reaction | null): Record<Mood, Reaction | null> => ({ funny: r, grumpy: r, sarcastic: r, sweet: r })

export const REACTIONS: Record<RobotEvent, Record<Mood, Reaction | null>> = {
  greet: {
    funny: { expr: 'joy', seq: 'hello-hand', ms: 2600 },
    grumpy: { expr: 'unimpressed', ms: 2000 },
    sarcastic: { expr: 'smug', prop: 'wave', ms: 2200 },
    sweet: { expr: 'happy', prop: 'heart', ms: 2600 },
  },
  agentWorking: {
    funny: { icon: 'dots', expr: 'typing', scene: 'typing' },
    grumpy: { icon: 'dots', expr: 'squint' },
    sarcastic: { icon: 'dots', expr: 'side-eye', prop: 'clipboard' },
    sweet: { icon: 'dots', expr: 'typing', scene: 'typing', prop: 'heart' },
  },
  agentLong: {
    funny: { icon: 'spinner', expr: 'focused', accessory: 'wizard-hat', prop: 'magnifier', ms: 3200 },
    grumpy: { expr: 'bored', seq: 'sigh', prop: 'clock', ms: 3400 },
    sarcastic: { expr: 'whistle', seq: 'whistle-away' },
    sweet: { icon: 'spinner', expr: 'puppy', prop: 'sparkles' },
  },
  agentNeeds: {
    funny: { icon: 'exclaim', expr: 'joy', prop: 'phone', ms: 5000 },
    grumpy: { icon: 'exclaim', expr: 'glare', prop: 'anger', ms: 5000 },
    sarcastic: { icon: 'exclaim', expr: 'unimpressed', seq: 'eye-roll', ms: 5000 },
    sweet: { icon: 'exclaim', expr: 'shy', prop: 'wave', ms: 5000 },
  },
  agentDone: {
    funny: { icon: 'check', expr: 'excited', seq: 'cheer', accessory: 'party-hat', prop: 'trophy', ms: 4500 },
    grumpy: { icon: 'check', expr: 'unimpressed', seq: 'sigh' },
    sarcastic: { icon: 'check', expr: 'smug', accessory: 'sunglasses' },
    sweet: { icon: 'check', expr: 'love', seq: 'clap', prop: 'sparkles', ms: 4000 },
  },
  musicStart: {
    funny: { icon: 'equalizer', expr: 'happy', prop: 'notes', ms: 3000 },
    grumpy: { icon: 'equalizer', expr: 'unimpressed', ms: 2500 },
    sarcastic: { icon: 'equalizer', expr: 'suspicious', ms: 3000 },
    sweet: { icon: 'equalizer', expr: 'content', prop: 'notes', ms: 3000 },
  },
  musicStop: {
    funny: { expr: 'bored', seq: 'look-around', ms: 2600 },
    grumpy: { expr: 'content', seq: 'sigh', ms: 2200 },
    sarcastic: { expr: 'smug', ms: 2000 },
    sweet: { expr: 'sad', ms: 2200 },
  },
  cpuHigh: {
    funny: { icon: 'warning', expr: 'dizzy', prop: 'sweat' },
    grumpy: { icon: 'warning', expr: 'angry', prop: 'thermometer' },
    sarcastic: { icon: 'warning', expr: 'teeth-grit' },
    sweet: { icon: 'warning', expr: 'worried', prop: 'sweat' },
  },
  batteryLow: {
    funny: { icon: 'battery', expr: 'sleepy', seq: 'yawn-sleep' },
    grumpy: { icon: 'battery', expr: 'glare' },
    sarcastic: { icon: 'battery', expr: 'dead' },
    sweet: { icon: 'battery', expr: 'worried' },
  },
  notification: {
    funny: { icon: 'envelope', expr: 'surprised', seq: 'double-take', ms: 2500 },
    grumpy: { icon: 'envelope', expr: 'bored', ms: 2000 },
    sarcastic: { icon: 'envelope', expr: 'unimpressed', seq: 'eye-roll', ms: 2200 },
    sweet: { icon: 'envelope', expr: 'happy', ms: 2200 },
  },
  update: {
    funny: { icon: 'download', expr: 'starstruck' },
    grumpy: { icon: 'download', expr: 'bored', seq: 'sigh' },
    sarcastic: { icon: 'download', expr: 'suspicious' },
    sweet: { icon: 'download', expr: 'happy', prop: 'sparkles' },
  },
  morning: {
    funny: { expr: 'sleepy', seq: 'wake-up', prop: 'coffee', ms: 4000 },
    grumpy: { expr: 'glare', prop: 'coffee', ms: 3500 },
    sarcastic: { expr: 'unimpressed', prop: 'coffee', ms: 3500 },
    sweet: { expr: 'content', prop: 'coffee', ms: 3500 },
  },
  noon: {
    funny: { expr: 'happy', accessory: 'chef-hat', seq: 'nod', ms: 4000 },
    grumpy: null,
    sarcastic: null,
    sweet: { expr: 'happy', accessory: 'chef-hat', ms: 3500 },
  },
  night: all({ expr: 'sleepy', seq: 'yawn-sleep', ms: 4500 }),
  weather: {
    funny: { expr: 'happy', ms: 2500 },
    grumpy: { expr: 'bored', ms: 2000 },
    sarcastic: { expr: 'smug', ms: 2000 },
    sweet: { expr: 'content', ms: 2500 },
  },
  pointerEnter: {
    funny: { expr: 'puppy', ms: 1500 },
    grumpy: { expr: 'unimpressed', ms: 1500 },
    sarcastic: { expr: 'side-eye', ms: 1500 },
    sweet: { expr: 'happy', ms: 1500 },
  },
  pointerEyes: all({ expr: 'squint', ms: 1400 }),
  pointerMouth: {
    funny: { expr: 'laughing', seq: 'giggle', ms: 1800 },
    grumpy: { expr: 'pout', ms: 1600 },
    sarcastic: { expr: 'mischievous', ms: 1600 },
    sweet: { expr: 'laughing', seq: 'giggle', ms: 1800 },
  },
  pointerShake: {
    funny: { expr: 'joy', ms: 1800 },
    grumpy: { expr: 'glare', ms: 1800 },
    sarcastic: { expr: 'side-eye', ms: 1800 },
    sweet: { expr: 'laughing', ms: 1800 },
  },
  pointerDizzy: all({ expr: 'dizzy', ms: 2200 }),
  pointerAnnoyed: {
    funny: { expr: 'pout', ms: 2500 },
    grumpy: { expr: 'angry', prop: 'anger', ms: 2600 },
    sarcastic: { expr: 'unimpressed', seq: 'eye-roll', ms: 2400 },
    sweet: { expr: 'sad', ms: 2400 },
  },
  pointerCircle: all({ expr: 'dizzy', ms: 2000 }),
  pointerLinger: {
    funny: { expr: 'shy', seq: 'cover-eyes', ms: 2600 },
    grumpy: { expr: 'suspicious', ms: 2200 },
    sarcastic: { expr: 'suspicious', ms: 2200 },
    sweet: { expr: 'love', ms: 2600 },
  },
  pointerApproach: all({ expr: 'suspicious', ms: 1800 }),
  pointerLeave: {
    funny: { icon: 'question', expr: 'bored', seq: 'shrug', ms: 1800 },
    grumpy: { expr: 'content', ms: 1600 },
    sarcastic: { icon: 'question', expr: 'smug', ms: 1600 },
    sweet: { icon: 'question', expr: 'sad', ms: 1800 },
  },
  pointerReturn: {
    funny: { expr: 'cheeky', seq: 'cheeky-wink', prop: 'sneakers', ms: 2000 },
    grumpy: { expr: 'unimpressed', ms: 1600 },
    sarcastic: { expr: 'surprised', seq: 'double-take', ms: 1800 },
    sweet: { expr: 'joy', prop: 'heart', ms: 2000 },
  },
}

export const BASELINES: Record<Mood, Record<BaselineState, ExpressionId>> = {
  funny: { idle: 'neutral', working: 'typing', waiting: 'puppy', music: 'happy', night: 'asleep' },
  grumpy: { idle: 'bored', working: 'squint', waiting: 'glare', music: 'unimpressed', night: 'asleep' },
  sarcastic: { idle: 'unimpressed', working: 'side-eye', waiting: 'side-eye', music: 'smug', night: 'asleep' },
  sweet: { idle: 'content', working: 'typing', waiting: 'puppy', music: 'content', night: 'asleep' },
}

/** Scene held for as long as the baseline lasts (DL-155). */
export const BASELINE_SCENE: Record<Mood, Partial<Record<BaselineState, SceneId>>> = {
  funny: { working: 'typing' },
  grumpy: {},
  sarcastic: {},
  sweet: { working: 'typing' },
}

export const IDLE_GAGS: Record<Mood, SequenceId[]> = {
  funny: ['look-around', 'hiccup', 'sneeze', 'peek-a-boo', 'giggle', 'wink', 'cheeky-wink', 'hello-hand', 'cover-eyes', 'inspect', 'phone-call', 'take-notes', 'relax', 'sneaker-walk', 'hand-on-chin', 'gasp-wink', 'evil-plan'],
  grumpy: ['sigh', 'head-shake', 'look-around', 'rage-fit', 'hand-on-chin'],
  sarcastic: ['eye-roll', 'whistle-away', 'look-around', 'shrug', 'evil-plan', 'what-now', 'inspect'],
  sweet: ['giggle', 'look-around', 'nod', 'wink', 'hello-hand', 'cover-eyes', 'relax', 'sad-moment', 'take-notes'],
}

export const PRIORITY: Record<RobotEvent, number> = {
  agentNeeds: 100, agentDone: 90, cpuHigh: 80, batteryLow: 80,
  pointerEnter: 70, pointerEyes: 70, pointerMouth: 70, pointerShake: 70, pointerDizzy: 72, pointerAnnoyed: 74,
  pointerCircle: 70, pointerLinger: 70, pointerApproach: 70, pointerLeave: 70, pointerReturn: 70,
  notification: 60, update: 60, greet: 55, musicStart: 50, musicStop: 45, agentWorking: 40, agentLong: 40,
  morning: 30, noon: 30, night: 30, weather: 30,
}

export const COOLDOWN_MS: Record<RobotEvent, number> = {
  greet: 0, agentWorking: 60_000, agentLong: 60_000, agentNeeds: 30_000, agentDone: 30_000,
  musicStart: 60_000, musicStop: 60_000, cpuHigh: 120_000, batteryLow: 600_000, notification: 60_000, update: 600_000,
  morning: 0, noon: 0, night: 0, weather: 600_000,
  pointerEnter: 6000, pointerEyes: 6000, pointerMouth: 6000, pointerShake: 6000, pointerDizzy: 6000,
  pointerAnnoyed: 6000, pointerCircle: 6000, pointerLinger: 6000, pointerApproach: 6000, pointerLeave: 6000, pointerReturn: 6000,
}

export const EVENT_GROUP: Partial<Record<RobotEvent, keyof RobotReactTo>> = {
  agentWorking: 'agent', agentLong: 'agent', agentNeeds: 'agent', agentDone: 'agent',
  musicStart: 'music', musicStop: 'music',
  cpuHigh: 'system', batteryLow: 'system',
  morning: 'ambient', noon: 'ambient', night: 'ambient', weather: 'ambient',
}
