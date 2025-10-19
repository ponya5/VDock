import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Theme, ServerConfig } from '@/types'
import apiClient from '@/api/client'

export const useSettingsStore = defineStore('settings', () => {
  const currentTheme = ref('default')
  const themes = ref<Theme[]>([])
  const serverConfig = ref<ServerConfig | null>(null)
  
  // Window settings
  const windowPinned = ref(false)
  const windowPosition = ref<{ x: number; y: number } | null>(null)
  const windowDocked = ref<'none' | 'left' | 'right' | 'top' | 'bottom'>('none')
  const alwaysOnTop = ref(false)
  
  // Display settings
  const buttonSize = ref(1.0) // Scale factor
  const showLabels = ref(true)
  const showTooltips = ref(true)
  const animationsEnabled = ref(true)
  const dockedSidebarEnabled = ref(true)
  const dockedSidebarWidth = ref(150) // Width in pixels (80-300)
  const dashboardBackground = ref('default')
  const startWithWindows = ref(false)
  
  // Grid settings
  const defaultGridRows = ref(3)
  const defaultGridCols = ref(3)

  // Authentication settings
  const authEnabled = ref(false)

  // System settings
  const startOnBoot = ref(false)

  // Search settings
  const recentActions = ref<string[]>([])
  const maxRecentActions = 10

  // Load settings from localStorage
  function loadSettings() {
    const stored = localStorage.getItem('vdock_settings')
    if (stored) {
      try {
        const settings = JSON.parse(stored)
        currentTheme.value = settings.currentTheme || 'default'
        buttonSize.value = settings.buttonSize || 1.0
        showLabels.value = settings.showLabels !== false
        showTooltips.value = settings.showTooltips !== false
        animationsEnabled.value = settings.animationsEnabled !== false
        dockedSidebarEnabled.value = settings.dockedSidebarEnabled !== false
        dockedSidebarWidth.value = settings.dockedSidebarWidth || 150
        dashboardBackground.value = settings.dashboardBackground || 'default'
        startWithWindows.value = settings.startWithWindows || false
        defaultGridRows.value = settings.defaultGridRows || 3
        defaultGridCols.value = settings.defaultGridCols || 3
        authEnabled.value = settings.authEnabled || false
        startOnBoot.value = settings.startOnBoot || false
        recentActions.value = settings.recentActions || []
      } catch (err) {
        console.error('Failed to load settings:', err)
      }
    }
  }

  // Save settings to localStorage
  function saveSettings() {
    const settings = {
      currentTheme: currentTheme.value,
      buttonSize: buttonSize.value,
      showLabels: showLabels.value,
      showTooltips: showTooltips.value,
      animationsEnabled: animationsEnabled.value,
      dockedSidebarEnabled: dockedSidebarEnabled.value,
      dockedSidebarWidth: dockedSidebarWidth.value,
      dashboardBackground: dashboardBackground.value,
      startWithWindows: startWithWindows.value,
      defaultGridRows: defaultGridRows.value,
      defaultGridCols: defaultGridCols.value,
      authEnabled: authEnabled.value,
      startOnBoot: startOnBoot.value,
      recentActions: recentActions.value
    }
    localStorage.setItem('vdock_settings', JSON.stringify(settings))
  }

  // Watch for changes and save
  watch(
    [currentTheme, buttonSize, showLabels, showTooltips, animationsEnabled, dockedSidebarEnabled, dockedSidebarWidth, dashboardBackground, defaultGridRows, defaultGridCols, authEnabled, recentActions],
    () => {
      saveSettings()
    },
    { deep: true }
  )

  function setTheme(themeId: string) {
    currentTheme.value = themeId
  }

  async function loadThemes() {
    try {
      const response = await apiClient.get('/themes')
      themes.value = response.data.themes
    } catch (err) {
      console.error('Failed to load themes:', err)
    }
  }

  async function loadServerConfig() {
    try {
      const response = await apiClient.get('/config')
      serverConfig.value = response.data.config
      // Sync authEnabled with server config
      authEnabled.value = response.data.config.require_auth
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
    // Remove if already exists
    const index = recentActions.value.indexOf(actionId)
    if (index !== -1) {
      recentActions.value.splice(index, 1)
    }
    
    // Add to beginning
    recentActions.value.unshift(actionId)
    
    // Limit size
    if (recentActions.value.length > maxRecentActions) {
      recentActions.value = recentActions.value.slice(0, maxRecentActions)
    }
  }

  function clearRecentActions() {
    recentActions.value = []
  }

  async function updateAuthSetting(enabled: boolean): Promise<boolean> {
    try {
      const success = await updateServerConfig({ require_auth: enabled })
      if (success) {
        authEnabled.value = enabled
        return true
      }
      return false
    } catch (err) {
      console.error('Failed to update auth setting:', err)
      return false
    }
  }

  // Initialize
  loadSettings()

  return {
    currentTheme,
    themes,
    serverConfig,
    windowPinned,
    windowPosition,
    windowDocked,
    alwaysOnTop,
    buttonSize,
    showLabels,
    showTooltips,
    animationsEnabled,
    dockedSidebarEnabled,
    dockedSidebarWidth,
    dashboardBackground,
    startWithWindows,
    defaultGridRows,
    defaultGridCols,
    authEnabled,
    startOnBoot,
    recentActions,
    setTheme,
    loadThemes,
    loadServerConfig,
    updateServerConfig,
    addRecentAction,
    clearRecentActions,
    updateAuthSetting,
    saveSettings,
    loadSettings
  }
})

