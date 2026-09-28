/**
 * DL-071 follow-up 11 — session pickers show informative names:
 * project · host app · a stable #n ordinal for same-dir collisions.
 * `buildSessionRows` is the pure label builder behind
 * `useAgentTargets().sessionRows`.
 */
import { describe, expect, it } from 'vitest'
import { buildSessionRows, hostBadge } from '@/composables/useAgentTargets'
import type { AgentSessionInfo } from '@/api/agentSessions'

function session(partial: Partial<AgentSessionInfo>): AgentSessionInfo {
  return {
    pid: 1,
    hwnd: 1,
    title: '✳ Claude Code',
    cwd: null,
    project: '',
    state: null,
    detail: '',
    started: null,
    ...partial,
  }
}

describe('buildSessionRows', () => {
  it('names a lone session by project and hosting app', () => {
    const rows = buildSessionRows([
      session({ pid: 100, project: 'backend', host: 'Windows Terminal' }),
    ])
    expect(rows[0].label).toBe('backend · Windows Terminal')
  })

  it('falls back to project alone when the host app is unknown', () => {
    const rows = buildSessionRows([
      session({ pid: 100, project: 'backend' }),
    ])
    expect(rows[0].label).toBe('backend')
  })

  it('numbers same-directory sessions instead of showing raw pids', () => {
    const rows = buildSessionRows([
      session({
        pid: 25712, project: 'backend', cwd: 'C:\\repos\\backend',
        started: 2000, host: 'Windows Terminal',
      }),
      session({
        pid: 10228, project: 'backend', cwd: 'C:\\repos\\backend',
        started: 1000, host: 'Windows Terminal',
      }),
    ])
    // #1 is the OLDER session (lower started) — stable across polls.
    expect(rows.find(r => r.pid === 10228)?.label)
      .toBe('backend #1 · Windows Terminal')
    expect(rows.find(r => r.pid === 25712)?.label)
      .toBe('backend #2 · Windows Terminal')
  })

  it('shows two-segment paths when same-named projects collide', () => {
    const rows = buildSessionRows([
      session({
        pid: 100, project: 'backend', cwd: 'C:\\Users\\me\\VDock2\\backend',
        host: 'Cursor',
      }),
      session({
        pid: 200, project: 'backend', cwd: 'C:\\Users\\me\\other\\backend',
        host: 'Windows Terminal',
      }),
    ])
    expect(rows.find(r => r.pid === 100)?.label)
      .toBe('VDock2/backend · Cursor')
    expect(rows.find(r => r.pid === 200)?.label)
      .toBe('other/backend · Windows Terminal')
  })

  it('host alone tells two same-dir sessions apart by surface', () => {
    const rows = buildSessionRows([
      session({
        pid: 100, project: 'backend', cwd: 'C:\\repos\\backend',
        started: 1000, host: 'Cursor',
      }),
      session({
        pid: 200, project: 'backend', cwd: 'C:\\repos\\backend',
        started: 2000, host: 'Windows Terminal',
      }),
    ])
    expect(rows.find(r => r.pid === 100)?.label).toBe('backend #1 · Cursor')
    expect(rows.find(r => r.pid === 200)?.label)
      .toBe('backend #2 · Windows Terminal')
  })

  it('keeps the backend ordering (newest first)', () => {
    const rows = buildSessionRows([
      session({ pid: 300, project: 'c', started: 3000 }),
      session({ pid: 100, project: 'a', started: 1000 }),
      session({ pid: 200, project: 'b', started: 2000 }),
    ])
    expect(rows.map(r => r.pid)).toEqual([300, 100, 200])
  })

  it('gives every session a distinct accent color', () => {
    const rows = buildSessionRows([
      session({ pid: 101, project: 'a' }),
      session({ pid: 202, project: 'b' }),
      session({ pid: 303, project: 'c' }),
    ])
    const accents = rows.map(r => r.accent)
    expect(new Set(accents).size).toBe(3)
    for (const a of accents) expect(a).toMatch(/^#[0-9a-f]{6}$/i)
  })

  it('keeps a session\'s accent when siblings come and go', () => {
    const first = buildSessionRows([
      session({ pid: 101, project: 'a' }),
      session({ pid: 202, project: 'b' }),
      session({ pid: 303, project: 'c' }),
    ]).find(r => r.pid === 101)!.accent
    const after = buildSessionRows([
      session({ pid: 101, project: 'a' }),
      session({ pid: 404, project: 'd' }),
    ]).find(r => r.pid === 101)!.accent
    expect(after).toBe(first)
  })
})

describe('hostBadge', () => {
  it('compresses multi-word hosts to initials', () => {
    expect(hostBadge('Windows Terminal')).toBe('WT')
    expect(hostBadge('VS Code')).toBe('VS')
    expect(hostBadge('Command Prompt')).toBe('CP')
  })
  it('uses camel-cased capitals inside one word', () => {
    expect(hostBadge('PowerShell')).toBe('PS')
  })
  it('falls back to the first two letters', () => {
    expect(hostBadge('Cursor')).toBe('CU')
    expect(hostBadge('WezTerm')).toBe('WT')
  })
  it('empty when the host is unknown', () => {
    expect(hostBadge(null)).toBe('')
    expect(hostBadge(undefined)).toBe('')
  })
})
