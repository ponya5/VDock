import type { AgentStateName } from '@/api/appProfiles'

/**
 * DL-165 / DL-166: helpers shared by the desktop action bar and the phone
 * console. Kept out of useAgentTargets so the bar's tests can keep mocking
 * that composable wholesale.
 */

/** Fold a session row's raw state into the states the deck acts on; null = unknown. */
export function toAgentState(state: string | null | undefined): AgentStateName | null {
  if (state === 'working' || state === 'permission') return state
  if (state === 'ready' || state === 'idle') return 'ready'
  return null
}

/** "2 others: 1 working, 1 ready" - what the sessions the bar is NOT linked to are doing. */
export function summarizeOtherSessions(
  rows: ReadonlyArray<{ pid: number; state: string | null }>,
  linkedPid: number | null | undefined,
): string {
  const others = rows.filter(r => r.pid !== linkedPid)
  if (linkedPid == null || !others.length) return ''
  const counts: Record<string, number> = {}
  for (const o of others) {
    const st = toAgentState(o.state) ?? 'unknown'
    counts[st] = (counts[st] ?? 0) + 1
  }
  const parts = Object.entries(counts).map(([st, n]) => `${n} ${st === 'permission' ? 'needs permission' : st}`)
  return `${others.length} other${others.length > 1 ? 's' : ''}: ${parts.join(', ')}`
}
