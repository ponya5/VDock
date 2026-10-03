// DL-147 Phase 3 leftovers (a): ButtonEditor and Settings are finger-sized on
// tablets without changing the desktop or the 7" panel.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect } from 'vitest'

const src = (...parts: string[]) => readFileSync(resolve(__dirname, '..', ...parts), 'utf-8')

describe('ButtonEditor on phones and tablets', () => {
  const editor = src('components', 'ButtonEditor.vue')

  it('gives the save and close buttons a 44 px box only on phone/tablet', () => {
    expect(editor).toMatch(
      /html:is\(\.device-phone, \.device-tablet\) \.save-profile-btn,\s*html:is\(\.device-phone, \.device-tablet\) \.close-btn\s*\{[^}]*min-width: 44px;[^}]*min-height: 44px/,
    )
  })

  it('makes checkbox rows 44 px tall so the whole row is the target', () => {
    expect(editor).toMatch(/html:is\(\.device-phone, \.device-tablet\) \.checkbox-label\s*\{[^}]*min-height: 44px/)
  })

  it('does the same for the template collapse chevron', () => {
    expect(src('components', 'QuickTemplates.vue')).toMatch(
      /html:is\(\.device-phone, \.device-tablet\) \.collapse-btn\s*\{[^}]*min-width: 44px;[^}]*min-height: 44px/,
    )
  })
})

describe('Settings on tablets', () => {
  const css = src('assets', 'styles', 'settings.css')
  const block = /@media \(pointer: coarse\) and \(min-width: 700px\) and \(min-height: 700px\)\s*\{([^}]*)\}/.exec(css)?.[1] ?? ''

  it('lifts the small controls to 44 px on touch viewports at least 700 px on both sides', () => {
    for (const selector of ['.setting-reset', '.dock-credit-link', '.dock-dismiss', '.dock-inbox', '.notification-bell']) {
      expect(block, selector).toContain(selector)
    }
    expect(block).toMatch(/min-width: 44px;\s*min-height: 44px/)
  })

  it('leaves the 7" panel (600 px tall) out of that block', () => {
    expect(block).not.toBe('')
    expect(css).toContain('min-height: 700px')
  })
})
