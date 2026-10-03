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
 *
 * A `ready` state only counts once the session was actually prompted
 * (DL-105): a freshly launched agent is idle too, but nothing was ever
 * asked of it — no alert.
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
  if (entry?.state !== 'ready' || !entry.prompted || isAgentWaitingDismissed(source)) return null
  return { profile, entry }
}

/**
 * Sources whose idle state the bottom "waiting" chip already owns — waiting,
 * snoozed or dismissed. The "needs you" banner stands down for these so one
 * idle event is not announced twice (permission asks are a different state
 * and still get the banner).
 */
export function waitingChipSources(
  scenes: readonly Pick<Scene, 'id' | 'name' | 'appId' | 'triggeredByApp' | 'pages'>[],
  integrations?: readonly AppIntegration[],
): Set<string> {
  const sources = new Set<string>()
  for (const scene of scenes) {
    const hit = sceneWaitingAgent(scene, integrations) ?? sceneSnoozedAgent(scene, integrations)
    if (hit) sources.add(hit.entry.source)
  }
  return sources
}

/**
 * Snooze bookkeeping (DL-080 follow-ups #2/#3): each dismissal records the
 * `ready` entry's `ts` plus an expiry. Same-episode + inside the window =
 * silenced; a fresh `ready` event stamps a new `entry.ts` and re-arms the
 * frame without a reset API; after `SNOOZE_MS` the timer deletes the record
 * (reactive deletion re-runs the computeds — `Date.now()` itself can't) so
 * a still-idle session alerts again.
 */
export const AGENT_SNOOZE_MS = 3 * 60 * 1000

const dismissedReadyTs = reactive<Record<string, { ts: number; until: number }>>({})
const snoozeTimers = new Map<string, ReturnType<typeof setTimeout>>()

/**
 * Silence this waiting episode. Default is the time-boxed snooze; pass
 * `Infinity` for a full dismiss — no timer, quiet until the agent records a
 * fresh `ready` event (the next idle), which stamps a new `entry.ts`.
 */
export function dismissAgentWaiting(
  source: string | null | undefined,
  durationMs: number = AGENT_SNOOZE_MS,
): void {
  const entry = agentStateEntry(source)
  if (!source || !entry) return
  clearTimeout(snoozeTimers.get(source))
  snoozeTimers.delete(source)
  dismissedReadyTs[source] = { ts: entry.ts, until: Date.now() + durationMs }
  if (!Number.isFinite(durationMs)) return
  snoozeTimers.set(source, setTimeout(() => {
    const d = dismissedReadyTs[source]
    if (d && d.until <= Date.now()) delete dismissedReadyTs[source]
  }, durationMs + 250))
}

/** End a snooze early: the next read sees the agent as waiting again. */
export function resumeAgentWaiting(source: string | null | undefined): void {
  if (!source) return
  clearTimeout(snoozeTimers.get(source))
  snoozeTimers.delete(source)
  delete dismissedReadyTs[source]
}

/** ms left on this source's active snooze (Infinity for a full dismiss), or 0
    when it isn't snoozed. */
export function agentSnoozeRemainingMs(source: string | null | undefined): number {
  if (!isAgentWaitingDismissed(source)) return 0
  return Math.max(0, dismissedReadyTs[source as string].until - Date.now())
}

/** The mirror of `sceneWaitingAgent`: a prompted `ready` agent the user has
    snoozed — what the "Resume" chip is shown for. */
export function sceneSnoozedAgent(
  scene: Pick<Scene, 'id' | 'name' | 'appId' | 'triggeredByApp' | 'pages'>,
  integrations?: readonly AppIntegration[],
): { profile: AppProfileDto | null; entry: AgentStateEntry } | null {
  const profile = sceneAppProfile(scene, integrations)
  const source = profile?.status_source
  const entry = agentStateEntry(source)
  if (entry?.state !== 'ready' || !entry.prompted || !isAgentWaitingDismissed(source)) return null
  return { profile, entry }
}

export function isAgentWaitingDismissed(source: string | null | undefined): boolean {
  const entry = agentStateEntry(source)
  if (!source || !entry || entry.state !== 'ready') return false
  const d = dismissedReadyTs[source]
  return !!d && d.ts === entry.ts && Date.now() < d.until
}
