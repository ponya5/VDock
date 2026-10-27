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
export interface EngineOptions { mood: Mood; quips: boolean; reactTo: RobotReactTo; rand?: () => number }

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
  private morningDay = ''
  private noonDay = ''
  private baseline: BaselineState = 'idle'
  private shownBaseExpr: ExpressionId | null = null
  private shownBaseAcc: AccessoryId | null | undefined = undefined
  private lastQuipAt = -Infinity
  private lastQuip = ''
  private nextGagAt = 0

  constructor(opts: EngineOptions) { this.opts = { rand: Math.random, ...opts } }

  configure(opts: Partial<EngineOptions>): void {
    this.opts = { ...this.opts, ...opts }
    this.shownBaseExpr = null // re-emit the baseline in the new mood
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
      if (s.hour >= 6 && s.hour <= 10) this.morningDay = s.day
      if (s.hour === 12) this.noonDay = s.day
    } else {
      events.push(...this.edges(this.prev!, s, now))
    }
    this.prev = s

    // baseline
    const nextBaseline = this.computeBaseline(s, lastPointerAt, now)
    if (nextBaseline === 'night' && this.baseline !== 'night' && !first) events.push('night')
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
        if (r) this.start(best, r, now, out)
      }
    }

    // due scheduled commands
    const due = this.pending.filter(p => p.at <= now)
    this.pending = this.pending.filter(p => p.at > now)
    for (const p of due) out.push(p.cmd)

    // reaction ended → back to baseline; idle gags
    if (this.reaction && now >= this.reactionUntil) {
      this.reaction = null
      this.shownBaseExpr = null
      this.shownBaseAcc = undefined
      this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
    }
    if (!this.reaction) {
      const expr = BASELINES[this.opts.mood][this.baseline]
      const acc = this.baselineAccessory(s, now)
      if (expr !== this.shownBaseExpr) { out.push({ type: 'expr', id: expr }); this.shownBaseExpr = expr }
      if (acc !== this.shownBaseAcc) { out.push({ type: 'accessory', id: acc }); this.shownBaseAcc = acc }
      if (this.baseline === 'idle') {
        if (this.nextGagAt === 0) this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
        else if (now >= this.nextGagAt) {
          const gags = IDLE_GAGS[this.opts.mood]
          out.push({ type: 'seq', id: gags[Math.floor(this.opts.rand() * gags.length) % gags.length] })
          this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
        }
      }
    }
    return out
  }

  private start(ev: RobotEvent, r: Reaction, now: number, out: RobotCommand[]): void {
    this.pending = []
    this.reaction = ev
    const faceAt = r.icon ? now + ICON_MS : now
    this.reactionUntil = faceAt + (r.ms ?? 4000)
    const face: RobotCommand[] = [r.seq ? { type: 'seq', id: r.seq } : { type: 'expr', id: r.expr }]
    if (r.seq) face.unshift({ type: 'expr', id: r.expr })
    if (r.prop) face.push({ type: 'prop', id: r.prop })
    if (r.accessory) face.push({ type: 'accessory', id: r.accessory })
    if (r.icon) {
      out.push({ type: 'icon', id: r.icon })
      this.pending.push({ at: faceAt, cmd: { type: 'icon', id: null } })
      for (const c of face) this.pending.push({ at: faceAt, cmd: c })
    } else {
      out.push(...face)
    }
    // the baseline accessory comes back when the reaction ends
    this.shownBaseAcc = r.accessory ?? this.shownBaseAcc
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
    if (s.hour >= 6 && s.hour <= 10 && this.morningDay !== s.day) { this.morningDay = s.day; ev.push('morning') }
    if (s.hour === 12 && this.noonDay !== s.day) { this.noonDay = s.day; ev.push('noon') }
    if (s.weather !== null && s.weather !== p.weather) ev.push('weather')
    return ev
  }

  private computeBaseline(s: RobotSignals, lastPointerAt: number, now: number): BaselineState {
    const nightHour = s.hour >= 23 || s.hour < 6
    if (s.agent === 'permission') return 'waiting'
    if (s.agent === 'working') return 'working'
    if (nightHour && !s.musicPlaying && now - lastPointerAt >= NIGHT_IDLE_MS) return 'night'
    if (s.musicPlaying) return 'music'
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
