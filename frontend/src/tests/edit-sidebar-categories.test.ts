import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

// DL-097: edit-mode action sidebar — the per-row ^/v category-reorder
// buttons are removed (they read as expand/collapse controls, truncated
// every category name, and the reorder was session-only anyway), rows
// become icon-chipped cards with full names, and the footer only mounts
// when it has content (edit controls / reveal pill / page dots) with a
// slide transition.

const src = resolve(__dirname, '..')

function readSrc(rel: string) {
  return readFileSync(resolve(src, rel), 'utf-8')
}

function styleBlock(content: string, file: string) {
  const styleMatch = content.match(/<style[^>]*>([\s\S]*?)<\/style>/)
  expect(styleMatch, `${file} should contain a style block`).not.toBeNull()
  return styleMatch![1]
}

test('EditSidebar no longer renders category reorder controls', () => {
  const sidebar = readSrc('components/EditSidebar.vue')
  expect(sidebar.includes('category-controls'), 'reorder controls block must be gone').toBe(false)
  expect(sidebar.includes('btn-control'), 'btn-control buttons must be gone').toBe(false)
  expect(sidebar.includes('moveCategory'), 'moveCategory emit wiring must be gone').toBe(false)
})

test('DashboardView drops the session-only category reorder handlers', () => {
  const view = readSrc('views/DashboardView.vue')
  expect(view.includes('moveCategoryUp'), 'moveCategoryUp handler must be gone').toBe(false)
  expect(view.includes('moveCategoryDown'), 'moveCategoryDown handler must be gone').toBe(false)
})

test('category rows carry icon chip, count pill and rotating chevron', () => {
  const sidebar = readSrc('components/EditSidebar.vue')
  for (const cls of ['category-icon', 'category-count', 'category-chevron']) {
    expect(sidebar.includes(cls), `EditSidebar should render .${cls}`).toBe(true)
  }
  const styles = styleBlock(sidebar, 'EditSidebar.vue')
  // chevron rotates instead of swapping icons
  expect(/\.category-chevron[^}]*transform\s*:/s.test(styles), 'chevron should rotate via transform').toBe(true)
  // per-category accent var drives the icon chip
  expect(styles.includes('--cat-accent'), 'icon chip should consume --cat-accent').toBe(true)
})

test('category header keeps its >=44px touch floor', () => {
  const styles = styleBlock(readSrc('components/EditSidebar.vue'), 'EditSidebar.vue')
  const ruleRegex = /\.category-header\s*(?:,[^{]*)?\{([^}]*)\}/g
  const matches = [...styles.matchAll(ruleRegex)]
  expect(matches.length).toBeGreaterThan(0)
  const hasFloor = matches.some((m) => /min-height\s*:\s*([0-9]+)px/.test(m[1]))
  expect(hasFloor, '.category-header must keep a px min-height baseline').toBe(true)
})

test('footer only mounts when it has content, with a slide transition', () => {
  const view = readSrc('views/DashboardView.vue')
  const footerBlock = view.match(/<DeckFooter[^>]*>/)?.[0] ?? ''
  // DL-102: the reveal control is a floating button now — the footer only
  // mounts for real content (edit controls / page dots) via footerVisible.
  expect(footerBlock.includes('footerVisible'), 'DeckFooter v-if must be the footerVisible computed').toBe(true)
  expect(footerBlock.includes('showHeader'), 'DeckFooter v-if must not depend on showHeader — hiding the header must not mount the footer').toBe(false)
  expect(view.includes('footer-slide'), 'DeckFooter should be wrapped in a footer-slide Transition').toBe(true)

  const footerStyles = styleBlock(readSrc('components/DeckFooter.vue'), 'DeckFooter.vue')
  expect(/\.footer-slide-leave-active[^}]*position\s*:\s*absolute/s.test(footerStyles),
    'leaving footer must go absolute so the grid reclaims space inside the slide').toBe(true)
})
