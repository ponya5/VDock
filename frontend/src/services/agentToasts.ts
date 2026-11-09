/**
 * DL-165 - toasts for AI agent state changes, each opted into under Settings -> AI agents -> Notifications:
 * idle (finished, waiting for your prompt), needs permission, started working. Independent of the app-level
 * toast level and of the "agent attention" banner. The first snapshot after load is ignored so opening the deck
 * does not replay the state the agents were already in.
 */
import { watch } from 'vue'
import { agentStates, type AgentStateEntry } from '@/services/agentState'
import { sourceLabelFor } from '@/services/agentAlerts'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'

let started = false

export function describeAgentChange(
  prev: string | undefined, next: string, settings: { agentToastIdle: boolean; agentToastPermission: boolean; agentToastWorking: boolean },
): { type: 'info' | 'warning' | 'success'; verb: string } | null {
  if (prev === next) return null
  if (next === 'ready' && prev === 'working' && settings.agentToastIdle) return { type: 'success', verb: 'finished and is waiting for you' }
  if (next === 'ready' && prev === undefined && settings.agentToastIdle) return null // first sighting, not a transition
  if (next === 'permission' && settings.agentToastPermission) return { type: 'warning', verb: 'needs your permission' }
  if (next === 'working' && prev !== 'working' && prev !== undefined && settings.agentToastWorking) return { type: 'info', verb: 'started working' }
  return null
}

export function startAgentToasts(): void {
  if (started) return
  started = true
  const settings = useSettingsStore()
  const notifications = useNotificationsStore()
  let previous: Record<string, string> | null = null
  const armedAt = Date.now() + 4000

  watch(() => Object.entries(agentStates).map(([source, e]) => [source, (e as AgentStateEntry).state, (e as AgentStateEntry).project] as const), (entries) => {
    const now: Record<string, string> = {}
    for (const [source, state] of entries) now[source] = state
    if (previous !== null && Date.now() >= armedAt) {
      for (const [source, state, project] of entries) {
        const change = describeAgentChange(previous[source], state, settings)
        if (!change) continue
        const name = sourceLabelFor(source)
        notifications.addNotification({
          type: change.type,
          title: `${name}${project ? ' - ' + project : ''}`,
          message: `${name} ${change.verb}.`,
          duration: 6000,
          dismissible: true,
          agent: true,
        })
      }
    }
    previous = now
  }, { deep: true, immediate: true })
}
