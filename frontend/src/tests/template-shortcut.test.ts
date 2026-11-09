// DL-165 — template keys show the shortcut they send under their name.
import { describe, it, expect } from 'vitest'
import { templateShortcut, formatKeys } from '@/utils/templateShortcut'
import { templateCategories } from '@/data/appTemplates'

describe('templateShortcut', () => {
  it('formats hotkey actions', () => {
    expect(formatKeys(['ctrl', 'shift', 'f5'])).toBe('Ctrl+Shift+F5')
    expect(templateShortcut({ action: { type: 'hotkey', config: { keys: ['escape'] } } })).toBe('Esc')
  })
  it('reads the chord or slash command from the tooltip', () => {
    expect(templateShortcut({ action: { type: 'cc_todos' }, tooltip: "Show or hide Claude's to-do checklist (Ctrl+T)" })).toBe('Ctrl+T')
    expect(templateShortcut({ action: { type: 'cc_queue' }, tooltip: 'Run after the turn (Ctrl+X, Enter)' })).toBe('Ctrl+X, Enter')
    expect(templateShortcut({ action: { type: 'cc_compact' }, tooltip: '/compact - free up context' })).toBe('/compact')
    expect(templateShortcut({ action: { type: 'url' }, tooltip: 'Open the docs' })).toBe('')
  })
  it('AI coding templates label most keys and Cowork opens the desktop app', () => {
    const all = templateCategories.flatMap(c => c.templates)
    const cc = all.find(t => t.id === 'claude-code')!
    const labelled = cc.buttons.filter(b => templateShortcut(b)).length
    expect(labelled).toBeGreaterThanOrEqual(cc.buttons.length - 6)
    const cowork = all.find(t => t.id === 'claude-cowork')!
    const open = cowork.buttons.find(b => b.label === 'Open Claude')!
    expect(open.action.config.path).toBe('Claude Desktop')
    expect(cowork.buttons.some(b => ['Scheduled', 'Connectors', 'Plugins'].includes(b.label))).toBe(true)
    expect(cowork.buttons.length).toBeLessThanOrEqual(20)
    for (const t of all) expect(t.buttons.length, t.id).toBeLessThanOrEqual(20)
  })
})
