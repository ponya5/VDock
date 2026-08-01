import { test, expect } from 'vitest'
import fc from 'fast-check'

test('Feature: vdock-ui-redesign, Property 8: Icon loop phase offset is a deterministic function of grid index', () => {
  const indexArb = fc.nat({ max: 10000 })

  fc.assert(
    fc.property(indexArb, indexArb, (idx1, idx2) => {
      const getOffset = (idx: number) => (idx * 137) % 1900

      const offset1 = getOffset(idx1)
      const offset2 = getOffset(idx2)

      // Determinism: Same index must always produce the same offset
      expect(getOffset(idx1)).toBe(offset1)

      // Periodicity/Uniqueness within cycle:
      // Since 137 and 1900 are coprime, the period is exactly 1900.
      // Therefore, offsets differ if and only if indices differ modulo 1900.
      if ((idx1 - idx2) % 1900 !== 0) {
        expect(offset1).not.toBe(offset2)
      } else {
        expect(offset1).toBe(offset2)
      }
    }),
    { numRuns: 1000 }
  )
})
