import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { ServerConfig } from '@/types'
import apiClient from '@/api/client'
import socketClient from '@/api/socket'

const SETTINGS_STORAGE_KEY = 'vdock_settings'
const SETTINGS_BROADCAST_CHANNEL = 'vdock-settings-sync'
const SERVER_SYNC_DELAY_MS = 400

export interface PersistedUserSettings {
  buttonSize: number
  showLabels: boolean
  showTooltips: boolean
  animationsEnabled: boolean
  tiltEffectEnabled: boolean
  dockedSidebarEnabled: boolean
  dockedSidebarWidth: number
  dashboardBackground: string
  backgroundPreference: string
  uiBrightness: number
  toastLevel: 'all' | 'errors-only' | 'off'
  touchMode: 'normal' | 'touch-friendly' | 'tablet'
  minimumTouchTargetSize: number
  defaultGridRows: number
  defaultGridCols: number
  startOnBoot: boolean
  openSettingsInNewTab: boolean
  recentActions: string[]
  weatherLocationMode: 'auto' | 'manual'
  weatherManualCity: string
  screensaverTimeout: number
  autoCloseLauncher: boolean
}

export const useSettingsStore = defineStore('settings', () => {
  const currentTheme = ref('dark')
  const serverConfig = ref<ServerConfig | null>(null)
  
  const windowPinned = ref(false)
  const windowPosition = ref<{ x: number; y: number } | null>(null)
  const windowDocked = ref<'none' | 'left' | 'right' | 'top' | 'bottom'>('none')
  const alwaysOnTop = ref(false)
  
  const buttonSize = ref(1.0)
  const showLabels = ref(true)
  const showTooltips = ref(true)
  const animationsEnabled = ref(true)
  const tiltEffectEnabled = ref(true)
  const dockedSidebarEnabled = ref(true)
  const dockedSidebarWidth = ref(190)
  const dashboardBackground = ref('default')
  const backgroundPreference = ref<'none' | 'particles' | 'waves' | 'lightning' | 'light-pillar' | 'floating-lines-wave' | 'prismatic-burst' | 'iridescence' | 'silk' | 'light-rays' | 'aurora'>('none')
  const uiBrightness = ref(100)
  // Ephemeral UI state (not persisted/synced): whether the auto-hiding header
  // is currently shown. Each window/tab manages its own header visibility
  // independently — this must never be part of the cross-window settings sync
  // or server persistence, otherwise one window's auto-hide timer would force
  // the header closed (and unable to reopen) in every other connected window.
  const showHeader = ref(true)
  const toastLevel = ref<'all' | 'errors-only' | 'off'>('all')
  
  const touchMode = ref<'normal' | 'touch-friendly' | 'tablet'>('normal')
  const minimumTouchTargetSize = ref(44)
  const touchModeMultiplier = computed(() => {
    switch (touchMode.value) {
      case 'normal':
        return 1.0
      case 'touch-friendly':
        return 1.5
      case 'tablet':
        return 2.0
      default:
        return 1.0
    }
  })
  
  const defaultGridRows = ref(3)
  const defaultGridCols = ref(3)

  const startOnBoot = ref(false)
  const openSettingsInNewTab = ref(false)
  const autoCloseLauncher = ref(true)

  const recentActions = ref<string[]>([])
  const maxRecentActions = 10

  const weatherLocationMode = ref<'auto' | 'manual'>('auto')
  const weatherManualCity = ref('')
  const screensaverTimeout = ref(120)

  const showHelpGuide = ref(false)

  let serverSyncTimer: ReturnType<typeof setTimeout> | null = null
  let serverSyncInFlight = false
  let isApplyingRemoteSettings = false
  let liveSyncInitialized = false
  let settingsBroadcastChannel: BroadcastChannel | null = null

  function settingsPayloadEquals(
    left: Partial<PersistedUserSettings>,
    right: Partial<PersistedUserSettings>
  ): boolean {
    return JSON.stringify(left) === JSON.stringify(right)
  }

  function applySettingsFromRemote(remoteSettings: Partial<PersistedUserSettings>) {
    const currentSettings = buildSettingsPayload()
    if (settingsPayloadEquals(currentSettings, remoteSettings)) {
      return
    }

    isApplyingRemoteSettings = true
    try {
      applySettingsObject(remoteSettings)
      saveSettingsLocalOnly()
      applyTouchModeStyles()
      applyUIBrightnessFilter()
    } finally {
      isApplyingRemoteSettings = false
    }
  }

  function broadcastSettingsToOtherWindows() {
    const payload = buildSettingsPayload()
    settingsBroadcastChannel?.postMessage(payload)
    socketClient.broadcastSettingsChange(payload)
  }

  function buildSettingsPayload(): PersistedUserSettings {
    return {
      buttonSize: buttonSize.value,
      showLabels: showLabels.value,
      showTooltips: showTooltips.value,
      animationsEnabled: animationsEnabled.value,
      tiltEffectEnabled: tiltEffectEnabled.value,
      dockedSidebarEnabled: dockedSidebarEnabled.value,
      dockedSidebarWidth: dockedSidebarWidth.value,
      dashboardBackground: dashboardBackground.value,
      backgroundPreference: backgroundPreference.value,
      uiBrightness: uiBrightness.value,
      toastLevel: toastLevel.value,
      touchMode: touchMode.value,
      minimumTouchTargetSize: minimumTouchTargetSize.value,
      defaultGridRows: defaultGridRows.value,
      defaultGridCols: defaultGridCols.value,
      startOnBoot: startOnBoot.value,
      openSettingsInNewTab: openSettingsInNewTab.value,
      autoCloseLauncher: autoCloseLauncher.value,
      // Spread into a plain array: `recentActions.value` is a Vue-reactive
      // Proxy, which the structured clone algorithm used by
      // BroadcastChannel.postMessage() cannot clone (throws DataCloneError)
      // even when empty. This payload is broadcast on every settings change.
      recentActions: [...recentActions.value],
      weatherLocationMode: weatherLocationMode.value,
      weatherManualCity: weatherManualCity.value,
      screensaverTimeout: screensaverTimeout.value,
    }
  }

  function applySettingsObject(settings: Partial<PersistedUserSettings>) {
    if (settings.buttonSize !== undefined) buttonSize.value = settings.buttonSize
    if (settings.showLabels !== undefined) showLabels.value = settings.showLabels
    if (settings.showTooltips !== undefined) showTooltips.value = settings.showTooltips
    if (settings.animationsEnabled !== undefined) animationsEnabled.value = settings.animationsEnabled
    if (settings.tiltEffectEnabled !== undefined) tiltEffectEnabled.value = settings.tiltEffectEnabled
    if (settings.dockedSidebarEnabled !== undefined) dockedSidebarEnabled.value = settings.dockedSidebarEnabled
    if (settings.dockedSidebarWidth !== undefined) dockedSidebarWidth.value = settings.dockedSidebarWidth
    if (settings.dashboardBackground !== undefined) dashboardBackground.value = settings.dashboardBackground
    if (settings.backgroundPreference !== undefined) {
      backgroundPreference.value = settings.backgroundPreference as typeof backgroundPreference.value
    }
    if (settings.uiBrightness !== undefined) uiBrightness.value = settings.uiBrightness
    if (settings.toastLevel !== undefined) toastLevel.value = settings.toastLevel
    if (settings.touchMode !== undefined) touchMode.value = settings.touchMode
    if (settings.minimumTouchTargetSize !== undefined) minimumTouchTargetSize.value = settings.minimumTouchTargetSize
    if (settings.defaultGridRows !== undefined) defaultGridRows.value = settings.defaultGridRows
    if (settings.defaultGridCols !== undefined) defaultGridCols.value = settings.defaultGridCols
    if (settings.startOnBoot !== undefined) startOnBoot.value = settings.startOnBoot
    if (settings.openSettingsInNewTab !== undefined) openSettingsInNewTab.value = settings.openSettingsInNewTab
    if (settings.autoCloseLauncher !== undefined) autoCloseLauncher.value = settings.autoCloseLauncher
    if (settings.recentActions !== undefined) recentActions.value = settings.recentActions
    if (settings.weatherLocationMode !== undefined) weatherLocationMode.value = settings.weatherLocationMode
    if (settings.weatherManualCity !== undefined) weatherManualCity.value = settings.weatherManualCity
    if (settings.screensaverTimeout !== undefined) screensaverTimeout.value = settings.screensaverTimeout
  }

  function saveSettingsLocalOnly() {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(buildSettingsPayload()))
  }

  function loadSettings() {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!stored) return

    try {
      const settings = JSON.parse(stored) as Partial<PersistedUserSettings> & { showRegularToasts?: boolean }
      applySettingsObject({
        ...settings,
        buttonSize: settings.buttonSize ?? 1.0,
        showLabels: settings.showLabels !== false,
        showTooltips: settings.showTooltips !== false,
        animationsEnabled: settings.animationsEnabled !== false,
        tiltEffectEnabled: settings.tiltEffectEnabled !== false,
        dockedSidebarEnabled: settings.dockedSidebarEnabled !== false,
        dockedSidebarWidth: settings.dockedSidebarWidth ?? 190,
        dashboardBackground: settings.dashboardBackground ?? 'default',
        backgroundPreference: settings.backgroundPreference ?? 'none',
        uiBrightness: settings.uiBrightness ?? 100,
        toastLevel: settings.toastLevel
          ?? (settings.showRegularToasts === false ? 'errors-only' : 'all'),
        touchMode: settings.touchMode ?? 'normal',
        minimumTouchTargetSize: settings.minimumTouchTargetSize ?? 44,
        defaultGridRows: settings.defaultGridRows ?? 3,
        defaultGridCols: settings.defaultGridCols ?? 3,
        startOnBoot: settings.startOnBoot ?? false,
        openSettingsInNewTab: settings.openSettingsInNewTab === true,
        autoCloseLauncher: settings.autoCloseLauncher !== false,
        recentActions: settings.recentActions ?? [],
        weatherLocationMode: settings.weatherLocationMode ?? 'auto',
        weatherManualCity: settings.weatherManualCity ?? '',
        screensaverTimeout: settings.screensaverTimeout ?? 120,
      })
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  function scheduleServerSync() {
    if (serverSyncTimer) {
      clearTimeout(serverSyncTimer)
    }

    serverSyncTimer = setTimeout(() => {
      void persistSettingsToServer()
    }, SERVER_SYNC_DELAY_MS)
  }

  async function persistSettingsToServer() {
    if (serverSyncInFlight) return

    serverSyncInFlight = true
    try {
      await apiClient.put('/user-settings', { settings: buildSettingsPayload() })
    } catch (error) {
      console.warn('Failed to persist settings to server:', error)
    } finally {
      serverSyncInFlight = false
    }
  }

  function saveSettings() {
    saveSettingsLocalOnly()
    scheduleServerSync()

    if (!isApplyingRemoteSettings) {
      broadcastSettingsToOtherWindows()
    }
  }

  async function flushSettingsToServer() {
    if (serverSyncTimer) {
      clearTimeout(serverSyncTimer)
      serverSyncTimer = null
    }

    saveSettingsLocalOnly()
    await persistSettingsToServer()
  }

  async function loadSettingsFromServer() {
    try {
      const response = await apiClient.get('/user-settings')
      const serverSettings = response.data?.settings as Partial<PersistedUserSettings> | undefined

      if (serverSettings && Object.keys(serverSettings).length > 0) {
        applySettingsObject(serverSettings)
        saveSettingsLocalOnly()
      } else if (localStorage.getItem(SETTINGS_STORAGE_KEY)) {
        await persistSettingsToServer()
      }

      applyTouchModeStyles()
      applyUIBrightnessFilter()
    } catch (error) {
      console.warn('Failed to load settings from server, using local cache:', error)
    }
  }

  watch(
    [
      buttonSize,
      showLabels,
      showTooltips,
      animationsEnabled,
      tiltEffectEnabled,
      dockedSidebarEnabled,
      dockedSidebarWidth,
      dashboardBackground,
      backgroundPreference,
      uiBrightness,
      toastLevel,
      touchMode,
      minimumTouchTargetSize,
      defaultGridRows,
      defaultGridCols,
      startOnBoot,
      openSettingsInNewTab,
      autoCloseLauncher,
      recentActions,
      weatherLocationMode,
      weatherManualCity,
      screensaverTimeout,
    ],
    () => {
      saveSettings()
      applyTouchModeStyles()
      applyUIBrightnessFilter()
    },
    { deep: true }
  )
  
  function applyTouchModeStyles() {
    const root = document.documentElement
    const multiplier = touchModeMultiplier.value
    
    root.style.setProperty('--touch-multiplier', multiplier.toString())
    root.style.setProperty('--min-touch-target', `${minimumTouchTargetSize.value}px`)
    root.style.setProperty('--spacing-touch-xs', `${0.25 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-sm', `${0.5 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-md', `${1 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-lg', `${1.5 * multiplier}rem`)
    root.style.setProperty('--button-padding-v', `${0.75 * multiplier}rem`)
    root.style.setProperty('--button-padding-h', `${1 * multiplier}rem`)
    root.style.setProperty('--button-min-height', `${Math.max(36 * multiplier, minimumTouchTargetSize.value)}px`)
    root.style.setProperty('--icon-size', `${1 * multiplier}rem`)
    root.style.setProperty('--text-scale', multiplier.toString())
  }

  function applyUIBrightnessFilter() {
    const root = document.documentElement
    const brightnessValue = uiBrightness.value / 100
    root.style.setProperty('--ui-brightness', brightnessValue.toString())
    
    const appElement = document.querySelector('#app')
    if (appElement) {
      (appElement as HTMLElement).style.filter = `brightness(${brightnessValue})`
    }
  }

  async function loadServerConfig() {
    try {
      const response = await apiClient.get('/config')
      serverConfig.value = response.data.config
    } catch (err) {
      console.error('Failed to load server config:', err)
    }
  }

  async function updateServerConfig(config: Partial<ServerConfig>): Promise<boolean> {
    try {
      const response = await apiClient.put('/config', config)
      if (response.data.success) {
        await loadServerConfig()
        return true
      }
      return false
    } catch (err) {
      console.error('Failed to update server config:', err)
      return false
    }
  }

  function addRecentAction(actionId: string) {
    const index = recentActions.value.indexOf(actionId)
    if (index !== -1) {
      recentActions.value.splice(index, 1)
    }
    
    recentActions.value.unshift(actionId)
    
    if (recentActions.value.length > maxRecentActions) {
      recentActions.value = recentActions.value.slice(0, maxRecentActions)
    }
  }

  function clearRecentActions() {
    recentActions.value = []
  }

  loadSettings()
  detectSmallScreenDefaults()
  applyTouchModeStyles()
  applyUIBrightnessFilter()

  function detectSmallScreenDefaults() {
    if (typeof window === 'undefined') return

    const isCompactScreen = window.innerWidth <= 1100 || window.innerHeight <= 650
    const isTouchDevice =
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      window.matchMedia('(pointer: coarse)').matches

    if ((isCompactScreen || isTouchDevice) && touchMode.value === 'normal') {
      touchMode.value = 'tablet'
      minimumTouchTargetSize.value = 48
      saveSettings()
      applyTouchModeStyles()
    }
  }

  function initLiveSync() {
    if (liveSyncInitialized || typeof window === 'undefined') {
      return () => {}
    }

    liveSyncInitialized = true

    if ('BroadcastChannel' in window) {
      settingsBroadcastChannel = new BroadcastChannel(SETTINGS_BROADCAST_CHANNEL)
      settingsBroadcastChannel.onmessage = (event) => {
        if (event.data && typeof event.data === 'object') {
          applySettingsFromRemote(event.data as Partial<PersistedUserSettings>)
        }
      }
    }

    const handleStorageEvent = (event: StorageEvent) => {
      if (event.key !== SETTINGS_STORAGE_KEY || !event.newValue) {
        return
      }

      try {
        applySettingsFromRemote(JSON.parse(event.newValue) as Partial<PersistedUserSettings>)
      } catch {
        // Ignore malformed cross-tab payloads
      }
    }

    const handleSocketSettingsUpdate = (data: { settings?: Partial<PersistedUserSettings> }) => {
      if (data?.settings) {
        applySettingsFromRemote(data.settings)
      }
    }

    window.addEventListener('storage', handleStorageEvent)
    socketClient.on('user_settings_updated', handleSocketSettingsUpdate)

    return () => {
      window.removeEventListener('storage', handleStorageEvent)
      socketClient.off('user_settings_updated', handleSocketSettingsUpdate)
      settingsBroadcastChannel?.close()
      settingsBroadcastChannel = null
      liveSyncInitialized = false
    }
  }

  return {
    currentTheme,
    serverConfig,
    windowPinned,
    windowPosition,
    windowDocked,
    alwaysOnTop,
    buttonSize,
    showLabels,
    showTooltips,
    animationsEnabled,
    tiltEffectEnabled,
    dockedSidebarEnabled,
    dockedSidebarWidth,
    dashboardBackground,
    backgroundPreference,
    uiBrightness,
    showHeader,
    toastLevel,
    touchMode,
    minimumTouchTargetSize,
    touchModeMultiplier,
    defaultGridRows,
    defaultGridCols,
    startOnBoot,
    openSettingsInNewTab,
    autoCloseLauncher,
    recentActions,
    weatherLocationMode,
    weatherManualCity,
    screensaverTimeout,
    showHelpGuide,
    applyTouchModeStyles,
    applyUIBrightnessFilter,
    loadServerConfig,
    updateServerConfig,
    addRecentAction,
    clearRecentActions,
    saveSettings,
    loadSettings,
    loadSettingsFromServer,
    flushSettingsToServer,
    initLiveSync,
  }
})
