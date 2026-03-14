<template>
  <div class="settings-view">
    <header class="settings-header">
      <h1>Settings</h1>
      <button class="btn btn-secondary" @click="router.push('/')">
        <FontAwesomeIcon :icon="['fas', 'arrow-left']" /> Back
      </button>
    </header>

    <div class="settings-layout-content">
      <nav class="settings-nav-rail">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['nav-rail-item', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <FontAwesomeIcon :icon="tab.icon" />
          <span>{{ tab.name }}</span>
        </button>
      </nav>

      <div class="settings-content">
      <!-- Appearance Tab -->
      <div v-if="activeTab === 'appearance'" class="tab-content">

        <!-- Appearance Sub-tabs -->
        <div class="sub-tab-bar">
          <button
            :class="['sub-tab-btn', { active: appearanceSubTab === 'display' }]"
            @click="appearanceSubTab = 'display'"
          >
            <FontAwesomeIcon :icon="['fas', 'sliders-h']" /> Display
          </button>
          <button
            :class="['sub-tab-btn', { active: appearanceSubTab === 'background' }]"
            @click="appearanceSubTab = 'background'"
          >
            <FontAwesomeIcon :icon="['fas', 'image']" /> Background
          </button>
        </div>

        <!-- Display sub-tab -->
        <section v-if="appearanceSubTab === 'display'" class="settings-section card">
          <h2>Display</h2>

          <TouchModeSelector />

          <div class="form-group">
            <div class="form-group-header">
              <label>Button Size</label>
              <button
                class="btn-reset"
                @click="settings.buttonSize = 1.0"
                title="Reset to default (1.0x)"
              >
                <FontAwesomeIcon :icon="['fas', 'undo']" /> Reset
              </button>
            </div>
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
              <input v-model="settings.showRegularToasts" type="checkbox" />
              <span>Show regular notifications</span>
            </label>
            <p class="form-help">Show success, info, and warning toasts. Error notifications are always shown.</p>
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
        </section>

        <!-- Background sub-tab -->
        <section v-if="appearanceSubTab === 'background'" class="settings-section card">
          <h2>Background</h2>

          <div class="form-group">
            <label>Animated Background</label>
            <div class="flex gap-sm">
              <select v-model="settings.backgroundPreference" class="select" style="flex: 1">
                <option value="none">None</option>
                <option value="particles">Dark Veil (Particles)</option>
                <option value="waves">Floating Lines (Waves)</option>
              </select>
            </div>
            <p class="form-help">Choose an animated background effect for your dashboard</p>
          </div>

          <div class="form-group">
            <label>Dashboard Background</label>
            <div class="flex gap-sm">
              <select v-model="settings.dashboardBackground" class="select" style="flex: 1">
                <option value="default">Default (Gradient)</option>
                <optgroup label="Custom Background" v-if="isCustomBackground">
                  <option :value="settings.dashboardBackground">Custom Uploaded Image</option>
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
                <option value="floating-paths">Floating Paths</option>
                <option value="floating-paths-v2">Floating Paths V2</option>
                <option value="beams-background">Beams Background</option>
              </optgroup>
            </select>
            </div>
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
                :disabled="uploadingBackground"
                @click="($refs.backgroundFileInput as HTMLInputElement).click()"
              >
                <FontAwesomeIcon :icon="uploadingBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingBackground" />
                {{ uploadingBackground ? 'Uploading...' : 'Choose Image or GIF' }}
              </button>
              <button
                v-if="isCustomBackground"
                class="btn btn-danger"
                @click="removeCustomBackground"
                title="Remove Custom Background"
              >
                <FontAwesomeIcon :icon="['fas', 'trash']" />
                Remove
              </button>
            </div>
            <div v-if="isCustomBackground" class="background-preview">
              <img :src="settings.dashboardBackground" alt="Custom Background" />
            </div>
            <p class="form-help">Upload your own image or GIF — it will be applied as the dashboard background immediately.</p>
          </div>

          <div class="form-group">
            <label>Scene Background — {{ currentScene?.name ?? 'No scene' }}</label>
            <p class="form-help" style="margin-bottom: var(--spacing-sm)">Override the background for the current scene only.</p>
            <div class="upload-section">
              <input
                ref="sceneBackgroundFileInput"
                type="file"
                accept="image/*,.gif"
                @change="handleSceneBackgroundUpload"
                class="file-input"
                style="display: none"
              />
              <button
                class="btn btn-secondary upload-btn"
                :disabled="uploadingSceneBackground || !currentScene"
                @click="($refs.sceneBackgroundFileInput as HTMLInputElement).click()"
              >
                <FontAwesomeIcon :icon="uploadingSceneBackground ? ['fas', 'spinner'] : ['fas', 'image']" :spin="uploadingSceneBackground" />
                {{ uploadingSceneBackground ? 'Uploading...' : 'Set Scene Background' }}
              </button>
              <button
                v-if="hasSceneBackground"
                class="btn btn-danger"
                @click="removeSceneBackground"
                title="Remove scene background"
              >
                <FontAwesomeIcon :icon="['fas', 'trash']" />
                Remove
              </button>
            </div>
            <div v-if="hasSceneBackground" class="background-preview">
              <img :src="currentScene!.background!.image" alt="Scene Background" />
            </div>
          </div>

        </section>

      </div>

      <!-- Templates Tab -->
      <div v-if="activeTab === 'templates'" class="tab-content">
        <section class="settings-section card">
          <h2>App Templates</h2>
          <p class="section-description">Add pre-built scenes for popular apps. Each template creates a new scene with ready-to-use buttons.</p>
        </section>

        <section
          v-for="category in templateCategories"
          :key="category.id"
          class="settings-section card template-category"
        >
          <button class="category-header" @click="toggleCategory(category.id)">
            <span class="category-title">
              <FontAwesomeIcon :icon="category.icon" class="category-icon" />
              {{ category.name }}
            </span>
            <FontAwesomeIcon
              :icon="['fas', expandedCategory === category.id ? 'chevron-up' : 'chevron-down']"
              class="category-chevron"
            />
          </button>

          <div v-if="expandedCategory === category.id" class="template-grid">
            <div
              v-for="template in category.templates"
              :key="template.id"
              class="template-card"
            >
              <div class="template-card-header" :style="{ borderLeftColor: template.color }">
                <div class="template-icon-wrap" :style="{ background: template.color + '22' }">
                  <img
                    v-if="template.logo"
                    :src="template.logo"
                    :alt="template.name"
                    class="template-logo-img"
                  />
                  <FontAwesomeIcon v-else :icon="template.icon" :style="{ color: template.color }" />
                </div>
                <div class="template-info">
                  <span class="template-name">{{ template.name }}</span>
                  <span class="template-desc">{{ template.description }}</span>
                </div>
                <button
                  class="btn btn-primary btn-sm template-add-btn"
                  :disabled="addingTemplate === template.id"
                  @click="addTemplateAsScene(template)"
                >
                  <FontAwesomeIcon :icon="addingTemplate === template.id ? ['fas', 'spinner'] : ['fas', 'plus']" :spin="addingTemplate === template.id" />
                  {{ addingTemplate === template.id ? 'Adding...' : 'Add Scene' }}
                </button>
              </div>
              <div class="template-buttons-preview">
                <span
                  v-for="btn in template.buttons.slice(0, 8)"
                  :key="btn.label"
                  class="template-btn-chip"
                  :style="{ background: btn.style?.backgroundColor ? btn.style.backgroundColor + '33' : template.color + '22', borderColor: btn.style?.backgroundColor ?? template.color }"
                >
                  <FontAwesomeIcon :icon="btn.icon" :style="{ color: btn.style?.backgroundColor ?? template.color }" />
                  {{ btn.label }}
                </span>
                <span v-if="template.buttons.length > 8" class="template-btn-chip template-btn-more">
                  +{{ template.buttons.length - 8 }} more
                </span>
              </div>
            </div>
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
            <div v-if="settings.authEnabled" class="auth-instructions">
              <div class="instruction-box">
                <h4><FontAwesomeIcon :icon="['fas', 'key']" /> Password Configuration</h4>
                <p><strong>To set your access password:</strong></p>
                <ol>
                  <li>Open <code>backend/.env</code> file in a text editor</li>
                  <li>Find the line: <code>AUTH_PASSWORD=your-secure-password-here</code></li>
                  <li>Replace <code>your-secure-password-here</code> with your desired password</li>
                  <li>Save the file and restart VDock</li>
                </ol>
                <p class="security-note">
                  <FontAwesomeIcon :icon="['fas', 'shield-alt']" />
                  <strong>Security tip:</strong> Use a strong password with at least 12 characters including letters, numbers, and symbols.
                </p>
              </div>
            </div>
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

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="settings.startWithWindows" type="checkbox" @change="handleStartWithWindowsToggle" />
              <span>Start with Windows (Desktop App)</span>
            </label>
            <p class="form-help">Launch VDock desktop application when Windows starts (requires desktop app)</p>
            <p v-if="startWithWindowsStatus" class="form-help" :class="startWithWindowsStatus.success ? 'text-success' : 'text-error'">
              {{ startWithWindowsStatus.message }}
            </p>
          </div>

          <div class="form-group">
            <label>Server Host</label>
            <input 
              v-model="serverHost" 
              type="text" 
              class="input" 
              placeholder="localhost"
              @change="updateServerConfig"
            />
            <p class="form-help">Server host address (default: localhost)</p>
          </div>

          <div class="form-group">
            <label>Server Port</label>
            <input 
              v-model.number="serverPort" 
              type="number" 
              class="input" 
              min="1024" 
              max="65535"
              placeholder="5000"
              @change="updateServerConfig"
            />
            <p class="form-help">Server port number (default: 5000)</p>
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
            
            <div class="mt-lg about-links">
              <a href="https://www.daniel-shalom.com/" target="_blank" rel="noopener" class="about-link-btn">
                <FontAwesomeIcon :icon="['fas', 'globe']" /> Website
              </a>
              <a href="https://github.com/ponya5" target="_blank" rel="noopener" class="about-link-btn">
                <FontAwesomeIcon :icon="['fab', 'github']" /> GitHub
              </a>
              <a href="https://www.linkedin.com/in/daniel-shalom-13987a1a/" target="_blank" rel="noopener" class="about-link-btn">
                <FontAwesomeIcon :icon="['fab', 'linkedin']" /> LinkedIn
              </a>
              <button class="about-link-btn" @click="contactEmail">
                <FontAwesomeIcon :icon="['fas', 'envelope']" /> Contact
              </button>
              <span class="about-copyright">Daniel Shalom. All rights reserved 2026 ©</span>
            </div>
          </div>
        </section>

        <!-- Ko-fi Support Section -->
        <section class="settings-section card kofi-section">
          <h2>Support the Project</h2>
          <p class="section-description">If you enjoy using VDock, consider buying me a coffee. It helps keep the project alive and growing.</p>
          <a
            href="https://ko-fi.com/danielshalom"
            target="_blank"
            rel="noopener"
            class="kofi-btn"
          >
            <img src="https://storage.ko-fi.com/cdn/cup-border.png" alt="Ko-fi" class="kofi-icon" />
            Support me on Ko-fi
          </a>
        </section>
      </div>
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
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import TouchModeSelector from '@/components/TouchModeSelector.vue'
import apiClient from '@/api/client'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import AppShortcutManager from '@/components/AppShortcutManager.vue'
import { hasShortcuts, getTopShortcutsForApp, type AppShortcut } from '@/data/appShortcuts'
import { templateCategories, type AppTemplate } from '@/data/appTemplates'
import type { RunningApp, AppIntegration, Scene, Button } from '@/types'

const router = useRouter()
const settingsStore = useSettingsStore()
const profilesStore = useProfilesStore()
const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()

const settings = computed(() => settingsStore)
const serverConfig = computed(() => settingsStore.serverConfig)

const activeTab = ref('appearance')
const appearanceSubTab = ref<'display' | 'background'>('display')

// Templates state
const expandedCategory = ref<string | null>(null)
const addingTemplate = ref<string | null>(null)

function toggleCategory(id: string) {
  expandedCategory.value = expandedCategory.value === id ? null : id
}

async function addTemplateAsScene(template: AppTemplate) {
  const profile = dashboardStore.currentProfile
  if (!profile) {
    notificationsStore.error('No profile', 'Load a profile first.')
    return
  }
  addingTemplate.value = template.id
  try {
    const buttons: Button[] = template.buttons.map((b, index) => ({
      id: `button-${Date.now()}-${index}`,
      label: b.label,
      icon: b.icon,
      icon_type: 'fontawesome',
      action: b.action,
      shape: 'rounded',
      position: { row: Math.floor(index / 5), col: index % 5 },
      size: { rows: 1, cols: 1 },
      style: { backgroundColor: b.style?.backgroundColor ?? template.color, textColor: b.style?.textColor ?? '#ffffff' },
      tooltip: b.tooltip ?? b.label,
      enabled: true
    }))

    const newScene: Scene = {
      id: `scene-${Date.now()}`,
      name: template.name,
      icon: template.icon[1] ?? 'layer-group',
      color: template.color,
      pages: [{
        id: `page-${Date.now()}`,
        name: 'Page 1',
        buttons,
        grid_config: { rows: 4, cols: 5 }
      }],
      autoCreated: false
    }

    dashboardStore.addScene(newScene)
    notificationsStore.success('Scene added', `"${template.name}" scene added to your dashboard.`)
  } finally {
    addingTemplate.value = null
  }
}

// Custom Background State
const backgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingBackground = ref(false)
const sceneBackgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingSceneBackground = ref(false)

const NAMED_BACKGROUNDS = ['ocean-breeze','sunset-glow','forest-mist','royal-purple','golden-hour','floating-particles','gradient-waves','geometric-patterns','aurora-borealis','starfield','bubble-float','neon-grid','floating-paths','floating-paths-v2','beams-background','default']

// True when the dashboardBackground is a custom uploaded image URL
const isCustomBackground = computed(() => {
  const bg = settings.value.dashboardBackground
  return bg.startsWith('/api/uploads/') ||
    bg.startsWith('/uploads/') ||
    (bg.startsWith('http') && !NAMED_BACKGROUNDS.includes(bg))
})

// Current scene background
const currentScene = computed(() => dashboardStore.currentScene)
const hasSceneBackground = computed(() =>
  !!currentScene.value?.background?.image
)

// Handle global background file upload
const handleBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']
  if (!validTypes.includes(file.type)) {
    notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    notificationsStore.error('File too large', 'Maximum file size is 10MB.')
    return
  }

  uploadingBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', 'dashboard_background')

    const response = await apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.success) {
      // Prepend /api so the URL matches the served route
      const url = response.data.url.startsWith('/api')
        ? response.data.url
        : '/api' + response.data.url
      settingsStore.dashboardBackground = url
      notificationsStore.success('Background updated', 'Custom background applied successfully.')
    } else {
      notificationsStore.error('Upload failed', response.data.error || 'Unknown error')
    }
  } catch (error: any) {
    notificationsStore.error('Upload failed', error.message || 'Unknown error')
  } finally {
    uploadingBackground.value = false
    if (target) target.value = ''
  }
}

