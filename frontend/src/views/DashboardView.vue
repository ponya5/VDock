<template>
  <div class="dashboard-view" :class="dashboardBackgroundClass" :style="dashboardBackgroundStyle">
    <header class="deck-header enhanced-header">
      <div class="header-background"></div>
      <div class="header-content">
        <div class="header-left">
          <div class="profile-avatar-container">
            <img 
              v-if="currentProfile?.avatar" 
              :src="currentProfile.avatar" 
              :alt="currentProfile.name"
              class="profile-avatar enhanced-avatar"
            />
            <div v-else class="profile-avatar-placeholder enhanced-avatar">
              <FontAwesomeIcon :icon="['fas', 'user']" />
            </div>
            <div class="avatar-status-indicator"></div>
          </div>
          <h1 class="profile-title-inline">{{ currentProfile?.name || 'VDock' }}</h1>
          <SceneNavigation
            v-if="currentProfile && currentProfile.scenes.length > 0"
            :scenes="currentProfile.scenes"
            :current-scene-index="currentSceneIndex"
            :is-edit-mode="isEditMode"
            @set-scene="setScene"
            @add-scene="addScene"
            @edit-scene="editScene"
            class="enhanced-scene-nav"
          />
        </div>

        <div class="header-center">
          <PageNavigation
            v-if="currentScene && currentScene.pages.length > 1"
            :pages="currentScene.pages"
            :current-page="currentPageIndex"
            @previous="previousPage"
            @next="nextPage"
            @go-to="setPage"
            class="enhanced-page-nav"
          />
        </div>

        <div class="header-right">
          <button class="btn btn-glass enhanced-btn" @click="showHelp = true" title="Help & Guide">
            <FontAwesomeIcon :icon="['fas', 'question-circle']" />
            <span class="btn-label">Help</span>
          </button>
          <button class="btn btn-glass enhanced-btn" @click="router.push('/profiles')" title="Profiles">
            <FontAwesomeIcon :icon="['fas', 'users']" />
            <span class="btn-label">Profiles</span>
          </button>
          <button
            class="btn enhanced-btn"
            :class="isEditMode ? 'btn-glow edit-active' : 'btn-glass'"
            @click="toggleEditMode"
            title="Toggle Edit Mode"
          >
            <FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" />
            <span class="btn-label">{{ isEditMode ? 'View' : 'Edit' }}</span>
          </button>
          <button class="btn btn-glass enhanced-btn" @click="router.push('/settings')" title="Settings">
            <FontAwesomeIcon :icon="['fas', 'cog']" />
            <span class="btn-label">Settings</span>
          </button>
        </div>
      </div>
    </header>

    <main class="deck-main" :style="mainStyle">
      <!-- Docked Sidebar -->
      <DockedSidebar
        v-if="settingsStore.dockedSidebarEnabled && currentPage"
        :docked-buttons="currentProfile?.dockedButtons || []"
        :grid-rows="currentPage.grid_config.rows"
        :is-edit-mode="isEditMode"
        :show-labels="settingsStore.showLabels"
        :show-tooltips="settingsStore.showTooltips"
        :button-size="settingsStore.buttonSize"
        @button-click="handleButtonClick"
        @button-edit="handleButtonEdit"
        @button-copy="handleButtonCopy"
        @button-delete="handleDockedButtonDelete"
        @button-drop="handleDockedButtonDrop"
        @add-button="handleAddDockedButton"
        @placeholder-click="handleDockedPlaceholderClick"
      />
      
      
      <div class="main-content" :class="{ 'with-sidebar': isEditMode, 'with-docked-sidebar': settingsStore.dockedSidebarEnabled }">
        <DeckGrid
          v-if="currentPage"
          :page="currentPage"
          :is-edit-mode="isEditMode"
          :button-size="settingsStore.buttonSize"
          :show-labels="settingsStore.showLabels"
          :show-tooltips="settingsStore.showTooltips"
          @button-click="handleButtonClick"
          @button-edit="handleButtonEdit"
          @button-copy="handleButtonCopy"
          @button-delete="handleButtonDelete"
          @swipe-left="nextPage"
          @swipe-right="previousPage"
          @action-drop="handleActionDrop"
          @placeholder-click="handlePlaceholderClick"
          @button-move="handleButtonMove"
        />

        <div v-else class="no-profile">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" class="no-profile-icon" />
          <p>No profile loaded</p>
          <button class="btn btn-primary" @click="router.push('/profiles')">
            Select Profile
          </button>
        </div>
      </div>

      <!-- Edit Sidebar -->
      <aside v-if="isEditMode" class="edit-sidebar">
        <div class="sidebar-header">
          <h3>Button Actions</h3>
          <button class="btn btn-sm btn-secondary" @click="closeSidebar" title="Close Sidebar">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>

        <div class="sidebar-content">
          <div class="search-section">
            <input 
              v-model="actionSearch" 
              type="text" 
              placeholder="Search actions..." 
              class="search-input"
            />
          </div>

          <div class="categories-section">
            <div 
              v-for="category in filteredCategories" 
              :key="category.id"
              class="category-group"
            >
              <div 
                class="category-header" 
                @click="toggleCategory(category.id)"
              >
                <FontAwesomeIcon 
                  :icon="['fas', expandedCategories.includes(category.id) ? 'chevron-down' : 'chevron-right']" 
                />
                <span>{{ category.name }}</span>
                <span class="category-count">({{ category.actions.length }})</span>
              </div>

              <div 
                v-if="expandedCategories.includes(category.id)" 
                class="category-actions"
              >
                <div 
                  v-for="action in category.actions" 
                  :key="action.id"
                  class="action-item"
                  draggable="true"
                  @click="selectAction(action)"
                  @dragstart="handleDragStart($event, action)"
                  @dragend="handleDragEnd"
                >
                  <FontAwesomeIcon :icon="action.icon" />
                  <span>{{ action.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <footer v-if="isEditMode" class="deck-footer" :class="{ 'with-docked-sidebar': settingsStore.dockedSidebarEnabled }">
      <div class="footer-section">
        <label>Grid Size:</label>
        <div class="grid-controls">
          <input
            v-model.number="currentPage.grid_config.rows"
            type="number"
            min="1"
            max="10"
            class="grid-input"
            title="Rows"
          />
          <span>×</span>
          <input
            v-model.number="currentPage.grid_config.cols"
            type="number"
            min="1"
            max="10"
            class="grid-input"
            title="Columns"
          />
        </div>
      </div>

      <div class="footer-section">
        <button
          class="btn btn-primary btn-sm"
          @click="addPageToCurrentScene"
          title="Add new page to current scene"
        >
          <FontAwesomeIcon :icon="['fas', 'plus']" />
          Add Page
        </button>
      </div>

      <div class="footer-section footer-spacer"></div>

      <div class="footer-section">
        <button
          class="btn btn-success btn-sm"
          @click="saveProfile"
          title="Save all changes to profile"
        >
          <FontAwesomeIcon :icon="['fas', 'save']" />
          Save Profile
        </button>
      </div>
    </footer>

    <!-- Button Editor Modal -->
    <ButtonEditor
      v-if="editingButton"
      :button="editingButton"
      :profile-id="currentProfile?.id || ''"
      @save="handleButtonSave"
      @save-profile="handleSaveProfileFromEditor"
      @close="editingButton = null"
    />

    <!-- Scene Editor Modal -->
    <SceneEditor
      v-if="editingScene"
      :scene="editingScene"
      :is-editing="isEditingExistingScene"
      @save="handleSceneSave"
      @delete="handleSceneDelete"
      @close="editingScene = null"
    />

    <!-- Action Result Toast -->
    <div v-if="actionResult" class="action-toast" :class="actionResult.success ? 'success' : 'error'">
      {{ actionResult.message }}
    </div>

    <!-- Help Modal -->
    <div v-if="showHelp" class="modal-overlay" @click.self="showHelp = false">
      <div class="help-modal modal">
        <div class="modal-header">
          <h2><FontAwesomeIcon :icon="['fas', 'question-circle']" /> VDock User Guide</h2>
          <button class="close-btn" @click="showHelp = false">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>
        <div class="help-content">
          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'rocket']" /> Quick Start</h3>
            <ol>
              <li><strong>Toggle Edit Mode</strong>: Click the Edit button to add/modify buttons</li>
              <li><strong>Add Buttons</strong>: Click empty cells or use the Actions sidebar</li>
              <li><strong>Configure Actions</strong>: Choose what each button does (Hotkey, Program, URL, etc.)</li>
              <li><strong>Save Changes</strong>: Click "Save Profile" button in footer</li>
            </ol>
          </div>

          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'keyboard']" /> Button Actions</h3>
            <ul>
              <li><strong>Hotkey</strong>: Send keyboard shortcuts (e.g., Ctrl+C, Ctrl+V)</li>
              <li><strong>Program</strong>: Launch applications</li>
              <li><strong>URL</strong>: Open websites in browser</li>
              <li><strong>Command</strong>: Run shell commands</li>
              <li><strong>Macro</strong>: Multi-step automation</li>
              <li><strong>System</strong>: Volume, brightness, media controls</li>
              <li><strong>Navigation</strong>: Navigate between pages</li>
              <li><strong>Metrics</strong>: Display system stats (CPU, RAM, GPU)</li>
            </ul>
          </div>

          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'layer-group']" /> Scenes & Pages</h3>
            <ul>
              <li><strong>Scenes</strong>: Different button layouts (Work, Gaming, Streaming)</li>
              <li><strong>Pages</strong>: Multiple pages within each scene</li>
              <li><strong>Add Page</strong>: Click "Add Page" button in footer</li>
              <li><strong>Navigate</strong>: Use Next/Previous buttons (loops around)</li>
              <li><strong>Edit Scene</strong>: Click edit icon next to scene name</li>
            </ul>
          </div>

          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" /> Troubleshooting</h3>
            <ul>
              <li><strong>Hotkeys not working?</strong> Restart backend server (see docs/)</li>
              <li><strong>Changes not saving?</strong> Click "Save Profile" button</li>
              <li><strong>Buttons disappeared?</strong> Hard refresh browser (Ctrl+Shift+R)</li>
              <li><strong>Backend not responding?</strong> Check if running at localhost:5000</li>
            </ul>
          </div>

          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'book']" /> Documentation</h3>
            <p>For detailed documentation, see:</p>
            <ul>
              <li><code>docs/USER_GUIDE.md</code> - Complete user guide</li>
              <li><code>docs/CHANGELOG.md</code> - Version history</li>
              <li><code>README.md</code> - Project overview</li>
            </ul>
          </div>

          <div class="help-section">
            <h3><FontAwesomeIcon :icon="['fas', 'envelope']" /> Support</h3>
            <p>Need help?</p>
            <ul>
              <li><strong>Email</strong>: <a href="mailto:ponya81@gmail.com">ponya81@gmail.com</a></li>
              <li><strong>GitHub</strong>: <a href="https://github.com/ponya5/VDock" target="_blank">Report Issues</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { useProfilesStore } from '@/stores/profiles'
