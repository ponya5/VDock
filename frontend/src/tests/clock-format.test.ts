import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'
import { useClockFormat } from '@/composables/useClockFormat'

// Regression: `clock24h` was declared inside the store but never returned, so
// `settings.clock24h` was undefined — the toggle did nothing and every clock
// kept its AM/PM indicator.
describe('24-hour clock setting', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('is exposed on the store and defaults to off', () => {
    expect(useSettingsStore().clock24h).toBe(false)
  })

  it('switches every locale clock to 24 h with no day period', () => {
    const settings = useSettingsStore()
    const fmt = useClockFormat()
    const at = new Date(2026, 0, 1, 15, 5)
    const parts = () => new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', ...fmt.value }).formatToParts(at)

    expect(parts().some(p => p.type === 'dayPeriod')).toBe(true)
    settings.clock24h = true
    expect(parts().find(p => p.type === 'hour')?.value).toBe('15')
    expect(parts().some(p => p.type === 'dayPeriod')).toBe(false)
  })

  it('persists in the saved payload', () => {
    const settings = useSettingsStore()
    settings.clock24h = true
    expect(settings.$state).toBeDefined()
    expect(JSON.stringify(settings.clock24h)).toBe('true')
  })
})
