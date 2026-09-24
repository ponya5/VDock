import { reactive, readonly } from 'vue'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import type { AgentStateName } from '@/api/appProfiles'

/**
 * Live coding-agent state (DL-064): is Claude Code / Cursor ready for a
 * prompt, working, or blocked on a permission dialog?
 *
 * Fed by agent hooks through the backend: the `agent_state` socket event
 * carries the full snapshot on every change, and GET /agent-events/states
 * re-syncs a freshly loaded or reconnected client.
 */

export interface AgentStateEntry {
  source: string
  state: Exclude<AgentStateName, 'unknown'>
  message: string
  cwd: string
  project: string
  /** Last prompt the user sent in this session (hooks, DL-065). */
  prompt?: string
  /** The agent's last reply, plain text. */
  reply?: string
  ts: number
  /** Live sessions of this agent folded into this entry. */
  session_count?: number
}

const statesBySource = reactive<Record<string, AgentStateEntry>>({})
let initialized = false

function replaceStates(nextStates: Record<string, AgentStateEntry> | undefined): void {
  for (const source of Object.keys(statesBySource)) {
    if (!nextStates?.[source]) delete statesBySource[source]
  }
  Object.assign(statesBySource, nextStates ?? {})
}

async function syncFromBackend(): Promise<void> {
  try {
    const response = await apiClient.get('/agent-events/states')
    replaceStates(response.data?.states)
  } catch (error) {
    console.warn('Could not load agent states:', error)
  }
}

export function initAgentState(): void {
  if (initialized) return
  initialized = true
  socketClient.on('agent_state', (payload: { states?: Record<string, AgentStateEntry> }) => {
    replaceStates(payload?.states)
  })
  socketClient.on('connect', () => { void syncFromBackend() })
  void syncFromBackend()
}

/** The reported state for an agent source, 'unknown' when it isn't reporting. */
export function agentStateFor(source: string | null | undefined): AgentStateName {
  if (!source) return 'unknown'
  return statesBySource[source]?.state ?? 'unknown'
}

export function agentStateEntry(source: string | null | undefined): AgentStateEntry | undefined {
  return source ? statesBySource[source] : undefined
}

export const agentStates = readonly(statesBySource)

/**
 * Agent sources whose action bar is on screen right now. The alert overlay
 * stands down for these: the bar already shows the state and the Approve/Deny
 * buttons, and the overlay would cover them on a small panel.
 */
const sourcesWithVisibleBar = reactive(new Set<string>())

export function setAgentBarVisible(source: string, isVisible: boolean): void {
  if (isVisible) {
    sourcesWithVisibleBar.add(source)
    return
  }
  sourcesWithVisibleBar.delete(source)
}

export function isAgentBarVisible(source: string | null | undefined): boolean {
  return source ? sourcesWithVisibleBar.has(source) : false
}
