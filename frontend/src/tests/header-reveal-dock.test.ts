import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// DL-102: the header reveal is an independent floating button owned by
// DashboardView — not a pill docked inside DeckFooter. Hiding the header no
// longer mounts a full-width footer strip just to host a ≥200px labelled
// pill; a compact circular FAB sits bottom-right (clear of the left-side
// docked sidebar and the footer's left/center content) and lifts above the
// footer whenever it is mounted for real content.

const srcDir = resolve(__dirname, '..')

function readSrc(file: string) {
  return readFileSync(resolve(srcDir, file), 'utf-8')
}

function styleBlock(content: string, file: string) {
  const styleMatch = content.match(/<style[^>]*>([\s\S]*?)<\/style>/)
  expect(styleMatch, `${file} should contain a style block`).not.toBeNull()
  return styleMatch![1]
}

test('DeckFooter no longer hosts the reveal trigger', () => {
  const footer = readSrc('components/DeckFooter.vue')
  expect(
    footer.includes('header-reveal-trigger') || footer.includes('reveal-pill'),
    'DeckFooter must not render the reveal control — it floats in DashboardView'
  ).toBe(false)
})

test('DashboardView renders the floating reveal button', () => {
  const view = readSrc('views/DashboardView.vue')
  expect(view.includes('header-reveal-fab'), 'DashboardView should own the header-reveal-fab').toBe(true)
  expect(view.includes('!settingsStore.showHeader'),
    'the FAB should render while the header is hidden').toBe(true)
  expect(view.includes('revealFabRef'), 'the FAB needs its ref for the swipe-down reveal').toBe(true)
})

test('the FAB is a compact window-glyph that keeps the >=44px touch floor', () => {
  const view = readSrc('views/DashboardView.vue')
  const styles = styleBlock(view, 'DashboardView.vue')
  const ruleRegex = /\.header-reveal-fab\s*(?:,[^{]*)?\{([^}]*)\}/g
  const matches = [...styles.matchAll(ruleRegex)]
  expect(matches.length, 'DashboardView should style .header-reveal-fab').toBeGreaterThan(0)

  const base = matches[0][1]
  expect(base.includes('position: fixed'), 'the FAB must float, not consume flow').toBe(true)
  expect(base.includes('right:'), 'the FAB anchors to the right edge (sidebar owns the left)').toBe(true)
  expect(base.includes('bottom:'), 'the FAB anchors to the bottom edge').toBe(true)
  // DL-104: it's a mini window, not a bare circle — rounded rect, clipped
  // so the header band fills the top edge.
  expect(/border-radius\s*:\s*50%/.test(base), 'the FAB is a window glyph now, not a circle').toBe(false)
  expect(base.includes('overflow: hidden'), 'the window frame should clip its header band').toBe(true)
  // DL-104: the window carries an accent "header" band + a caret — the
  // self-explanatory glyph, not a bare arrow.
  expect(view.includes('fab-head'), 'the FAB should render the header-band element').toBe(true)
  expect(view.includes('fab-caret'), 'the FAB should render the caret element').toBe(true)
  const headRule = styles.match(/\.fab-head\s*\{([^}]*)\}/)?.[1] ?? ''
  expect(headRule.includes('top: 0') && /background/.test(headRule),
    'fab-head should be an accent band across the top of the mini window').toBe(true)
  // 44px touch floor on both axes.
  expect(/\d{2}px/.test(base), 'the FAB should size around the touch floor').toBe(true)
  // Compact: no fixed multi-hundred-px width like the old pill had.
  expect(/min-width\s*:\s*calc\(200px/.test(base) ||
         /width\s*:\s*(?:calc\()?1[5-9][0-9]px|width\s*:\s*(?:calc\()?[2-9][0-9]{2}px/.test(base),
    'the FAB must stay compact — no pill-width footprint').toBe(false)
})

test('the FAB lifts above the footer when the footer is mounted', () => {
  const view = readSrc('views/DashboardView.vue')
  const styles = styleBlock(view, 'DashboardView.vue')
  expect(view.includes('above-footer'), 'FAB should bind the above-footer class').toBe(true)
  const rule = styles.match(/\.header-reveal-fab\.above-footer\s*\{([^}]*)\}/)?.[1] ?? ''
  expect(/bottom\s*:\s*calc\(/.test(rule), 'above-footer must raise the FAB clear of the footer strip').toBe(true)
})
