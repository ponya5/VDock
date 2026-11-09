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
import type { SceneId } from './scenes'
import type { PointerGesture } from './pointerSense'
import type { Tempo, Vibe } from './beatTracker'
import {
  REACTIONS, BASELINES, BASELINE_SCENE, MUSIC_SCENES, MUSIC_ROTATE_MS, MUSIC_FEEL, TEMPO_SCENES, MUSIC_OUTFIT, MUSIC_DWELL_MS, IDLE_GAGS, PRIORITY, COOLDOWN_MS, EVENT_GROUP, ICON_MS,
  type Mood, type RobotEvent, type BaselineState, type Reaction,
} from './reactions'
import { QUIPS } from './quips'
import { SEQUENCES } from './sequences'

export type WeatherKind = 'sunny' | 'rain' | 'snow' | 'cold' | 'other'
export interface RobotSignals {
  agent: 'idle' | 'working' | 'permission' | 'ready'
  musicPlaying: boolean
  /** DL-165: detected tempo bucket / loudness feel of the music (absent = unknown). */
  tempo?: Tempo | null
  vibe?: Vibe
  cpuPercent: number | null
  memPercent?: number | null
  tempC?: number | null
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
  | { type: 'accessory'; id: AccessoryId | null; ids?: AccessoryId[] } | { type: 'scene'; id: SceneId | null } | { type: 'quip'; text: string }
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
const TYPING_LOT_MS = 60_000
const LONG_WORK_MS = 180_000
const AGENT_IDLE_NOD_MS = 52_000
const BORED_IDLE_MS = 75_000
const NIGHT_IDLE_MS = 120_000

export class MoodEngine {
  private opts: Required<EngineOptions>
  private prev: RobotSignals | null = null
  private lastFired = new Map<RobotEvent, number>()
  private reaction: RobotEvent | null = null
  private reactionUntil = 0
  private pending: Array<{ at: number; cmd: RobotCommand }> = []
  private workingSince: number | null = null
  private typingLotFired = false
  private longFired = false
  private agentIdleSince: number | null = null
  private agentIdleNodFired = false
  private quietSince: number | null = null
  private boredFired = false
  private cpuSince: number | null = null
  private cpuArmed = true
  private heavySince: number | null = null
  private heavyArmed = true
  private memSince: number | null = null
  private memArmed = true
  private batteryArmed = true
  private marks: { morning?: string; noon?: string } = {}
  private gagUntil = 0
  private baseline: BaselineState = 'idle'
  private shownBaseExpr: ExpressionId | null = null
  private shownBaseAcc: string | undefined = undefined
  private feelAt = -Infinity
  private shownBaseScene: SceneId | null | undefined = undefined
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
    this.shownBaseScene = undefined
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
      if (s.agent === 'idle') this.agentIdleSince = now
      this.quietSince = now
    } else {
      events.push(...this.edges(this.prev!, s, lastPointerAt, now))
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
        const r = this.resolveReaction(best, s)
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
      this.shownBaseScene = undefined
      this.nextGagAt = now + 20_000 + this.opts.rand() * 25_000
    }
    if (!this.reaction) {
      if (this.gagUntil > 0 && now >= this.gagUntil) { this.gagUntil = 0; this.shownBaseExpr = null }
      let expr = this.baselineExpr(s, now)
      let outfit = this.baselineOutfit(s, now)
      let scene = this.baselineScene(s, now)
      // DL-165: while music plays, a new feel (tempo / loudness) may not swap face, scene and outfit more often than MUSIC_DWELL_MS
      if (this.musicFeelActive(s) && this.shownBaseExpr !== null && this.shownBaseAcc !== undefined && this.shownBaseScene !== undefined) {
        const changed = expr !== this.shownBaseExpr || outfit.join(',') !== this.shownBaseAcc || scene !== this.shownBaseScene
        if (changed && now - this.feelAt < MUSIC_DWELL_MS) {
          expr = this.shownBaseExpr
          outfit = this.shownBaseAcc ? (this.shownBaseAcc.split(',') as AccessoryId[]) : []
          scene = this.shownBaseScene
        } else if (changed) this.feelAt = now
      }
      if (expr !== this.shownBaseExpr) { out.push({ type: 'expr', id: expr }); this.shownBaseExpr = expr }
      const outfitKey = outfit.join(',')
      if (outfitKey !== this.shownBaseAcc) { out.push({ type: 'accessory', id: outfit[0] ?? null, ids: outfit }); this.shownBaseAcc = outfitKey }
      if (this.gagUntil === 0 && scene !== this.shownBaseScene) { out.push({ type: 'scene', id: scene }); this.shownBaseScene = scene }
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

  private resolveReaction(ev: RobotEvent, s: RobotSignals): Reaction | null {
    const base = REACTIONS[ev][this.opts.mood]
    if (!base) return null
    if (ev === 'weather') {
      if (s.weather === 'rain') return { ...base, expr: 'cozy', seq: 'rainy-day', scene: 'weather-rain', ms: 3800 }
      if (s.weather === 'snow' || s.weather === 'cold') return { ...base, expr: 'shivering', seq: 'snowy-day', scene: 'weather-snow', accessory: 'scarf', ms: 3600 }
      if (s.weather === 'sunny') return { ...base, expr: 'relaxed', seq: 'sunny-day', scene: 'weather-sunny', accessory: 'sunglasses', ms: 3400 }
    }
    return base
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
    face.push({ type: 'scene', id: r.scene ?? null })
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

  private edges(p: RobotSignals, s: RobotSignals, lastPointerAt: number, now: number): RobotEvent[] {
    const ev: RobotEvent[] = []
    if (s.agent === 'working' && p.agent !== 'working') {
      ev.push('agentWorking')
      this.workingSince = now
      this.typingLotFired = false
      this.longFired = false
    }
    if (s.agent !== 'working') this.workingSince = null
    if (this.workingSince !== null && !this.typingLotFired && now - this.workingSince >= TYPING_LOT_MS) {
      this.typingLotFired = true
      ev.push('agentTypingLot')
    }
    if (this.workingSince !== null && !this.longFired && now - this.workingSince >= LONG_WORK_MS) {
      this.longFired = true
      ev.push('agentLong')
    }
    if (s.agent === 'permission' && p.agent !== 'permission') ev.push('agentNeeds')
    if (p.agent === 'working' && (s.agent === 'ready' || s.agent === 'idle')) ev.push('agentDone')

    // AI agent idle nodding: fires when agent transitions from ready -> idle, or sits idle for AGENT_IDLE_NOD_MS
    if (p.agent === 'ready' && s.agent === 'idle') {
      ev.push('agentIdleNod')
      this.agentIdleSince = now
      this.agentIdleNodFired = true
    } else if (s.agent === 'idle') {
      if (this.agentIdleSince === null) { this.agentIdleSince = now; this.agentIdleNodFired = false }
      else if (!this.agentIdleNodFired && now - this.agentIdleSince >= AGENT_IDLE_NOD_MS) {
        this.agentIdleNodFired = true
        ev.push('agentIdleNod')
      }
    } else {
      this.agentIdleSince = null
      this.agentIdleNodFired = false
    }

    // Boredom progression when nothing is happening and pointer is away
    const activePointer = lastPointerAt > 0 && now - lastPointerAt < 15_000
    if (s.agent === 'idle' && !s.musicPlaying && !activePointer) {
      if (this.quietSince === null) { this.quietSince = now; this.boredFired = false }
      else if (!this.boredFired && now - this.quietSince >= BORED_IDLE_MS) {
        this.boredFired = true
        ev.push('bored')
      }
    } else {
      this.quietSince = null
      this.boredFired = false
    }

    if (s.musicPlaying && !p.musicPlaying) ev.push('musicStart')
    if (!s.musicPlaying && p.musicPlaying) ev.push('musicStop')
    if (s.cpuPercent !== null && s.cpuPercent >= 95) {
      if (this.cpuSince === null) this.cpuSince = now
      if (this.cpuArmed && now - this.cpuSince >= 10_000) { this.cpuArmed = false; ev.push('cpuHigh') }
    } else {
      this.cpuSince = null
      if (!this.cpuArmed && (s.cpuPercent === null || s.cpuPercent < 65)) {
        this.cpuArmed = true
        ev.push('cpuRecovered')
      } else if (s.cpuPercent === null || s.cpuPercent < 85) {
        this.cpuArmed = true
      }
    }
    // Machine working hard (CPU 80-94% or combined CPU+RAM load)
    const hardCpu = s.cpuPercent !== null && s.cpuPercent >= 80 && s.cpuPercent < 95
    const hardCombo = (s.cpuPercent ?? 0) >= 68 && (s.memPercent ?? 0) >= 80
    if (hardCpu || hardCombo) {
      if (this.heavySince === null) this.heavySince = now
      if (this.heavyArmed && now - this.heavySince >= 8000) { this.heavyArmed = false; ev.push('heavyLoad') }
    } else {
      this.heavySince = null
      if ((s.cpuPercent ?? 0) < 65) this.heavyArmed = true
    }
    // High memory usage (RAM >= 85%)
    if (s.memPercent !== undefined && s.memPercent !== null && s.memPercent >= 85) {
      if (this.memSince === null) this.memSince = now
      if (this.memArmed && now - this.memSince >= 8000) { this.memArmed = false; ev.push('memHigh') }
    } else {
      this.memSince = null
      if (s.memPercent === undefined || s.memPercent === null || s.memPercent < 75) this.memArmed = true
    }

    if (s.batteryPercent !== null && s.batteryPercent < 20 && s.batteryCharging !== true) {
      if (this.batteryArmed) { this.batteryArmed = false; ev.push('batteryLow') }
    } else if (s.batteryCharging === true || (s.batteryPercent !== null && s.batteryPercent >= 25)) this.batteryArmed = true
    if (s.batteryCharging === true && p.batteryCharging === false) ev.push('batteryCharged')
    if (s.notificationCount > p.notificationCount) ev.push('notification')
    if (s.updateAvailable && !p.updateAvailable) ev.push('update')
    if (s.weather !== null && p.weather !== null && s.weather !== p.weather) ev.push('weather')
    return ev
  }

  private computeBaseline(s: RobotSignals, lastPointerAt: number, now: number): BaselineState {
    const nightHour = s.hour >= 23 || s.hour < 6
    if (s.agent === 'permission' && this.opts.reactTo.agent) return 'waiting'
    if (s.agent === 'working' && this.opts.reactTo.agent) return 'working'
    if (this.opts.reactTo.system && ((s.cpuPercent !== null && s.cpuPercent >= 82) || (s.memPercent !== undefined && s.memPercent !== null && s.memPercent >= 88))) {
      return 'overworked'
    }
    if (nightHour && this.opts.reactTo.ambient && !s.musicPlaying && now - lastPointerAt >= NIGHT_IDLE_MS) return 'night'
    if (s.musicPlaying && this.opts.reactTo.music) return 'music'
    return 'idle'
  }

  private baselineExpr(s: RobotSignals, _now: number): ExpressionId {
    if (this.baseline === 'overworked' && (s.memPercent ?? 0) >= 88 && (s.cpuPercent ?? 0) < 82) {
      return 'overloaded'
    }
    if (this.baseline === 'idle' && this.opts.reactTo.ambient) {
      if (s.weather === 'rain') return 'cozy'
      if (s.weather === 'snow' || s.weather === 'cold') return 'shivering'
    }
    if (this.musicFeelActive(s)) {
      const feel = MUSIC_FEEL[this.opts.mood]
      if (feel) {
        if (s.vibe === 'hype' && feel.hype) return feel.hype
        if (s.vibe === 'calm' && feel.calm) return feel.calm
        if (s.tempo && feel[s.tempo]) return feel[s.tempo]!
      }
    }
    return BASELINES[this.opts.mood][this.baseline]
  }

  private baselineScene(s: RobotSignals, _now: number): SceneId | null {
    if (this.baseline === 'overworked' && (s.memPercent ?? 0) >= 88 && (s.cpuPercent ?? 0) < 82) {
      return 'brain-overload'
    }
    if (this.baseline === 'idle' && this.opts.reactTo.ambient) {
      if (s.weather === 'rain') return 'weather-rain'
      if (s.weather === 'snow') return 'weather-snow'
      if (s.weather === 'sunny' && s.isDay) return 'weather-sunny'
    }
    if (this.baseline === 'music') {
      const byTempo = s.tempo ? TEMPO_SCENES[this.opts.mood]?.[s.tempo] : undefined
      if (byTempo) return byTempo
      const cycle = MUSIC_SCENES[this.opts.mood]
      if (cycle?.length) return cycle[Math.floor(_now / MUSIC_ROTATE_MS) % cycle.length]
    }
    return BASELINE_SCENE[this.opts.mood][this.baseline] ?? null
  }

  private musicFeelActive(s: RobotSignals): boolean {
    return this.opts.reactTo.music && s.musicPlaying && (this.baseline === 'music' || this.baseline === 'working')
  }

  /** Everything worn right now: while music plays (even while the agent works) the feel picks a combined outfit. */
  private baselineOutfit(s: RobotSignals, now: number): AccessoryId[] {
    if (this.musicFeelActive(s)) {
      const table = MUSIC_OUTFIT[this.opts.mood]
      const key = s.vibe === 'hype' ? 'hype' : s.tempo ?? 'mid'
      const set = table?.[key] ?? table?.mid
      if (set) return [...set]
      return ['headphones']
    }
    const a = this.baselineAccessory(s, now)
    return a ? [a] : []
  }

  private baselineAccessory(s: RobotSignals, now: number): AccessoryId | null {
    switch (this.baseline) {
      case 'music': return this.opts.reactTo.music ? 'headphones' : null
      case 'night': return 'nightcap'
      case 'working': return this.workingSince !== null && now - this.workingSince >= LONG_WORK_MS ? 'wizard-hat' : null
      case 'idle':
        if (!this.opts.reactTo.ambient) return null
        if (s.weather === 'sunny' && s.isDay) return 'sunglasses'
        if (s.weather === 'cold' || s.weather === 'snow') return 'scarf'
        return null
      default: return null
    }
  }
}
