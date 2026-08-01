import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

test('Feature: vdock-ui-redesign, Property 20: New animations touch only transform and opacity', () => {
  const css = readFileSync(
    resolve(__dirname, '../assets/styles/main.css'),
    'utf-8'
  )

  // Find the start of Phase 4 Animations section
  const sectionStart = css.indexOf('/* ── Phase 4 Animations ── */')
  expect(sectionStart).toBeGreaterThan(-1)
  const phase4Css = css.slice(sectionStart)

  // Find all @keyframes in the Phase 4 section
  const keyframeRegex = /@keyframes\s+([a-zA-Z0-9_-]+)\s*\{([\s\S]*?)\}/g
  let match
  const allowedProperties = ['transform', 'opacity']

  const keyframesFound: string[] = []

  while ((match = keyframeRegex.exec(phase4Css)) !== null) {
    const name = match[1]
    const body = match[2]
    keyframesFound.push(name)

    // Extract all CSS property names using a clean regex
    const propMatches = body.matchAll(/([a-zA-Z0-9-]+)\s*:/g)
    for (const propMatch of propMatches) {
      const prop = propMatch[1]
      const isAllowed = allowedProperties.includes(prop) || prop.startsWith('--')
      expect(isAllowed, `Property "${prop}" in @keyframes "${name}" is not allowed! Only transform and opacity are permitted.`).toBe(true)
    }
  }

  expect(keyframesFound.length).toBeGreaterThan(0)
})
