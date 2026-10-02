import { ref } from 'vue'
import apiClient from '@/api/client'

/**
 * Agent Mission Control + approval inbox (DL-144).
 *
 * One row per live agent *session* (the combined per-source view in
 * `agentState` hides that two Claude sessions are running). The server
 * decides what each row may do (`can_decide`, `can_focus`) so the UI never
 * offers a verb the backend would refuse.
 */

export interface MissionSession {
  source: string
  session_id: string
  project: string
  cwd: string
  state: 'ready' | 'working' | 'permission' | string
  message: string
  prompt: string
  reply: string
  prompted: boolean
  ts: number
  idle_seconds: number
  needs_you: boolean
  can_decide: boolean
  can_focus: boolean
  /** DL-145: ready, and the agent can take a typed prompt. */
  can_prompt: boolean
}

/** A built-in prompt the Prompt menu offers (the list lives on the server). */
export interface MissionPreset {
  id: string
  label: string
}

export interface ChangedFile {
  path: string
  added: number
  removed: number
  status: 'M' | 'A' | 'D' | '?'
}

/** What a session changed this turn (GET /agent-mission/changes). */
export interface SessionChanges {
  success: boolean
  files: ChangedFile[]
  totals: { files: number; added: number; removed: number }
}

export interface MissionSnapshot {
  sessions: MissionSession[]
  presets: MissionPreset[]
  needs_you: number
  pending_approvals: number
}

export type MissionDecision = 'approve' | 'deny'

/** Shared open flag: the modal, the deck action and the dock chip all use it. */
export const missionControlOpen = ref(false)

export function openMissionControl(): void {
  missionControlOpen.value = true
}

export function closeMissionControl(): void {
  missionControlOpen.value = false
}

export function toggleMissionControl(): void {
  missionControlOpen.value = !missionControlOpen.value
}

export async function fetchMission(): Promise<MissionSnapshot> {
  const { data } = await apiClient.get('/agent-mission')
  return {
    sessions: data.sessions ?? [],
    presets: data.presets ?? [],
    needs_you: data.needs_you ?? 0,
    pending_approvals: data.pending_approvals ?? 0,
  }
}

export async function focusMissionSession(source: string, sessionId: string): Promise<void> {
  await apiClient.post('/agent-mission/focus', { source, session_id: sessionId })
}

export async function decideMissionSession(
  source: string,
  sessionId: string,
  decision: MissionDecision,
): Promise<void> {
  await apiClient.post('/agent-mission/decide', {
    source,
    session_id: sessionId,
    decision,
  })
}

export async function promptMissionSession(
  source: string,
  sessionId: string,
  preset: string,
): Promise<void> {
  await apiClient.post('/agent-mission/prompt', { source, session_id: sessionId, preset })
}

export async function fetchSessionChanges(source: string, sessionId: string): Promise<SessionChanges> {
  const { data } = await apiClient.get('/agent-mission/changes', { source, session_id: sessionId })
  return data
}

export async function openSessionDiff(source: string, sessionId: string, path: string): Promise<void> {
  await apiClient.post('/agent-mission/open-diff', { source, session_id: sessionId, path })
}

/** "now", "42s", "4m", "2h 5m" - compact idle time for a row. */
export function formatIdle(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds))
  if (s < 5) return 'now'
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  const rem = m % 60
  return rem ? `${h}h ${rem}m` : `${h}h`
}

export type MissionGroupId = 'approval' | 'waiting' | 'working' | 'idle'

export interface MissionGroup {
  id: MissionGroupId
  title: string
  sessions: MissionSession[]
}

/** Split rows into the sections the modal renders; empty groups are dropped. */
export function groupMission(sessions: MissionSession[]): MissionGroup[] {
  const groups: MissionGroup[] = [
    { id: 'approval', title: 'Needs your approval', sessions: [] },
    { id: 'waiting', title: 'Waiting for your next prompt', sessions: [] },
    { id: 'working', title: 'Working', sessions: [] },
    { id: 'idle', title: 'Idle', sessions: [] },
  ]
  for (const session of sessions) {
    if (session.state === 'permission') groups[0].sessions.push(session)
    else if (session.needs_you) groups[1].sessions.push(session)
    else if (session.state === 'working') groups[2].sessions.push(session)
    else groups[3].sessions.push(session)
  }
  return groups.filter((g) => g.sessions.length > 0)
}
