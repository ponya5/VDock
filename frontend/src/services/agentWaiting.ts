import { reactive } from 'vue'
import { agentStateEntry } from '@/services/agentState'
import type { AgentStateEntry } from '@/services/agentState'
import { sceneAppProfile } from '@/services/appDetection'
import type { AppProfileDto } from '@/api/appProfiles'
import type { AppIntegration, Scene } from '@/types'

/**
 * True when a scene resolves to a coding-agent profile whose hook state is
 * `ready` — the session is idle and waiting for the user's next prompt.
 *
 * Scene rails use this to flag WHICH scene's agent wants attention while the
 * user is on a different scene (DL-080 follow-up): it reads the hook-driven
 * agent-state map, so it works even with app scanning off — a `ready` state
 * is proof the agent is alive regardless of process detection.
 *
 * A snoozed entry (see `dismissAgentWaiting`) reports false until the agent
 * records a fresh event, so every waiting surface quiets down together and
 * re-arms on the next waiting episode.
 */
export function sceneAgentIsWaiting(
  scene: Pick<Scene, 'id' | 'name' | 'appId' | 'triggeredByApp' | 'pages'>,
  integrations?: readonly AppIntegration[],
): boolean {
  return sceneWaitingAgent(scene, integrations) !== null
}

/** The waiting episode behind a scene, or null when the agent is not
    currently `ready` (or the user snoozed this episode). */
export function sceneWaitingAgent(
  scene: Pick<Scene, 'id' | 'name' | 'appId' | 'triggeredByApp' | 'pages'>,
  integrations?: readonly AppIntegration[],
): { profile: AppProfileDto | null; entry: AgentStateEntry } | null {
  const profile = sceneAppProfile(scene, integrations)
  const source = profile?.status_source
  const entry = agentStateEntry(source)
  if (entry?.state !== 'ready' || isAgentWaitingDismissed(source)) return null
  return { profile, entry }
}

/**
 * Snooze bookkeeping (DL-080 follow-up #2): keying the dismissal on the
 * `ready` entry's `ts` means the alert stays silent for exactly this waiting
 * episode — the backend stamps a fresh `ts` on every hook event, so a new
 * `ready` report (the next episode) re-arms the frame without a reset API.
 */
const dismissedReadyTs = reactive<Record<string, number>>({})

export function dismissAgentWaiting(source: string | null | undefined): void {
  const entry = agentStateEntry(source)
  if (!source || !entry) return
  dismissedReadyTs[source] = entry.ts
}

export function isAgentWaitingDismissed(source: string | null | undefined): boolean {
  const entry = agentStateEntry(source)
  if (!source || !entry || entry.state !== 'ready') return false
  return dismissedReadyTs[source] === entry.ts
}
