import { io, type Socket } from 'socket.io-client'
import type { ActionResult } from '@/types'

class SocketClient {
  private socket: Socket | null = null
  private actionCallbacks: Map<number, (result: ActionResult) => void> = new Map()
  private actionIdCounter = 0

  connect(token: string) {
    const url = import.meta.env.VITE_WS_URL || 'http://localhost:5000'
    
    this.socket = io(url, {
      auth: {
        token
      },
      transports: ['websocket', 'polling']
    })

    this.socket.on('connected', (data) => {
      console.log('Connected to VDock server:', data.message)
    })

    this.socket.on('action_result', (result: ActionResult) => {
      // Find and call the callback for this action
      const callback = this.actionCallbacks.get(this.actionIdCounter - 1)
      if (callback) {
        callback(result)
        this.actionCallbacks.delete(this.actionIdCounter - 1)
      }
    })

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
    })

    this.socket.on('disconnect', () => {
      console.log('Disconnected from VDock server')
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
      this.actionCallbacks.set(actionId, resolve)

      // Send action
      this.socket.emit('execute_action', { action })

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.actionCallbacks.has(actionId)) {
          this.actionCallbacks.delete(actionId)
          reject(new Error('Action execution timeout'))
        }
      }, 30000)
    })
  }

  on(event: string, callback: (...args: any[]) => void) {
    if (this.socket) {
      this.socket.on(event, callback)
    }
  }

  off(event: string, callback?: (...args: any[]) => void) {
    if (this.socket) {
      this.socket.off(event, callback)
    }
  }
}

export default new SocketClient()

