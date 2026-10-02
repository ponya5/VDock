import socketClient from '@/api/socket'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useSettingsStore } from '@/stores/settings'

/**
 * Server-pushed deck events: triggers (DL-120) and MCP tools (DL-121) act on
 * the panel by emitting socket events rather than going through a client.
 *
 *  - `navigate_scene {scene}` — a trigger or MCP `switch_scene` resolved
 *    server-side asks this client to show that scene. Scene names are matched
 *    case-insensitively against the active profile, the same way the
 *    `switch_scene` button action does it.
 *  - `trigger_fired {id,label,ok,detail}` — surfaces automation runs in the
 *    notification history; failures use the error channel so they pierce the
 *    default errors-only toast level.
 *  - `vdock:navigate-scene` CustomEvent {source} — fired by the agent-waiting
 *    dock (DL-119) when the user taps a waiting agent's chip; we route it to
 *    that agent's scene by substring-matching the source against scene names
 *    ("claude" → "Claude Code", "cursor" → "Cursor").
 */

const NAVIGATE_SCENE_EVENT = 'vdock:navigate-scene'

let initialized = false

function sceneIndexByName(name: string): number {
  const wanted = name.trim().toLowerCase()
  const scenes = useDashboardStore().currentProfile?.scenes ?? []
  return scenes.findIndex(s => s.name.trim().toLowerCase() === wanted)
}

function navigateToScene(name: string) {
  const idx = sceneIndexByName(name)
  if (idx >= 0) useDashboardStore().setScene(idx)
}

function navigateToAgentScene(source: string) {
  const needle = source.trim().toLowerCase()
  if (!needle) return
  const scenes = useDashboardStore().currentProfile?.scenes ?? []
  const idx = scenes.findIndex(s => s.name.trim().toLowerCase().includes(needle))
  if (idx >= 0) useDashboardStore().setScene(idx)
}

// Sources that were waiting on the user as of the last `agent_state`
// broadcast. "Waiting" mirrors the glow/pill: a prompted session that went
// idle (`ready`) or is blocked on a permission dialog. Only a source that
// newly starts waiting pulls focus, so later broadcasts (another agent's
// events, TTL pruning) never yank the user back to a scene they just left.
let waitingSources = new Set<string>()
// The first broadcast after load only records who is already waiting.
let statePrimed = false

function isWaiting(entry: { state?: string; prompted?: boolean } | undefined): boolean {
  return !!entry && (entry.state === 'permission' || (entry.state === 'ready' && entry.prompted === true))
}

function focusNewlyWaitingAgents(states: Record<string, { state?: string; prompted?: boolean }> | undefined): void {
  const current = new Set(Object.keys(states ?? {}).filter(source => isWaiting(states?.[source])))
  const fresh = [...current].filter(source => !waitingSources.has(source))
  waitingSources = current
  if (!statePrimed) { statePrimed = true; return }
  if (!fresh.length) return
  const settings = useSettingsStore()
  if (settings.agentAlertsEnabled === false || settings.agentAutoFocusScene === false) return
  // Don't pull the scene out from under an edit session.
  if (useDashboardStore().isEditMode) return
  navigateToAgentScene(fresh[0])
}

export function initTriggerEvents(): void {
  if (initialized) return
  initialized = true

  socketClient.on('agent_state', (payload: { states?: Record<string, { state?: string; prompted?: boolean }> }) => {
    focusNewlyWaitingAgents(payload?.states)
  })

  socketClient.on('navigate_scene', (payload: { scene?: string }) => {
    if (typeof payload?.scene === 'string') navigateToScene(payload.scene)
  })

  socketClient.on('trigger_fired', (payload: {
    label?: string
    ok?: boolean
    detail?: string
  }) => {
    const notifications = useNotificationsStore()
    const label = payload?.label || 'Trigger'
    if (payload?.ok === false) {
      notifications.error('Trigger failed', label, payload.detail || undefined)
    } else {
      // Success entries keep the bell history honest without popping a toast
      // past the errors-only default level.
      notifications.info('Trigger fired', label)
    }
  })

  window.addEventListener(NAVIGATE_SCENE_EVENT, (event: Event) => {
    const source = (event as CustomEvent).detail?.source
    if (typeof source === 'string') navigateToAgentScene(source)
  })
}
