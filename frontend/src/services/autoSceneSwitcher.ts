/**
 * Auto Scene Switcher
 * Automatically switches scenes based on active application and integrations
 */

import { appMonitorService } from './appMonitor'
import { appMatchesExe, exeKey } from '@/utils/appExe'
import type { RunningApp, AppIntegration, Profile } from '@/types'

class AutoSceneSwitcher {
  private enabled: boolean = false
  private appIntegrations: AppIntegration[] = []
  private onSceneSwitchCallbacks: Array<(sceneId: string, appExe: string) => void> = []
  private boundHandleAppChange: ((app: RunningApp) => void) | null = null

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

    // Store bound reference so we can remove it later
    this.boundHandleAppChange = this.handleAppChange.bind(this)
    appMonitorService.onAppChange(this.boundHandleAppChange)

    const started = await appMonitorService.start()
    
    if (started) {
      this.enabled = true
      console.warn('Auto scene switching enabled')
    }

    return started
  }

  async disable(): Promise<boolean> {
    if (!this.enabled) {
      return true
    }

    if (this.boundHandleAppChange) {
      appMonitorService.offAppChange(this.boundHandleAppChange)
      this.boundHandleAppChange = null
    }

    const stopped = await appMonitorService.stop()
    
    if (stopped) {
      this.enabled = false
      console.warn('Auto scene switching disabled')
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

    // Find matching integration. The scan list stores process names while
    // the macOS monitor reports bundle names ('Spotify.app') — match on
    // normalized identity, not raw equality (DL-025).
    const integration = this.integrationForApp(app)

    if (integration && integration.sceneId) {
      console.warn(`Switching to scene for app: ${app.exe}`)
      
      this.onSceneSwitchCallbacks.forEach(callback => {
        try {
          callback(integration.sceneId!, app.exe)
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
   * The enabled, scene-linked integration a foreground app belongs to.
   */
  private integrationForApp(app: RunningApp): AppIntegration | undefined {
    return this.appIntegrations.find(
      int => int.enabled && int.sceneId && appMatchesExe(app, int.appExe, int.appName)
    )
  }

  /**
   * Find scene ID for an app
   */
  findSceneForApp(appExe: string): string | null {
    const key = exeKey(appExe)
    const integration = this.appIntegrations.find(
      int => int.enabled && int.sceneId && exeKey(int.appExe) === key && key !== ''
    )

    return integration?.sceneId || null
  }
}

// Export singleton instance
export const autoSceneSwitcher = new AutoSceneSwitcher()

export default autoSceneSwitcher

