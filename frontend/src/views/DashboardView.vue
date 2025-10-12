<template>
  <div class="dashboard-view">
    <header class="deck-header">
      <div class="header-left">
        <h1>{{ currentProfile?.name || 'VDock' }}</h1>
      </div>

      <div class="header-center">
        <PageNavigation
          v-if="currentProfile && currentProfile.pages.length > 1"
          :pages="currentProfile.pages"
          :current-page="currentPageIndex"
          @previous="previousPage"
          @next="nextPage"
          @go-to="setPage"
        />
      </div>

      <div class="header-right">
        <button class="btn btn-secondary" @click="router.push('/profiles')" title="Profiles">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        </button>
        <button class="btn btn-secondary" @click="toggleEditMode" title="Toggle Edit Mode">
          <FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" />
        </button>
        <button class="btn btn-secondary" @click="router.push('/settings')" title="Settings">
          <FontAwesomeIcon :icon="['fas', 'cog']" />
        </button>
      </div>
    </header>

    <main class="deck-main" :style="mainStyle">
      <div class="main-content" :class="{ 'with-sidebar': isEditMode }">
        <DeckGrid
          v-if="currentPage"
          :page="currentPage"
          :is-edit-mode="isEditMode"
          @button-click="handleButtonClick"
          @button-edit="handleButtonEdit"
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

    <footer v-if="isEditMode" class="deck-footer">
      <div class="edit-mode-toolbar">
        <button class="btn btn-secondary" @click="undo" :disabled="!canUndo">
          <FontAwesomeIcon :icon="['fas', 'undo']" /> Undo
        </button>
        <button class="btn btn-secondary" @click="redo" :disabled="!canRedo">
          <FontAwesomeIcon :icon="['fas', 'redo']" /> Redo
        </button>
        <button class="btn btn-primary" @click="addNewButton">
          <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Button
        </button>
        <button class="btn btn-success" @click="saveProfile">
          <FontAwesomeIcon :icon="['fas', 'save']" /> Save
        </button>
      </div>
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
    </footer>

    <!-- Button Editor Modal -->
    <ButtonEditor
      v-if="editingButton"
      :button="editingButton"
      @save="handleButtonSave"
      @close="editingButton = null"
    />

    <!-- Action Result Toast -->
    <div v-if="actionResult" class="action-toast" :class="actionResult.success ? 'success' : 'error'">
      {{ actionResult.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { useProfilesStore } from '@/stores/profiles'
import type { Button, ActionResult } from '@/types'
import DeckGrid from '@/components/DeckGrid.vue'
import PageNavigation from '@/components/PageNavigation.vue'
import ButtonEditor from '@/components/ButtonEditor.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const dashboardStore = useDashboardStore()
const profilesStore = useProfilesStore()

const editingButton = ref<Button | null>(null)
const actionResult = ref<ActionResult | null>(null)
let actionResultTimeout: number | null = null

// Sidebar state
const actionSearch = ref('')
const expandedCategories = ref<string[]>(['system', 'media', 'web'])
const selectedAction = ref<any>(null)

const currentProfile = computed(() => dashboardStore.currentProfile)
const currentPage = computed(() => dashboardStore.currentPage)
const currentPageIndex = computed(() => dashboardStore.currentPageIndex)
const isEditMode = computed(() => dashboardStore.isEditMode)

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

function handlePlaceholderClick(position: { row: number; col: number }) {
  console.log('Placeholder clicked at:', position)
  
  // Create a default button at the clicked position
  const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  const button = {
    id: buttonId,
    name: 'New Button',
    icon_type: 'fontawesome' as const,
    icon: ['fas', 'home'],
    position: {
      row: position.row,
      col: position.col
    },
    size: {
      width: 1,
      height: 1
    },
    style: {
      background_color: '#2c3e50',
      text_color: '#ffffff',
      border_radius: 8
    },
    enabled: true,
    action: {
      type: 'custom',
      description: 'New button'
    }
  }
  
  dashboardStore.addButton(button)
}

function handleButtonMove(buttonId: string, newPosition: { row: number; col: number }) {
  console.log('Moving button:', buttonId, 'to:', newPosition)
  dashboardStore.moveButton(buttonId, newPosition)
}

// Preconfigured button templates
function createPreconfiguredButton(action: any, position: { row: number; col: number }) {
  const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  // Base button configuration
  const baseButton = {
    id: buttonId,
    name: action.name,
    icon_type: 'fontawesome' as const,
    icon: action.icon,
    position: {
      row: position.row,
      col: position.col
    },
    size: {
      width: 1,
      height: 1
    },
    style: {
      background_color: '#2c3e50',
      text_color: '#ffffff',
      border_radius: 8
    }
  }

  // Action-specific configurations
  switch (action.id) {
    case 'shutdown':
      return {
        ...baseButton,
        name: 'Shutdown',
        icon: ['fas', 'power-off'],
        style: { ...baseButton.style, background_color: '#e74c3c' },
        action: {
          type: 'system',
          command: 'shutdown /s /t 0'
        }
      }

    case 'restart':
      return {
        ...baseButton,
        name: 'Restart',
        icon: ['fas', 'redo'],
        style: { ...baseButton.style, background_color: '#f39c12' },
        action: {
          type: 'system',
          command: 'shutdown /r /t 0'
        }
      }

    case 'sleep':
      return {
        ...baseButton,
        name: 'Sleep',
        icon: ['fas', 'moon'],
        style: { ...baseButton.style, background_color: '#9b59b6' },
        action: {
          type: 'system',
          command: 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0'
        }
      }

    case 'lock':
      return {
        ...baseButton,
        name: 'Lock',
        icon: ['fas', 'lock'],
        style: { ...baseButton.style, background_color: '#34495e' },
        action: {
          type: 'system',
          command: 'rundll32.exe user32.dll,LockWorkStation'
        }
      }

    case 'volume-up':
      return {
        ...baseButton,
        name: 'Volume Up',
        icon: ['fas', 'volume-up'],
        style: { ...baseButton.style, background_color: '#27ae60' },
        action: {
          type: 'hotkey',
          keys: ['VolumeUp']
        }
      }

    case 'volume-down':
      return {
        ...baseButton,
        name: 'Volume Down',
        icon: ['fas', 'volume-down'],
        style: { ...baseButton.style, background_color: '#27ae60' },
        action: {
          type: 'hotkey',
          keys: ['VolumeDown']
        }
      }

    case 'volume-mute':
      return {
        ...baseButton,
        name: 'Mute',
        icon: ['fas', 'volume-mute'],
        style: { ...baseButton.style, background_color: '#e67e22' },
        action: {
          type: 'hotkey',
          keys: ['VolumeMute']
        }
      }

    case 'play-pause':
      return {
        ...baseButton,
        name: 'Play/Pause',
        icon: ['fas', 'play'],
        style: { ...baseButton.style, background_color: '#3498db' },
        action: {
          type: 'hotkey',
          keys: ['Space']
        }
      }

    case 'next-track':
      return {
        ...baseButton,
        name: 'Next Track',
        icon: ['fas', 'forward'],
        style: { ...baseButton.style, background_color: '#3498db' },
        action: {
          type: 'hotkey',
          keys: ['MediaNext']
        }
      }

    case 'prev-track':
      return {
        ...baseButton,
        name: 'Previous Track',
        icon: ['fas', 'backward'],
        style: { ...baseButton.style, background_color: '#3498db' },
        action: {
          type: 'hotkey',
          keys: ['MediaPrevious']
        }
      }

    case 'screenshot':
      return {
        ...baseButton,
        name: 'Screenshot',
        icon: ['fas', 'camera'],
        style: { ...baseButton.style, background_color: '#8e44ad' },
        action: {
          type: 'hotkey',
          keys: ['PrintScreen']
        }
      }

    case 'open-url':
      return {
        ...baseButton,
        name: 'Open URL',
        icon: ['fas', 'globe'],
        style: { ...baseButton.style, background_color: '#16a085' },
        action: {
          type: 'url',
          url: 'https://example.com'
        }
      }

    case 'custom-icon':
      return {
        ...baseButton,
        name: 'Custom Icon',
        icon_type: 'custom' as const,
        icon: '',
        media_type: 'image' as const,
        media_url: '',
        style: { ...baseButton.style, background_color: '#2c3e50' },
        action: {
          type: 'custom',
          description: 'Custom icon button'
        }
      }

    default:
      return {
        ...baseButton,
        action: {
          type: 'custom',
          description: `${action.name} action`
        }
      }
  }
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

function undo() {
  dashboardStore.undo()
}

function redo() {
  dashboardStore.redo()
}

async function handleButtonClick(button: Button) {
  if (!button.action) return

  const result = await dashboardStore.executeButtonAction(button)
  showActionResult(result)
}

function handleButtonEdit(button: Button) {
  editingButton.value = { ...button }
}

function handleButtonDelete(buttonId: string) {
  if (confirm('Delete this button?')) {
    dashboardStore.removeButton(buttonId)
  }
}

function handleButtonSave(button: Button) {
  dashboardStore.updateButton(button.id, button)
  editingButton.value = null
}

function addNewButton() {
  // Create a new empty button
  const newButton: Button = {
    id: `btn_${Date.now()}`,
    label: 'New Button',
    icon_type: 'fontawesome',
    icon: 'fas fa-home',
    shape: 'rounded',
    position: { row: 0, col: 0 },
    size: { rows: 1, cols: 1 },
    enabled: true
  }
  dashboardStore.addButton(newButton)
  editingButton.value = newButton
}

async function saveProfile() {
  const success = await dashboardStore.saveProfile()
  if (success) {
    showActionResult({ success: true, message: 'Profile saved successfully' })
  } else {
    showActionResult({ success: false, message: 'Failed to save profile' })
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

.deck-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.header-left,
.header-right {
  flex: 1;
  display: flex;
  gap: var(--spacing-sm);
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-text);
}

.header-right {
  justify-content: flex-end;
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.deck-main {
  flex: 1;
  overflow: hidden;
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
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  margin-right: 350px; /* Account for sidebar width */
}

.footer-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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

.edit-mode-toolbar {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-start;
  flex-wrap: wrap;
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
}

.main-content.with-sidebar {
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
</style>

