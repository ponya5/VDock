// DL-147 Tasks 2.4 / 2.5 - notch / home-indicator padding and the 44 px touch
// floor on phone surfaces. Source-level on purpose: jsdom has no safe-area
// insets or layout, and the point is that panel/desktop CSS stays untouched
// (env() resolves to 0 there, and every size bump hangs off `.device-phone`).
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { compileStyle } from 'vue/compiler-sfc'

const read = (file: string) => readFileSync(resolve(__dirname, '..', file), 'utf-8')

const dashboard = read('views/DashboardView.vue')

describe('safe-area padding', () => {
  it('pads the phone deck root on the top and sides, and the grid host at the bottom', () => {
    expect(dashboard).toMatch(
      /\.dashboard-view:is\(\.device-phone, \.device-tablet\)\s*\{[^}]*env\(safe-area-inset-top[^}]*env\(safe-area-inset-right[^}]*env\(safe-area-inset-left/,
    )
    expect(dashboard).toMatch(/\.dashboard-view:is\(\.device-phone, \.device-tablet\)\s+\.deck-grid-host\s*\{[^}]*env\(safe-area-inset-bottom/)
  })

  it('keeps the header reveal FAB and the action toast clear of the insets', () => {
    expect(dashboard).toMatch(/\.header-reveal-fab\s*\{[^}]*env\(safe-area-inset-right[^}]*env\(safe-area-inset-bottom/)
    expect(dashboard).toMatch(/\.action-toast\s*\{[^}]*env\(safe-area-inset-bottom/)
  })

  it.each([
    'components/AgentWaitingDock.vue',
    'components/AgentMissionControl.vue',
    'components/AgentAlertOverlay.vue',
    'components/NotificationCenter.vue',
    'components/RotateToLandscape.vue',
  ])('%s respects safe-area insets', (file) => {
    expect(read(file)).toContain('env(safe-area-inset')
  })

  it('lifts the agent dock by the same inset the FAB uses so they cannot overlap', () => {
    const dock = read('components/AgentWaitingDock.vue')
    // (the footer variant needs none: phones never mount the footer)
    expect(dock).toMatch(/html\.reveal-fab-visible \.agent-waiting-dock\s*\{[^}]*env\(safe-area-inset-bottom/)
  })

  it('compiles the html-scoped dock rules with their descendant selector intact', () => {
    // `:global(html.x) .child` in a scoped block compiles to a bare `html.x`
    // rule that drops `.child`, so the dock never lifted above the FAB.
    const source = read('components/AgentWaitingDock.vue')
    const style = /<style scoped>([\s\S]*?)<\/style>/.exec(source)![1]
    const { code, errors } = compileStyle({ source: style, filename: 'AgentWaitingDock.vue', id: 'data-v-test', scoped: true })
    expect(errors).toEqual([])
    expect(code).toMatch(/html\.reveal-fab-visible \.agent-waiting-dock\[data-v-test\]/)
    expect(code).toMatch(/html:is\(\.device-phone, \.device-tablet\) \.dock-dismiss\[data-v-test\]/)
  })

  it('does not double-pad surfaces that already handle the inset themselves', () => {
    expect(read('components/MobileAgentConsole.vue')).toContain('env(safe-area-inset-bottom')
    expect(dashboard).not.toMatch(/\.device-phone[^{]*\.mobile-agent-console/)
  })
})

describe('html device class', () => {
  it('publishes device-phone / device-tablet on <html> for teleported surfaces', () => {
    expect(dashboard).toContain('`device-${name}`')
    expect(dashboard).toMatch(/classList\.remove\([^)]*device-phone/)
  })
})

describe('44 px phone and tablet targets', () => {
  const phoneRule = (source: string, selector: string) =>
    new RegExp(`html:is\\(\\.device-phone, \\.device-tablet\\)\\s+${selector}\\s*\\{[^}]*(min-)?(width|height)[^}]*44px`).test(source)

  it('grows dock chips, dock dismiss and Mission Control entry on phones', () => {
    const dock = read('components/AgentWaitingDock.vue')
    expect(phoneRule(dock, '\\.dock-dismiss')).toBe(true)
    expect(phoneRule(dock, '\\.dock-inbox')).toBe(true)
  })

  it('grows toast dismiss and Show Details on phones', () => {
    const toast = read('components/NotificationToast.vue')
    expect(phoneRule(toast, '\\.toast-close')).toBe(true)
    expect(phoneRule(toast, '\\.details-toggle')).toBe(true)
  })

  it('extends the slider quick-jump chip hit area on phones without resizing it', () => {
    const slider = read('components/SliderButtonFace.vue')
    expect(slider).toMatch(/device-phone[^{]*\.slider-preset::before\s*\{[^}]*inset:\s*-14px -2px/)
  })

  it('makes the Mission Control close button 44 px', () => {
    expect(read('components/AgentMissionControl.vue')).toMatch(/\.mc-close\s*\{[^}]*width: 44px; height: 44px/)
  })
})
