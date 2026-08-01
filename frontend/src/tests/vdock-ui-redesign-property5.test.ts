import { test, expect, vi } from 'vitest'
import fc from 'fast-check'
import { setActivePinia, createPinia } from 'pinia'
import { useDashboardStore } from '../stores/dashboard'
import type { Button, ButtonLayers, ButtonShape, ButtonSize, Profile } from '@/types'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(() => Promise.resolve({ data: { success: true } })),
    delete: vi.fn()
  }
}))

test('Feature: vdock-ui-redesign, Property 5: Saving edited buttons never alters untouched buttons', async () => {
  setActivePinia(createPinia())
  const store = useDashboardStore()

  // Generate a mock button
  const buttonArb = fc.record({
    id: fc.string({ minLength: 5 }).filter(s => s.trim().length > 0),
    label: fc.string(),
    secondary_label: fc.option(fc.string()),
    icon: fc.option(fc.string()),
    icon_type: fc.option(fc.constantFrom('fontawesome', 'material', 'custom')),
    shape: fc.constantFrom('rectangle', 'rounded', 'circle') as fc.Arbitrary<ButtonShape>,
    position: fc.record({ row: fc.nat({ max: 5 }), col: fc.nat({ max: 5 }) }),
    size: fc.record({ rows: fc.constant(1), cols: fc.constant(1) }) as fc.Arbitrary<ButtonSize>,
    enabled: fc.constant(true)
  })

  // We want a list of buttons with unique positions to avoid collisions in the store helper
  const buttonsListArb = fc.array(buttonArb, { minLength: 2, maxLength: 10 }).filter(buttons => {
    // Ensure ids and positions are unique
    const ids = buttons.map(b => b.id)
    const positions = buttons.map(b => `${b.position.row},${b.position.col}`)
    return new Set(ids).size === ids.length && new Set(positions).size === positions.length
  })

  await fc.assert(
    fc.asyncProperty(buttonsListArb, async (originalButtons) => {
      // Set up a mock profile with a default scene and page
      const mockProfile: Profile = {
        id: 'test-profile',
        name: 'Test Profile',
        description: 'Test Description',
        theme: 'default',
        scenes: [{
          id: 'scene-1',
          name: 'Scene 1',
          pages: [{
            id: 'page-1',
            name: 'Page 1',
            buttons: JSON.parse(JSON.stringify(originalButtons)),
            grid_config: { rows: 6, cols: 6 }
          }]
        }]
      }

      // Initialize the store
      store.setProfile(mockProfile)

      // Choose a subset of buttons to edit (e.g. index 0)
      const editedButtonIndex = 0
      const editedButtonId = originalButtons[editedButtonIndex].id
      
      const layersUpdate: ButtonLayers = {
        fill: { type: 'solid', value: '#ff0000' },
        effect: { type: 'glow', tint: 'brand' }
      }

      const buttonBeforeUpdate = JSON.parse(JSON.stringify(originalButtons[editedButtonIndex]))
      const updatedButton: Button = {
        ...buttonBeforeUpdate,
        layers: layersUpdate
      }

      // Call updateButton to save changes
      store.updateButton(editedButtonId, updatedButton)

      // Assertions
      const page = store.currentPage
      expect(page).toBeDefined()
      if (page) {
        // 1. The edited button should gain/update its layers field
        const buttonAfter = page.buttons.find(b => b.id === editedButtonId)
        expect(buttonAfter).toBeDefined()
        expect(buttonAfter?.layers).toEqual(layersUpdate)

        // 2. Every other button outside that subset MUST remain exactly deep-equal to its pre-save value
        for (let i = 0; i < originalButtons.length; i++) {
          if (i === editedButtonIndex) continue
          
          const untouchedId = originalButtons[i].id
          const buttonUntouched = page.buttons.find(b => b.id === untouchedId)
          expect(buttonUntouched).toEqual(originalButtons[i])
        }
      }
    }),
    { numRuns: 100 }
  )
})