import { useSettingsStore } from '@/stores/settings'
import type { Button, ActionResult, Scene } from '@/types'
import DeckGrid from '@/components/DeckGrid.vue'
import PageNavigation from '@/components/PageNavigation.vue'
import SceneNavigation from '@/components/SceneNavigation.vue'
import ButtonEditor from '@/components/ButtonEditor.vue'
import SceneEditor from '@/components/SceneEditor.vue'
import DockedSidebar from '@/components/DockedSidebar.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const dashboardStore = useDashboardStore()
const profilesStore = useProfilesStore()
const settingsStore = useSettingsStore()

const editingButton = ref<Button | null>(null)
const editingScene = ref<Scene | null>(null)
const actionResult = ref<ActionResult | null>(null)
const clipboardButton = ref<Button | null>(null)
const showHelp = ref(false)
let actionResultTimeout: number | null = null

// Sidebar state
const actionSearch = ref('')
const expandedCategories = ref<string[]>(['system', 'media', 'web', 'metrics', 'time', 'weather', 'navigation'])
const selectedAction = ref<any>(null)

const currentProfile = computed(() => dashboardStore.currentProfile)
const currentScene = computed(() => dashboardStore.currentScene)
const currentPage = computed(() => dashboardStore.currentPage)
const currentSceneIndex = computed(() => dashboardStore.currentSceneIndex)
const currentPageIndex = computed(() => dashboardStore.currentPageIndex)
const isEditMode = computed(() => dashboardStore.isEditMode)

