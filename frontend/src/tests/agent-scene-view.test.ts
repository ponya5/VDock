// DL-166: the Groups / All choice and the selected category are remembered per scene, per device.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref } from 'vue'
import { resetAgentSceneViews, selectedCategoryId, useAgentSceneView } from '@/composables/useAgentSceneView'

beforeEach(() => resetAgentSceneViews())
afterEach(() => vi.restoreAllMocks())

describe('useAgentSceneView', () => {
  it('defaults to groups with no remembered category', () => {
    const v = useAgentSceneView(ref('a'))
    expect(v.mode.value).toBe('groups')
    expect(v.category.value).toBeUndefined()
  })

  it('stores mode and category per scene id', () => {
    const a = useAgentSceneView(ref('a'))
    const b = useAgentSceneView(ref('b'))
    a.setMode('all')
    a.setCategory('review')
    expect(a.mode.value).toBe('all')
    expect(a.category.value).toBe('review')
    expect(b.mode.value).toBe('groups')
    expect(b.category.value).toBeUndefined()
    const raw = JSON.parse(window.localStorage.getItem('vdock.agentSceneView')!)
    expect(raw.a).toEqual({ mode: 'all', category: 'review' })
  })

  it('keeps working in memory when localStorage throws', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('private mode') })
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('private mode') })
    const v = useAgentSceneView(ref('mem'))
    expect(() => v.setMode('all')).not.toThrow()
    expect(v.mode.value).toBe('all')
  })

  it('does nothing without a scene id', () => {
    const v = useAgentSceneView(ref(null))
    v.setMode('all')
    expect(v.mode.value).toBe('groups')
  })
})

describe('selectedCategoryId', () => {
  const groups = [{ id: 'session' as const }, { id: 'review' as const }]
  it('uses the remembered category while it still has buttons', () => {
    expect(selectedCategoryId('review', groups)).toBe('review')
  })
  it('falls back to the first group when it is stale or missing', () => {
    expect(selectedCategoryId('context', groups)).toBe('session')
    expect(selectedCategoryId(undefined, groups)).toBe('session')
  })
  it('is null with no groups', () => {
    expect(selectedCategoryId('session', [])).toBeNull()
  })
})
