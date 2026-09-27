import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { nextTick } from 'vue'
import type { AgentStateEntry } from '@/services/agentState'

// DL-080 follow-up #3 — the snooze is time-boxed to 3 minutes: the same
// episode re-alerts after the window, a NEW episode re-arms instantly.

const entryRef = { value: undefined as AgentStateEntry | undefined }

vi.mock('@/services/agentState', () => ({
  agentStateEntry: (source: string | null | undefined) =>
    source === 'claude' ? entryRef.value : undefined,
}))

vi.mock('@/services/appDetection', () => ({
  sceneAppProfile: () => ({ id: 'claude-code', status_source: 'claude', label: 'Claude Code' }),
}))

import { dismissAgentWaiting, isAgentWaitingDismissed, sceneWaitingAgent, AGENT_SNOOZE_MS } from '@/services/agentWaiting'

function readyEntry(ts: number): AgentStateEntry {
  return { source: 'claude', state: 'ready', message: '', cwd: '', project: 'backend', ts }
}

const scene = { id: 's1', name: 'Claude Code', appId: 'claude', triggeredByApp: false, pages: [] } as never

describe('agentWaiting snooze window', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    entryRef.value = readyEntry(1000)
  })
  afterEach(() => { vi.useRealTimers() })

  it('snoozes the current episode and re-alerts after 3 minutes', async () => {
    expect(sceneWaitingAgent(scene)).not.toBeNull()
    dismissAgentWaiting('claude')
    expect(isAgentWaitingDismissed('claude')).toBe(true)
    expect(sceneWaitingAgent(scene)).toBeNull()

    // Still snoozed just inside the window…
    vi.advanceTimersByTime(AGENT_SNOOZE_MS - 60_000)
    expect(isAgentWaitingDismissed('claude')).toBe(true)

    // …and re-alerting once it lapses (the same episode is still waiting).
    vi.advanceTimersByTime(120_000)
    await nextTick()
    expect(isAgentWaitingDismissed('claude')).toBe(false)
    expect(sceneWaitingAgent(scene)).not.toBeNull()
  })

  it('re-arms immediately when a new waiting episode starts', () => {
    dismissAgentWaiting('claude')
    expect(isAgentWaitingDismissed('claude')).toBe(true)
    entryRef.value = readyEntry(2000) // fresh ready event → new ts
    expect(isAgentWaitingDismissed('claude')).toBe(false)
    expect(sceneWaitingAgent(scene)).not.toBeNull()
  })

  it('clears when the agent leaves ready mid-snooze', () => {
    dismissAgentWaiting('claude')
    entryRef.value = { ...readyEntry(1000), state: 'busy' }
    expect(isAgentWaitingDismissed('claude')).toBe(false)
  })

  it('re-snoozing inside the window extends to a fresh 3 minutes', async () => {
    dismissAgentWaiting('claude')
    vi.advanceTimersByTime(AGENT_SNOOZE_MS - 30_000)
    dismissAgentWaiting('claude')
    vi.advanceTimersByTime(AGENT_SNOOZE_MS - 30_000)
    expect(isAgentWaitingDismissed('claude')).toBe(true)
    vi.advanceTimersByTime(120_000)
    await nextTick()
    expect(isAgentWaitingDismissed('claude')).toBe(false)
  })
})
