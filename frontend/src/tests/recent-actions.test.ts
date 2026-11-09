// DL-165 — pressing a button now feeds Settings -> Recent actions (it was never recorded before).
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'

describe('recent actions', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('keeps the newest first, without duplicates, and can be cleared', () => {
    const s = useSettingsStore()
    s.addRecentAction('Volume Up · cross_platform')
    s.addRecentAction('Mute · cross_platform')
    s.addRecentAction('Volume Up · cross_platform')
    expect(s.recentActions).toEqual(['Volume Up · cross_platform', 'Mute · cross_platform'])
    s.clearRecentActions()
    expect(s.recentActions).toEqual([])
  })
})
