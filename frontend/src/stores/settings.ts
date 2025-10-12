import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Theme, ServerConfig } from '@/types'
import apiClient from '@/api/client'

export const useSettingsStore = defineStore('settings', () => {
  const currentTheme = ref('dark')
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
  
  // Search settings
  const recentActions = ref<string[]>([])
  const maxRecentActions = 10

  // Load settings from localStorage
  function loadSettings() {
    const stored = localStorage.getItem('vdock_settings')
    if (stored) {
      try {
        const settings = JSON.parse(stored)
        currentTheme.value = settings.currentTheme || 'dark'
        buttonSize.value = settings.buttonSize || 1.0
        showLabels.value = settings.showLabels !== false
        showTooltips.value = settings.showTooltips !== false
        animationsEnabled.value = settings.animationsEnabled !== false
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
      recentActions: recentActions.value
    }
    localStorage.setItem('vdock_settings', JSON.stringify(settings))
  }

  // Watch for changes and save
  watch(
    [currentTheme, buttonSize, showLabels, showTooltips, animationsEnabled, recentActions],
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
    recentActions,
    setTheme,
    loadThemes,
    loadServerConfig,
    updateServerConfig,
    addRecentAction,
    clearRecentActions,
    saveSettings,
    loadSettings
  }
})

