<template>
  <div class="settings-view">
    <header class="settings-header">
      <h1>Settings</h1>
      <button class="btn btn-secondary" @click="router.push('/')">
        <FontAwesomeIcon :icon="['fas', 'arrow-left']" /> Back
      </button>
    </header>

    <div class="settings-tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <FontAwesomeIcon :icon="tab.icon" />
        {{ tab.name }}
      </button>
    </div>

    <div class="settings-content">
      <!-- Appearance Tab -->
      <div v-if="activeTab === 'appearance'" class="tab-content">
        <section class="settings-section card">
          <h2>Appearance</h2>
          
          <div class="form-group">
            <label>Theme</label>
            <select v-model="settings.currentTheme" class="select">
              <option value="default">Default (Colorful)</option>
              <option value="light">Light Mode</option>
              <option value="dark">Dark Mode</option>
            </select>
            <p class="form-help">Choose your preferred color scheme</p>
          </div>

          <div class="form-group">
            <label>Button Size</label>
            <input 
              v-model.number="settings.buttonSize" 
              type="range" 
              min="0.5" 
              max="2" 
              step="0.1" 
              class="slider"
            />
            <span class="slider-value">{{ settings.buttonSize.toFixed(1) }}x</span>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.showLabels" type="checkbox" />
              <span>Show button labels</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.showTooltips" type="checkbox" />
              <span>Show tooltips</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.animationsEnabled" type="checkbox" />
              <span>Enable animations</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.dockedSidebarEnabled" type="checkbox" />
              <span>Show docked sidebar</span>
            </label>
            <p class="form-help">Display the left sidebar with persistent buttons</p>
          </div>

          <div v-if="settings.dockedSidebarEnabled" class="form-group">
            <label>Docked Sidebar Width</label>
            <input 
              v-model.number="settings.dockedSidebarWidth" 
              type="range" 
              min="80" 
              max="300" 
              step="10" 
              class="slider"
            />
            <span class="slider-value">{{ settings.dockedSidebarWidth }}px</span>
            <p class="form-help">Adjust the width of the docked sidebar (80-300px)</p>
          </div>

          <div class="form-group">
            <label>Dashboard Background</label>
            <select v-model="settings.dashboardBackground" class="select">
              <option value="default">Default (Gradient)</option>
              <optgroup label="Custom Background" v-if="customBackgroundUrl">
                <option :value="customBackgroundUrl">Custom Uploaded Image</option>
              </optgroup>
              <optgroup label="Static Gradients">
                <option value="ocean-breeze">Ocean Breeze</option>
                <option value="sunset-glow">Sunset Glow</option>
                <option value="forest-mist">Forest Mist</option>
                <option value="royal-purple">Royal Purple</option>
                <option value="golden-hour">Golden Hour</option>
              </optgroup>
              <optgroup label="Animated Backgrounds">
                <option value="floating-particles">Floating Particles</option>
                <option value="gradient-waves">Gradient Waves</option>
                <option value="geometric-patterns">Geometric Patterns</option>
                <option value="aurora-borealis">Aurora Borealis</option>
                <option value="starfield">Starfield</option>
                <option value="bubble-float">Floating Bubbles</option>
                <option value="neon-grid">Neon Grid</option>
              </optgroup>
            </select>
            <p class="form-help">Choose a background style for your dashboard</p>
          </div>

          <div class="form-group">
            <label>Upload Custom Background</label>
            <div class="upload-section">
              <input 
                ref="backgroundFileInput"
                type="file" 
                accept="image/*,.gif" 
                @change="handleBackgroundUpload"
                class="file-input"
                style="display: none"
              />
              <button 
                class="btn btn-secondary upload-btn" 
                @click="$refs.backgroundFileInput.click()"
              >
                <FontAwesomeIcon :icon="['fas', 'upload']" />
                Choose Image or GIF
              </button>
              <button 
                v-if="customBackgroundUrl"
                class="btn btn-danger"
                @click="removeCustomBackground"
                title="Remove Custom Background"
              >
                <FontAwesomeIcon :icon="['fas', 'trash']" />
                Remove
              </button>
            </div>
            <div v-if="customBackgroundUrl" class="background-preview">
              <img :src="customBackgroundUrl" alt="Custom Background" />
            </div>
            <p class="form-help">Upload your own image or GIF as a dashboard background (supports PNG, JPG, GIF)</p>
          </div>

        </section>
      </div>

      <!-- Server Configuration Tab -->
      <div v-if="activeTab === 'server'" class="tab-content">
        <section class="settings-section card">
          <h2>Server Configuration</h2>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.authEnabled" type="checkbox" @change="handleAuthToggle" />
              <span>Enable Authentication</span>
            </label>
            <p class="form-help">Require password to access the application</p>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.startOnBoot" type="checkbox" @change="handleStartOnBootToggle" />
              <span>Start VDock on System Boot</span>
            </label>
            <p class="form-help">Automatically launch VDock when your computer starts</p>
            <p v-if="startOnBootStatus" class="form-help" :class="startOnBootStatus.success ? 'text-success' : 'text-error'">
              {{ startOnBootStatus.message }}
            </p>
          </div>
          
          <div v-if="serverConfig" class="server-info">
            <div class="info-row">
              <span class="info-label">Host:</span>
              <span class="info-value">{{ serverConfig.host }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Port:</span>
              <span class="info-value">{{ serverConfig.port }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Authentication:</span>
              <span class="info-value">{{ serverConfig.require_auth ? 'Enabled' : 'Disabled' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">LAN Access:</span>
              <span class="info-value">{{ serverConfig.allow_lan ? 'Enabled' : 'Disabled' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">SSL:</span>
              <span class="info-value">{{ serverConfig.use_ssl ? 'Enabled' : 'Disabled' }}</span>
            </div>
          </div>

          <p class="settings-note">
            <small>Server configuration can be changed in the backend .env file</small>
          </p>
        </section>
      </div>

      <!-- Integration Tab -->
      <div v-if="activeTab === 'integration'" class="tab-content">
        <!-- Auto Scene Switching Section -->
        <section class="settings-section card">
          <div class="section-header">
            <h2>Auto Scene Switching</h2>
            <label class="toggle-switch-inline">
              <input 
                type="checkbox" 
                :checked="autoSwitchingEnabled"
                @change="toggleAutoSwitching"
              />
              <span class="toggle-slider"></span>
              <span class="toggle-label">{{ autoSwitchingEnabled ? 'Enabled' : 'Disabled' }}</span>
            </label>
          </div>
          <p class="section-description">
            Automatically switch scenes when monitored applications become active. Enable app integrations below to use this feature.
          </p>
          
          <div v-if="autoSwitchingEnabled" class="auto-switch-status">
            <FontAwesomeIcon :icon="['fas', 'check-circle']" class="status-icon success" />
            <span>Monitoring active application and switching scenes automatically</span>
          </div>
        </section>

        <!-- App Integration Section -->
        <section class="settings-section card">
          <div class="section-header">
            <h2>App Integration</h2>
            <button class="btn btn-sm btn-primary" @click="refreshRunningApps">
              <FontAwesomeIcon :icon="['fas', 'sync']" :spin="loadingApps" />
              Refresh Apps
            </button>
          </div>
          <p class="section-description">
            Configure which applications trigger automatic scene switching.
          </p>

          <div v-if="loadingApps" class="loading-state">
            <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
            <span>Loading running applications...</span>
          </div>

          <div v-else-if="runningApps.length === 0" class="empty-state">
            <FontAwesomeIcon :icon="['fas', 'desktop']" />
            <p>No applications detected</p>
            <button class="btn btn-secondary" @click="refreshRunningApps">
              Refresh
            </button>
          </div>

          <div v-else class="app-integration-list">
            <div class="list-header">
              <span class="header-col-app">Application</span>
              <span class="header-col-status">Status</span>
              <span class="header-col-scene">Scene</span>
              <span class="header-col-actions">Actions</span>
            </div>

            <div 
              v-for="app in runningApps" 
              :key="app.exe"
              class="app-item"
            >
              <div class="app-info">
                <FontAwesomeIcon :icon="['fas', 'window-maximize']" class="app-icon" />
                <div class="app-details">
                  <span class="app-name">{{ app.name }}</span>
                  <span class="app-exe">{{ app.exe }}</span>
                </div>
              </div>

              <div class="app-status">
                <label class="toggle-switch">
                  <input 
                    type="checkbox" 
                    :checked="isAppIntegrationEnabled(app.exe)"
                    @change="toggleAppIntegration(app)"
                  />
                  <span class="toggle-slider"></span>
                </label>
                <span class="status-text">
                  {{ isAppIntegrationEnabled(app.exe) ? 'Enabled' : 'Disabled' }}
                </span>
              </div>

              <div class="app-scene">
                <select 
                  v-if="isAppIntegrationEnabled(app.exe)"
                  :value="getAppScene(app.exe)"
                  @change="updateAppScene(app.exe, ($event.target as HTMLSelectElement).value)"
                  class="select-sm"
                >
                  <option value="">Create New Scene</option>
                  <option 
                    v-for="scene in availableScenes" 
                    :key="scene.id"
                    :value="scene.id"
                  >
                    {{ scene.name }}
                  </option>
                </select>
                <span v-else class="scene-placeholder">—</span>
              </div>

              <div class="app-actions">
                <button 
                  v-if="isAppIntegrationEnabled(app.exe)"
                  class="btn-icon btn-sm"
                  @click="openShortcutManager(app)"
                  title="Manage Shortcuts"
                >
                  <FontAwesomeIcon :icon="['fas', 'cog']" />
                </button>
                <button 
                  v-if="isAppIntegrationEnabled(app.exe) && !getAppScene(app.exe)"
                  class="btn-icon btn-sm btn-primary"
                  @click="createSceneForApp(app)"
                  title="Create Scene"
                >
                  <FontAwesomeIcon :icon="['fas', 'plus']" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="appIntegrations.length > 0" class="integration-summary">
            <FontAwesomeIcon :icon="['fas', 'info-circle']" />
            <span>
              {{ appIntegrations.length }} app{{ appIntegrations.length > 1 ? 's' : '' }} integrated
            </span>
          </div>
        </section>

        <section class="settings-section card">
          <h2>Recent Actions</h2>
          
          <div v-if="settings.recentActions.length > 0" class="recent-actions">
            <div 
              v-for="(actionId, index) in settings.recentActions" 
              :key="index"
              class="recent-action-item"
            >
              {{ actionId }}
            </div>
            <button class="btn btn-secondary mt-md" @click="clearRecentActions">
              Clear Recent Actions
            </button>
          </div>
          <div v-else class="empty-state">
            No recent actions
          </div>
        </section>

        <section class="settings-section card">
          <h2>Plugins</h2>
          <p>Plugin management features coming soon...</p>
        </section>
      </div>

      <!-- Shortcut Manager Modal -->
      <AppShortcutManager
        v-if="showShortcutManager"
        :app-exe="selectedAppForShortcuts?.exe || ''"
        :scene-id="getAppScene(selectedAppForShortcuts?.exe || '')"
        @close="showShortcutManager = false"
        @add-shortcut="handleAddShortcut"
      />

      <!-- About Tab -->
      <div v-if="activeTab === 'about'" class="tab-content">
        <section class="settings-section card">
          <h2>About</h2>
          
          <div class="about-info">
            <h3>VDock</h3>
            <p>Virtual Stream Interface v1.0.0</p>
            <p class="mt-md">
              A powerful virtual stream interface for controlling your computer with customizable 
              buttons, macros, system metrics, and intelligent app integration.
            </p>
            
            <div class="feature-highlights mt-md">
              <h4>Key Features</h4>
              <ul>
                <li>✨ Real-time System Metrics Monitoring</li>
                <li>🎬 Advanced Macro Automation</li>
                <li>🔗 Smart App Integration</li>
                <li>🎨 Customizable Buttons & Backgrounds</li>
                <li>🤖 Automatic Scene Switching</li>
                <li>📊 Professional Dashboard Interface</li>
              </ul>
            </div>
            
            <div class="mt-lg">
              <div style="display: flex; gap: var(--spacing-md); flex-wrap: wrap;">
                <button class="btn btn-secondary" @click="openGitHub">
                  <FontAwesomeIcon :icon="['fab', 'github']" /> GitHub
                </button>
                <button class="btn btn-secondary" @click="contactEmail">
                  <FontAwesomeIcon :icon="['fas', 'envelope']" /> Contact
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { useDashboardStore } from '@/stores/dashboard'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import AppShortcutManager from '@/components/AppShortcutManager.vue'
import { hasShortcuts, getTopShortcutsForApp, type AppShortcut } from '@/data/appShortcuts'
import type { RunningApp, AppIntegration, Scene, Button } from '@/types'

const router = useRouter()
const settingsStore = useSettingsStore()
const profilesStore = useProfilesStore()
const dashboardStore = useDashboardStore()

const settings = computed(() => settingsStore)
const themes = computed(() => settingsStore.themes)
const serverConfig = computed(() => settingsStore.serverConfig)

const activeTab = ref('appearance')

// Custom Background State
const customBackgroundUrl = ref<string | null>(null)
const backgroundFileInput = ref<HTMLInputElement | null>(null)

// Load custom background from localStorage
const loadCustomBackground = () => {
  const stored = localStorage.getItem('customBackgroundUrl')
  if (stored) {
    customBackgroundUrl.value = stored
  }
}

// Save custom background to localStorage
const saveCustomBackground = (url: string) => {
  customBackgroundUrl.value = url
  localStorage.setItem('customBackgroundUrl', url)
  // Don't auto-select - let user choose from dropdown
}

// Handle background file upload
const handleBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  // Validate file type
  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']
  if (!validTypes.includes(file.type)) {
    alert('Please upload a valid image file (PNG, JPG, or GIF)')
    return
  }
  
  // Validate file size (max 10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    alert('File size must be less than 10MB')
    return
  }
  
  try {
    // Create form data
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', 'background')
    
    // Upload to backend
    const response = await apiClient.post('/upload/icon', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      const imageUrl = response.data.url
      saveCustomBackground(imageUrl)
      alert('Background uploaded successfully! Select "Custom Uploaded Image" from the Dashboard Background dropdown above to use it.')
    } else {
      alert('Failed to upload background: ' + (response.data.error || 'Unknown error'))
    }
  } catch (error: any) {
    console.error('Error uploading background:', error)
    alert('Failed to upload background: ' + (error.message || 'Unknown error'))
  } finally {
    // Reset file input
    if (target) target.value = ''
  }
}

// Remove custom background
const removeCustomBackground = () => {
  if (confirm('Are you sure you want to remove the custom background?')) {
    customBackgroundUrl.value = null
    localStorage.removeItem('customBackgroundUrl')
    // Reset to default background
    if (settings.value.dashboardBackground.startsWith('/api/uploads/')) {
      settings.value.dashboardBackground = 'default'
    }
  }
}

// App Integration State
const runningApps = ref<RunningApp[]>([])
const loadingApps = ref(false)
const appIntegrations = ref<AppIntegration[]>([])
const autoSwitchingEnabled = ref(false)
const showShortcutManager = ref(false)
const selectedAppForShortcuts = ref<RunningApp | null>(null)
const startOnBootStatus = ref<{success: boolean, message: string} | null>(null)

// Get all scenes from current profile
const availableScenes = computed(() => {
  const profile = profilesStore.currentProfile
  if (!profile) return []
  
  // Return all scenes from the profile
  return profile.pages.flatMap(page => 
    page.scenes.map(scene => ({
      id: scene.id,
      name: scene.name,
      pageId: page.id,
      pageName: page.name
    }))
  )
})

const tabs = [
  { id: 'appearance', name: 'Appearance', icon: ['fas', 'palette'] },
  { id: 'server', name: 'Server', icon: ['fas', 'server'] },
  { id: 'integration', name: 'Integration', icon: ['fas', 'plug'] },
  { id: 'about', name: 'About', icon: ['fas', 'info-circle'] }
]

onMounted(() => {
  settingsStore.loadThemes()
  settingsStore.loadServerConfig()
})

function clearRecentActions() {
  if (confirm('Clear all recent actions?')) {
    settingsStore.clearRecentActions()
  }
}

async function handleAuthToggle() {
  const success = await settingsStore.updateAuthSetting(settings.value.authEnabled)
  if (!success) {
    // Revert the change if it failed
    settings.value.authEnabled = !settings.value.authEnabled
    alert('Failed to update authentication setting')
  }
}

async function handleStartOnBootToggle() {
  try {
    const response = await apiClient.post('/system/autostart', {
      enabled: settings.value.startOnBoot
    })

    if (response.data.success) {
      startOnBootStatus.value = {
        success: true,
        message: settings.value.startOnBoot
          ? 'VDock will now start automatically on system boot'
          : 'Auto-start disabled'
      }
    } else {
      startOnBootStatus.value = {
        success: false,
        message: response.data.message || 'Failed to update auto-start setting'
      }
      settings.value.startOnBoot = !settings.value.startOnBoot
    }
  } catch (error) {
    console.error('Failed to toggle auto-start:', error)
    startOnBootStatus.value = {
      success: false,
      message: 'Failed to update auto-start setting. This feature may require administrator privileges.'
    }
    settings.value.startOnBoot = !settings.value.startOnBoot
  }

  // Clear status after 5 seconds
  setTimeout(() => {
    startOnBootStatus.value = null
  }, 5000)
}

function openGitHub() {
  window.open('https://github.com/ponya5/VDock', '_blank')
}

function contactEmail() {
  window.location.href = 'mailto:ponya81@gmail.com?subject=VDock%20Support'
}

// App Integration Functions
async function refreshRunningApps() {
  loadingApps.value = true
  try {
    const response = await apiClient.get('/metrics/running-apps')
    runningApps.value = response.data.success ? response.data.data : []
  } catch (error) {
    console.error('Failed to fetch running apps:', error)
    runningApps.value = []
  } finally {
    loadingApps.value = false
  }
}

function isAppIntegrationEnabled(appExe: string): boolean {
  return appIntegrations.value.some(integration => integration.appExe === appExe && integration.enabled)
}

function getAppScene(appExe: string): string {
  const integration = appIntegrations.value.find(i => i.appExe === appExe)
  return integration?.sceneId || ''
}

function toggleAppIntegration(app: RunningApp) {
  const existingIndex = appIntegrations.value.findIndex(i => i.appExe === app.exe)
  
  if (existingIndex >= 0) {
    // Toggle existing integration
    appIntegrations.value[existingIndex].enabled = !appIntegrations.value[existingIndex].enabled
  } else {
    // Create new integration
    appIntegrations.value.push({
      appExe: app.exe,
      appName: app.name,
      sceneId: '',
      enabled: true,
      autoSwitch: true
    })
  }
  
  saveAppIntegrations()
}

function updateAppScene(appExe: string, sceneId: string) {
  const integration = appIntegrations.value.find(i => i.appExe === appExe)
  if (integration) {
    integration.sceneId = sceneId
    saveAppIntegrations()
  }
}

async function createSceneForApp(app: RunningApp) {
  const profile = dashboardStore.currentProfile
  if (!profile) {
    alert('No profile loaded.')
    return
  }
  
  if (!profile.scenes || profile.scenes.length === 0) {
    alert('No scenes available. Please create a scene first.')
    return
  }
  
  // Get the first scene
  const firstScene = profile.scenes[0]
  if (!firstScene.pages || firstScene.pages.length === 0) {
    alert('No pages in scene.')
    return
  }
  
  // Create a new scene named after the app
  const sceneName = app.name.replace('.exe', '')
  
  try {
    // Check if we have shortcuts for this app
    const topShortcuts = hasShortcuts(app.exe) ? getTopShortcutsForApp(app.exe, 8) : []
    
    // Create buttons from shortcuts
    const buttons: Button[] = topShortcuts.map((shortcut, index) => createButtonFromShortcut(shortcut, index))
    
    const newScene: Scene = {
      id: `scene-${Date.now()}`,
      name: sceneName,
      icon: 'window-maximize',
      color: '#3498db',
      pages: [{
        id: `page-${Date.now()}`,
        name: 'Page 1',
        buttons: buttons,
        grid_config: { rows: 4, cols: 5 }
      }],
      triggeredByApp: app.exe,
      autoCreated: true
    }
    
    // Add scene to profile
    dashboardStore.addScene(newScene)
    
    // Update the integration with the new scene
    updateAppScene(app.exe, newScene.id)
    
    alert(`Scene "${sceneName}" created with ${buttons.length} shortcut buttons!`)
  } catch (error) {
    console.error('Failed to create scene:', error)
    alert('Failed to create scene')
  }
}

function createButtonFromShortcut(shortcut: AppShortcut, index: number): Button {
  const row = Math.floor(index / 5)
  const col = index % 5
  
  return {
    id: `button-${Date.now()}-${index}`,
    label: shortcut.name,
    secondary_label: shortcut.keys.join(' + '),
    icon: ['fas', 'keyboard'],
    icon_type: 'fontawesome',
    action: {
      type: 'hotkey',
      config: {
        keys: shortcut.keys
      }
    },
    shape: 'rounded',
    position: { row, col },
    size: { rows: 1, cols: 1 },
    style: {
      backgroundColor: '#3498db',
      textColor: '#ffffff'
    },
    tooltip: shortcut.description,
    enabled: true
  }
}

function openShortcutManager(app: RunningApp) {
  selectedAppForShortcuts.value = app
  showShortcutManager.value = true
}

function handleAddShortcut(shortcut: AppShortcut) {
  const sceneId = getAppScene(selectedAppForShortcuts.value?.exe || '')
  if (!sceneId) {
    alert('Please create a scene first')
    return
  }
  
  // Find the scene
  const profile = dashboardStore.currentProfile
  if (!profile) return
  
  const scene = profile.scenes.find(s => s.id === sceneId)
  if (!scene || !scene.pages || scene.pages.length === 0) {
    alert('Scene not found')
    return
  }
  
  // Add button to first page of scene
  const page = scene.pages[0]
  const buttons = page.buttons || []
  
  // Find first empty slot
  const gridRows = page.grid_config.rows
  const gridCols = page.grid_config.cols
  let emptySlot = null
  
  for (let row = 0; row < gridRows; row++) {
    for (let col = 0; col < gridCols; col++) {
      const occupied = buttons.some(b => 
        b.position.row === row && b.position.col === col
      )
      if (!occupied) {
        emptySlot = { row, col }
        break
      }
    }
    if (emptySlot) break
  }
  
  if (!emptySlot) {
    alert('No empty slots available in the scene')
    return
  }
  
  const newButton = createButtonFromShortcut(shortcut, 0)
  newButton.position = emptySlot
  
  dashboardStore.addButton(newButton)
  
  // Close modal
  showShortcutManager.value = false
  
  alert(`Added "${shortcut.name}" to scene!`)
}

function saveAppIntegrations() {
  // Save to localStorage
  localStorage.setItem('appIntegrations', JSON.stringify(appIntegrations.value))
}

function loadAppIntegrations() {
  const stored = localStorage.getItem('appIntegrations')
  if (stored) {
    try {
      appIntegrations.value = JSON.parse(stored)
      // Update auto scene switcher with loaded integrations
      autoSceneSwitcher.updateIntegrations(appIntegrations.value)
    } catch (error) {
      console.error('Failed to load app integrations:', error)
    }
  }
  
  // Load auto switching state
  const autoSwitchStored = localStorage.getItem('autoSceneSwitching')
  if (autoSwitchStored) {
    autoSwitchingEnabled.value = autoSwitchStored === 'true'
  }
}

async function toggleAutoSwitching() {
  const newValue = !autoSwitchingEnabled.value
  
  try {
    if (newValue) {
      // Enable auto switching
      autoSceneSwitcher.initialize(appIntegrations.value)
      const success = await autoSceneSwitcher.enable()
      
      if (success) {
        autoSwitchingEnabled.value = true
        localStorage.setItem('autoSceneSwitching', 'true')
        
        // Register scene switch callback
        autoSceneSwitcher.onSceneSwitch(handleAutoSceneSwitch)
      } else {
        alert('Failed to enable auto scene switching')
      }
    } else {
      // Disable auto switching
      const success = await autoSceneSwitcher.disable()
      
      if (success) {
        autoSwitchingEnabled.value = false
        localStorage.setItem('autoSceneSwitching', 'false')
      } else {
        alert('Failed to disable auto scene switching')
      }
    }
  } catch (error) {
    console.error('Error toggling auto switching:', error)
    alert('Error toggling auto scene switching')
  }
}

function handleAutoSceneSwitch(sceneId: string, appExe: string) {
  console.log(`Auto switching to scene ${sceneId} for app ${appExe}`)
  
  // Find the scene and switch to it
  const profile = profilesStore.currentProfile
  if (!profile) return
  
  // Find which page contains this scene
  for (const page of profile.pages) {
    const scene = page.scenes.find(s => s.id === sceneId)
    if (scene) {
      // Switch to this page and scene
      profilesStore.setCurrentPage(page.id)
      profilesStore.setCurrentScene(sceneId)
      
      // Show notification
      console.log(`Switched to scene "${scene.name}" for ${appExe}`)
      break
    }
  }
}

onMounted(async () => {
  settingsStore.loadThemes()
  settingsStore.loadServerConfig()
  loadAppIntegrations()
  loadCustomBackground()
  
  // Load running apps if on integration tab
  if (activeTab.value === 'integration') {
    await refreshRunningApps()
  }
  
  // Re-enable auto switching if it was enabled before
  if (autoSwitchingEnabled.value) {
    autoSceneSwitcher.initialize(appIntegrations.value)
    await autoSceneSwitcher.enable()
    autoSceneSwitcher.onSceneSwitch(handleAutoSceneSwitch)
  }
})

onUnmounted(() => {
  // Clean up auto scene switcher
  if (autoSwitchingEnabled.value) {
    autoSceneSwitcher.offSceneSwitch(handleAutoSceneSwitch)
  }
})
</script>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-xl);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.settings-header h1 {
  font-size: 2rem;
  font-weight: bold;
}

.settings-tabs {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.tab-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
  font-size: 0.875rem;
  font-weight: 500;
}

.tab-button:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.tab-button.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  background-color: var(--color-surface);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-width: 800px;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.settings-section h2 {
  font-size: 1.25rem;
  font-weight: bold;
}

.form-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  margin-bottom: 0;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.slider {
  width: 100%;
  height: 6px;
  background: var(--color-border);
  border-radius: var(--radius-full);
  outline: none;
  margin-bottom: var(--spacing-xs);
}

.slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  cursor: pointer;
  border: none;
}

.slider-value {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-background);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.server-info {
  margin-bottom: var(--spacing-md);
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.info-label {
  font-weight: 500;
}

.info-value {
  color: var(--color-text-secondary);
}

.settings-note {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
}

.recent-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.recent-action-item {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-family: monospace;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.about-info h3 {
  font-size: 2rem;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.about-info p {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.feature-highlights {
  background: var(--color-surface);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.feature-highlights h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}

.feature-highlights ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-highlights li {
  padding: var(--spacing-xs) 0;
  color: var(--color-text);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}


.link {
  color: var(--color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

/* App Integration Styles */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.section-description {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--spacing-lg);
}

.app-integration-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.list-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 0.5fr;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.app-item {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 0.5fr;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.app-item:hover {
  border-color: var(--color-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.app-icon {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.app-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-name {
  font-weight: 600;
  color: var(--color-text);
}

.app-exe {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-family: 'Courier New', monospace;
}

.app-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border);
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--color-primary);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.status-text {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.app-scene {
  display: flex;
  align-items: center;
}

.select-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  width: 100%;
}

.select-sm:focus {
  outline: none;
  border-color: var(--color-primary);
}

.scene-placeholder {
  color: var(--color-text-secondary);
  font-size: 1.25rem;
}

.app-actions {
  display: flex;
  gap: var(--spacing-xs);
  justify-content: flex-end;
}

.btn-icon {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-xs);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.btn-icon:hover {
  background: var(--color-surface);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.btn-icon.btn-primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn-icon.btn-primary:hover {
  background: var(--color-primary-dark);
}

.integration-summary {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  font-size: 0.875rem;
  font-weight: 500;
  margin-top: var(--spacing-md);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

/* Auto Switching Styles */
.toggle-switch-inline {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.toggle-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.auto-switch-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: #d1fae5;
  border: 1px solid #10b981;
  border-radius: var(--radius-md);
  color: #065f46;
  font-size: 0.875rem;
  margin-top: var(--spacing-md);
}

.status-icon {
  font-size: 1.25rem;
}

.status-icon.success {
  color: #10b981;
}

/* Custom Background Upload Styles */
.upload-section {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xs);
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.background-preview {
  margin-top: var(--spacing-md);
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--color-border);
  max-width: 400px;
}

.background-preview img {
  width: 100%;
  height: auto;
  display: block;
}
</style>