const isEditingExistingScene = computed(() => {
  if (!editingScene.value || !currentProfile.value) return false
  return currentProfile.value.scenes.some(scene => scene.id === editingScene.value!.id)
})

const dashboardBackgroundClass = computed(() => {
  const bg = settingsStore.dashboardBackground
  if (bg === 'default') return ''
  // Check if it's a custom uploaded image (URL)
  if (bg.startsWith('/api/uploads/') || bg.startsWith('http')) {
    return 'dashboard-bg-custom'
  }
  return `dashboard-bg-${bg}`
})

const dashboardBackgroundStyle = computed(() => {
  const bg = settingsStore.dashboardBackground
  // Handle custom image backgrounds
  if (bg.startsWith('/api/uploads/') || bg.startsWith('http')) {
    return {
      backgroundImage: `url(${bg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  return {}
})

// Button action categories
const actionCategories = ref([
  {
    id: 'system',
    name: 'System',
    actions: [
      { id: 'shutdown', name: 'Shutdown', icon: ['fas', 'power-off'] },
      { id: 'restart', name: 'Restart', icon: ['fas', 'redo'] },
      { id: 'sleep', name: 'Sleep', icon: ['fas', 'moon'] },
      { id: 'lock', name: 'Lock Screen', icon: ['fas', 'lock'] },
      { id: 'fullscreen', name: 'Full Screen', icon: ['fas', 'expand'] },
      { id: 'volume-up', name: 'Volume Up', icon: ['fas', 'volume-up'] },
      { id: 'volume-down', name: 'Volume Down', icon: ['fas', 'volume-down'] },
      { id: 'volume-mute', name: 'Mute', icon: ['fas', 'volume-mute'] },
      { id: 'brightness-up', name: 'Brightness Up', icon: ['fas', 'sun'] },
      { id: 'brightness-down', name: 'Brightness Down', icon: ['fas', 'moon'] }
    ]
  },
  {
    id: 'media',
    name: 'Media Control',
    actions: [
      { id: 'play-pause', name: 'Play/Pause', icon: ['fas', 'play'] },
      { id: 'next-track', name: 'Next Track', icon: ['fas', 'forward'] },
      { id: 'prev-track', name: 'Previous Track', icon: ['fas', 'backward'] },
      { id: 'stop', name: 'Stop', icon: ['fas', 'stop'] },
      { id: 'volume-up-media', name: 'Volume Up', icon: ['fas', 'volume-up'] },
      { id: 'volume-down-media', name: 'Volume Down', icon: ['fas', 'volume-down'] },
      { id: 'mute-media', name: 'Mute', icon: ['fas', 'volume-mute'] }
    ]
  },
  {
    id: 'web',
    name: 'Web & Apps',
    actions: [
      { id: 'open-url', name: 'Open URL', icon: ['fas', 'globe'] },
      { id: 'open-app', name: 'Open Application', icon: ['fas', 'rocket'] },
      { id: 'open-folder', name: 'Open Folder', icon: ['fas', 'folder-open'] },
      { id: 'open-file', name: 'Open File', icon: ['fas', 'file'] },
      { id: 'screenshot', name: 'Screenshot', icon: ['fas', 'camera'] },
      { id: 'clipboard', name: 'Copy to Clipboard', icon: ['fas', 'clipboard'] }
    ]
  },
  {
    id: 'text',
    name: 'Text & Input',
    actions: [
      { id: 'type-text', name: 'Type Text', icon: ['fas', 'keyboard'] },
      { id: 'hotkey', name: 'Hotkey', icon: ['fas', 'keyboard'] },
      { id: 'delay', name: 'Delay', icon: ['fas', 'clock'] },
      { id: 'enter-key', name: 'Enter Key', icon: ['fas', 'arrow-down'] },
      { id: 'tab-key', name: 'Tab Key', icon: ['fas', 'arrow-right'] },
      { id: 'escape-key', name: 'Escape Key', icon: ['fas', 'times'] }
    ]
  },
  {
    id: 'streaming',
    name: 'Streaming',
    actions: [
      { id: 'obs-scene', name: 'OBS Scene', icon: ['fas', 'video'] },
      { id: 'obs-source', name: 'OBS Source', icon: ['fas', 'layer-group'] },
      { id: 'obs-filter', name: 'OBS Filter', icon: ['fas', 'filter'] },
      { id: 'stream-start', name: 'Start Stream', icon: ['fas', 'play-circle'] },
      { id: 'stream-stop', name: 'Stop Stream', icon: ['fas', 'stop-circle'] },
      { id: 'recording-start', name: 'Start Recording', icon: ['fas', 'record-vinyl'] },
      { id: 'recording-stop', name: 'Stop Recording', icon: ['fas', 'stop'] }
    ]
  },
  {
    id: 'custom',
    name: 'Custom',
    actions: [
      { id: 'custom-icon', name: 'Custom Icon', icon: ['fas', 'image'] },
      { id: 'custom-gif', name: 'Custom GIF', icon: ['fas', 'film'] },
      { id: 'custom-video', name: 'Custom Video', icon: ['fas', 'video'] },
      { id: 'custom-sound', name: 'Custom Sound', icon: ['fas', 'volume-up'] }
    ]
  },
  {
    id: 'metrics',
    name: 'Monitor Metrics',
    actions: [
      { id: 'metric_memory', name: 'Memory', icon: ['fas', 'memory'] },
      { id: 'metric_cpu_usage', name: 'CPU usage', icon: ['fas', 'microchip'] },
      { id: 'metric_cpu_temperature', name: 'CPU temperature', icon: ['fas', 'thermometer-half'] },
      { id: 'metric_cpu_frequency', name: 'CPU frequency', icon: ['fas', 'wave-square'] },
      { id: 'metric_cpu_power', name: 'CPU package power', icon: ['fas', 'bolt'] },
      { id: 'metric_internet_speed', name: 'Internet speed', icon: ['fas', 'network-wired'] },
      { id: 'metric_harddisk', name: 'Harddisk', icon: ['fas', 'hdd'] },
      { id: 'metric_gpu_temperature', name: 'GPU temperature', icon: ['fas', 'thermometer-half'] },
      { id: 'metric_gpu_frequency', name: 'GPU core frequency', icon: ['fas', 'wave-square'] },
      { id: 'metric_gpu_usage', name: 'GPU Core Usage', icon: ['fas', 'grip-vertical'] },
      { id: 'metric_gpu_memory_freq', name: 'GPU memory frequency', icon: ['fas', 'memory'] },
      { id: 'metric_gpu_memory_usage', name: 'GPU Memory Usage', icon: ['fas', 'memory'] }
    ]
  },
  {
    id: 'time',
    name: 'Time',
    actions: [
      { id: 'time_world_clock', name: 'World Time', icon: ['fas', 'globe'] },
      { id: 'time_timer', name: 'Timer', icon: ['fas', 'stopwatch'] },
      { id: 'time_countdown', name: 'Countdown', icon: ['fas', 'hourglass-half'] }
    ]
  },
  {
    id: 'weather',
    name: 'Weather',
    actions: [
      { id: 'weather', name: 'Weather query', icon: ['fas', 'cloud-sun'] }
    ]
  },
  {
    id: 'navigation',
    name: 'Navigation',
    actions: [
      { id: 'next-page', name: 'Next Page', icon: ['fas', 'arrow-right'] },
      { id: 'previous-page', name: 'Previous Page', icon: ['fas', 'arrow-left'] },
      { id: 'home-page', name: 'Home Page', icon: ['fas', 'home'] }
    ]
  }
])

// Filtered categories based on search
const filteredCategories = computed(() => {
  if (!actionSearch.value) return actionCategories.value
  
  return actionCategories.value.map(category => ({
    ...category,
    actions: category.actions.filter(action => 
      action.name.toLowerCase().includes(actionSearch.value.toLowerCase())
    )
  })).filter(category => category.actions.length > 0)
})
const canUndo = computed(() => dashboardStore.canUndo)
const canRedo = computed(() => dashboardStore.canRedo)

const mainStyle = computed(() => {
  if (!currentPage.value?.background) return {}
  
  const bg = currentPage.value.background
  if (bg.type === 'solid') {
    return { backgroundColor: bg.color }
  } else if (bg.type === 'gradient' && bg.gradient) {
    return {
      background: `linear-gradient(${bg.gradient.direction || '135deg'}, ${bg.gradient.from}, ${bg.gradient.to})`
    }
  } else if (bg.type === 'image' && bg.image) {
    return {
      backgroundImage: `url(${bg.image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

onMounted(async () => {
  // Load last used profile or first available profile
  const lastProfileId = localStorage.getItem('vdock_last_profile')
  if (lastProfileId) {
    const profile = await profilesStore.getProfile(lastProfileId)
    if (profile) {
      dashboardStore.setProfile(profile)
      return
    }
  }

  // Load first available profile
  await profilesStore.loadProfiles()
  if (profilesStore.profiles.length > 0) {
    const profile = await profilesStore.getProfile(profilesStore.profiles[0].id)
    if (profile) {
      dashboardStore.setProfile(profile)
    }
  }
  
  // Add keyboard shortcuts
  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.ctrlKey || event.metaKey) {
      if (event.key === 'v' && clipboardButton.value) {
        // Ctrl+V to paste at current position (if in edit mode)
        if (isEditMode.value) {
          event.preventDefault()
          showActionResult({
            success: true,
            message: 'Click on a placeholder to paste the button'
          })
        }
      }
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })
})

watch(currentProfile, (profile) => {
  if (profile) {
    localStorage.setItem('vdock_last_profile', profile.id)
  }
})

function toggleEditMode() {
  dashboardStore.toggleEditMode()
}

// Sidebar methods
function toggleCategory(categoryId: string) {
  const index = expandedCategories.value.indexOf(categoryId)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

function closeSidebar() {
  dashboardStore.toggleEditMode()
}

function selectAction(action: any) {
  selectedAction.value = action
  console.log('Selected action:', action)
  // TODO: Implement action selection logic
  // This could open a configuration dialog or directly apply the action
}

// Drag and drop handlers
function handleDragStart(event: DragEvent, action: any) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vdock-action', JSON.stringify(action))
    event.dataTransfer.effectAllowed = 'copy'
  }
}

function handleDragEnd() {
  // Clean up any drag state if needed
}

function handleActionDrop(action: any, position: { row: number; col: number }) {
  console.log('Action dropped:', action, 'at position:', position)
  
  // Create preconfigured button based on action type
  const button = createPreconfiguredButton(action, position)
  
  if (button) {
    // Add button to the current page
    dashboardStore.addButton(button)
    console.log('Created button:', button)
  }
}


function handleButtonMove(buttonId: string, newPosition: { row: number; col: number }) {
  console.log('Moving button:', buttonId, 'to:', newPosition)
  dashboardStore.moveButton(buttonId, newPosition)
}

function handleButtonEdit(button: Button) {
  console.log('Editing button:', button)
  editingButton.value = { ...button }
}

function handleButtonDelete(buttonId: string) {
  console.log('Deleting button:', buttonId)
  if (confirm('Are you sure you want to delete this button?')) {
    dashboardStore.removeButton(buttonId)
  }
}

// Preconfigured button templates
function createPreconfiguredButton(action: any, position: { row: number; col: number }): Button {
  const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  // Base button configuration
  const baseButton: Button = {
    id: buttonId,
    label: action.name,
    icon_type: 'fontawesome',
    icon: action.icon,
    shape: 'rounded',
    position: {
      row: position.row,
      col: position.col
    },
    size: {
      rows: 1,
      cols: 1
    },
    style: {
      backgroundColor: '#2c3e50',
      textColor: '#ffffff'
    },
    enabled: true,
    action: {
      type: 'custom',
      config: {}
    }
  }

  // Action-specific configurations
  switch (action.id) {
    case 'shutdown':
      return {
        ...baseButton,
        label: 'Shutdown',
        icon: ['fas', 'power-off'],
        style: { ...baseButton.style, backgroundColor: '#e74c3c' },
        action: {
          type: 'cross_platform',
          config: { action: 'shutdown' }
        }
      }

    case 'restart':
      return {
        ...baseButton,
        label: 'Restart',
        icon: ['fas', 'redo'],
        style: { ...baseButton.style, backgroundColor: '#f39c12' },
        action: {
          type: 'cross_platform',
          config: { action: 'restart' }
        }
      }

    case 'sleep':
      return {
        ...baseButton,
        label: 'Sleep',
        icon: ['fas', 'moon'],
        style: { ...baseButton.style, backgroundColor: '#9b59b6' },
        action: {
          type: 'cross_platform',
          config: { action: 'sleep' }
        }
      }

    case 'lock':
      return {
        ...baseButton,
        label: 'Lock',
        icon: ['fas', 'lock'],
        style: { ...baseButton.style, backgroundColor: '#34495e' },
        action: {
          type: 'cross_platform',
          config: { action: 'lock_screen' }
        }
      }

    case 'fullscreen':
      return {
        ...baseButton,
        label: 'Full Screen',
        icon: ['fas', 'expand'],
        style: { ...baseButton.style, backgroundColor: '#16a085' },
        action: {
          type: 'system_control',
          config: { action: 'fullscreen' }
        }
      }

    case 'volume-up':
      return {
        ...baseButton,
        label: 'Volume Up',
        icon: ['fas', 'volume-up'],
        style: { ...baseButton.style, backgroundColor: '#27ae60' },
        action: {
          type: 'cross_platform',
          config: { action: 'volume_up', step: 10 }
        }
      }

    case 'volume-down':
      return {
        ...baseButton,
        label: 'Volume Down',
        icon: ['fas', 'volume-down'],
        style: { ...baseButton.style, backgroundColor: '#27ae60' },
        action: {
          type: 'cross_platform',
          config: { action: 'volume_down', step: 10 }
        }
      }

    case 'volume-mute':
      return {
        ...baseButton,
        label: 'Mute',
        icon: ['fas', 'volume-mute'],
        style: { ...baseButton.style, backgroundColor: '#e67e22' },
        action: {
          type: 'cross_platform',
          config: { action: 'volume_mute' }
        }
      }

    case 'play-pause':
      return {
        ...baseButton,
        label: 'Play/Pause',
        icon: ['fas', 'play'],
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'cross_platform',
          config: { action: 'media_play_pause' }
        }
      }

    case 'next-track':
      return {
        ...baseButton,
        label: 'Next Track',
        icon: ['fas', 'forward'],
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'cross_platform',
          config: { action: 'media_next' }
        }
      }

    case 'prev-track':
      return {
        ...baseButton,
        label: 'Previous Track',
        icon: ['fas', 'backward'],
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'cross_platform',
          config: { action: 'media_previous' }
        }
      }

    case 'stop':
      return {
        ...baseButton,
        label: 'Stop',
        icon: ['fas', 'stop'],
        style: { ...baseButton.style, backgroundColor: '#e74c3c' },
        action: {
          type: 'cross_platform',
          config: { action: 'media_stop' }
        }
      }

    case 'screenshot':
      return {
        ...baseButton,
        label: 'Screenshot',
        icon: ['fas', 'camera'],
        style: { ...baseButton.style, backgroundColor: '#8e44ad' },
        action: {
          type: 'cross_platform',
          config: { action: 'screenshot', path: 'screenshot.png' }
        }
      }

    case 'open-url':
      return {
        ...baseButton,
        label: 'Open URL',
        icon: ['fas', 'globe'],
        style: { ...baseButton.style, backgroundColor: '#16a085' },
        action: {
          type: 'cross_platform',
          config: { action: 'open_url', url: 'https://example.com' }
        }
      }

    case 'brightness-up':
      return {
        ...baseButton,
        label: 'Brightness Up',
        icon: ['fas', 'sun'],
        style: { ...baseButton.style, backgroundColor: '#f1c40f' },
        action: {
          type: 'cross_platform',
          config: { action: 'brightness_up', step: 10 }
        }
      }

    case 'brightness-down':
      return {
        ...baseButton,
        label: 'Brightness Down',
        icon: ['fas', 'moon'],
        style: { ...baseButton.style, backgroundColor: '#95a5a6' },
        action: {
          type: 'cross_platform',
          config: { action: 'brightness_down', step: 10 }
        }
      }

    case 'open-app':
      return {
        ...baseButton,
        label: 'Open App',
        icon: ['fas', 'rocket'],
        style: { ...baseButton.style, backgroundColor: '#e67e22' },
        action: {
          type: 'cross_platform',
          config: { action: 'open_app', path: 'notepad.exe' }
        }
      }

    case 'open-folder':
      return {
        ...baseButton,
        label: 'Open Folder',
        icon: ['fas', 'folder-open'],
        style: { ...baseButton.style, backgroundColor: '#8e44ad' },
        action: {
          type: 'cross_platform',
          config: { action: 'open_folder', path: 'C:\\' }
        }
      }

    case 'open-file':
      return {
        ...baseButton,
        label: 'Open File',
        icon: ['fas', 'file'],
        style: { ...baseButton.style, backgroundColor: '#2c3e50' },
        action: {
          type: 'cross_platform',
          config: { action: 'open_file', path: 'C:\\Windows\\System32\\notepad.exe' }
        }
      }


    case 'custom-icon':
      return {
        ...baseButton,
        label: 'Custom Icon',
        icon_type: 'custom',
        icon: '',
        media_type: 'image',
        media_url: '',
        style: { ...baseButton.style, backgroundColor: '#2c3e50' },
        action: {
          type: 'custom',
          config: {}
        }
      }

    // Monitor Metrics
    case 'metric_memory':
    case 'metric_cpu_usage':
    case 'metric_cpu_temperature':
    case 'metric_cpu_frequency':
    case 'metric_cpu_power':
    case 'metric_internet_speed':
    case 'metric_harddisk':
    case 'metric_gpu_temperature':
    case 'metric_gpu_frequency':
    case 'metric_gpu_usage':
    case 'metric_gpu_memory_freq':
    case 'metric_gpu_memory_usage':
      return {
        ...baseButton,
        label: action.name,
        icon: action.icon,
        size: { rows: 1, cols: 1 },
        style: { ...baseButton.style, backgroundColor: '#2980b9' },
        action: {
          type: action.id as any,
          config: { refresh_interval: 2 }
        }
      }

    // Time
    case 'time_world_clock':
      return {
        ...baseButton,
        label: 'World Clock',
        icon: ['fas', 'globe'],
        size: { rows: 2, cols: 2 },
        style: { ...baseButton.style, backgroundColor: '#8e44ad' },
        action: {
          type: 'time_world_clock',
          config: { timezone: 'local' }
        }
      }

    case 'time_timer':
      return {
        ...baseButton,
        label: 'Timer',
        icon: ['fas', 'stopwatch'],
        size: { rows: 2, cols: 2 },
        style: { ...baseButton.style, backgroundColor: '#8e44ad' },
        action: {
          type: 'time_timer',
          config: { timer_duration: 0 }
        }
      }

    case 'time_countdown':
      return {
        ...baseButton,
        label: 'Countdown',
        icon: ['fas', 'hourglass-half'],
        size: { rows: 2, cols: 2 },
        style: { ...baseButton.style, backgroundColor: '#8e44ad' },
        action: {
          type: 'time_countdown',
          config: { countdown_target: '' }
        }
      }

    // Weather
    case 'weather':
      return {
        ...baseButton,
        label: 'Weather',
        icon: ['fas', 'cloud-sun'],
        size: { rows: 2, cols: 2 },
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'weather',
          config: { weather_location: 'auto', refresh_interval: 15 }
        }
      }

    // Navigation
    case 'next-page':
      return {
        ...baseButton,
        label: 'Next Page',
        icon: ['fas', 'arrow-right'],
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'next_page',
          config: {}
        }
      }

    case 'previous-page':
      return {
        ...baseButton,
        label: 'Previous Page',
        icon: ['fas', 'arrow-left'],
        style: { ...baseButton.style, backgroundColor: '#3498db' },
        action: {
          type: 'previous_page',
          config: {}
        }
      }

    case 'home-page':
      return {
        ...baseButton,
        label: 'Home',
        icon: ['fas', 'home'],
        style: { ...baseButton.style, backgroundColor: '#16a085' },
        action: {
          type: 'home_page',
          config: {}
        }
      }

    default:
      return {
        ...baseButton,
        action: {
          type: 'custom',
          config: {}
        }
      }
  }
}

