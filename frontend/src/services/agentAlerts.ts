import { reactive, computed } from 'vue'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import { useNotificationsStore } from '@/stores/notifications'

/**
 * "Agent needs you" alerts. The backend broadcasts `agent_alert` over
 * Socket.IO when an agent hook (e.g. the Claude Code Notification hook)
 * reports the agent is waiting for input. A GET on /current re-syncs a
 * freshly loaded or reconnected client so an alert raised while the
 * dashboard was closed still shows.
 *
 * DL-119: alerts are per-source — `alerts` is the full pending list,
 * newest first, while `alert` stays the newest entry for back-compat.
 * The same feed also drives the persistent AgentWaitingDock chips.
 *
 * The `panel_notification` socket event (W5 triggers / W6 MCP push) is a
 * separate one-shot notice: each one lands in the notification-center
 * history and toast queue via the notifications store.
 */

export interface AgentAlert {
  source: string
  message: string
  project: string
  cwd: string
  ts: number
}

export interface PanelNotification {
  source?: string
  title?: string
  message?: string
  ts?: number
}

interface AgentAlertState {
  alert: AgentAlert | null
  alerts: AgentAlert[]
  receivedAt: number | null // wall-clock for "x min ago"
}

const state = reactive<AgentAlertState>({ alert: null, alerts: [], receivedAt: null })
let initialized = false

const SOURCE_LABELS: Record<string, string> = {
  claude: 'Claude Code',
  cursor: 'Cursor',
  devin: 'Devin',
  antigravity: 'Antigravity',
  generic: 'Agent',
  // panel_notification sources (W5 triggers / W6 MCP) — not agents, but the
  // label is shared for "Source: X" details on notification entries.
  mcp: 'MCP',
  trigger: 'Trigger',
}

export function sourceLabelFor(source: string | null | undefined): string {
  if (!source) return 'Agent'
  return SOURCE_LABELS[source] || source.charAt(0).toUpperCase() + source.slice(1)
}

function applyAlerts(alert: AgentAlert | null, alerts: AgentAlert[] | undefined): void {
  // A pre-DL-119 backend sends only `alert`; treat it as a 1-item list.
  const list = alerts ?? (alert ? [alert] : [])
  state.alerts = [...list].sort((a, b) => (b.ts ?? 0) - (a.ts ?? 0))
  state.alert = alert ?? state.alerts[0] ?? null
  state.receivedAt = state.alert ? Date.now() : null
}

function recordPanelNotification(payload: PanelNotification): void {
  // Lazy: Pinia isn't guaranteed active at module import / socket time in
  // tests or unusual mounts — resolve the store when an event arrives.
  const title = String(payload?.title || 'Notification').slice(0, 80)
  const message = String(payload?.message || '').slice(0, 300)
  try {
    useNotificationsStore().warning(title, message, {
      details: payload?.source ? `Source: ${sourceLabelFor(payload.source)}` : undefined,
    })
  } catch {
    // No active Pinia (edge mounts/tests) — dropping is better than crashing.
  }
}

export function useAgentAlerts() {
  const alert = computed(() => state.alert)
  const alerts = computed(() => state.alerts)
  const sourceLabel = computed(() =>
    state.alert ? sourceLabelFor(state.alert.source) : ''
  )

  function init() {
    if (initialized) return
    initialized = true

    socketClient.on('agent_alert', (payload: { alert?: AgentAlert | null; alerts?: AgentAlert[] }) => {
      applyAlerts(payload?.alert ?? null, payload?.alerts)
    })

    socketClient.on('panel_notification', (payload: PanelNotification) => {
      recordPanelNotification(payload ?? {})
    })

    // Pick up alerts raised while we were offline.
    apiClient.get('/agent-events/current')
      .then((res) => {
        applyAlerts(res.data?.alert ?? null, res.data?.alerts)
      })
      .catch(() => { /* backend offline — ignore */ })
  }

  async function dismiss(source?: string) {
    if (source) {
      state.alerts = state.alerts.filter((a) => a.source !== source)
      state.alert = state.alerts[0] ?? null
      if (!state.alerts.length) state.receivedAt = null
      try {
        await apiClient.delete(`/agent-events/current?source=${encodeURIComponent(source)}`)
      } catch {
        /* best effort — local state already cleared */
      }
      return
    }
    state.alert = null
    state.alerts = []
    state.receivedAt = null
    try {
      await apiClient.delete('/agent-events/current')
    } catch {
      /* best effort — local state already cleared */
    }
  }

  return { alert, alerts, sourceLabel, sourceLabelFor, init, dismiss }
}
