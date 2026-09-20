/**
 * Cross-window UI commands — one-off "do something in the deck window" signals
 * sent from surfaces like the Settings screen, which may live in a separate
 * window/tab (or even the same tab, where the dashboard is unmounted while
 * settings is open).
 *
 * Delivery uses four paths so the command lands wherever a deck is mounted:
 *
 * 1. A module-level pending queue — same-tab route navigation: the dashboard
 *    unmounts while settings is open, so the command waits for the next
 *    `listenForUiCommands` registration and fires then.
 * 2. A window CustomEvent — same-tab listeners that are mounted right now.
 * 3. BroadcastChannel (+ localStorage storage-event fallback) — other tabs in
 *    this browser, mirroring `useVdockRefresh`.
 * 4. The backend's `ui_command` socket relay — other clients entirely, like a
 *    second Electron window or a LAN-connected panel. The relay is
 *    allowlisted server-side, so only known commands go through.
 */
import socketClient from '@/api/socket'

export type UiCommand = 'show_screensaver' | 'screensaver_layout_edit' | 'toggle_quick_deck'

const UI_COMMAND_CHANNEL = 'vdock-ui-command'
const UI_COMMAND_STORAGE_KEY = 'vdock_ui_command'
const UI_COMMAND_EVENT = 'vdock-ui-command'

const pendingCommands: UiCommand[] = []

export function sendUiCommand(command: UiCommand): void {
  pendingCommands.push(command)

  window.dispatchEvent(new CustomEvent(UI_COMMAND_EVENT, { detail: { command } }))

  if ('BroadcastChannel' in window) {
    const channel = new BroadcastChannel(UI_COMMAND_CHANNEL)
    channel.postMessage({ command })
    channel.close()
  }

  localStorage.setItem(UI_COMMAND_STORAGE_KEY, JSON.stringify({ command, at: Date.now() }))

  socketClient.sendUiCommand(command)
}

/**
 * Registers a handler for UI commands on every delivery path and returns a
 * cleanup function. Commands queued while no listener was registered are
 * delivered immediately — that is what lets a "Test Screensaver" press in
 * settings reach the dashboard after the router remounts it.
 */
export function listenForUiCommands(handler: (command: UiCommand) => void): () => void {
  const handleDomEvent = (event: Event) => {
    const command = (event as CustomEvent).detail?.command
    if (typeof command === 'string') handler(command as UiCommand)
  }
  window.addEventListener(UI_COMMAND_EVENT, handleDomEvent)

  let broadcastChannel: BroadcastChannel | null = null
  if ('BroadcastChannel' in window) {
    broadcastChannel = new BroadcastChannel(UI_COMMAND_CHANNEL)
    broadcastChannel.onmessage = (event) => {
      const command = event.data?.command
      if (typeof command === 'string') handler(command as UiCommand)
    }
  }

  const handleStorageEvent = (event: StorageEvent) => {
    if (event.key !== UI_COMMAND_STORAGE_KEY || !event.newValue) return
    try {
      const command = JSON.parse(event.newValue)?.command
      if (typeof command === 'string') handler(command as UiCommand)
    } catch {
      // Ignore malformed payloads
    }
  }
  window.addEventListener('storage', handleStorageEvent)

  const handleSocketEvent = (data: { command?: string }) => {
    if (typeof data?.command === 'string') handler(data.command as UiCommand)
  }
  socketClient.on('ui_command', handleSocketEvent)

  while (pendingCommands.length) {
    const command = pendingCommands.shift()
    if (command) handler(command)
  }

  return () => {
    window.removeEventListener(UI_COMMAND_EVENT, handleDomEvent)
    window.removeEventListener('storage', handleStorageEvent)
    broadcastChannel?.close()
    socketClient.off('ui_command', handleSocketEvent)
  }
}
