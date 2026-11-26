import { test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '../stores/dashboard'
import apiClient from '@/api/client'
import { ensurePortrait, projectPortrait } from '@/utils/portraitLayout'
import { layoutPortraitPage } from '@/utils/gridReflow'
import type { Button, Page, Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

const btn = (id: string, row: number, col: number, extra: Partial<Button> = {}): Button =>
  ({ id, label: id, shape: 'rounded', enabled: true, position: { row, col }, size: { rows: 1, cols: 1 }, ...extra }) as Button
const mkPage = (): Page => ({
  id: 'pg', name: 'P', grid_config: { rows: 3, cols: 6 },
  buttons: [btn('a', 0, 0), btn('b', 0, 1), btn('c', 0, 2), btn('d', 1, 0)],
})

function setup() {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  store.setProfile({
    id: 'prof', name: 'P', description: '', theme: 'default',
    scenes: [{ id: 's', name: 'S', pages: [mkPage()] }],
  } as unknown as Profile)
  const page = () => store.currentProfile!.scenes.find(s => s.id === 's')!.pages[0]
  store.setScene(store.currentProfile!.scenes.findIndex(s => s.id === 's'))
  return { store, page }
}

test('seed folds landscape into fewer columns, reading order, nothing overlaps', () => {
  const p = mkPage()
  ensurePortrait(p)
  expect(p.portrait_grid).toEqual({ rows: 2, cols: 3 })
  expect(p.buttons.map(b => b.portrait!.position)).toEqual([
    { row: 0, col: 0 }, { row: 0, col: 1 }, { row: 0, col: 2 }, { row: 1, col: 0 },
  ])
})

test('a button added later is placed in the first free portrait cell', () => {
  const p = mkPage()
  ensurePortrait(p)
  p.buttons.push(btn('e', 2, 5))
  ensurePortrait(p)
  expect(p.buttons[4].portrait!.position).toEqual({ row: 1, col: 1 })
})

test('projectPortrait leaves pages without a portrait layout untouched', () => {
  const p = mkPage()
  expect(projectPortrait(p)).toBe(p)
  ensurePortrait(p)
  const view = projectPortrait(p)
  expect(view.grid_config).toEqual({ rows: 2, cols: 3 })
  expect(view.buttons[3].position).toEqual({ row: 1, col: 0 })
  expect(p.grid_config).toEqual({ rows: 3, cols: 6 })
})

test('layoutPortraitPage scrolls when rows would be below the minimum cell', () => {
  const p = projectPortrait({ ...mkPage(), portrait_grid: { rows: 8, cols: 2 } })
  expect(layoutPortraitPage(p, { width: 300, height: 400, minCell: 72, enabled: true }).scroll).toBe('y')
  expect(layoutPortraitPage(p, { width: 300, height: 900, minCell: 72, enabled: true }).scroll).toBe('none')
})

test('portrait edit: move saves a canonical profile; landscape is untouched', async () => {
  const { store, page } = setup()
  store.setEditOrientation('portrait')
  expect(page().grid_config).toEqual({ rows: 2, cols: 3 })
  store.moveButton('d', { row: 1, col: 2 })
  await Promise.resolve()
  const sent = (apiClient.put as any).mock.calls.at(-1)[1] as Profile
  const sentPage = sent.scenes.find(s => s.id === 's')!.pages[0]
  expect(sentPage.grid_config).toEqual({ rows: 3, cols: 6 })
  expect(sentPage.portrait_grid).toEqual({ rows: 2, cols: 3 })
  const d = sentPage.buttons.find(b => b.id === 'd')!
  expect(d.position).toEqual({ row: 1, col: 0 })
  expect(d.portrait!.position).toEqual({ row: 1, col: 2 })
})

test('peeking at portrait without saving leaves no portrait data behind', () => {
  const { store, page } = setup()
  store.setEditOrientation('portrait')
  store.setEditOrientation('landscape')
  expect(page().portrait_grid).toBeUndefined()
  expect(page().buttons.every(b => b.portrait === undefined)).toBe(true)
  expect(page().grid_config).toEqual({ rows: 3, cols: 6 })
})

test('button added in portrait view gets a landscape placement on the way back', () => {
  const { store, page } = setup()
  store.setEditOrientation('portrait')
  store.addButton(btn('n', 1, 1))
  store.setEditOrientation('landscape')
  const n = page().buttons.find(b => b.id === 'n')!
  expect(n.portrait!.position).toEqual({ row: 1, col: 1 })
  expect(n.position).toEqual({ row: 0, col: 3 })
})

test('leaving edit mode returns to landscape', () => {
  const { store, page } = setup()
  store.isEditMode = true
  store.setEditOrientation('portrait')
  store.toggleEditMode()
  expect(store.editOrientation).toBe('landscape')
  expect(page().grid_config).toEqual({ rows: 3, cols: 6 })
})

test('an empty page seeds portrait with the landscape capacity', () => {
  const p: Page = { id: 'e', name: 'E', buttons: [], grid_config: { rows: 3, cols: 5 } }
  ensurePortrait(p)
  expect(p.portrait_grid).toEqual({ rows: 5, cols: 3 })
})
