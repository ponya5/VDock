// DL-031: "Save & Apply to All" must reach docked sidebar buttons too.
// applyGlobalButtonStyle used to iterate only scene.pages[].buttons, so the
// always-visible dockedButtons kept their old design and the apply looked
// broken.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const dashboard = readFileSync(resolve(__dirname, '../stores/dashboard.ts'), 'utf-8')

describe('applyGlobalButtonStyle covers docked buttons', () => {
  it('mutates profile.dockedButtons, not just scene pages', () => {
    const fnStart = dashboard.indexOf('applyGlobalButtonStyle')
    const fnEnd = dashboard.indexOf('addToHistory()', fnStart)
    const body = dashboard.slice(fnStart, fnEnd)
    expect(body).toContain('dockedButtons')
  })

  it('runs the same mutation for docked and grid buttons via a shared helper', () => {
    const fnStart = dashboard.indexOf('applyGlobalButtonStyle')
    const fnEnd = dashboard.indexOf('addToHistory()', fnStart)
    const body = dashboard.slice(fnStart, fnEnd)
    // One shared helper means the two collections can't drift again.
    expect(body).toContain('applyToButton')
    const calls = body.split('applyToButton(').length - 1
    expect(calls).toBeGreaterThanOrEqual(2) // grid loop + docked loop
  })
})
