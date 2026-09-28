import { test, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '../stores/settings'
import apiClient from '@/api/client'

// DL-076 follow-up: 'all' was the factory toastLevel default until Sep 2026,
// and the whole settings payload is rewritten on every save — so every blob
// persisted since carries 'all', whether the user ever opened the
// Notifications section or not. An unmarked 'all' is therefore migrated to
// 'errors-only' once; a `toastLevelMigrated` marker keeps a deliberate
// post-migration "All" pick from being flipped.

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn()
  }
}))

function serverReturns(settings: Record<string, unknown>) {
  vi.mocked(apiClient.get).mockResolvedValue({ data: { success: true, settings } } as any)
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

test('localStorage blob with inherited "all" migrates to errors-only', () => {
  localStorage.setItem('vdock_settings', JSON.stringify({ toastLevel: 'all' }))
  const store = useSettingsStore() // loadSettings() runs inside store setup
  expect(store.toastLevel).toBe('errors-only')
  expect(store.toastLevelMigrated).toBe(true)
})

test('migration persists the marker back to localStorage', async () => {
  localStorage.setItem('vdock_settings', JSON.stringify({ toastLevel: 'all' }))
  useSettingsStore()
  // The settings watcher persists on the next microtask after the flip.
  await new Promise(r => setTimeout(r, 0))
  const stored = JSON.parse(localStorage.getItem('vdock_settings') ?? '{}')
  expect(stored.toastLevel).toBe('errors-only')
  expect(stored.toastLevelMigrated).toBe(true)
})

test('server payload with unmarked "all" migrates on load', async () => {
  const store = useSettingsStore()
  serverReturns({ toastLevel: 'all' })
  await store.loadSettingsFromServer()
  expect(store.toastLevel).toBe('errors-only')
  expect(store.toastLevelMigrated).toBe(true)
})

test('server payload "all" with marker is a deliberate pick — respected', async () => {
  const store = useSettingsStore()
  serverReturns({ toastLevel: 'all', toastLevelMigrated: true })
  await store.loadSettingsFromServer()
  expect(store.toastLevel).toBe('all')
})

test('blob missing the key entirely falls back to errors-only', () => {
  localStorage.setItem('vdock_settings', JSON.stringify({ buttonSize: 1.2 }))
  const store = useSettingsStore()
  expect(store.toastLevel).toBe('errors-only')
})

test('"off" passes through untouched', async () => {
  const store = useSettingsStore()
  serverReturns({ toastLevel: 'off' })
  await store.loadSettingsFromServer()
  expect(store.toastLevel).toBe('off')
})
