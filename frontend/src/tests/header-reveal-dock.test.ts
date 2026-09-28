import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// DL-014 follow-up (2026-09-28): the "Show Header" reveal pill must live
// inside the footer chrome as an in-flow flex item. As a `position: fixed`
// overlay it covered the footer's left end (where page dots render when a
// scene has multiple pages — a touch blocker) and grazed the bottom edge of
// whatever tile occupied the grid's bottom-left cell.

const componentsDir = resolve(__dirname, '../components')

function readComponent(file: string) {
  return readFileSync(resolve(componentsDir, file), 'utf-8')
}

function styleBlock(content: string, file: string) {
  const styleMatch = content.match(/<style[^>]*>([\s\S]*?)<\/style>/)
  expect(styleMatch, `${file} should contain a style block`).not.toBeNull()
  return styleMatch![1]
}

test('reveal trigger is not rendered by DeckHeader anymore', () => {
  const header = readComponent('DeckHeader.vue')
  expect(
    header.includes('header-reveal-trigger'),
    'DeckHeader must not own the reveal trigger — it was a position:fixed overlay that overlapped footer content and grid tiles'
  ).toBe(false)
})

test('reveal trigger is docked in DeckFooter and never position:fixed', () => {
  const footer = readComponent('DeckFooter.vue')
  expect(
    footer.includes('header-reveal-trigger'),
    'DeckFooter should render the reveal trigger in-flow (inside the footer chrome)'
  ).toBe(true)

  const styles = styleBlock(footer, 'DeckFooter.vue')
  const ruleRegex = /\.header-reveal-trigger\s*(?:,[^{]*)?\{([^}]*)\}/g
  const matches = [...styles.matchAll(ruleRegex)]
  expect(matches.length, 'DeckFooter should style .header-reveal-trigger').toBeGreaterThan(0)
  for (const match of matches) {
    expect(
      /position\s*:\s*fixed/.test(match[1]),
      '.header-reveal-trigger must not be position:fixed — that is what let it overlap the deck'
    ).toBe(false)
  }
})

test('reveal pill keeps its >=44px touch floor', () => {
  const styles = styleBlock(readComponent('DeckFooter.vue'), 'DeckFooter.vue')
  const ruleRegex = /\.reveal-pill\s*(?:,[^{]*)?\{([^}]*)\}/g
  const matches = [...styles.matchAll(ruleRegex)]
  expect(matches.length, 'DeckFooter should style .reveal-pill').toBeGreaterThan(0)
  const hasFloor = matches.some((m) => {
    const minHeight = /min-height\s*:\s*([0-9]+)px/.exec(m[1])
    return minHeight !== null && parseInt(minHeight[1]) >= 44
  })
  expect(hasFloor, '.reveal-pill must keep a >=44px min-height baseline').toBe(true)
})