// Handle per-scene background upload
const handleSceneBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !currentScene.value) return

  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']
  if (!validTypes.includes(file.type)) {
    notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    notificationsStore.error('File too large', 'Maximum file size is 10MB.')
    return
  }

  uploadingSceneBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', 'dashboard_background')

    const response = await apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.success) {
      const url = response.data.url.startsWith('/api')
        ? response.data.url
        : '/api' + response.data.url
      dashboardStore.updateScene(currentScene.value!.id, {
        background: { type: 'image', image: url }
      })
      notificationsStore.success('Scene background updated', `Background applied to "${currentScene.value!.name}".`)
    } else {
      notificationsStore.error('Upload failed', response.data.error || 'Unknown error')
    }
  } catch (error: any) {
    notificationsStore.error('Upload failed', error.message || 'Unknown error')
  } finally {
    uploadingSceneBackground.value = false
    if (target) target.value = ''
  }
}

// Remove custom background
const removeCustomBackground = () => {
  settingsStore.dashboardBackground = 'default'
  notificationsStore.success('Background removed', 'Reverted to default background.')
}

// Remove scene background
const removeSceneBackground = () => {
  if (!currentScene.value) return
  dashboardStore.updateScene(currentScene.value.id, { background: undefined })
  notificationsStore.success('Scene background removed', `Background cleared for "${currentScene.value.name}".`)
}

