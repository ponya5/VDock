import { reactive } from 'vue'

/**
 * Whether the deck can currently hear the PC (DL-147).
 *
 * socket.io reconnects by itself; this only turns "the socket is down" into
 * something the UI can show. A drop shorter than RECONNECTING_AFTER_MS never
 * surfaces (page loads and quick blips stay silent), and past OFFLINE_AFTER_MS
 * the banner stops promising a reconnect and asks whether the PC is awake.
 */
export type ConnectionStatus = 'connected' | 'reconnecting' | 'offline'

export const RECONNECTING_AFTER_MS = 2000
export const OFFLINE_AFTER_MS = 15000

export const connection = reactive<{ status: ConnectionStatus }>({ status: 'connected' })

let down = false
let reconnectingTimer: ReturnType<typeof setTimeout> | null = null
let offlineTimer: ReturnType<typeof setTimeout> | null = null

function clearTimers() {
  if (reconnectingTimer) clearTimeout(reconnectingTimer)
  if (offlineTimer) clearTimeout(offlineTimer)
  reconnectingTimer = null
  offlineTimer = null
}

/** The socket dropped or a connect attempt failed. Repeats keep the original clock. */
export function markDisconnected() {
  if (down) return
  down = true
  reconnectingTimer = setTimeout(() => { connection.status = 'reconnecting' }, RECONNECTING_AFTER_MS)
  offlineTimer = setTimeout(() => { connection.status = 'offline' }, OFFLINE_AFTER_MS)
}

export function markConnected() {
  down = false
  clearTimers()
  connection.status = 'connected'
}
