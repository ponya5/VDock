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


      <!-- About Tab -->
      <div v-if="activeTab === 'about'" class="tab-content">
        <section class="settings-section card">
          <h2>About</h2>
          
          <div class="about-info">
            <h3>VDock</h3>
            <p>Virtual Stream Deck v1.0.0</p>
            <p class="mt-md">
              A customizable virtual stream deck application for controlling your computer
              with buttons and actions.
            </p>
            <div class="mt-lg">
              <button class="btn btn-secondary" @click="openGitHub">
                <FontAwesomeIcon :icon="['fab', 'github']" /> GitHub
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const settingsStore = useSettingsStore()

const settings = computed(() => settingsStore)
const themes = computed(() => settingsStore.themes)
const serverConfig = computed(() => settingsStore.serverConfig)

const activeTab = ref('appearance')

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

function openGitHub() {
  window.open('https://github.com/ponya5/VDock', '_blank')
}


onMounted(async () => {
  settingsStore.loadThemes()
  settingsStore.loadServerConfig()
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
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.about-info p {
  color: var(--color-text-secondary);
}


.link {
  color: var(--color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}
</style>

