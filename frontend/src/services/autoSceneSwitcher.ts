/**
 * Auto Scene Switcher
 * Automatically switches scenes based on active application and integrations
 */

import { appMonitorService } from './appMonitor'
import { appMatchesExe, exeKey } from '@/utils/appExe'
import { fetchAgentSessions } from '@/api/agentSessions'
import type { RunningApp, AppIntegration, Profile } from '@/types'

/** How often to re-check for a Claude session while Cursor stays in front. */
const AGENT_POLL_MS = 3000

class AutoSceneSwitcher {
  private enabled: boolean = false
  private appIntegrations: AppIntegration[] = []
  private onSceneSwitchCallbacks: Array<(sceneId: string, appExe: string) => void> = []
  private boundHandleAppChange: ((app: RunningApp) => void) | null = null
  // DL-159: Claude CLI inside Cursor → Claude scene. Resolver + switch live in
  // App.vue/settings so this stays free of store imports.
  private claudeSceneId: (() => string | null) | null = null
  private claudeAware: () => boolean = () => true
  private agentTimer: ReturnType<typeof setInterval> | null = null
  private agentApp: RunningApp | null = null
  private lastEmitted: string | null = null

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

    this.stopAgentWatch()
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
   * DL-159: where the Claude scene is, and whether the user wants the
   * "Claude running in Cursor → Claude scene" rule at all.
   */
  setClaudeSceneSource(sceneId: () => string | null, enabled: () => boolean): void {
    this.claudeSceneId = sceneId
    this.claudeAware = enabled
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

    if (!integration || !integration.sceneId) {
      this.stopAgentWatch()
      return
    }
    const appScene = integration.sceneId

    // DL-159: Cursor in front + a Claude scene to jump to → decide once
    // Claude's state is known (one request), then keep watching while Cursor
    // stays in front. Everything else switches immediately, as before.
    if (this.isCursor(app) && this.claudeAware() && this.claudeSceneId?.()) {
      this.startAgentWatch(app, appScene)
      void this.resolveScene(app, appScene).then(sceneId => {
        if (this.agentApp !== app) return // focus moved on while resolving
        this.lastEmitted = sceneId
        this.emitSwitch(sceneId, app)
      })
      return
    }
    this.stopAgentWatch()
    this.emitSwitch(appScene, app)
  }

  private emitSwitch(sceneId: string, app: RunningApp): void {
    console.warn(`Switching to scene for app: ${app.exe}`)
    this.onSceneSwitchCallbacks.forEach(callback => {
      try {
        callback(sceneId, app.exe)
      } catch (error) {
        console.error('Error in scene switch callback:', error)
      }
    })
  }

  private isCursor(app: RunningApp): boolean {
    return exeKey(app.exe) === 'cursor'
  }

  /**
   * True when a Claude CLI session hosted by Cursor is active: working, on a
   * permission ask, or idle after a prompt (same "waiting" meaning as the
   * agent alerts, DL-105). Any failure → false (fall back to the Cursor scene).
   */
  private async claudeActiveInCursor(): Promise<boolean> {
    try {
      const { sessions } = await fetchAgentSessions('claude')
      return sessions.some(sess =>
        /cursor/i.test(sess.host ?? '') &&
        (sess.state === 'working' || sess.state === 'permission' ||
          (sess.state === 'ready' && sess.prompted === true)))
    } catch {
      return false
    }
  }

  /** The Claude scene when Claude is live in Cursor, else Cursor's own scene. */
  private async resolveScene(_app: RunningApp, appScene: string): Promise<string> {
    const claudeScene = this.claudeSceneId?.() ?? null
    return claudeScene && await this.claudeActiveInCursor() ? claudeScene : appScene
  }

  private startAgentWatch(app: RunningApp, appScene: string): void {
    this.stopAgentWatch()
    this.agentApp = app
    this.agentTimer = setInterval(() => { void this.pollAgent(app, appScene) }, AGENT_POLL_MS)
  }

  /** Emit only when Claude appears/disappears, so a manual pick isn't undone. */
  private async pollAgent(app: RunningApp, appScene: string): Promise<void> {
    if (!this.enabled || !this.claudeAware()) return this.stopAgentWatch()
    const sceneId = await this.resolveScene(app, appScene)
    if (this.agentApp !== app || sceneId === this.lastEmitted) return
    this.lastEmitted = sceneId
    this.emitSwitch(sceneId, app)
  }

  private stopAgentWatch(): void {
    if (this.agentTimer) clearInterval(this.agentTimer)
    this.agentTimer = null
    this.agentApp = null
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