// App Integration State
const runningApps = ref<RunningApp[]>([])
const loadingApps = ref(false)
const appIntegrations = ref<AppIntegration[]>([])
const autoSwitchingEnabled = ref(false)
const showShortcutManager = ref(false)
const selectedAppForShortcuts = ref<RunningApp | null>(null)
const startOnBootStatus = ref<{success: boolean, message: string} | null>(null)
const startWithWindowsStatus = ref<{success: boolean, message: string} | null>(null)

// Server configuration
const serverHost = ref('localhost')
const serverPort = ref(5000)

const availableScenes = computed(() => {
  const profile = profilesStore.currentProfile
  if (!profile) return []
  
  // Return all scenes from the profile
  return (profile.scenes || []).map(scene => ({
    id: scene.id,
    name: scene.name
  }))
})

const tabs = [
  { id: 'appearance', name: 'Appearance', icon: ['fas', 'palette'] },
  { id: 'templates', name: 'Templates', icon: ['fas', 'layer-group'] },
  { id: 'server', name: 'Server', icon: ['fas', 'server'] },
  { id: 'integration', name: 'Integration', icon: ['fas', 'plug'] },
  { id: 'about', name: 'About', icon: ['fas', 'info-circle'] }
]

onMounted(() => {
  // Theme is fixed to dark mode - no need to load themes
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

async function handleStartWithWindowsToggle() {
  try {
    // Check if we're running in Electron
    if (window.electronAPI) {
      const result = await window.electronAPI.toggleAutoLaunch(settings.value.startWithWindows)
      startWithWindowsStatus.value = {
        success: result,
        message: result 
          ? 'VDock will now start with Windows'
          : 'Auto-start with Windows disabled'
      }
    } else {
      startWithWindowsStatus.value = {
        success: false,
        message: 'This feature is only available in the desktop application'
      }
      settings.value.startWithWindows = !settings.value.startWithWindows
    }
  } catch (error) {
    console.error('Failed to toggle Windows auto-start:', error)
    startWithWindowsStatus.value = {
      success: false,
      message: 'Failed to update Windows auto-start setting'
    }
    settings.value.startWithWindows = !settings.value.startWithWindows
  }

  // Clear status after 5 seconds
  setTimeout(() => {
    startWithWindowsStatus.value = null
  }, 5000)
}

function openGitHub() {
  window.open('https://github.com/ponya5/VDock', '_blank')
}

function contactEmail() {
  window.location.href = 'mailto:ponya81@gmail.com?subject=VDock%20Support'
}

function updateServerConfig() {
  // Update server configuration
  // Note: This would typically require backend restart to take effect
  console.log('Server config updated:', { host: serverHost.value, port: serverPort.value })
  
  // Save to localStorage for persistence
  localStorage.setItem('vdock_server_host', serverHost.value)
  localStorage.setItem('vdock_server_port', serverPort.value.toString())
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
  // Theme is fixed to dark mode - no need to load themes
  settingsStore.loadServerConfig()
  loadAppIntegrations()
  
  // Load server configuration from localStorage
  const savedHost = localStorage.getItem('vdock_server_host')
  const savedPort = localStorage.getItem('vdock_server_port')
  if (savedHost) serverHost.value = savedHost
  if (savedPort) serverPort.value = parseInt(savedPort)
  
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
  font-size: clamp(1.60rem, 2vw + 1.00rem, 2.40rem);
  font-weight: bold;
}

.settings-layout-content {
  display: flex;
  flex: 1;
  gap: var(--spacing-xl);
  overflow: hidden;
  min-height: 0;
}

.settings-nav-rail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  width: 200px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  padding-right: var(--spacing-md);
  overflow-y: auto;
}

.nav-rail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  font-size: clamp(0.90rem, 2vw + 0.56rem, 1.35rem);
  font-weight: 500;
  min-height: 48px;
}

