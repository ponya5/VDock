import { computed, onMounted, onUnmounted, ref, watch, type ComputedRef, type Ref } from 'vue'
import type { AppProfileDto } from '@/api/appProfiles'
import {
  fetchAgentSessions,
  identifyAgentSession,
  pinAgentSession,
  type AgentSessionInfo,
} from '@/api/agentSessions'

/** The session marker a profile's commands carry ('claude', 'devin'), if any. */
export function profileSessionMarker(
  profile: AppProfileDto | null | undefined,
): string | null {
  return profile?.commands?.find(command => command.session_marker)?.session_marker ?? null
}

/**
 * Which live agent session the deck's buttons will drive (DL-071).
 *
 * The backend ranks sessions automatically (button cwd → focused editor's
 * project → newest); this composable exposes that list plus the pinned
 * target the user picked in the action bar.
 */
const POLL_MS = 4000

export interface AgentSessionRow extends AgentSessionInfo {
  /** Display label — a `· #pid` suffix is added when sessions collide on
      project/title (several CLIs in the same directory look identical). */
  label: string
}

export interface AgentTargets {
  sessions: Ref<AgentSessionInfo[]>
  sessionRows: ComputedRef<AgentSessionRow[]>
  pinnedPid: Ref<number | null>
  resolvedPid: Ref<number | null>
  /** The session actually receiving keys (pinned, else auto-resolved). */
  effectiveSession: ComputedRef<AgentSessionInfo | null>
  targetLabel: ComputedRef<string>
  refresh: () => Promise<void>
  setTarget: (pid: number | null) => Promise<void>
  /** Flash a session's window so the user can see which terminal it is. */
  identify: (pid: number) => Promise<void>
}

export function useAgentTargets(marker: Ref<string | null>): AgentTargets {
  const sessions = ref<AgentSessionInfo[]>([])
  const pinnedPid = ref<number | null>(null)
  const resolvedPid = ref<number | null>(null)
  let timer: number | undefined

  async function refresh(): Promise<void> {
    if (!marker.value) {
      sessions.value = []
      pinnedPid.value = null
      resolvedPid.value = null
      return
    }
    try {
      const data = await fetchAgentSessions(marker.value)
      sessions.value = data.sessions
      pinnedPid.value = data.pinned_pid
      resolvedPid.value = data.resolved_pid
    } catch {
      // Stale backend or transient failure — keep the last known state.
    }
  }

  async function setTarget(pid: number | null): Promise<void> {
    if (!marker.value) return
    try {
      pinnedPid.value = await pinAgentSession(marker.value, pid)
    } catch {
      return
    }
    await refresh()
  }

  async function identify(pid: number): Promise<void> {
    if (!marker.value) return
    try {
      await identifyAgentSession(marker.value, pid)
    } catch {
      // Cosmetic affordance — a failed flash doesn't affect the pick.
    }
  }

  onMounted(() => {
    void refresh()
    timer = window.setInterval(() => void refresh(), POLL_MS)
  })
  onUnmounted(() => {
    if (timer) window.clearInterval(timer)
  })
  watch(marker, () => void refresh())

  const sessionRows = computed<AgentSessionRow[]>(() => {
    const base = (s: AgentSessionInfo) => s.project || s.title || `pid ${s.pid}`
    const counts = new Map<string, number>()
    for (const s of sessions.value) {
      const label = base(s)
      counts.set(label, (counts.get(label) ?? 0) + 1)
    }
    return sessions.value.map(s => {
      const label = base(s)
      return { ...s, label: (counts.get(label) ?? 0) > 1 ? `${label} · #${s.pid}` : label }
    })
  })

  const effectiveSession = computed(() => {
    const pid = pinnedPid.value ?? resolvedPid.value
    return sessionRows.value.find(s => s.pid === pid) ?? null
  })

  const targetLabel = computed(() => {
    if (!sessions.value.length) return 'No session'
    const name = effectiveSession.value?.label || 'session'
    return pinnedPid.value !== null ? name : `Auto · ${name}`
  })

  return {
    sessions,
    sessionRows,
    pinnedPid,
    resolvedPid,
    effectiveSession,
    targetLabel,
    refresh,
    setTarget,
    identify,
  }
}
