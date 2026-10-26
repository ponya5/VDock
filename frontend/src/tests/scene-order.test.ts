import { test, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '../stores/dashboard'
import type { Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn(),
  },
}))

const page = { id: 'p', name: 'Page 1', buttons: [], grid_config: { rows: 4, cols: 5 } }
const scene = (id: string) => ({ id, name: id, pages: [{ ...page }] })

function setup() {
  setActivePinia(createPinia())
  const store = useDashboardStore()
  store.setProfile({
    id: 'prof', name: 'P', description: '', theme: 'default',
    scenes: [scene('a'), scene('b'), scene('c')],
  } as Profile)
  const ids = () => store.currentProfile!.scenes.map(s => s.id).filter(id => ['a', 'b', 'c'].includes(id))
  return { store, ids }
}

test('moveScene reorders and keeps the viewed scene selected', () => {
  const { store, ids } = setup()
  store.setScene(store.currentProfile!.scenes.findIndex(s => s.id === 'b'))

  store.moveScene('b', -1)
  expect(ids()).toEqual(['b', 'a', 'c'])
  expect(store.currentProfile!.scenes[store.currentSceneIndex].id).toBe('b')

  store.moveScene('a', 1)
  expect(ids()).toEqual(['b', 'c', 'a'])
  expect(store.currentProfile!.scenes[store.currentSceneIndex].id).toBe('b')
})

test('moveScene is a no-op at the ends', () => {
  const { store, ids } = setup()
  store.moveScene('a', -1)
  expect(ids()).toEqual(['a', 'b', 'c'])
})

test('mobile rail collapses inactive scene names when there are more than 3 (DL-027)', () => {
  const src = readFileSync(resolve(__dirname, '../components/MobileDeckChrome.vue'), 'utf-8')
  expect(src).toContain('props.scenes.length > 3')
  expect(src).toContain('!compactRail || i === currentSceneIndex')
})
