/**
 * App Detection — live "is this scene's app running" state.
 *
 * Polls /api/app-monitor/detected-profiles on an interval and exposes two
 * reactive sets: `detectedProfiles` (app-profile ids whose process is up —
 * terminal agents matched by session marker, editors by exe) and
 * `runningExes` (all running process names, for custom integrations that
 * point at arbitrary exes).
 *
 * Scene → app resolution, most specific first:
 *   1. `scene.appId` (stamped by template adds / auto-create)
 *   2. button command ids — a scene whose buttons invoke `cc_prompt`,
 *      `cursor_chat`, … belongs to the profile that owns those commands.
 *      This is the strongest signal on real profiles: saved scenes rarely
 *      carry app metadata, but their buttons always carry command ids.
 *   3. `triggeredByApp` / integration exe → profile id via /api/app-profiles.
 *      Host terminal exes must resolve through the marker-verified profile,
 *      never the running-exe list (an open cmd.exe is not a Claude session).
 *   4. unknown custom exe → raw running-exe check.
 *
 * Module-level singleton: one poller no matter how many consumers.
 */
import { ref, shallowRef, type Ref } from 'vue'
import apiClient from '@/api/client'
import type { AppProfileDto } from '@/api/appProfiles'
import type { Scene, AppIntegration } from '@/types'

const detectedProfiles: Ref<Set<string>> = ref(new Set())
const runningExes: Ref<Set<string>> = ref(new Set())
/** Full profile DTOs by id — reactive so consumers re-render once loaded. */
const profilesById = shallowRef<Map<string, AppProfileDto>>(new Map())

/** exe (lowercase) → profile id, command id → profile id — built from
 * /api/app-profiles. Last write wins, same rule the backend uses for shared
 * host exes. */
const profileIdByExe = new Map<string, string>()
const profileIdByCommand = new Map<string, string>()

let timer: number | null = null
let inflight = false
let profilesLoaded = false

const POLL_MS = 10_000

/** Load /api/app-profiles once. Detection polling calls it too; consumers
 * that need profiles while scanning is off (the agent bar) call it directly. */
export async function loadProfileMaps(): Promise<void> {
  if (profilesLoaded) return
  try {
    const res = await apiClient.get('/app-profiles')
    const loadedProfiles: AppProfileDto[] = res?.data?.profiles ?? []
    profilesById.value = new Map(loadedProfiles.map(profile => [profile.id, profile]))
    for (const p of loadedProfiles) {
      for (const exe of p.exes ?? []) {
        profileIdByExe.set(String(exe).toLowerCase(), p.id)
      }
      for (const cmd of p.commands ?? []) {
        if (cmd?.id) profileIdByCommand.set(String(cmd.id), p.id)
      }
      // Plugin action types the profile owns (e.g. claude_pack's
      // claude_prompt) vote for the profile exactly like command ids.
      for (const t of p.action_types ?? []) {
        profileIdByCommand.set(String(t), p.id)
      }
    }
    profilesLoaded = true
  } catch {
    // Profiles are static in practice — retry on next poll tick.
  }
}

async function poll(): Promise<void> {
  if (inflight) return
  inflight = true
  try {
    await loadProfileMaps()
    const res = await apiClient.get('/app-monitor/detected-profiles')
    const data = res?.data ?? {}
    detectedProfiles.value = new Set(data.detected_profiles ?? [])
    runningExes.value = new Set(data.running_exes ?? [])
  } catch {
    // Backend unreachable (Electron restart, dev without backend) — keep the
    // last known state rather than blanking every indicator.
  } finally {
    inflight = false
  }
}

/** Start polling. Idempotent — safe to call from multiple mounts. */
export function startAppDetection(): void {
  if (timer !== null) return
  poll()
  timer = window.setInterval(poll, POLL_MS)
}

export function stopAppDetection(): void {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
  // Clearing the sets flips every sceneAppIsLive result to false — the dots
  // disappear the moment scanning is disabled rather than lingering stale.
  detectedProfiles.value = new Set()
  runningExes.value = new Set()
}

/** Profile owning the most command-typed button actions in the scene. */
function profileIdBySceneCommands(
  scene: Pick<Scene, 'pages'>,
): string | null {
  const votes = new Map<string, number>()
  for (const page of scene.pages ?? []) {
    for (const button of page.buttons ?? []) {
      const pid = button.action?.type
        ? profileIdByCommand.get(button.action.type)
        : undefined
      if (pid) votes.set(pid, (votes.get(pid) ?? 0) + 1)
    }
  }
  let best: string | null = null
  let bestVotes = 0
  for (const [pid, n] of votes) {
    if (n > bestVotes) {
      best = pid
      bestVotes = n
    }
  }
  return best
}

type SceneLink = Pick<Scene, 'id' | 'appId' | 'triggeredByApp' | 'pages'>

function sceneExe(scene: SceneLink, integrations?: readonly AppIntegration[]): string | null {
  const integ = integrations?.find(i => i.sceneId === scene.id && i.enabled)
  const exe = scene.triggeredByApp ?? integ?.appExe
  return exe ? exe.toLowerCase() : null
}

/** The app-profile id a scene belongs to, or null (see resolution order above). */
function resolveSceneProfileId(
  scene: SceneLink,
  integrations?: readonly AppIntegration[],
): string | null {
  if (scene.appId) return scene.appId
  const commandProfile = profileIdBySceneCommands(scene)
  if (commandProfile) return commandProfile
  const exe = sceneExe(scene, integrations)
  return exe ? profileIdByExe.get(exe) ?? null : null
}

/** The app's live state for a scene, or false when it isn't app-linked. */
export function sceneAppIsLive(
  scene: SceneLink,
  integrations?: readonly AppIntegration[],
): boolean {
  // Read both refs unconditionally — an early return before a `.value` read
  // leaves the calling render with no dependency on poll results, and the
  // dot would never appear once detection resolves.
  const detected = detectedProfiles.value
  const running = runningExes.value

  const profileId = resolveSceneProfileId(scene, integrations)
  // Known app → trust the marker/exe-verified profile detection. Unknown
  // exe (custom integration, e.g. spotify.exe) → raw running check.
  if (profileId) return detected.has(profileId)
  const exe = sceneExe(scene, integrations)
  return exe ? running.has(exe) : false
}

/** The full app profile a scene belongs to, once profiles have loaded. */
export function sceneAppProfile(
  scene: SceneLink,
  integrations?: readonly AppIntegration[],
): AppProfileDto | null {
  const profiles = profilesById.value
  const profileId = resolveSceneProfileId(scene, integrations)
  return profileId ? profiles.get(profileId) ?? null : null
}

export { detectedProfiles, runningExes }
