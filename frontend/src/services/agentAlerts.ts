import { reactive, computed } from 'vue'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'

/**
 * "Agent needs you" alerts. The backend broadcasts `agent_alert` over
 * Socket.IO when an agent hook (e.g. the Claude Code Notification hook)
 * reports the agent is waiting for input. A GET on /current re-syncs a
 * freshly loaded or reconnected client so an alert raised while the
 * dashboard was closed still shows.
 */

export interface AgentAlert {
  source: string
  message: string
  project: string
  cwd: string
  ts: number
}

interface AgentAlertState {
  alert: AgentAlert | null
  receivedAt: number | null // wall-clock for "x min ago"
}

const state = reactive<AgentAlertState>({ alert: null, receivedAt: null })
let initialized = false

const SOURCE_LABELS: Record<string, string> = {
  claude: 'Claude Code',
  cursor: 'Cursor',
  devin: 'Devin',
  generic: 'Agent',
}

export function useAgentAlerts() {
  const alert = computed(() => state.alert)
  const sourceLabel = computed(() =>
    state.alert ? SOURCE_LABELS[state.alert.source] || 'Agent' : ''
  )

  function init() {
    if (initialized) return
    initialized = true

    socketClient.on('agent_alert', (payload: { alert: AgentAlert | null }) => {
      state.alert = payload?.alert ?? null
      state.receivedAt = state.alert ? Date.now() : null
    })

    // Pick up an alert raised while we were offline.
    apiClient.get('/agent-events/current')
      .then((res) => {
        if (res.data?.alert) {
          state.alert = res.data.alert
          state.receivedAt = Date.now()
        }
      })
      .catch(() => { /* backend offline — ignore */ })
  }

  async function dismiss() {
    state.alert = null
    state.receivedAt = null
    try {
      await apiClient.delete('/agent-events/current')
    } catch {
      /* best effort — local state already cleared */
    }
  }

  return { alert, sourceLabel, init, dismiss }
}
