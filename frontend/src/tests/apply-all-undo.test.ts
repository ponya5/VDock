import { test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore, previewButtonStyleChanges } from '../stores/dashboard'
import type { Button, Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

const btn = (id: string, extra: Partial<Button> = {}): Button => ({
  id, label: id, shape: 'rounded', position: { row: 0, col: 0 }, size: { rows: 1, cols: 1 }, enabled: true,
  style: { backgroundColor: '#123456' }, ...extra,
})

function setup() {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  store.setProfile({
    id: 'prof', name: 'P', description: '', theme: 'default',
    scenes: [{ id: 's', name: 'S', pages: [{ id: 'p', name: 'P', grid_config: { rows: 3, cols: 4 },
      buttons: [btn('a'), btn('b', { style: { backgroundColor: '#fff', animation: 'pulse' } })] }] }],
    dockedButtons: [btn('d')],
  } as Profile)
  return store
}
const all = (store: ReturnType<typeof setup>) => [
  ...store.currentProfile!.scenes.flatMap(s => s.pages.flatMap(p => p.buttons)),
  ...(store.currentProfile!.dockedButtons ?? []),
].filter(b => ['a', 'b', 'd'].includes(b.id))

test('review counts what would change without mutating', () => {
  const store = setup()
  const before = JSON.stringify(store.currentProfile)
  const r = previewButtonStyleChanges(store.currentProfile!, { animation: 'pulse', effect: 'none' })
  expect(r.total).toBeGreaterThanOrEqual(3)
  // setProfile seeds extra default scenes, so assert relatively: 'b' already pulses.
  expect(r.perField.animation).toBeGreaterThanOrEqual(2)
  expect(r.perField.animation).toBeLessThan(r.total)
  expect(JSON.stringify(store.currentProfile)).toBe(before)
})

test('apply then undo restores every changed key exactly', async () => {
  const store = setup()
  const before = JSON.stringify(all(store))
  expect(store.canUndoButtonStyle).toBe(false)

  expect(await store.applyGlobalButtonStyle({ animation: 'bounce', iconLoop: 'spin', effect: 'none' })).toBe(true)
  expect(JSON.stringify(all(store))).not.toBe(before)
  expect(all(store).every(b => b.style?.animation === 'bounce')).toBe(true)
  expect(store.canUndoButtonStyle).toBe(true)

  expect(await store.undoGlobalButtonStyle()).toBeGreaterThan(0)
  expect(JSON.stringify(all(store))).toBe(before)
  expect(store.canUndoButtonStyle).toBe(false)
})
