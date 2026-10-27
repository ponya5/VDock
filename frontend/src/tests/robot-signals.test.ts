// DL-153 — signal adapters: agent aggregation, weather mapping, daily random mood.
import { describe, it, expect } from 'vitest'
import { aggregateAgent, mapWeather, resolveMood } from '@/services/robot/signals'

function memStorage() {
  const m = new Map<string, string>()
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v) }
}

describe('robot signals', () => {
  it('aggregates agent states by urgency', () => {
    expect(aggregateAgent([])).toBe('idle')
    expect(aggregateAgent([{ state: 'ready', prompted: false }])).toBe('idle')
    expect(aggregateAgent([{ state: 'ready', prompted: true }])).toBe('ready')
    expect(aggregateAgent([{ state: 'ready', prompted: true }, { state: 'working' }])).toBe('working')
    expect(aggregateAgent([{ state: 'working' }, { state: 'permission' }])).toBe('permission')
  })

  it('maps WMO weather codes', () => {
    expect(mapWeather(null)).toBeNull()
    expect(mapWeather({ code: 0, temperature: 22 })).toBe('sunny')
    expect(mapWeather({ code: 61, temperature: 12 })).toBe('rain')
    expect(mapWeather({ code: 73, temperature: 8 })).toBe('snow')
    expect(mapWeather({ code: 2, temperature: 3 })).toBe('cold')
    expect(mapWeather({ code: 3, temperature: 15 })).toBe('other')
  })

  it('random mood is stable for a day and re-rolls the next', () => {
    const st = memStorage()
    const a = resolveMood('random', '2026-10-27', st, () => 0.1)
    expect(resolveMood('random', '2026-10-27', st, () => 0.9)).toBe(a)
    expect(resolveMood('random', '2026-10-28', st, () => 0.9)).not.toBe(a)
    expect(resolveMood('grumpy', '2026-10-27', st)).toBe('grumpy')
  })

  it('random mood survives a throwing storage', () => {
    const bad = { getItem: () => { throw new Error('x') }, setItem: () => { throw new Error('x') } }
    expect(['funny', 'grumpy', 'sarcastic', 'sweet']).toContain(resolveMood('random', '2026-10-27', bad))
  })
})