function setScene(index: number) {
  dashboardStore.setScene(index)
}

function addScene() {
  editingScene.value = {
    id: `scene_${Date.now()}`,
    name: 'New Scene',
    icon: '',
    color: '#3498db',
    pages: [{
      id: `page_${Date.now()}`,
      name: 'Page 1',
      buttons: [],
      grid_config: {
        rows: 4,
        cols: 5
      }
    }],
    isActive: false,
    buttonSize: 1.0
  }
}

function editScene(scene: Scene) {
  editingScene.value = { ...scene }
}

function setPage(index: number) {
  dashboardStore.setPage(index)
}

function nextPage() {
  dashboardStore.nextPage()
}

function previousPage() {
  dashboardStore.previousPage()
}

function handleSceneSave(scene: Scene) {
  if (isEditingExistingScene.value) {
    // Editing existing scene
    dashboardStore.updateScene(scene.id, scene)
  } else {
    // Creating new scene
    dashboardStore.addScene(scene)
  }
  editingScene.value = null
}

function handleSceneDelete(sceneId: string) {
  dashboardStore.removeScene(sceneId)
  editingScene.value = null
}

async function handleButtonClick(button: Button) {
  if (!button.action) return

  const result = await dashboardStore.executeButtonAction(button)
  showActionResult(result)
}


