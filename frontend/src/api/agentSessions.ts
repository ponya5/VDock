import apiClient from '@/api/client'

/**
 * Live terminal-agent sessions (DL-071): one row per running CLI session that
 * owns a window, plus the pinned deck target and which session a button press
 * would hit right now.
 */
export interface AgentSessionInfo {
  pid: number
  hwnd: number
  title: string
  cwd: string | null
  project: string
  /** Hook-reported state ('ready' | 'working' | 'permission') or null. */
  state: string | null
  /** Hook detail — the current task or last prompt, when reported. */
  detail: string
  /** Unix start time of the session process, or null. */
  started: number | null
}

export interface AgentSessionsResponse {
  sessions: AgentSessionInfo[]
  pinned_pid: number | null
  resolved_pid: number | null
}

export async function fetchAgentSessions(source: string): Promise<AgentSessionsResponse> {
  // apiClient.get's second arg IS the params object (it wraps it into axios
  // config itself) — passing `{ params: … }` here double-wraps and the
  // backend receives `params[source]` instead of `source` → 400.
  const { data } = await apiClient.get('/agent-sessions', { source })
  return {
    sessions: data.sessions ?? [],
    pinned_pid: data.pinned_pid ?? null,
    resolved_pid: data.resolved_pid ?? null,
  }
}

/** Pin a target session (pid), or pass null to return to auto resolution. */
export async function pinAgentSession(source: string, pid: number | null): Promise<number | null> {
  const { data } = await apiClient.post('/agent-sessions/target', { source, pid })
  return data.pinned_pid ?? null
}

/**
 * Flash a session's host window — "which terminal is this row". Cosmetic
 * best-effort: the call failing just means no flash, not a broken pick.
 */
export async function identifyAgentSession(source: string, pid: number): Promise<void> {
  await apiClient.post('/agent-sessions/identify', { source, pid })
}
