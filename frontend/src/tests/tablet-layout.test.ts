// DL-147 Phase 3 - tablet chrome. Layout numbers come from the live matrix
// check; these pin the structure (jsdom has no layout engine) and that
// nothing leaks onto the panel/desktop paths.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { dashboardLayout } from '@/utils/dashboardLayout'

const read = (file: string) => readFileSync(resolve(__dirname, '..', file), 'utf-8')
const dashboard = read('views/DashboardView.vue')

describe('tablet portrait strip', () => {
  const tablet = (orientation: 'portrait' | 'landscape', innerWidth: number) =>
    dashboardLayout({ layoutClass: 'tablet', orientation, innerWidth, compactTouch: false })

  it('stacks with a strip in portrait at every matrix width, columns in landscape', () => {
    for (const w of [744, 768, 800, 820, 834, 1024]) {
      expect(tablet('portrait', w)).toEqual({ stacked: true, sidebar: 'strip' })
    }
    for (const w of [1133, 1180, 1194, 1280, 1366]) {
      expect(tablet('landscape', w)).toEqual({ stacked: false, sidebar: 'column' })
    }
  })

  it('a tablet narrower than 600px (split view) lays out as the phone', () => {
    expect(dashboardLayout({ layoutClass: 'phone', orientation: 'portrait', innerWidth: 405, compactTouch: true }))
      .toEqual({ stacked: false, sidebar: 'hidden' })
  })

  it('puts the strip in flow above the deck instead of fixed over it, tablet only', () => {
    expect(dashboard).toMatch(
      /\.dashboard-view\.device-tablet\.layout-stacked :deep\(\.docked-sidebar\.is-mobile\)\s*\{[^}]*position: relative;[^}]*width: 100% !important/,
    )
  })
})

describe('tablet safe areas', () => {
  it('pads the footer with the home-indicator inset when the footer is mounted', () => {
    expect(dashboard).toMatch(/\.dashboard-view\.device-tablet\.footer-open \.deck-footer\s*\{[^}]*env\(safe-area-inset-bottom/)
    expect(dashboard).toMatch(/\.dashboard-view\.device-tablet\.footer-open \.deck-grid-host\s*\{[^}]*padding-bottom: 0/)
  })
})

describe('tablet edit drawer', () => {
  it('overlays the deck (absolute) instead of sharing the row, tablet only', () => {
    expect(dashboard).toMatch(/\.dashboard-view\.device-tablet \.edit-sidebar\s*\{[^}]*position: absolute/)
  })

  it('is a bottom sheet capped at half the height in portrait', () => {
    expect(dashboard).toMatch(
      /\.dashboard-view\.device-tablet\.orient-portrait \.edit-sidebar\s*\{[^}]*width: 100%;[^}]*height: 50%/,
    )
  })

  it('has a 44px handle that only exists on the tablet layout class in edit mode', () => {
    expect(dashboard).toMatch(/v-if="isEditMode && layoutClass === 'tablet'"[^>]*\n?\s*type="button"\s+class="edit-drawer-toggle"/)
    expect(dashboard).toMatch(/\.edit-drawer-toggle\s*\{[^}]*width: 44px;[^}]*height: 56px/)
    expect(dashboard).toMatch(/\.orient-portrait \.edit-drawer-toggle\s*\{[^}]*width: 56px;[^}]*height: 44px/)
  })

  it('marks the hidden drawer inert so it is not focusable off-screen', () => {
    expect(dashboard).toContain(':inert="!editDrawerOpen"')
  })
})

describe('tablet edit chips', () => {
  const buttonCss = read('components/DeckButton.vue')

  it('grows edit/copy to 44px and stacks them, scoped to the tablet class', () => {
    expect(buttonCss).toMatch(/html\.device-tablet \.edit-btn,\s*html\.device-tablet \.copy-btn\s*\{[^}]*width: 44px;[^}]*height: 44px/)
    expect(buttonCss).toMatch(/html\.device-tablet \.edit-overlay-actions\s*\{[^}]*flex-direction: column/)
  })

  it('grows the slider resize chips to 44px and spaces the pair apart on tablets only', () => {
    const grid = read('components/DeckGrid.vue')
    expect(grid).toMatch(/html\.device-tablet \.slider-resize-chip\s*\{[^}]*--chip-offset: 24px;[^}]*width: 44px;[^}]*height: 44px/)
    expect(grid).toContain('translateY(var(--chip-offset, 17px))')
  })
})
