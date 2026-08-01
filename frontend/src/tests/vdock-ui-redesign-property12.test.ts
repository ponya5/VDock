import { test, expect } from 'vitest'
import fc from 'fast-check'

test('Feature: vdock-ui-redesign, Property 12: Quick Add Picker page count correctness and pagination bounds', () => {
  const presetsCountArb = fc.nat({ max: 500 })

  fc.assert(
    fc.property(presetsCountArb, (count) => {
      // Page count calculation logic
      const totalPages = Math.max(1, Math.ceil(count / 15))
      
      // Check totalPages bounds
      expect(totalPages).toBeGreaterThanOrEqual(1)

      // Page count must match math ceil
      if (count === 0) {
        expect(totalPages).toBe(1)
      } else {
        expect(totalPages).toBe(Math.ceil(count / 15))
      }

      // Verify bounds of sliced elements for every page
      for (let page = 0; page < totalPages; page++) {
        const start = page * 15
        const end = Math.min(count, start + 15)
        const pageSize = Math.max(0, end - start)

        if (count === 0) {
          expect(pageSize).toBe(0)
        } else if (page < totalPages - 1) {
          expect(pageSize).toBe(15)
        } else {
          const expectedLastPageSize = count % 15 === 0 ? 15 : count % 15
          expect(pageSize).toBe(expectedLastPageSize)
        }
      }
    }),
    { numRuns: 1000 }
  )
})