async function handleSaveProfileFromEditor() {
  console.log('DashboardView: saving profile from editor')
  await saveProfile()
}

async function handleButtonSave(button: Button) {
  console.log('DashboardView: handleButtonSave', button.id)
  // Check if this is a docked button
  const isDockedButton = currentProfile.value?.dockedButtons?.some(btn => btn.id === button.id)
  
  if (isDockedButton) {
    console.log('DashboardView: saving docked button')
    // Update docked button
    const updatedDockedButtons = currentProfile.value?.dockedButtons?.map(btn => 
      btn.id === button.id ? button : btn
    ) || []
    
    if (currentProfile.value) {
      // Create updated profile and set directly to avoid backend round-trip
      const updatedProfile = {
        ...currentProfile.value,
        dockedButtons: updatedDockedButtons
      }
      
      dashboardStore.setProfile(updatedProfile)
      
      showActionResult({
        success: true,
        message: 'Docked button updated'
      })
    }
  } else {
    // Update regular button
    console.log('DashboardView: saving regular button')
    dashboardStore.updateButton(button.id, button)
  }
  
  editingButton.value = null
}

async function handleDockedButtonDelete(buttonId: string) {
  console.log('DashboardView: deleting docked button', buttonId)
  if (currentProfile.value) {
    const updatedDockedButtons = currentProfile.value.dockedButtons?.filter(btn => btn.id !== buttonId) || []
    
    // Create updated profile and set directly
    const updatedProfile = {
      ...currentProfile.value,
      dockedButtons: updatedDockedButtons
    }
    
    dashboardStore.setProfile(updatedProfile)
    
    showActionResult({
      success: true,
      message: 'Docked button deleted'
    })
  }
}