.nav-rail-item:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.nav-rail-item.active {
  color: var(--color-primary);
  background-color: var(--color-primary-light);
  font-weight: 600;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--spacing-md);
  max-width: 800px;
}

@media (max-width: 768px) {
  .settings-layout-content {
    flex-direction: column;
  }
  
  .settings-nav-rail {
    flex-direction: row;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
    padding-right: 0;
    padding-bottom: var(--spacing-md);
    overflow-x: auto;
    overflow-y: hidden;
  }
  
  .nav-rail-item {
    flex-direction: column;
    justify-content: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    flex: 1;
    min-width: 70px;
  }
  
  .nav-rail-item span {
    font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  }

  /* App integration responsive */
  .list-header {
    display: none; /* Hide multi-col header on mobile */
  }

  .app-item {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }

  .app-status, .app-scene, .app-actions {
    justify-content: flex-start;
  }
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.settings-section h2 {
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
  font-weight: bold;
}

.form-help {
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
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
  min-height: 44px; /* Touch target */
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
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  font-weight: 500;
}

.form-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.btn-reset {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.btn-reset:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
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
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  font-family: monospace;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.about-info h3 {
  font-size: clamp(1.60rem, 2vw + 1.00rem, 2.40rem);
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
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
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
  font-size: clamp(0.72rem, 2vw + 0.45rem, 1.08rem);
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
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
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
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
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
  font-size: clamp(1.20rem, 2vw + 0.75rem, 1.80rem);
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
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
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
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.app-scene {
  display: flex;
  align-items: center;
}

.select-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  width: 100%;
  min-height: 44px; /* Touch target */
}

.select-sm:focus {
  outline: none;
  border-color: var(--color-primary);
}

.scene-placeholder {
  color: var(--color-text-secondary);
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
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
  width: 44px; /* Touch target */
  height: 44px; /* Touch target */
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
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
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
  min-height: 44px; /* Touch target */
}

.toggle-label {
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
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
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  margin-top: var(--spacing-md);
}

.status-icon {
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
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

.auth-instructions {
  margin-top: var(--spacing-md);
}

.instruction-box {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-top: var(--spacing-sm);
}

.instruction-box h4 {
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.instruction-box ol {
  margin: var(--spacing-md) 0;
  padding-left: var(--spacing-xl);
}

.instruction-box li {
  margin-bottom: var(--spacing-xs);
  line-height: 1.5;
}

.instruction-box code {
  background: var(--color-background);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: var(--color-primary);
}

.security-note {
  background: rgba(52, 152, 219, 0.1);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  margin-top: var(--spacing-md);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  font-size: 0.9em;
}

.security-note svg {
  color: var(--color-primary);
  margin-top: 2px;
}

/* Appearance sub-tabs */
.sub-tab-bar {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-background);
  padding-top: var(--spacing-xs);
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
  font-weight: 500;
  transition: all var(--transition-fast);
  min-height: 44px;
  border-bottom: 2px solid transparent;
}

.sub-tab-btn:hover {
  color: var(--color-text);
  background: var(--color-surface);
}

.sub-tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

/* Template styles */
.template-category {
  padding: 0;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text);
  font-size: clamp(0.90rem, 2vw + 0.56rem, 1.35rem);
  font-weight: 600;
  transition: background var(--transition-fast);
  min-height: 56px;
}

.category-header:hover {
  background: var(--color-surface);
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.category-icon {
  color: var(--color-primary);
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
}

.category-chevron {
  color: var(--color-text-secondary);
  transition: transform var(--transition-fast);
}

.template-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-lg) var(--spacing-lg);
}

.template-card {
  background: var(--glass-bg, rgba(0,0,0,0.25));
  backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  border-radius: var(--radius-md);
  overflow: hidden;
}

.template-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-left: 3px solid var(--color-primary);
}

