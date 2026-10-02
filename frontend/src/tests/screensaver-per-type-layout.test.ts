// DL-142: each screensaver type keeps its own widget arrangement — editing
// the Spectrum overlay must never rewrite the Widget dashboard layout.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'
import apiClient from '@/api/client'
import { defaultScreensaverLayout } from '@/utils/screensaverLayout'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

function moved(x: number) {
  const l = defaultScreensaverLayout()
  l.clock = { x, y: 20, scale: 1.4 }
  return l
}

describe('per-type screensaver layouts', () => {
  it('starts with no spectrum layout (falls back to the widget one)', () => {
    expect(useSettingsStore().screensaverSpectrumLayout).toBeNull()
  })

  it('saving the spectrum layout leaves the widget layout untouched', () => {
    const store = useSettingsStore()
    const before = JSON.stringify(store.screensaverLayout)
    store.setScreensaverLayout('spectrum', moved(77))
    expect(store.screensaverSpectrumLayout?.clock.x).toBe(77)
    expect(JSON.stringify(store.screensaverLayout)).toBe(before)
  })

  it('saving the widget layout leaves the spectrum layout untouched', () => {
    const store = useSettingsStore()
    store.setScreensaverLayout('spectrum', moved(77))
    store.setScreensaverLayout('widgets', moved(11))
    expect(store.screensaverLayout.clock.x).toBe(11)
    expect(store.screensaverSpectrumLayout?.clock.x).toBe(77)
  })

  it('persists to the local payload and applies from the server', async () => {
    const a = useSettingsStore()
    a.setScreensaverLayout('spectrum', moved(64))
    a.saveSettingsLocalOnly()
    const payload = JSON.parse(localStorage.getItem('vdock_settings') ?? '{}')
    expect(payload.screensaverSpectrumLayout?.clock.x).toBe(64)

    setActivePinia(createPinia())
    const b = useSettingsStore()
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { settings: { screensaverSpectrumLayout: moved(64) } },
    })
    await b.loadSettingsFromServer()
    expect(b.screensaverSpectrumLayout?.clock.x).toBe(64)
  })

  it.each([['null', null], ['a string', 'junk']])(
    'treats %s from the server as "not customised"',
    async (_l, bad) => {
      const store = useSettingsStore()
      store.setScreensaverLayout('spectrum', moved(64))
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: { settings: { screensaverSpectrumLayout: bad } },
      })
      await store.loadSettingsFromServer()
      expect(store.screensaverSpectrumLayout).toBeNull()
    },
  )
})

describe('per-type layout wiring', () => {
  const read = (p: string) => readFileSync(resolve(__dirname, p), 'utf-8')

  it('ScreenSaver reads and saves by layout target', () => {
    const src = read('../components/ScreenSaver.vue')
    expect(src).toContain('settingsStore.screensaverSpectrumLayout ?? settingsStore.screensaverLayout')
    expect(src).toContain("emit('save-layout', JSON.parse(JSON.stringify(editLayout.value)), layoutTarget.value)")
  })

  it('is allowlisted for server persistence', () => {
    expect(read('../../../backend/routes/user_settings.py')).toContain("'screensaverSpectrumLayout'")
  })
})