async function handleAddDockedButton(position: { row: number; col: number }) {
  console.log('DashboardView: handleAddDockedButton at', position)
  const newButton: Button = {
    id: `docked_${Date.now()}`,
    label: 'New Button',
    secondary_label: '',
    icon: ['fas', 'star'],
    icon_type: 'fontawesome',
    media_url: null,
    media_type: null,
    shape: 'rounded',
    position: { row: position.row, col: position.col },
    size: { rows: 1, cols: 1 },
    style: {
      backgroundColor: '#3498db',
      textColor: '#ffffff'
    },
    tooltip: '',
    enabled: true,
    action: {
      type: 'custom',
      config: {}
    }
  }
  
  console.log('DashboardView: creating new docked button', newButton)
  
  if (currentProfile.value) {
    // Create updated profile with new docked button
    const updatedProfile = {
      ...currentProfile.value,
      dockedButtons: [...(currentProfile.value.dockedButtons || []), newButton]
    }
    
    console.log('DashboardView: setting updated profile with', updatedProfile.dockedButtons.length, 'docked buttons')
    
    // Use setProfile to trigger reactivity properly
    dashboardStore.setProfile(updatedProfile)
    
    showActionResult({
      success: true,
      message: `Button added to docked sidebar`
    })
  }
}

async function handleDockedButtonDrop(event: DragEvent, position: { row: number; col: number }) {
  console.log('DashboardView: handleDockedButtonDrop called at', position)
  if (!event.dataTransfer) {
    console.log('DashboardView: no dataTransfer')
    return
  }
  
  try {
    const buttonData = event.dataTransfer.getData('application/vdock-button')
    console.log('DashboardView: button data', buttonData)
    if (buttonData) {
      const button = JSON.parse(buttonData)
      console.log('DashboardView: parsed button', button)
      
      // Create a copy of the button for docking at the specific position
      const dockedButton: Button = {
        ...button,
        id: `docked_${Date.now()}`,
        position: { row: position.row, col: position.col },
        size: { rows: 1, cols: 1 }
      }
      
      console.log('DashboardView: created docked button', dockedButton)
      
      if (currentProfile.value) {
        // Create updated profile with new docked button
        const updatedProfile = {
          ...currentProfile.value,
          dockedButtons: [...(currentProfile.value.dockedButtons || []), dockedButton]
        }
        
        console.log('DashboardView: setting updated profile with', updatedProfile.dockedButtons.length, 'docked buttons')
        
        // Use setProfile to trigger reactivity properly
        dashboardStore.setProfile(updatedProfile)
        
        showActionResult({
          success: true,
          message: `Button docked successfully`
        })
      } else {
        console.log('DashboardView: no current profile')
      }
    } else {
      console.log('DashboardView: no button data found')
    }
  } catch (err) {
    console.error('Failed to handle docked drop:', err)
    showActionResult({
      success: false,
      message: `Failed to dock button: ${err}`
    })
  }
}

