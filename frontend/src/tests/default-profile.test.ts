import { test, expect } from 'vitest'
import { createDefaultProfile, createDefaultScene, createFactoryIdeScene } from '../utils/defaultProfile'

test('createDefaultProfile seeds Media + Claude Code scenes', () => {
  const profile = createDefaultProfile()

  // DL-100: the out-of-box set is Media + Claude Code. Cursor/Websites
  // stay reachable via the template gallery, not the seeded profile.
  const names = profile.scenes.map((s) => s.name)
  expect(names).toEqual(['Media', 'Claude Code'])

  const home = profile.scenes[0]
  expect(home.isDefault).toBe(true)
  expect(home.isActive).toBe(true)
})

test('every seeded button has an action, position inside the grid, and a label', () => {
  const profile = createDefaultProfile()

  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      const { rows, cols } = page.grid_config
      for (const btn of page.buttons) {
        expect(btn.label).toBeTruthy()
        expect(btn.action?.type).toBeTruthy()
        expect(btn.position.row).toBeGreaterThanOrEqual(0)
        expect(btn.position.row).toBeLessThan(rows)
        expect(btn.position.col).toBeGreaterThanOrEqual(0)
        expect(btn.position.col).toBeLessThan(cols)
        expect(btn.enabled).toBe(true)
      }
    }
  }
})

test('seeded buttons use only no-key action types', () => {
  const profile = createDefaultProfile()
  const allowed = new Set([
    'url', 'hotkey', 'cross_platform', 'macro',
    'claude_continue', 'claude_slash', 'claude_prompt', 'claude_open',
    'cc_prompt',
    'cursor_new_chat', 'cursor_prompt', 'cursor_inline_edit', 'cursor_toggle_terminal',
    'now_playing' // DL-129: the SMTC track card — local feed, no key needed
  ])

  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      for (const btn of page.buttons) {
        expect(allowed.has(btn.action!.type)).toBe(true)
      }
    }
  }
})

test('Claude grid leaves state-dependent actions to the agent action bar', () => {
  const claudeScene = createDefaultProfile().scenes.find((scene) => scene.name === 'Claude Code')!
  const buttons = claudeScene.pages[0].buttons
  const barOwnedTypes = new Set(['cc_submit', 'cc_interrupt', 'cc_accept', 'cc_approve', 'cc_deny'])

  expect(buttons.some((button) => barOwnedTypes.has(button.action!.type))).toBe(false)
  expect(buttons.some((button) => button.action?.config?.text === 'continue')).toBe(false)
  expect(claudeScene.pages[0].grid_config).toEqual({ rows: 2, cols: 4 })
})

// DL-066 follow-up: the Cursor scene shipped with a 3x5 grid_config while only using a
// 2x4 area, so its buttons rendered visibly smaller than Claude's in the
// same 2x4 space — this pins both scenes to the same grid so that can't
// silently regress again, and confirms Cursor's own state-dependent actions
// (Submit/Continue/Stop/Accept/Reject, backend/integrations/keymaps/cursor.py)
// stay out of the grid the same way Claude's do.
// DL-100: Cursor is no longer seeded into the default profile, but the
// template stays reachable via createFactoryIdeScene — test that builder.
test('Cursor grid matches Claude\'s density and leaves state-dependent actions to the agent action bar', () => {
  const cursorScene = createFactoryIdeScene('Cursor')!
  const buttons = cursorScene.pages[0].buttons
  const barOwnedTypes = new Set(['cursor_submit', 'cursor_followup', 'cursor_cancel', 'cursor_accept', 'cursor_reject'])

  expect(cursorScene.pages[0].grid_config).toEqual({ rows: 2, cols: 4 })
  expect(buttons.some((button) => barOwnedTypes.has(button.action!.type))).toBe(false)
  expect(buttons).toHaveLength(8)
})

test('button ids are unique across the profile', () => {
  const profile = createDefaultProfile()
  const ids = profile.scenes.flatMap((s) =>
    s.pages.flatMap((p) => p.buttons.map((b) => b.id))
  )
  expect(new Set(ids).size).toBe(ids.length)
})

test('createDefaultScene output is unchanged (reset parity)', () => {
  const scene = createDefaultScene()
  expect(scene.name).toBe('Media')
  expect(scene.isDefault).toBe(true)
  expect(scene.pages[0].buttons.length).toBeGreaterThan(0)
})
