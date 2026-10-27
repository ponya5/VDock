/**
 * DL-153 — the robot's brain. Each step compares the live signal snapshot
 * with the previous one, turns edges and pointer gestures into events, picks
 * the highest-priority one the mood/settings allow, and emits commands
 * (expression, sequence, icon, prop, accessory, quip). Pure; time is passed in.
 */
import type { RobotReactTo } from '@/stores/settings'
import type { ExpressionId } from './expressions'
import type { SequenceId } from './sequences'
import type { AccessoryId, IconId, PropId } from './robotArt'
import type { PointerGesture } from './pointerSense'
import {
  REACTIONS, BASELINES, IDLE_GAGS, PRIORITY, COOLDOWN_MS, EVENT_GROUP, ICON_MS,
  type Mood, type RobotEvent, type BaselineState, type Reaction,
} from './reactions'
import { QUIPS } from './quips'
import { SEQUENCES } from './sequences'

export type WeatherKind = 'sunny' | 'rain' | 'snow' | 'cold' | 'other'
export interface RobotSignals {
  agent: 'idle' | 'working' | 'permission' | 'ready'
  musicPlaying: boolean
  cpuPercent: number | null
  batteryPercent: number | null
  batteryCharging: boolean | null
  notificationCount: number
  updateAvailable: boolean
  weather: WeatherKind | null
  isDay: boolean
  hour: number
  day: string
}
export type RobotCommand =
  | { type: 'expr'; id: ExpressionId } | { type: 'seq'; id: SequenceId }
  | { type: 'icon'; id: IconId | null } | { type: 'prop'; id: PropId }
  | { type: 'accessory'; id: AccessoryId | null } | { type: 'quip'; text: string }
type DayStorage = Pick<Storage, 'getItem' | 'setItem'>
export interface EngineOptions {
  mood: Mood; quips: boolean; reactTo: RobotReactTo; rand?: () => number
  /** Per-device store for the morning/noon once-a-day marks (default: localStorage). */
  storage?: DayStorage | null
}
const DAY_MARKS_KEY = 'vdock.robot.dayMarks'

const GESTURE_EVENT: Record<PointerGesture, RobotEvent> = {
  enter: 'pointerEnter', eyes: 'pointerEyes', mouth: 'pointerMouth', shake: 'pointerShake', dizzy: 'pointerDizzy',
  annoyed: 'pointerAnnoyed', circle: 'pointerCircle', linger: 'pointerLinger', approach: 'pointerApproach',
  leave: 'pointerLeave', return: 'pointerReturn',
}
const LONG_WORK_MS = 180_000
const NIGHT_IDLE_MS = 120_000

export class MoodEngine {
  private opts: Required<EngineOptions>
  private prev: RobotSignals | null = null
  private lastFired = new Map<RobotEvent, number>()
  private reaction: RobotEvent | null = null
  private reactionUntil = 0
  private pending: Array<{ at: number; cmd: RobotCommand }> = []
  private workingSince: number | null = null
  private longFired = false
  private cpuSince: number | null = null
  private cpuArmed = true
  private batteryArmed = true
  private marks: { morning?: string; noon?: string } = {}
  private gagUntil = 0
  private baseline: BaselineState = 'idle'
  private shownBaseExpr: ExpressionId | null = null
  private shownBaseAcc: AccessoryId | null | undefined = undefined
  private lastQuipAt = -Infinity
  private lastQuip = ''
  private nextGagAt = 0
  private iconUp = false

  constructor(opts: EngineOptions) {
    this.opts = {
      rand: Math.random,
      storage: typeof localStorage !== 'undefined' ? localStorage : null,
      ...opts,
    }
    try {
      const saved = JSON.parse(this.opts.storage?.getItem(DAY_MARKS_KEY) ?? 'null') as { morning?: string; noon?: string } | null
      if (saved && typeof saved === 'object') this.marks = { morning: saved.morning, noon: saved.noon }
    } catch { /* storage unavailable or corrupt — start fresh */ }
  }

  private markDay(kind: 'morning' | 'noon', day: string): void {
    this.marks = { ...this.marks, [kind]: day }
    try { this.opts.storage?.setItem(DAY_MARKS_KEY, JSON.stringify(this.marks)) } catch { /* ignore */ }
  }

