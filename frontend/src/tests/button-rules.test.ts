// Feature: DL-122 — the conditional-style rule evaluator. Pure function,
// first match wins; this pins the operator matrix and the patch shape.
import { describe, it, expect } from 'vitest'
import { evaluateRules, type RuleState } from '@/services/buttonRules'
import type { ButtonRule } from '@/types'

const state: RuleState = {
  volume: { value: 42, muted: true, seen: true },
  nowPlaying: {
    playing: true, title: 'Song', artist: 'Artist',
    source_app: 'spotify.exe', seen: true,
  },
  agent: { states: { claude: { state: 'permission' } } },
  spectrum: { level: 55, live: true, seen: true },
  time: { hour: 19, minute: 30 },
  timer: { running: true },
}

function rule(
  source: string, op: ButtonRule['when']['op'], value: unknown,
  then: ButtonRule['then'] = { tone: 'critical' }
): ButtonRule {
  return { when: { source, op, value }, then }
}

describe('evaluateRules', () => {
  it('returns null when there are no rules', () => {
    expect(evaluateRules(undefined, state)).toBeNull()
    expect(evaluateRules([], state)).toBeNull()
  })

  it('returns null when nothing matches', () => {
    expect(evaluateRules([rule('volume.muted', 'eq', false)], state)).toBeNull()
  })

  it('matches a boolean source with eq', () => {
    const patch = evaluateRules(
      [rule('volume.muted', 'eq', true, { tone: 'critical', sublabel: 'Muted' })],
      state
    )
    expect(patch).toEqual({ tone: 'critical', sublabel: 'Muted' })
  })

  it('coerces the string "true" from the editor text input', () => {
    const patch = evaluateRules([rule('volume.muted', 'eq', 'true')], state)
    expect(patch?.tone).toBe('critical')
  })

  it('supports numeric comparisons with string values', () => {
    expect(evaluateRules([rule('volume.level', 'lt', '50')], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('volume.level', 'gt', '50')], state)).toBeNull()
    expect(evaluateRules([rule('volume.level', 'gte', '42')], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('volume.level', 'lte', '41')], state)).toBeNull()
  })

  it('neq is the inverse of eq', () => {
    expect(evaluateRules([rule('now_playing.source_app', 'neq', 'spotify.exe')], state)).toBeNull()
    expect(evaluateRules([rule('now_playing.source_app', 'neq', 'chrome.exe')], state)?.tone).toBe('critical')
  })

  it('truthy ignores the value field', () => {
    expect(evaluateRules([rule('now_playing.playing', 'truthy', undefined)], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('spectrum.live', 'truthy', 'false')], state)?.tone).toBe('critical')
  })

  it('resolves agent.<src>.state sources', () => {
    expect(evaluateRules([rule('agent.claude.state', 'eq', 'permission')], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('agent.cursor.state', 'eq', 'permission')], state)).toBeNull()
  })

  it('reads the per-button timer.running source', () => {
    expect(evaluateRules([rule('timer.running', 'truthy', undefined)], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('timer.running', 'truthy', undefined)], { ...state, timer: { running: false } })).toBeNull()
  })

  it('reads the local clock sources', () => {
    expect(evaluateRules([rule('time.hour', 'gte', '18')], state)?.tone).toBe('critical')
    expect(evaluateRules([rule('time.hour', 'lt', '18')], state)).toBeNull()
    expect(evaluateRules([rule('time.minute', 'eq', '30')], state)?.tone).toBe('critical')
  })

  it('first matching rule wins', () => {
    const rules: ButtonRule[] = [
      rule('volume.muted', 'eq', true, { tone: 'warning' }),
      rule('volume.muted', 'eq', true, { tone: 'critical' }),
    ]
    expect(evaluateRules(rules, state)?.tone).toBe('warning')
  })

  it('skips non-matching rules and applies the first hit', () => {
    const rules: ButtonRule[] = [
      rule('volume.muted', 'eq', false, { tone: 'success' }),
      rule('volume.level', 'gt', '10', { dim: true }),
    ]
    expect(evaluateRules(rules, state)).toEqual({ dim: true })
  })

  it('passes through a valid [prefix, name] icon override', () => {
    const patch = evaluateRules(
      [rule('volume.muted', 'eq', true, { icon: ['fas', 'volume-mute'] })],
      state
    )
    expect(patch?.icon).toEqual(['fas', 'volume-mute'])
  })

  it('drops malformed patches — a match with empty then is no patch', () => {
    expect(evaluateRules([rule('volume.muted', 'eq', true, {})], state)).toBeNull()
    expect(evaluateRules(
      [rule('volume.muted', 'eq', true, { icon: ['fas'] as any })],
      state
    )).toBeNull()
  })

  it('tolerates missing rule fields and unknown sources', () => {
    const weird = [
      { when: { source: '', op: 'eq' }, then: { tone: 'critical' } },
      { when: { source: 'bogus.source', op: 'eq', value: 'x' }, then: { tone: 'critical' } },
      { then: { tone: 'critical' } },
    ] as unknown as ButtonRule[]
    expect(evaluateRules(weird, state)).toBeNull()
  })

  it('handles absent state slices without throwing', () => {
    const empty: RuleState = {}
    expect(evaluateRules([rule('volume.muted', 'eq', true)], empty)).toBeNull()
    expect(evaluateRules([rule('volume.muted', 'eq', false)], empty)?.tone).toBe('critical')
    expect(evaluateRules([rule('agent.claude.state', 'eq', 'unknown')], empty)?.tone).toBe('critical')
  })
})
