/**
 * App Monitor Service
 * Handles automatic scene switching based on active application
 */

import apiClient from '@/api/client'
import type { RunningApp, AppIntegration } from '@/types'

interface AppMonitorStatus {
  running: boolean
  current_app: RunningApp | null
  poll_interval: number
}

class AppMonitorService {
  private pollingInterval: number | null = null
  private isMonitoring: boolean = false
  private currentApp: RunningApp | null = null
  private onAppChangeCallbacks: Array<(app: RunningApp) => void> = []

  /**
   * Start monitoring the active application
   */
  async start(pollInterval: number = 5000): Promise<boolean> {
    if (this.isMonitoring) {
      console.log('App monitoring already running')
      return true
    }

    try {
      // Start backend monitoring
      await apiClient.post('/app-monitor/start', {
        poll_interval: pollInterval / 1000 // Convert to seconds
      })

      // Start frontend polling to check for app changes
      this.isMonitoring = true
      this.pollingInterval = window.setInterval(
        () => this.checkActiveApp(),
        pollInterval
      )

      console.log('App monitoring started')
      return true
    } catch (error) {
      console.error('Failed to start app monitoring:', error)
      return false
    }
  }

  /**
   * Stop monitoring the active application
   */
  async stop(): Promise<boolean> {
    if (!this.isMonitoring) {
      return true
    }

    try {
      // Stop backend monitoring
      await apiClient.post('/app-monitor/stop')

      // Stop frontend polling
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }

      this.isMonitoring = false
      this.currentApp = null

      console.log('App monitoring stopped')
      return true
    } catch (error) {
      console.error('Failed to stop app monitoring:', error)
      return false
    }
  }

  /**
   * Check if monitoring is active
   */
  isActive(): boolean {
    return this.isMonitoring
  }

  /**
   * Get current active application
   */
  getCurrentApp(): RunningApp | null {
    return this.currentApp
  }

  /**
   * Register a callback for when the active app changes
   */
  onAppChange(callback: (app: RunningApp) => void): void {
    this.onAppChangeCallbacks.push(callback)
  }

  /**
   * Unregister an app change callback
   */
  offAppChange(callback: (app: RunningApp) => void): void {
    const index = this.onAppChangeCallbacks.indexOf(callback)
    if (index > -1) {
      this.onAppChangeCallbacks.splice(index, 1)
    }
  }

  /**
   * Check for active app changes
   */
  private async checkActiveApp(): Promise<void> {
    try {
      const response = await apiClient.get<RunningApp>('/app-monitor/active-app')
      const activeApp = response.data

      // Check if app has changed
      if (!activeApp || !activeApp.exe) {
        return
      }

      const currentExe = this.currentApp?.exe
      const newExe = activeApp.exe

      if (currentExe !== newExe) {
        console.log(`Active app changed: ${currentExe} -> ${newExe}`)
        this.currentApp = activeApp

        // Trigger callbacks
        this.onAppChangeCallbacks.forEach(callback => {
          try {
            callback(activeApp)
          } catch (error) {
            console.error('Error in app change callback:', error)
          }
        })
      }
    } catch (error) {
      // Silently ignore errors (e.g., no active app detected)
      // Only log if it's not a 404
      if (error && typeof error === 'object' && 'response' in error) {
        const err = error as { response?: { status: number } }
        if (err.response?.status !== 404) {
          console.error('Error checking active app:', error)
        }
      }
    }
  }

  /**
   * Get monitoring status from backend
   */
  async getStatus(): Promise<AppMonitorStatus | null> {
    try {
      const response = await apiClient.get<AppMonitorStatus>('/app-monitor/status')
      return response.data
    } catch (error) {
      console.error('Failed to get monitor status:', error)
      return null
    }
  }

  /**
   * Get current active app (one-time check, no monitoring)
   */
  async getCurrentActiveApp(): Promise<RunningApp | null> {
    try {
      const response = await apiClient.get<RunningApp>('/app-monitor/current-app')
      return response.data
    } catch (error) {
      console.error('Failed to get current active app:', error)
      return null
    }
  }
}

// Export singleton instance
export const appMonitorService = new AppMonitorService()

export default appMonitorService