  configure(opts: Partial<EngineOptions>): void {
    this.opts = { ...this.opts, ...opts }
    this.shownBaseExpr = null // re-emit the baseline in the new mood
    this.shownBaseAcc = undefined
  }

  get state(): { reaction: RobotEvent | null; baseline: BaselineState; mood: Mood } {
    return { reaction: this.reaction, baseline: this.baseline, mood: this.opts.mood }
  }

  step(s: RobotSignals, gestures: PointerGesture[], lastPointerAt: number, now: number): RobotCommand[] {
    const out: RobotCommand[] = []
    const events: RobotEvent[] = gestures.map(g => GESTURE_EVENT[g])
    const first = this.prev === null
    if (first) {
      events.push('greet')
      if (s.agent === 'working') this.workingSince = now
    } else {
      events.push(...this.edges(this.prev!, s, now))
    }
    // morning / noon: pending until a reaction actually starts (marked in step below)
    if (s.hour >= 6 && s.hour <= 10 && this.marks.morning !== s.day) events.push('morning')
    if (s.hour === 12 && this.marks.noon !== s.day) events.push('noon')
    this.prev = s

    // baseline
    const nextBaseline = this.computeBaseline(s, lastPointerAt, now)
    if (nextBaseline === 'night' && this.baseline !== 'night' && !first) events.push('night')
    if (nextBaseline === 'idle' && this.baseline !== 'idle') this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
    this.baseline = nextBaseline

    // pick the strongest allowed event
    let best: RobotEvent | null = null
    for (const ev of events) {
      const group = EVENT_GROUP[ev]
      if (group && !this.opts.reactTo[group]) continue
      const last = this.lastFired.get(ev)
      if (last !== undefined && now - last < COOLDOWN_MS[ev]) continue
      if (best === null || PRIORITY[ev] > PRIORITY[best]) best = ev
    }
    if (best) {
      const active = this.reaction && now < this.reactionUntil
      if (!active || PRIORITY[best] >= PRIORITY[this.reaction!]) {
        this.lastFired.set(best, now)
        const r = REACTIONS[best][this.opts.mood]
        if (r) {
          this.start(best, r, now, out)
          this.gagUntil = 0
          if (best === 'morning' || best === 'noon') this.markDay(best, s.day)
        }
      }
    }

    // due scheduled commands
    const due = this.pending.filter(p => p.at <= now)
    this.pending = this.pending.filter(p => p.at > now)
    for (const p of due) {
      if (p.cmd.type === 'icon' && p.cmd.id === null) this.iconUp = false
      out.push(p.cmd)
    }

    // reaction ended → back to baseline; idle gags
    if (this.reaction && now >= this.reactionUntil) {
      this.reaction = null
      this.shownBaseExpr = null
      this.shownBaseAcc = undefined
      this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
    }
    if (!this.reaction) {
      if (this.gagUntil > 0 && now >= this.gagUntil) { this.gagUntil = 0; this.shownBaseExpr = null }
      const expr = BASELINES[this.opts.mood][this.baseline]
      const acc = this.baselineAccessory(s, now)
      if (expr !== this.shownBaseExpr) { out.push({ type: 'expr', id: expr }); this.shownBaseExpr = expr }
      if (acc !== this.shownBaseAcc) { out.push({ type: 'accessory', id: acc }); this.shownBaseAcc = acc }
      if (this.baseline === 'idle') {
        if (this.nextGagAt === 0) this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
        else if (now >= this.nextGagAt) {
          const gags = IDLE_GAGS[this.opts.mood]
          const id = gags[Math.floor(this.opts.rand() * gags.length) % gags.length]
          out.push({ type: 'seq', id })
          this.gagUntil = now + SEQUENCES[id].duration
          this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
        }
      }
    }
    return out
  }

