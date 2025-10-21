import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Theme, ServerConfig } from '@/types'
import apiClient from '@/api/client'

export const useSettingsStore = defineStore('settings', () => {
  // Fixed to dark mode only
  const currentTheme = ref('dark')
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
  
  // Touch mode settings
  const touchMode = ref<'normal' | 'touch-friendly' | 'tablet'>('normal')
  const minimumTouchTargetSize = ref(44) // px (WCAG 2.1 AA standard)
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
        // Theme is fixed to dark mode
        buttonSize.value = settings.buttonSize || 1.0
        showLabels.value = settings.showLabels !== false
        showTooltips.value = settings.showTooltips !== false
        animationsEnabled.value = settings.animationsEnabled !== false
        dockedSidebarEnabled.value = settings.dockedSidebarEnabled !== false
        dockedSidebarWidth.value = settings.dockedSidebarWidth || 150
        dashboardBackground.value = settings.dashboardBackground || 'default'
        startWithWindows.value = settings.startWithWindows || false
        touchMode.value = settings.touchMode || 'normal'
        minimumTouchTargetSize.value = settings.minimumTouchTargetSize || 44
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
      // Theme is fixed to dark mode
      buttonSize: buttonSize.value,
      showLabels: showLabels.value,
      showTooltips: showTooltips.value,
      animationsEnabled: animationsEnabled.value,
      dockedSidebarEnabled: dockedSidebarEnabled.value,
      dockedSidebarWidth: dockedSidebarWidth.value,
      dashboardBackground: dashboardBackground.value,
      startWithWindows: startWithWindows.value,
      touchMode: touchMode.value,
      minimumTouchTargetSize: minimumTouchTargetSize.value,
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
    [buttonSize, showLabels, showTooltips, animationsEnabled, dockedSidebarEnabled, dockedSidebarWidth, dashboardBackground, touchMode, minimumTouchTargetSize, defaultGridRows, defaultGridCols, authEnabled, recentActions],
    () => {
      saveSettings()
      applyTouchModeStyles()
    },
    { deep: true }
  )
  
  // Apply touch mode styles to document
  function applyTouchModeStyles() {
    const root = document.documentElement
    const multiplier = touchModeMultiplier.value
    
    // Update CSS variables based on touch mode
    root.style.setProperty('--touch-multiplier', multiplier.toString())
    root.style.setProperty('--min-touch-target', `${minimumTouchTargetSize.value}px`)
    
    // Scale spacing
    root.style.setProperty('--spacing-touch-xs', `${0.25 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-sm', `${0.5 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-md', `${1 * multiplier}rem`)
    root.style.setProperty('--spacing-touch-lg', `${1.5 * multiplier}rem`)
    
    // Scale interactive elements
    root.style.setProperty('--button-padding-v', `${0.75 * multiplier}rem`)
    root.style.setProperty('--button-padding-h', `${1 * multiplier}rem`)
    root.style.setProperty('--button-min-height', `${Math.max(36 * multiplier, minimumTouchTargetSize.value)}px`)
    
    // Scale icons and text
    root.style.setProperty('--icon-size', `${1 * multiplier}rem`)
    root.style.setProperty('--text-scale', multiplier.toString())
  }

  // Theme is fixed to dark mode - no setTheme function needed

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
  applyTouchModeStyles()

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
    dockedSidebarEnabled,
    dockedSidebarWidth,
    dashboardBackground,
    startWithWindows,
    touchMode,
    minimumTouchTargetSize,
    touchModeMultiplier,
    defaultGridRows,
    defaultGridCols,
    authEnabled,
    startOnBoot,
    recentActions,
    applyTouchModeStyles,
    loadServerConfig,
    updateServerConfig,
    addRecentAction,
    clearRecentActions,
    updateAuthSetting,
    saveSettings,
    loadSettings
  }
})

