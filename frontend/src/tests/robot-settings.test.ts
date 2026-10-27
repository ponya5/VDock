// DL-153 — robot screensaver type + its four settings.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { SAVER_TYPES, SHUFFLE_POOL, saverTypeLabel } from '@/services/screensaverTypes'
import { useSettingsStore, SETTINGS_DEFAULTS, sanitizeRobotReactTo } from '@/stores/settings'
import type { AxiosResponse } from 'axios'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

// The store applies a loaded payload via loadSettingsFromServer (same feed as
// settings-malformed-payload.test.ts).
async function applySettings(s: ReturnType<typeof useSettingsStore>, settings: any) {
  vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { settings } } as unknown as AxiosResponse)
  await s.loadSettingsFromServer()
}

describe('robot saver type', () => {
  it('is registered before shuffle and joins the shuffle pool', () => {
    expect(SAVER_TYPES.map(t => t.id)).toEqual(['widgets', 'spectrum', 'stats', 'robot', 'shuffle'])
    expect(SHUFFLE_POOL).toContain('robot')
    expect(saverTypeLabel('robot')).toBe('Robot buddy')
  })
})

describe('robot settings', () => {
  it('has the spec defaults', () => {
    expect(SETTINGS_DEFAULTS.robotMood).toBe('funny')
    expect(SETTINGS_DEFAULTS.robotFaceSide).toBe('left')
    expect(SETTINGS_DEFAULTS.robotQuips).toBe(true)
    expect(SETTINGS_DEFAULTS.robotReactTo).toEqual({ agent: true, music: true, system: true, ambient: true })
    const s = useSettingsStore()
    expect(s.robotMood).toBe('funny')
    expect(s.robotFaceSide).toBe('left')
    expect(s.robotQuips).toBe(true)
    expect(s.robotReactTo).toEqual({ agent: true, music: true, system: true, ambient: true })
  })

  it('accepts robot as a screensaverStyle and valid robot values from a payload', async () => {
    const s = useSettingsStore()
    await applySettings(s, {
      screensaverStyle: 'robot',
      robotMood: 'sarcastic',
      robotFaceSide: 'right',
      robotQuips: false,
      robotReactTo: { agent: true, music: false, system: true, ambient: false },
    })
    expect(s.screensaverStyle).toBe('robot')
    expect(s.robotMood).toBe('sarcastic')
    expect(s.robotFaceSide).toBe('right')
    expect(s.robotQuips).toBe(false)
    expect(s.robotReactTo).toEqual({ agent: true, music: false, system: true, ambient: false })
  })

  it('ignores malformed robot values', async () => {
    const s = useSettingsStore()
    await applySettings(s, { robotMood: 'evil', robotFaceSide: 'up', robotQuips: 'yes', robotReactTo: 7 })
    expect(s.robotMood).toBe('funny')
    expect(s.robotFaceSide).toBe('left')
    expect(s.robotQuips).toBe(true)
    expect(s.robotReactTo).toEqual({ agent: true, music: true, system: true, ambient: true })
  })

  it('sanitizeRobotReactTo fills missing/invalid groups with true', () => {
    expect(sanitizeRobotReactTo({ music: false, agent: 'x' })).toEqual({ agent: true, music: false, system: true, ambient: true })
    expect(sanitizeRobotReactTo(null)).toEqual({ agent: true, music: true, system: true, ambient: true })
  })
})