  private start(ev: RobotEvent, r: Reaction, now: number, out: RobotCommand[]): void {
    this.pending = []
    if (!r.icon && this.iconUp) { out.push({ type: 'icon', id: null }); this.iconUp = false }
    this.reaction = ev
    const faceAt = r.icon ? now + ICON_MS : now
    this.reactionUntil = faceAt + (r.ms ?? 4000)
    const face: RobotCommand[] = [r.seq ? { type: 'seq', id: r.seq } : { type: 'expr', id: r.expr }]
    if (r.seq) face.unshift({ type: 'expr', id: r.expr })
    if (r.prop) face.push({ type: 'prop', id: r.prop })
    if (r.accessory) face.push({ type: 'accessory', id: r.accessory })
    if (r.icon) {
      out.push({ type: 'icon', id: r.icon })
      this.iconUp = true
      this.pending.push({ at: faceAt, cmd: { type: 'icon', id: null } })
      for (const c of face) this.pending.push({ at: faceAt, cmd: c })
    } else {
      out.push(...face)
    }
    this.maybeQuip(ev, now, out)
  }

  private maybeQuip(ev: RobotEvent, now: number, out: RobotCommand[]): void {
    if (!this.opts.quips || now - this.lastQuipAt < 20_000) return
    const lines = (QUIPS[this.opts.mood][ev] ?? []).filter(l => l !== this.lastQuip)
    if (!lines.length) return
    const text = lines[Math.floor(this.opts.rand() * lines.length) % lines.length]
    this.lastQuipAt = now
    this.lastQuip = text
    out.push({ type: 'quip', text })
  }

  private edges(p: RobotSignals, s: RobotSignals, now: number): RobotEvent[] {
    const ev: RobotEvent[] = []
    if (s.agent === 'working' && p.agent !== 'working') { ev.push('agentWorking'); this.workingSince = now; this.longFired = false }
    if (s.agent !== 'working') this.workingSince = null
    if (this.workingSince !== null && !this.longFired && now - this.workingSince >= LONG_WORK_MS) { this.longFired = true; ev.push('agentLong') }
    if (s.agent === 'permission' && p.agent !== 'permission') ev.push('agentNeeds')
    if (p.agent === 'working' && (s.agent === 'ready' || s.agent === 'idle')) ev.push('agentDone')
    if (s.musicPlaying && !p.musicPlaying) ev.push('musicStart')
    if (!s.musicPlaying && p.musicPlaying) ev.push('musicStop')
    if (s.cpuPercent !== null && s.cpuPercent >= 95) {
      if (this.cpuSince === null) this.cpuSince = now
      if (this.cpuArmed && now - this.cpuSince >= 10_000) { this.cpuArmed = false; ev.push('cpuHigh') }
    } else {
      this.cpuSince = null
      if (s.cpuPercent === null || s.cpuPercent < 85) this.cpuArmed = true
    }
    if (s.batteryPercent !== null && s.batteryPercent < 20 && s.batteryCharging !== true) {
      if (this.batteryArmed) { this.batteryArmed = false; ev.push('batteryLow') }
    } else if (s.batteryCharging === true || (s.batteryPercent !== null && s.batteryPercent >= 25)) this.batteryArmed = true
    if (s.notificationCount > p.notificationCount) ev.push('notification')
    if (s.updateAvailable && !p.updateAvailable) ev.push('update')
    if (s.weather !== null && p.weather !== null && s.weather !== p.weather) ev.push('weather')
    return ev
  }

  private computeBaseline(s: RobotSignals, lastPointerAt: number, now: number): BaselineState {
    const nightHour = s.hour >= 23 || s.hour < 6
    if (s.agent === 'permission' && this.opts.reactTo.agent) return 'waiting'
    if (s.agent === 'working' && this.opts.reactTo.agent) return 'working'
    if (nightHour && this.opts.reactTo.ambient && !s.musicPlaying && now - lastPointerAt >= NIGHT_IDLE_MS) return 'night'
    if (s.musicPlaying && this.opts.reactTo.music) return 'music'
    return 'idle'
  }

  private baselineAccessory(s: RobotSignals, now: number): AccessoryId | null {
    switch (this.baseline) {
      case 'music': return this.opts.reactTo.music ? 'headphones' : null
      case 'night': return 'nightcap'
      case 'working': return this.workingSince !== null && now - this.workingSince >= LONG_WORK_MS ? 'wizard-hat' : null
      case 'idle':
        if (!this.opts.reactTo.ambient) return null
        if (s.weather === 'sunny' && s.isDay) return 'sunglasses'
        if (s.weather === 'cold') return 'scarf'
        return null
      default: return null
    }
  }
}