.template-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  font-size: clamp(1.20rem, 2vw + 0.75rem, 1.80rem);
}

.template-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 6px;
}

.template-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.template-name {
  font-weight: 600;
  font-size: clamp(0.85rem, 2vw + 0.53rem, 1.28rem);
  color: var(--color-text);
}

.template-desc {
  font-size: clamp(0.65rem, 2vw + 0.41rem, 0.98rem);
  color: var(--color-text-secondary);
}

.template-add-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  min-height: 44px;
}

.template-buttons-preview {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.template-btn-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px var(--spacing-sm);
  border-radius: var(--radius-full);
  border: 1px solid;
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  color: var(--color-text);
  white-space: nowrap;
}

.template-btn-more {
  background: var(--color-surface) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-secondary);
}

/* About links */
.about-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
}

.about-link-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--glass-bg, rgba(0,0,0,0.25));
  backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--transition-fast);
  min-height: 44px;
}

.about-link-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.about-copyright {
  color: var(--color-text-secondary);
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  margin-left: auto;
}

/* Ko-fi section */
.kofi-section {
  text-align: center;
}

.kofi-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background: #00b9fe;
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  font-size: clamp(0.90rem, 2vw + 0.56rem, 1.35rem);
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--transition-fast);
  min-height: 52px;
  margin-top: var(--spacing-md);
}

.kofi-btn:hover {
  background: #009fd9;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 185, 254, 0.35);
}

.kofi-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
}
</style>

