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
  /** Display label — see `buildSessionRows` (project, host, #ordinal). */
  label: string
  /** Per-session accent color — same pid → same color, distinct within
      the live set. Painted as the row badge / chip edge. */
  accent: string
  /** Two-letter host badge ('WT', 'CU', 'PS') — '' when host unknown. */
  badge: string
}

/** Palette slot assignment is stable when sessions come and go: slots
    are claimed oldest-first so a newcomer probes around incumbents
    instead of evicting them. */
const ACCENT_PALETTE = [
  '#7aa2ff', '#63d0a3', '#f5a962', '#e587d6', '#9f8bff',
  '#5ec8e5', '#d9c04f', '#ff8a8a', '#9cd05c', '#f08cd0',
]

/**
 * Two-letter badge for the host name — 'Windows Terminal' → 'WT',
 * 'PowerShell' → 'PS', 'Cursor' → 'CU'. Uppercase letters win; a plain
 * word falls back to its first two letters.
 */
export function hostBadge(host: string | null | undefined): string {
  if (!host) return ''
  const caps = host.replace(/[^A-Z]/g, '')
  if (caps.length >= 2) return caps.slice(0, 2)
  const words = host.split(/\s+/).filter(Boolean)
  if (words.length >= 2) {
    return words.slice(0, 2).map(w => w[0].toUpperCase()).join('')
  }
  return host.slice(0, 2).toUpperCase()
}

/**
 * Compose a human-readable label per live session (DL-071 follow-up 11).
 *
 *  - Base: `project` (cwd basename), else window title, else `pid N`.
 *  - Same base on different directories → the two-segment cwd tail
 *    (`VDock2/backend` vs `other/backend`) so projects tell apart.
 *  - Still-identical labels (several CLIs in one directory) → ` #1`,
 *    ` #2` by start order — stable across polls, unlike raw pids.
 *  - `· {host}` appended when the backend names the window owner:
 *    `backend · Cursor` vs `backend · Windows Terminal` says which
 *    surface the session lives in.
 */
export function buildSessionRows(sessions: AgentSessionInfo[]): AgentSessionRow[] {
  const base = (s: AgentSessionInfo) => s.project || s.title || `pid ${s.pid}`
  const cwdTail = (cwd: string | null) => {
    const parts = (cwd || '').split(/[\\/]+/).filter(Boolean)
    return parts.slice(-2).join('/')
  }

  // Pass 1: group sessions by base label; when a base covers more than
  // one directory, upgrade each member to its two-segment cwd tail.
  const groups = new Map<string, AgentSessionInfo[]>()
  for (const s of sessions) {
    const b = base(s)
    groups.set(b, [...(groups.get(b) ?? []), s])
  }
  const preLabel = new Map<number, string>()
  for (const [b, members] of groups) {
    const cwds = new Set(members.map(m => (m.cwd || '').toLowerCase()))
    for (const s of members) {
      preLabel.set(s.pid, cwds.size > 1 && s.cwd ? cwdTail(s.cwd) : b)
    }
  }

  // Pass 2: identical resolved labels get ` #n` ordinals, oldest first.
  const byLabel = new Map<string, AgentSessionInfo[]>()
  for (const s of sessions) {
    const l = preLabel.get(s.pid) ?? base(s)
    byLabel.set(l, [...(byLabel.get(l) ?? []), s])
  }
  const labels = new Map<number, string>()
  for (const [l, members] of byLabel) {
    members
      .slice()
      .sort((a, b) => (a.started ?? 0) - (b.started ?? 0))
      .forEach((s, i) => {
        const numbered = members.length > 1 ? `${l} #${i + 1}` : l
        labels.set(s.pid, s.host ? `${numbered} · ${s.host}` : numbered)
      })
  }

  // Accent assignment, oldest session first: a session's color survives
  // siblings joining/leaving — a newcomer probes around taken slots.
  const taken = new Set<number>()
  const accents = new Map<number, string>()
  const byAge = sessions.slice().sort((a, b) => (a.started ?? 0) - (b.started ?? 0))
  for (const s of byAge) {
    const n = ACCENT_PALETTE.length
    let slot = ((s.pid % n) + n) % n
    while (taken.has(slot)) slot = (slot + 1) % n
    taken.add(slot)
    accents.set(s.pid, ACCENT_PALETTE[slot])
  }

  return sessions.map(s => ({
    ...s,
    label: labels.get(s.pid) ?? base(s),
    accent: accents.get(s.pid) ?? ACCENT_PALETTE[0],
    badge: hostBadge(s.host),
  }))
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

  const sessionRows = computed<AgentSessionRow[]>(() => buildSessionRows(sessions.value))

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
