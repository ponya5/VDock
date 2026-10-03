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

import {
  dismissAgentWaiting, isAgentWaitingDismissed, sceneWaitingAgent, AGENT_SNOOZE_MS,
  resumeAgentWaiting, sceneSnoozedAgent, agentSnoozeRemainingMs, waitingChipSources,
} from '@/services/agentWaiting'

function readyEntry(ts: number): AgentStateEntry {
  return { source: 'claude', state: 'ready', message: '', cwd: '', project: 'backend', prompted: true, ts }
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

  it('ignores a ready state from a session that was never prompted (DL-105)', () => {
    // A freshly launched agent sits idle by definition — the waiting
    // surfaces only fire once the user has actually prompted it.
    entryRef.value = { ...readyEntry(1000), prompted: false }
    expect(sceneWaitingAgent(scene)).toBeNull()
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
  it('a full dismiss never lapses on a timer, and a new idle episode re-arms it', async () => {
    dismissAgentWaiting('claude', Infinity)
    expect(agentSnoozeRemainingMs('claude')).toBe(Infinity)
    vi.advanceTimersByTime(AGENT_SNOOZE_MS * 10)
    await nextTick()
    expect(isAgentWaitingDismissed('claude')).toBe(true)
    expect(sceneWaitingAgent(scene)).toBeNull()

    entryRef.value = readyEntry(2000) // agent went idle again
    expect(isAgentWaitingDismissed('claude')).toBe(false)
    expect(sceneWaitingAgent(scene)).not.toBeNull()
  })

  it('resume ends the snooze at once and re-arms the alert', () => {
    dismissAgentWaiting('claude')
    expect(sceneWaitingAgent(scene)).toBeNull()
    expect(sceneSnoozedAgent(scene)).not.toBeNull()
    expect(agentSnoozeRemainingMs('claude')).toBeGreaterThan(0)

    resumeAgentWaiting('claude')
    expect(isAgentWaitingDismissed('claude')).toBe(false)
    expect(sceneWaitingAgent(scene)).not.toBeNull()
    expect(sceneSnoozedAgent(scene)).toBeNull()
    expect(agentSnoozeRemainingMs('claude')).toBe(0)
  })

  it('reports remaining snooze time and no snoozed agent when not snoozed', () => {
    expect(sceneSnoozedAgent(scene)).toBeNull()
    dismissAgentWaiting('claude')
    vi.advanceTimersByTime(60_000)
    expect(agentSnoozeRemainingMs('claude')).toBe(AGENT_SNOOZE_MS - 60_000)
  })
  it('the chip owns a source while waiting, snoozed or dismissed — never for other states', () => {
    expect([...waitingChipSources([scene])]).toEqual(['claude'])         // waiting
    dismissAgentWaiting('claude')
    expect([...waitingChipSources([scene])]).toEqual(['claude'])         // snoozed
    dismissAgentWaiting('claude', Infinity)
    expect([...waitingChipSources([scene])]).toEqual(['claude'])         // dismissed
    entryRef.value = { ...readyEntry(3000), state: 'permission' }
    expect(waitingChipSources([scene]).size).toBe(0)                     // approval asks keep the banner
    entryRef.value = { ...readyEntry(4000), prompted: false }
    expect(waitingChipSources([scene]).size).toBe(0)                     // never prompted: no chip, banner stays
  })
})