function handleButtonCopy(button: Button) {
  clipboardButton.value = { ...button }
  showActionResult({
    success: true,
    message: `Button "${button.label}" copied to clipboard`
  })
}

function handleDockedPlaceholderClick(position: { row: number; col: number }) {
  console.log('DashboardView: docked placeholder clicked at', position)
  if (clipboardButton.value && currentProfile.value) {
    // Paste the copied button to the docked sidebar
    const pastedButton: Button = {
      ...clipboardButton.value,
      id: `docked_${Date.now()}`,
      position: { row: position.row, col: position.col },
      size: { rows: 1, cols: 1 }
    }
    
    console.log('DashboardView: pasting button to docked sidebar', pastedButton)
    
    // Create updated profile with pasted button
    const updatedProfile = {
      ...currentProfile.value,
      dockedButtons: [...(currentProfile.value.dockedButtons || []), pastedButton]
    }
    
    dashboardStore.setProfile(updatedProfile)
    
    showActionResult({
      success: true,
      message: 'Button pasted to docked sidebar'
    })
  } else {
    // No clipboard, add a new button
    handleAddDockedButton(position)
  }
}

function handlePlaceholderClick(position: { row: number; col: number }) {
  console.log('Placeholder clicked at:', position)
  
  if (clipboardButton.value) {
    // Paste the button at the clicked position
    const newButton: Button = {
      ...clipboardButton.value,
      id: `button_${Date.now()}`,
      label: `${clipboardButton.value.label} (Copy)`,
      position: { row: position.row, col: position.col }
    }
    
    dashboardStore.addButton(newButton)
    showActionResult({
      success: true,
      message: `Button "${newButton.label}" pasted`
    })
  } else {
    // Create a default button at the clicked position
    const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const button: Button = {
      id: buttonId,
      label: 'New Button',
      icon_type: 'fontawesome',
      icon: ['fas', 'home'],
      shape: 'rounded',
      position: {
        row: position.row,
        col: position.col
      },
      size: {
        rows: 1,
        cols: 1
      },
      style: {
        backgroundColor: '#2c3e50',
        textColor: '#ffffff'
      },
      enabled: true,
      action: {
        type: 'custom',
        config: {}
      }
    }
    
    dashboardStore.addButton(button)
    console.log('Created button:', button)
  }
}


function addPageToCurrentScene() {
  if (!currentScene.value) {
    showActionResult({
      success: false,
      message: 'No scene selected'
    })
    return
  }

  const pageNumber = currentScene.value.pages.length + 1
  dashboardStore.addPage({
    id: `page_${Date.now()}`,
    name: `Page ${pageNumber}`,
    buttons: [],
    grid_config: {
      rows: settingsStore.defaultGridRows || 4,
      cols: settingsStore.defaultGridCols || 5
    }
  })

  showActionResult({
    success: true,
    message: `Page ${pageNumber} added to ${currentScene.value.name}`
  })
}

async function saveProfile() {
  if (!currentProfile.value) {
    showActionResult({
      success: false,
      message: 'No profile loaded'
    })
    return
  }

  const success = await dashboardStore.saveProfile()

  if (success) {
    showActionResult({
      success: true,
      message: 'Profile saved successfully'
    })
  } else {
    showActionResult({
      success: false,
      message: 'Failed to save profile'
    })
  }
}

function showActionResult(result: ActionResult) {
  actionResult.value = result

  if (actionResultTimeout) {
    clearTimeout(actionResultTimeout)
  }

  actionResultTimeout = setTimeout(() => {
    actionResult.value = null
  }, 3000)
}
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* Enhanced Header Styles */
.deck-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: relative;
  overflow: hidden;
}

.enhanced-header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}

.header-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.05) 0%, 
    rgba(118, 75, 162, 0.05) 50%, 
    rgba(255, 107, 107, 0.05) 100%);
  animation: headerGradientShift 10s ease-in-out infinite;
}

@keyframes headerGradientShift {
  0%, 100% {
    background: linear-gradient(135deg, 
      rgba(102, 126, 234, 0.05) 0%, 
      rgba(118, 75, 162, 0.05) 50%, 
      rgba(255, 107, 107, 0.05) 100%);
  }
  50% {
    background: linear-gradient(135deg, 
      rgba(255, 107, 107, 0.05) 0%, 
      rgba(102, 126, 234, 0.05) 50%, 
      rgba(118, 75, 162, 0.05) 100%);
  }
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  position: relative;
  z-index: 1;
}

.header-left,
.header-right {
  flex: 1;
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.header-left {
  flex-direction: row;
  align-items: center;
}

/* Enhanced Profile Header */
.profile-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.profile-title-inline {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  white-space: nowrap;
}

.profile-avatar-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.enhanced-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  object-fit: cover;
  border: 3px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: all var(--transition-normal);
}

