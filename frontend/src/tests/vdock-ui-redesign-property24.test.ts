import { test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import fc from 'fast-check'
import DeckButton from '../components/DeckButton.vue'
import type { Button, ButtonShape, ButtonSize } from '@/types'

test('Feature: vdock-ui-redesign, Property 24: Legacy profiles load and render without error', () => {
  setActivePinia(createPinia())

  // Generate an arbitrary legacy Button record (no layers field)
  const legacyButtonArb = fc.record({
    id: fc.string({ minLength: 5 }).filter(s => s.trim().length > 0),
    label: fc.string(),
    secondary_label: fc.option(fc.string()),
    icon: fc.option(fc.string()),
    icon_type: fc.option(fc.constantFrom('fontawesome', 'material', 'custom')),
    media_url: fc.option(fc.string()),
    media_type: fc.option(fc.constantFrom('video', 'gif', 'image')),
    shape: fc.constantFrom('rectangle', 'rounded', 'circle') as fc.Arbitrary<ButtonShape>,
    position: fc.record({ row: fc.nat({ max: 5 }), col: fc.nat({ max: 5 }) }),
    size: fc.record({ rows: fc.constant(1), cols: fc.constant(1) }) as fc.Arbitrary<ButtonSize>,
    enabled: fc.boolean()
  })

  fc.assert(
    fc.property(legacyButtonArb, (button) => {
      // Assert button has no layers field
      expect((button as any).layers).toBeUndefined()

      // Mounting the DeckButton component with only legacy fields should NOT throw
      const wrapper = mount(DeckButton, {
        props: {
          button: button as Button,
          isEditMode: false
        },
        global: {
          stubs: {
            FontAwesomeIcon: true,
            PerformanceMonitorButton: true,
            TimeOptionsButton: true,
            WeatherQueryButton: true,
            CalendarButton: true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
    }),
    { numRuns: 100 }
  )
})
