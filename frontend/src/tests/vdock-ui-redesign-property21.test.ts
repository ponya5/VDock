import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

test('Feature: vdock-ui-redesign, Property 21: will-change is applied only during active transitions', () => {
  const cssMain = readFileSync(resolve(__dirname, '../assets/styles/main.css'), 'utf-8')
  const cssView = readFileSync(resolve(__dirname, '../views/DashboardView.vue'), 'utf-8')

  const verifyWillChange = (css: string, filename: string) => {
    // Regex to match CSS rules: selector { body }
    const ruleRegex = /([^{]+)\{([^}]+)\}/g
    let match

    while ((match = ruleRegex.exec(css)) !== null) {
      const selector = match[1].trim()
      const body = match[2]

      if (body.includes('will-change')) {
        // Assert that the selector indicates an active transition or state
        const isTransitionState = 
          selector.includes('-active') || 
          selector.includes(':active') || 
          selector.includes(':hover') ||
          selector.includes('transition')

        expect(isTransitionState, `will-change found in static selector "${selector}" in ${filename}! It must only be applied during active transitions.`).toBe(true)
      }
    }
  }

  verifyWillChange(cssMain, 'main.css')
  verifyWillChange(cssView, 'DashboardView.vue')
})
