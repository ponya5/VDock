// DL-165 — which presses ask "Are you sure?" and the setting that turns it off.
import { describe, it, expect } from 'vitest'
import { codeActionRisk } from '@/utils/codeActionRisk'

const btn = (label: string, type: string, config: Record<string, unknown> = {}) =>
  ({ label, action: { type, config } }) as never

describe('codeActionRisk', () => {
  it('flags a terminal command that pushes (danger)', () => {
    const r = codeActionRisk(btn('Push', 'command', { command: 'git push' }))
    expect(r?.danger).toBe(true)
    expect(r?.title).toMatch(/push/i)
  })
  it('flags force push and history rewrites as danger', () => {
    expect(codeActionRisk(btn('x', 'command', { command: 'git push --force' }))?.danger).toBe(true)
    expect(codeActionRisk(btn('x', 'command', { command: 'git reset --hard HEAD~1' }))?.danger).toBe(true)
  })
  it('flags an agent prompt that commits and pushes', () => {
    expect(codeActionRisk(btn('Ship it', 'cc_prompt', { text: 'Commit and push the changes' }))).not.toBeNull()
  })
  it('flags a Cursor / GitHub button by its label', () => {
    expect(codeActionRisk(btn('Git Push', 'hotkey', { keys: ['ctrl', 'shift', 'g'] }))).not.toBeNull()
    expect(codeActionRisk(btn('Merge PR', 'gh_merge'))).not.toBeNull()
  })
  it('leaves everyday buttons alone', () => {
    expect(codeActionRisk(btn('Volume Up', 'cross_platform', { action: 'volume_up' }))).toBeNull()
    expect(codeActionRisk(btn('Explain', 'cc_prompt', { text: 'Explain what this code does' }))).toBeNull()
    expect(codeActionRisk(btn('Pull', 'command', { command: 'git pull' }))).toBeNull()
  })
})