.enhanced-avatar:hover {
  transform: scale(1.05);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.profile-avatar-placeholder.enhanced-avatar {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
  font-size: 1.4rem;
}

.avatar-status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #4ade80, #22c55e);
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  animation: pulse 2s infinite;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.profile-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  background: linear-gradient(135deg, var(--color-text), var(--color-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.profile-subtitle {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  opacity: 0.8;
}

.header-right {
  justify-content: flex-end;
}

/* Enhanced Button Styles */
.enhanced-btn {
  position: relative;
  padding: 0.75rem var(--spacing-md); /* Increased vertical padding for better touch targets */
  min-height: 44px; /* Minimum 44px for accessibility */
  border-radius: var(--radius-lg);
  font-weight: 500;
  transition: all var(--transition-normal);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.enhanced-btn .btn-label {
  margin-left: var(--spacing-xs);
  font-size: 0.85rem;
  opacity: 0;
  transform: translateX(-10px);
  transition: all var(--transition-fast);
}

.enhanced-btn:hover .btn-label {
  opacity: 1;
  transform: translateX(0);
}

.edit-active {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary)) !important;
  color: white !important;
  box-shadow: 0 0 20px rgba(var(--color-primary-rgb, 255, 107, 107), 0.4);
}

.edit-active .btn-label {
  opacity: 1;
  transform: translateX(0);
}

/* Enhanced Navigation */
.enhanced-scene-nav,
.enhanced-page-nav {
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xs);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.deck-main {
  flex: 1;
  overflow: hidden;
  display: flex;
}

.no-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-lg);
  color: var(--color-text-secondary);
}

.no-profile-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.deck-footer {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  margin-right: 350px; /* Account for edit sidebar width */
  gap: var(--spacing-md);
}

.deck-footer.with-docked-sidebar {
  margin-left: 280px; /* Account for docked sidebar width */
}

.footer-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.footer-spacer {
  flex: 1;
}

.grid-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.grid-input {
  width: 50px;
  padding: var(--spacing-xs);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-background);
  color: var(--color-text);
  text-align: center;
  font-size: 0.875rem;
}

.grid-input:focus {
  outline: none;
  border-color: var(--color-primary);
}


.action-toast {
  position: fixed;
  bottom: var(--spacing-lg);
  right: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  animation: slideUp var(--transition-normal);
  z-index: 1000;
}

.action-toast.success {
  background-color: var(--color-success);
  color: white;
}

.action-toast.error {
  background-color: var(--color-error);
  color: white;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Sidebar Styles */
.deck-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.main-content {
  flex: 1;
  transition: all var(--transition-medium);
  display: flex;
  flex-direction: column;
}

.main-content.with-sidebar {
  margin-right: 350px;
}

.main-content.with-docked-sidebar {
  margin-left: 16px;
}

.main-content.with-sidebar.with-docked-sidebar {
  margin-left: 16px;
  margin-right: 350px;
}

.edit-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 350px;
  height: 100vh;
  background-color: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface-solid);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--color-text-primary);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.search-section {
  margin-bottom: var(--spacing-md);
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-surface-solid);
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.categories-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.category-group {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm);
  background-color: var(--color-surface-solid);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  gap: var(--spacing-xs);
}

.category-header:hover {
  background-color: var(--color-surface-hover);
}

.category-header svg {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}

.category-count {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.category-actions {
  border-top: 1px solid var(--color-border);
  background-color: var(--color-surface);
}

.action-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm);
  cursor: grab;
  transition: all var(--transition-fast);
  gap: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.action-item:last-child {
  border-bottom: none;
}

.action-item:hover {
  background-color: var(--color-surface-hover);
  transform: translateX(2px);
}

.action-item:active {
  cursor: grabbing;
  transform: scale(0.98);
}

.action-item[draggable="true"] {
  user-select: none;
}

.action-item svg {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  width: 16px;
}

.action-item span {
  font-size: 0.9rem;
  color: var(--color-text-primary);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.8rem;
}

/* Dashboard Background Styles */
.dashboard-view.dashboard-bg-ocean-breeze {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.dashboard-view.dashboard-bg-sunset-glow {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.dashboard-view.dashboard-bg-forest-mist {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.dashboard-view.dashboard-bg-royal-purple {
  background: linear-gradient(135deg, #b721ff 0%, #21d4fd 100%);
}

.dashboard-view.dashboard-bg-golden-hour {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

/* Animated Backgrounds */
.dashboard-view.dashboard-bg-floating-particles {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.dashboard-view.dashboard-bg-gradient-waves {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-size: 200% 200%;
  animation: gradientShift 15s ease infinite;
}

.dashboard-view.dashboard-bg-geometric-patterns {
  background: 
    linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%),
    repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.05) 10px, rgba(255,255,255,.05) 20px);
}

.dashboard-view.dashboard-bg-aurora-borealis {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 400% 400%;
  animation: aurora 20s ease infinite;
}

.dashboard-view.dashboard-bg-starfield {
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
  position: relative;
}

.dashboard-view.dashboard-bg-bubble-float {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  position: relative;
  overflow: hidden;
}

.dashboard-view.dashboard-bg-neon-grid {
  background: #0a0a0a;
  background-image: 
    linear-gradient(rgba(102, 126, 234, 0.3) 1px, transparent 1px),
    linear-gradient(90deg, rgba(102, 126, 234, 0.3) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* Custom Background (applied via inline styles) */
.dashboard-view.dashboard-bg-custom {
  /* Styles are applied via computed backgroundStyle */
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes aurora {
  0% { background-position: 0% 50%; }
  25% { background-position: 50% 100%; }
  50% { background-position: 100% 50%; }
  75% { background-position: 50% 0%; }
  100% { background-position: 0% 50%; }
}

/* Help Modal */
.help-modal {
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.help-content {
  padding: var(--spacing-lg);
}

.help-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-primary);
}

.help-section h3 {
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.help-section ul,
.help-section ol {
  margin-left: var(--spacing-lg);
  line-height: 1.8;
}

.help-section li {
  margin-bottom: var(--spacing-sm);
}

.help-section li strong {
  color: var(--color-text);
}

.help-section code {
  background: var(--color-background);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: monospace;
  color: var(--color-primary);
}

.help-section a {
  color: var(--color-primary);
  text-decoration: none;
}

.help-section a:hover {
  text-decoration: underline;
}
</style>

