import { io, type Socket } from 'socket.io-client'
import type { ActionResult } from '@/types'

type SocketListener = (...args: any[]) => void

class SocketClient {
  private socket: Socket | null = null
  private actionCallbacks: Map<number, {
    resolve: (result: ActionResult) => void
    reject: (error: Error) => void
    timeout: ReturnType<typeof setTimeout>
  }> = new Map()
  private actionIdCounter = 0
  private pendingListeners: Array<{ event: string; callback: SocketListener }> = []

  connect() {
    // The socket lives on the backend port, not necessarily the page's origin:
    // dev serves the app from Vite (:5173/:4444) while the API stays on the
    // backend. Deriving the host from location.hostname is what makes a second
    // device work — a phone loading http://192.168.1.173:5000 must dial that
    // same LAN address, not 127.0.0.1 (which would be the phone itself).
    const backendPort = import.meta.env.VITE_BACKEND_PORT || '5000'
    const url = import.meta.env.VITE_WS_URL
      || `${window.location.protocol}//${window.location.hostname}:${backendPort}`

    this.socket = io(url, {
      transports: ['websocket', 'polling']
    })

    for (const { event, callback } of this.pendingListeners) {
      this.socket.on(event, callback)
    }
    this.pendingListeners = []

    this.socket.on('connected', (data) => {
      console.log('Connected to VDock server:', data.message)
    })

    this.socket.on('action_result', (result: ActionResult & { request_id?: number }) => {
      // Match the result to the action that produced it. Resolving by the
      // latest issued id meant that with two actions in flight the first
      // result settled the second one's promise and the second was dropped.
      const { request_id: requestId, ...actionResult } = result
      if (requestId === undefined) return

      const pending = this.actionCallbacks.get(requestId)
      if (!pending) return

      clearTimeout(pending.timeout)
      this.actionCallbacks.delete(requestId)
      pending.resolve(actionResult as ActionResult)
    })

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
    })

    this.socket.on('disconnect', () => {
      console.log('Disconnected from VDock server')
    })

    this.socket.on('toggle_fullscreen', (data) => {
      console.log('Fullscreen toggle requested:', data)
      this.toggleFullscreen()
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  executeAction(action: any): Promise<ActionResult> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error('Socket not connected'))
        return
      }

      const actionId = this.actionIdCounter++

      // Timeout after 30 seconds
      const timeout = setTimeout(() => {
        if (this.actionCallbacks.has(actionId)) {
          this.actionCallbacks.delete(actionId)
          reject(new Error('Action execution timeout'))
        }
      }, 30000)

      this.actionCallbacks.set(actionId, { resolve, reject, timeout })

      // Send action, tagged so the server can echo the id back
      this.socket.emit('execute_action', { action, request_id: actionId })
    })
  }

  broadcastSettingsChange(settings: Record<string, unknown>) {
    if (this.socket?.connected) {
      this.socket.emit('user_settings_changed', { settings })
    }
  }

  sendUiCommand(command: string) {
    if (this.socket?.connected) {
      this.socket.emit('ui_command', { command })
    }
  }

  on(event: string, callback: SocketListener) {
    if (this.socket) {
      this.socket.on(event, callback)
      return
    }

    this.pendingListeners.push({ event, callback })
  }

  off(event: string, callback?: SocketListener) {
    if (this.socket) {
      this.socket.off(event, callback)
      return
    }

    if (!callback) {
      this.pendingListeners = this.pendingListeners.filter((listener) => listener.event !== event)
      return
    }

    this.pendingListeners = this.pendingListeners.filter(
      (listener) => !(listener.event === event && listener.callback === callback)
    )
  }

  toggleFullscreen() {
    try {
      if (!document.fullscreenElement) {
        // Enter fullscreen
        document.documentElement.requestFullscreen()
      } else {
        // Exit fullscreen
        document.exitFullscreen()
      }
    } catch (error) {
      console.error('Failed to toggle fullscreen:', error)
    }
  }
}

export default new SocketClient()

