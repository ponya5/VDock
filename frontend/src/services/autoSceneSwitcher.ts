/**
 * Auto Scene Switcher
 * Automatically switches scenes based on active application and integrations
 */

import { appMonitorService } from './appMonitor'
import type { RunningApp, AppIntegration, Profile } from '@/types'

class AutoSceneSwitcher {
  private enabled: boolean = false
  private appIntegrations: AppIntegration[] = []
  private onSceneSwitchCallbacks: Array<(sceneId: string, appExe: string) => void> = []

  /**
   * Initialize the auto scene switcher
   */
  initialize(appIntegrations: AppIntegration[]): void {
    this.appIntegrations = appIntegrations
  }

  /**
   * Enable auto scene switching
   */
  async enable(): Promise<boolean> {
    if (this.enabled) {
      return true
    }

    // Register callback for app changes
    appMonitorService.onAppChange(this.handleAppChange.bind(this))

    // Start monitoring
    const started = await appMonitorService.start()
    
    if (started) {
      this.enabled = true
      console.log('Auto scene switching enabled')
    }

    return started
  }

  /**
   * Disable auto scene switching
   */
  async disable(): Promise<boolean> {
    if (!this.enabled) {
      return true
    }

    // Unregister callback
    appMonitorService.offAppChange(this.handleAppChange.bind(this))

    // Stop monitoring
    const stopped = await appMonitorService.stop()
    
    if (stopped) {
      this.enabled = false
      console.log('Auto scene switching disabled')
    }

    return stopped
  }

  /**
   * Check if auto switching is enabled
   */
  isEnabled(): boolean {
    return this.enabled
  }

  /**
   * Update app integrations
   */
  updateIntegrations(appIntegrations: AppIntegration[]): void {
    this.appIntegrations = appIntegrations
  }

  /**
   * Register callback for scene switches
   */
  onSceneSwitch(callback: (sceneId: string, appExe: string) => void): void {
    this.onSceneSwitchCallbacks.push(callback)
  }

  /**
   * Unregister scene switch callback
   */
  offSceneSwitch(callback: (sceneId: string, appExe: string) => void): void {
    const index = this.onSceneSwitchCallbacks.indexOf(callback)
    if (index > -1) {
      this.onSceneSwitchCallbacks.splice(index, 1)
    }
  }

  /**
   * Handle active app change
   */
  private handleAppChange(app: RunningApp): void {
    if (!this.enabled) {
      return
    }

    // Find matching integration
    const integration = this.appIntegrations.find(
      int => int.appExe === app.exe && int.enabled && int.autoSwitch
    )

    if (integration && integration.sceneId) {
      console.log(`Switching to scene for app: ${app.exe}`)
      
      // Trigger callbacks
      this.onSceneSwitchCallbacks.forEach(callback => {
        try {
          callback(integration.sceneId, app.exe)
        } catch (error) {
          console.error('Error in scene switch callback:', error)
        }
      })
    }
  }

  /**
   * Manually check and switch scene based on current app
   */
  async checkAndSwitch(): Promise<void> {
    const currentApp = await appMonitorService.getCurrentActiveApp()
    
    if (currentApp) {
      this.handleAppChange(currentApp)
    }
  }

  /**
   * Find scene ID for an app
   */
  findSceneForApp(appExe: string): string | null {
    const integration = this.appIntegrations.find(
      int => int.appExe === appExe && int.enabled && int.sceneId
    )
    
    return integration?.sceneId || null
  }
}

// Export singleton instance
export const autoSceneSwitcher = new AutoSceneSwitcher()

export default autoSceneSwitcher

