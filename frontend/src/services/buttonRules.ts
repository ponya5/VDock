/**
 * Conditional-style rule evaluator (DL-122) — pure, no imports beyond
 * types, so it's trivially testable and cheap to run per button per
 * render.
 *
 * A rule is `{ when: { source, op, value? }, then: { tone?, icon?,
 * sublabel?, dim? } }`. The FIRST matching rule wins — ordering is the
 * priority mechanism, same as stream-deck dynamic states.
 *
 * Sources:
 *   volume.muted            bool   — system mute state
 *   volume.level            0-100  — system output level
 *   now_playing.playing     bool   — SMTC play state
 *   now_playing.source_app  string — e.g. 'spotify.exe'
 *   now_playing.title       string — current track title
 *   agent.<src>.state       string — e.g. agent.claude.state → 'permission'
 *   spectrum.live           bool   — audio spectrum is live
 *   spectrum.level          0-100  — current loudness
 *   timer.running           bool   — THIS button's timer is running
 *   time.hour               0-23   — local hour
 *   time.minute             0-59   — local minute
 *
 * Ops: eq | neq | lt | lte | gt | gte | truthy (value ignored).
 */
import type { ButtonRule } from '@/types'

export type RulePatch = ButtonRule['then']

export interface RuleState {
  volume?: { value?: number | null; muted?: boolean; seen?: boolean }
  nowPlaying?: {
    playing?: boolean
    title?: string
    artist?: string
    source_app?: string
    seen?: boolean
  }
  agent?: { states?: Record<string, { state?: string } & Record<string, any>> }
  spectrum?: { level?: number; live?: boolean; seen?: boolean }
  time?: { hour?: number; minute?: number }
  /** Composed per-button by the caller: is THIS button's timer running. */
  timer?: { running?: boolean }
}

const AGENT_STATE_RE = /^agent\.([^.]+)\.state$/

function resolveSource(state: RuleState, source: string): unknown {
  switch (source) {
    case 'volume.muted': return state.volume?.muted === true
    case 'volume.level': return state.volume?.value ?? null
    case 'now_playing.playing': return state.nowPlaying?.playing === true
    case 'now_playing.source_app': return state.nowPlaying?.source_app ?? ''
    case 'now_playing.title': return state.nowPlaying?.title ?? ''
    case 'spectrum.live': return state.spectrum?.live === true
    case 'spectrum.level': return state.spectrum?.level ?? 0
    case 'timer.running': return state.timer?.running === true
    case 'time.hour': return state.time?.hour ?? null
    case 'time.minute': return state.time?.minute ?? null
  }
  const agentMatch = AGENT_STATE_RE.exec(source)
  if (agentMatch) {
    return state.agent?.states?.[agentMatch[1]]?.state ?? 'unknown'
  }
  return undefined
}

function asNumber(v: unknown): number | null {
  if (typeof v === 'number' && Number.isFinite(v)) return v
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v)
    return Number.isFinite(n) ? n : null
  }
  return null
}

/** Loose value parsing for the editor's text input: 'true'/'false'/
 *  numerals become their real types so `eq true` matches a boolean. */
function coerceExpected(value: unknown): unknown {
  if (typeof value !== 'string') return value
  const v = value.trim()
  if (v === 'true') return true
  if (v === 'false') return false
  const n = Number(v)
  if (v !== '' && Number.isFinite(n)) return n
  return value
}

function matches(actual: unknown, op: string, rawValue: unknown): boolean {
  if (op === 'truthy') return !!actual

  const expected = coerceExpected(rawValue)
  if (op === 'eq' || op === 'neq') {
    const aNum = asNumber(actual)
    const eNum = asNumber(expected)
    // Numeric compare when both sides parse; otherwise strict equality on
    // loosely-normalised strings.
    const equal = aNum !== null && eNum !== null
      ? aNum === eNum
      : String(actual ?? '') === String(expected ?? '')
    return op === 'eq' ? equal : !equal
  }

  const a = asNumber(actual)
  const e = asNumber(expected)
  if (a === null || e === null) return false
  switch (op) {
    case 'lt': return a < e
    case 'lte': return a <= e
    case 'gt': return a > e
    case 'gte': return a >= e
    default: return false
  }
}

/**
 * First matching rule wins. `null` when there is nothing to apply — the
 * caller treats that as "render the stock face" (zero-cost path).
 */
export function evaluateRules(
  rules: ButtonRule[] | undefined | null,
  state: RuleState
): RulePatch | null {
  if (!rules?.length) return null
  for (const rule of rules) {
    const when = rule?.when
    const then = rule?.then
    if (!when?.source || !when.op || !then) continue
    if (matches(resolveSource(state, when.source), when.op, when.value)) {
      const patch: RulePatch = {}
      if (then.tone) patch.tone = then.tone
      if (Array.isArray(then.icon) && then.icon[0] && then.icon[1]) {
        patch.icon = [then.icon[0], then.icon[1]]
      }
      if (typeof then.sublabel === 'string' && then.sublabel) {
        patch.sublabel = then.sublabel
      }
      if (then.dim) patch.dim = true
      return Object.keys(patch).length ? patch : null
    }
  }
  return null
}

export default evaluateRules
