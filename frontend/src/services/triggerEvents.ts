import socketClient from '@/api/socket'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'

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

export function initTriggerEvents(): void {
  if (initialized) return
  initialized = true

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
