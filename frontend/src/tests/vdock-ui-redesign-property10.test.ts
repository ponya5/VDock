import { test, expect } from 'vitest'
import fc from 'fast-check'
import { computeStaggerOrder } from '../utils/stagger'
import type { StaggerOrder } from '../utils/stagger'

test('Feature: vdock-ui-redesign, Property 10: Grid transition stagger order is always a permutation of grid cells', () => {
  const rowsArb = fc.integer({ min: 1, max: 20 })
  const colsArb = fc.integer({ min: 1, max: 20 })
  const orderArb = fc.constantFrom('by-column', 'by-row', 'diagonal', 'random', 'none') as fc.Arbitrary<StaggerOrder>

  fc.assert(
    fc.property(rowsArb, colsArb, orderArb, (rows, cols, order) => {
      const staggerOrder = computeStaggerOrder(rows, cols, order)

      // Expected size is exactly R * C
      expect(staggerOrder.length).toBe(rows * cols)

      // It must contain every index from 0 to R*C - 1 exactly once
      const sorted = [...staggerOrder].sort((a, b) => a - b)
      const expected = Array.from({ length: rows * cols }, (_, i) => i)
      expect(sorted).toEqual(expected)
    }),
    { numRuns: 100 }
  )
})
