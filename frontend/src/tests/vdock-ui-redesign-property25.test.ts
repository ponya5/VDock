import { test, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import fc from 'fast-check'
import { useDashboardStore } from '../stores/dashboard'
import apiClient from '@/api/client'
import type { Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: { profiles: [] } })),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn()
  }
}))

test('Feature: vdock-ui-redesign, Property 25: Loading a profile never triggers a write', async () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()

  // Generate a mock profile structure
  const profileArb = fc.record({
    id: fc.string({ minLength: 5 }),
    name: fc.string(),
    description: fc.string(),
    theme: fc.string(),
    scenes: fc.array(fc.record({
      id: fc.string(),
      name: fc.string(),
      pages: fc.array(fc.record({
        id: fc.string(),
        name: fc.string(),
        buttons: fc.constant([]),
        grid_config: fc.record({ rows: fc.constant(4), cols: fc.constant(5) })
      }))
    }))
  })

  await fc.assert(
    fc.asyncProperty(profileArb, async (profile) => {
      const putSpy = vi.spyOn(apiClient, 'put')
      putSpy.mockClear()

      // Load/set the profile
      store.setProfile(profile as Profile)

      // Verify that no write (PUT request) was made
      expect(putSpy).toHaveBeenCalledTimes(0)
      
      putSpy.mockRestore()
    }),
    { numRuns: 100 }
  )
})
