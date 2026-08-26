<template>
  <div class="dashboard-view" :class="dashboardBackgroundClass" :style="dashboardBackgroundStyle">
    <!-- Component-based animated backgrounds -->
    <FloatingPathsBackground v-if="dashboardBackgroundClass === 'dashboard-bg-floating-paths'" />
    <FloatingPathsBackgroundV2 v-if="dashboardBackgroundClass === 'dashboard-bg-floating-paths-v2'" />
    <BeamsBackground v-if="dashboardBackgroundClass === 'dashboard-bg-beams-background'" />
    
    <!-- Decomposed Header component -->
    <DeckHeader
      :current-profile="currentProfile"
      :current-scene="currentScene"
      :current-scene-index="currentSceneIndex"
      :current-page-index="currentPageIndex"
      :is-edit-mode="isEditMode"
      @toggle-edit="dashboardStore.toggleEditMode"
      @navigate-settings="handleNavigateSettings"
      @navigate-profiles="router.push('/profiles')"
      @set-scene="setScene"
      @add-scene="addScene"
      @edit-scene="editScene"
      @set-page="setPage"
      @previous-page="previousPage"
      @next-page="nextPage"
    />

    <main class="deck-main" :style="mainStyle">
      <!-- Docked Sidebar -->
      <DockedSidebar
        v-slot:default
        v-if="settingsStore.dockedSidebarEnabled && currentPage"
        :docked-buttons="currentProfile?.dockedButtons || []"
        :grid-rows="currentPage.grid_config.rows"
        :is-edit-mode="isEditMode"
        :show-labels="settingsStore.showLabels"
        :show-tooltips="settingsStore.showTooltips"
        :button-size="settingsStore.buttonSize * settingsStore.touchModeMultiplier"
        :show-header="settingsStore.showHeader"
        @button-click="handleButtonClick"
        @button-edit="handleButtonEdit"
        @button-copy="handleButtonCopy"
        @button-delete="handleDockedButtonDelete"
        @button-drop="handleDockedButtonDrop"
        @add-button="onDockedAddButton"
        @placeholder-click="onDockedPlaceholderClick"
        @toggle-header="settingsStore.showHeader = !settingsStore.showHeader"
      />
      
      <div class="main-content" :class="{ 'with-sidebar': isEditMode, 'with-docked-sidebar': settingsStore.dockedSidebarEnabled }">
        <template v-if="currentPage">
          <DeckGrid
            :page="currentPage"
            :is-edit-mode="isEditMode"
            :button-size="settingsStore.buttonSize * settingsStore.touchModeMultiplier"
            :show-labels="settingsStore.showLabels"
            :show-tooltips="settingsStore.showTooltips"
            :compact="shouldUseCompactMode"
            @button-click="handleButtonClick"
            @button-edit="handleButtonEdit"
            @button-copy="handleButtonCopy"
            @button-delete="handleButtonDelete"
            @swipe-left="nextPage"
            @swipe-right="previousPage"
            @action-drop="handleActionDrop"
            @placeholder-click="onPlaceholderClick"
            @placeholder-long-press="handlePlaceholderLongPress"
            @button-move="handleButtonMove"
            @swipe-up="nextScene"
            @swipe-down="previousScene"
            @long-press="handleDeckButtonLongPress"
            @double-tap="handleButtonClick"
            @exit-edit-mode="dashboardStore.toggleEditMode"
          />
        </template>

        <div v-if="!currentPage" class="no-profile">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" class="no-profile-icon" />
          <p>No profile loaded</p>
          <button class="btn btn-primary" @click="router.push('/profiles')">
            Select Profile
          </button>
        </div>
      </div>

      <!-- Decomposed Edit Sidebar component -->
      <EditSidebar
        v-if="isEditMode"
        v-model:action-search="actionSearch"
        :expanded-categories="expandedCategories"
        :filtered-categories="filteredCategories"
        @toggle-category="toggleCategory"
        @move-category-up="moveCategoryUp"
        @move-category-down="moveCategoryDown"
        @select-action="selectAction"
        @close="closeSidebar"
      />
    </main>

    <!-- Decomposed Footer component -->
    <DeckFooter
      :is-edit-mode="isEditMode"
      :total-pages="currentScene?.pages.length || 1"
      :current-page-index="currentPageIndex"
      :grid-rows="currentPage?.grid_config.rows || 3"
      :grid-cols="currentPage?.grid_config.cols || 3"
      @set-page="setPage"
      @add-page="addPageToCurrentScene"
      @delete-page="deleteCurrentPage"
      @save-profile="saveProfile"
      @update-rows="updateGridRows"
      @update-cols="updateGridCols"
    />

    <!-- Screen Saver overlay -->
    <ScreenSaver v-if="screensaverVisible" :visible="screensaverVisible" @dismiss="dismissScreensaver" />

    <!-- Quick Add Picker Modal -->
    <QuickAddPicker
      :visible="quickAddVisible"
      :position="quickAddPosition"
      @select="onQuickAddSelect"
      @close="quickAddVisible = false"
    />

    <!-- Global OnScreenKeypad Component -->
    <OnScreenKeypad
      :visible="keypadVisible"
      :model-value="keypadValue"
      @update:modelValue="handleKeypadUpdate"
      @close="handleKeypadClose"
      class="global-onscreen-keypad"
    />

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
      @reset="handleSceneReset"
      @close="editingScene = null"
    />

    <!-- Action Result Toast -->
    <div v-if="actionResult && settingsStore.toastLevel !== 'off' && actionResult.success === false" class="action-toast error">
      {{ actionResult.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { useProfilesStore } from '@/stores/profiles'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import type { Button, Scene } from '@/types'
import DeckGrid from '@/components/DeckGrid.vue'
import ButtonEditor from '@/components/ButtonEditor.vue'
import SceneEditor from '@/components/SceneEditor.vue'
import DockedSidebar from '@/components/DockedSidebar.vue'
import DeckHeader from '@/components/DeckHeader.vue'
import DeckFooter from '@/components/DeckFooter.vue'
import ScreenSaver from '@/components/ScreenSaver.vue'
import EditSidebar from '@/components/EditSidebar.vue'
import QuickAddPicker from '@/components/QuickAddPicker.vue'
import OnScreenKeypad from '@/components/OnScreenKeypad.vue'
import FloatingPathsBackground from '@/components/backgrounds/FloatingPathsBackground.vue'
import FloatingPathsBackgroundV2 from '@/components/backgrounds/FloatingPathsBackgroundV2.vue'
import BeamsBackground from '@/components/backgrounds/BeamsBackground.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { createDefaultProfile } from '@/utils/defaultProfile'
import { openStandaloneSettings } from '@/utils/openStandaloneSettings'
import { useButtonActions } from '@/composables/useButtonActions'
import { listenForVdockRefreshRequests } from '@/composables/useVdockRefresh'

const router = useRouter()
const dashboardStore = useDashboardStore()
const profilesStore = useProfilesStore()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()

const editingScene = ref<Scene | null>(null)
let stopVdockRefreshListener: (() => void) | null = null

// Composables logic
const {
  editingButton,
  clipboardButton,
  selectedAction,
  actionResult,
  showActionResult,
  handleButtonClick,
  handleButtonEdit,
  handleButtonCopy,
  handleButtonDelete,
  handleButtonMove,
  handleActionDrop,
  handlePlaceholderClick,
  handlePlaceholderLongPress,
  handleDeckButtonLongPress,
  handleDockedButtonDelete,
  handleDockedButtonDrop,
  handleDockedPlaceholderClick,
  handleButtonSave,
  selectAction
} = useButtonActions()

// Quick Add states
const quickAddVisible = ref(false)
const quickAddPosition = ref({ row: 0, col: 0 })
// Which button collection a QuickAddPicker selection should be added to —
// the docked sidebar has its own placeholder/add-button flow that used to
// create a blank, action-less "New Button" straight into dockedButtons with
// no way to pick an action. Routing it through the same picker as the main
// grid lets the user choose an action up front, same as page buttons.
const quickAddTarget = ref<'page' | 'docked'>('page')

// Screensaver / idle-timer state
const screensaverVisible = ref(false)
let idleTimer: ReturnType<typeof setTimeout> | null = null

const IDLE_EVENTS = ['pointermove', 'pointerdown', 'keydown'] as const

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer)
  const timeoutMs = settingsStore.screensaverTimeout * 1000
  if (timeoutMs <= 0) return
  idleTimer = setTimeout(() => {
    screensaverVisible.value = true
  }, timeoutMs)
}

function dismissScreensaver() {
  screensaverVisible.value = false
  resetIdleTimer()
}

function onPlaceholderClick(position: { row: number; col: number }) {
  if (clipboardButton.value) {
    handlePlaceholderClick(position)
  } else {
    quickAddTarget.value = 'page'
    quickAddPosition.value = position
    quickAddVisible.value = true
  }
}

function onDockedPlaceholderClick(position: { row: number; col: number }) {
  if (clipboardButton.value) {
    handleDockedPlaceholderClick(position)
  } else {
    quickAddTarget.value = 'docked'
    quickAddPosition.value = position
    quickAddVisible.value = true
  }
}

// The sidebar's "+" header button picks the first empty slot itself and
// reports it here — same flow as clicking that slot directly.
const onDockedAddButton = onDockedPlaceholderClick

function onQuickAddSelect(button: Button) {
  if (quickAddTarget.value === 'docked') {
    if (currentProfile.value) {
      const dockedButton: Button = { ...button, id: `docked_${Date.now()}` }
      const updatedProfile = {
        ...currentProfile.value,
        dockedButtons: [...(currentProfile.value.dockedButtons || []), dockedButton]
      }
      dashboardStore.setProfile(updatedProfile)
      dashboardStore.saveProfile()
    }
  } else {
    dashboardStore.addButton(button)
  }
  quickAddVisible.value = false
  quickAddTarget.value = 'page'
  showActionResult({
    success: true,
    message: `Button added`
  })
}

// Global Virtual Keyboard logic
const keypadVisible = ref(false)
const keypadValue = ref('')
let activeInputElement: HTMLInputElement | HTMLTextAreaElement | null = null

function handleGlobalFocus(event: FocusEvent) {
  const target = event.target as HTMLElement
  if (
    target &&
    (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') &&
    !(target as HTMLInputElement).readOnly &&
    (target as HTMLInputElement).type !== 'checkbox' &&
    (target as HTMLInputElement).type !== 'radio' &&
    (target as HTMLInputElement).type !== 'file'
  ) {
    activeInputElement = target as HTMLInputElement | HTMLTextAreaElement
    keypadValue.value = activeInputElement.value || ''
    keypadVisible.value = true
  }
}

function handleKeypadUpdate(newValue: string) {
  keypadValue.value = newValue
  if (activeInputElement) {
    activeInputElement.value = newValue
    activeInputElement.dispatchEvent(new Event('input', { bubbles: true }))
    activeInputElement.dispatchEvent(new Event('change', { bubbles: true }))
  }
}

function handleKeypadClose() {
  keypadVisible.value = false
  activeInputElement = null
}

// Sidebar categories state
const actionSearch = ref('')
const expandedCategories = ref<string[]>([
  'quick-launch', 'system', 'audio', 'media', 'window-management', 
  'web', 'text', 'metrics', 'time', 'weather', 'navigation'
])

const actionCategories = ref([
  {
    id: 'quick-launch',
    name: 'Quick Launch',
    actions: [
      { id: 'launch-browser', name: 'Web Browser', icon: ['fas', 'globe'] },
      { id: 'launch-file-explorer', name: 'File Explorer', icon: ['fas', 'folder'] },
      { id: 'launch-calculator', name: 'Calculator', icon: ['fas', 'calculator'] },
      { id: 'launch-notepad', name: 'Notepad', icon: ['fas', 'file-alt'] },
      { id: 'launch-cmd', name: 'Command Prompt', icon: ['fas', 'terminal'] },
      { id: 'launch-powershell', name: 'PowerShell', icon: ['fas', 'terminal'] },
      { id: 'launch-paint', name: 'Paint', icon: ['fas', 'paint-brush'] },
      { id: 'launch-snipping-tool', name: 'Snipping Tool', icon: ['fas', 'cut'] }
    ]
  },
  {
    id: 'system',
    name: 'System',
    actions: [
      { id: 'shutdown', name: 'Shutdown', icon: ['fas', 'power-off'] },
      { id: 'restart', name: 'Restart', icon: ['fas', 'redo'] },
      { id: 'sleep', name: 'Sleep', icon: ['fas', 'moon'] },
      { id: 'lock', name: 'Lock Screen', icon: ['fas', 'lock'] },
      { id: 'brightness-up', name: 'Brightness Up', icon: ['fas', 'sun'] },
      { id: 'brightness-down', name: 'Brightness Down', icon: ['fas', 'moon'] },
      { id: 'empty-recycle-bin', name: 'Empty Recycle Bin', icon: ['fas', 'trash-alt'] },
      { id: 'task-manager', name: 'Task Manager', icon: ['fas', 'tasks'] },
      { id: 'control-panel', name: 'Control Panel', icon: ['fas', 'cog'] },
      { id: 'device-manager', name: 'Device Manager', icon: ['fas', 'hard-drive'] }
    ]
  },
  {
    id: 'audio',
    name: 'Audio & Volume',
    actions: [
      { id: 'volume-up', name: 'Volume Up', icon: ['fas', 'volume-up'] },
      { id: 'volume-down', name: 'Volume Down', icon: ['fas', 'volume-down'] },
      { id: 'mute', name: 'Mute/Unmute', icon: ['fas', 'volume-mute'] },
      { id: 'microphone-mute', name: 'Mute Microphone', icon: ['fas', 'microphone-slash'] },
      { id: 'microphone-unmute', name: 'Unmute Microphone', icon: ['fas', 'microphone'] }
    ]
  },
  {
    id: 'media',
    name: 'Media Control',
    actions: [
      { id: 'play-pause', name: 'Play/Pause', icon: ['fas', 'play'] },
      { id: 'next-track', name: 'Next Track', icon: ['fas', 'forward'] },
      { id: 'prev-track', name: 'Previous Track', icon: ['fas', 'backward'] },
      { id: 'stop', name: 'Stop', icon: ['fas', 'stop'] }
    ]
  },
  {
    id: 'window-management',
    name: 'Window Management',
    actions: [
      { id: 'minimize-window', name: 'Minimize Window', icon: ['fas', 'window-minimize'] },
      { id: 'maximize-window', name: 'Maximize Window', icon: ['fas', 'window-maximize'] },
      { id: 'close-window', name: 'Close Window', icon: ['fas', 'window-close'] },
      { id: 'switch-window', name: 'Switch Window (Alt+Tab)', icon: ['fas', 'window-restore'] },
      { id: 'show-desktop', name: 'Show Desktop', icon: ['fas', 'desktop'] }
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
      { id: 'run-command', name: 'Run Command', icon: ['fas', 'terminal'] },
      { id: 'close-app', name: 'Close Application', icon: ['fas', 'times-circle'] }
    ]
  },
  {
    id: 'text',
    name: 'Text & Input',
    actions: [
      { id: 'type-text', name: 'Type Text', icon: ['fas', 'keyboard'] },
      { id: 'hotkey', name: 'Hotkey', icon: ['fas', 'keyboard'] },
      { id: 'macro', name: 'Macro (Multiple Actions)', icon: ['fas', 'list-ol'] },
      { id: 'clipboard', name: 'Copy to Clipboard', icon: ['fas', 'clipboard'] }
    ]
  },
  {
    id: 'metrics',
    name: 'Monitor Metrics',
    actions: [
      { id: 'metric_cpu_usage', name: 'CPU Usage', icon: ['fas', 'microchip'] },
      { id: 'metric_memory', name: 'Memory', icon: ['fas', 'memory'] },
      { id: 'metric_harddisk', name: 'Hard Disk', icon: ['fas', 'hdd'] },
      { id: 'metric_cpu_frequency', name: 'CPU Frequency', icon: ['fas', 'wave-square'] },
      { id: 'metric_internet_speed', name: 'Internet Speed', icon: ['fas', 'network-wired'] },
      { id: 'metric_gpu_temperature', name: 'GPU Temperature', icon: ['fas', 'thermometer-half'] },
      { id: 'metric_gpu_usage', name: 'GPU Core Usage', icon: ['fas', 'grip-vertical'] },
      { id: 'metric_gpu_memory_usage', name: 'GPU Memory Usage', icon: ['fas', 'memory'] },
      { id: 'metric_gpu_frequency', name: 'GPU Core Frequency', icon: ['fas', 'wave-square'] },
      { id: 'metric_gpu_memory_freq', name: 'GPU Memory Frequency', icon: ['fas', 'memory'] }
    ]
  },
  {
    id: 'time',
    name: 'Time & Date',
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
      { id: 'weather', name: 'Weather', icon: ['fas', 'cloud-sun'] }
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
  },
  {
    id: 'streaming',
    name: 'Streaming (OBS)',
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
    name: 'Custom Media',
    actions: [
      { id: 'custom-icon', name: 'Custom Icon', icon: ['fas', 'image'] },
      { id: 'custom-gif', name: 'Custom GIF', icon: ['fas', 'film'] },
      { id: 'custom-video', name: 'Custom Video', icon: ['fas', 'video'] },
      { id: 'custom-sound', name: 'Custom Sound', icon: ['fas', 'volume-up'] }
    ]
  }
])

const filteredCategories = computed(() => {
  if (!actionSearch.value) return actionCategories.value
  return actionCategories.value.map(category => ({
    ...category,
    actions: category.actions.filter(action => 
      action.name.toLowerCase().includes(actionSearch.value.toLowerCase())
    )
  })).filter(category => category.actions.length > 0)
})

const currentProfile = computed(() => dashboardStore.currentProfile)
const currentScene = computed(() => dashboardStore.currentScene)
const currentPage = computed(() => dashboardStore.currentPage)
const currentSceneIndex = computed(() => dashboardStore.currentSceneIndex)
const currentPageIndex = computed(() => dashboardStore.currentPageIndex)
const isEditMode = computed(() => dashboardStore.isEditMode)

function toggleCategory(categoryId: string) {
  const index = expandedCategories.value.indexOf(categoryId)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

function moveCategoryUp(index: number) {
  if (index > 0) {
    const categories = actionCategories.value
    const temp = categories[index]
    categories[index] = categories[index - 1]
    categories[index - 1] = temp
  }
}

function moveCategoryDown(index: number) {
  if (index < actionCategories.value.length - 1) {
    const categories = actionCategories.value
    const temp = categories[index]
    categories[index] = categories[index + 1]
    categories[index + 1] = temp
  }
}

function closeSidebar() {
  dashboardStore.toggleEditMode()
}

// Background preferences
const dashboardBackgroundClass = computed(() => {
  if (settingsStore.backgroundPreference !== 'none') {
    return 'dashboard-bg-transparent'
  }
  if (currentPage.value?.background) {
    return ''
  }
  if (currentScene.value?.background?.image) {
    return 'dashboard-bg-custom'
  }
  const bg = settingsStore.dashboardBackground
  if (bg === 'default') return ''
  if (bg.startsWith('/api/uploads/') || bg.startsWith('/uploads/') || bg.startsWith('http')) {
    return 'dashboard-bg-custom'
  }
  return `dashboard-bg-${bg}`
})

const dashboardBackgroundStyle = computed(() => {
  if (settingsStore.backgroundPreference !== 'none') return {}
  if (currentScene.value?.background?.image) {
    return {
      backgroundImage: `url(${currentScene.value.background.image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  const bg = settingsStore.dashboardBackground
  if (bg.startsWith('/api/uploads/') || bg.startsWith('/uploads/') || bg.startsWith('http')) {
    return {
      backgroundImage: `url(${bg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  return {}
})

const mainStyle = computed(() => {
  if (settingsStore.backgroundPreference !== 'none') return {}
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

const shouldUseCompactMode = computed(() => {
  if (!currentPage.value) return false
  return currentPage.value.buttons.some(button => {
    const actionType = button.action?.type
    return actionType === 'weather' || 
           actionType === 'time_world_clock' || 
           actionType === 'time_timer' || 
           actionType === 'time_countdown'
  })
})

const isEditingExistingScene = computed(() => {
  if (!editingScene.value || !currentProfile.value) return false
  return currentProfile.value.scenes.some(scene => scene.id === editingScene.value!.id)
})

// Navigation & Scene handlers
function handleNavigateSettings() {
  if (settingsStore.openSettingsInNewTab) {
    openStandaloneSettings({ router })
    return
  }
  router.push('/settings')
}

function setScene(sceneId: string) {
  const idx = currentProfile.value?.scenes.findIndex(s => s.id === sceneId)
  if (idx !== undefined && idx >= 0) {
    dashboardStore.setScene(idx)
  }
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
        rows: 3,
        cols: 3
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
    dashboardStore.updateScene(scene.id, scene)
  } else {
    dashboardStore.addScene(scene)
  }
  editingScene.value = null
}

function handleSceneDelete(sceneId: string) {
  dashboardStore.removeScene(sceneId)
  editingScene.value = null
}

function handleSceneReset(sceneId: string) {
  dashboardStore.resetScene(sceneId)
  editingScene.value = null
  notificationsStore.success('Scene Reset', 'Scene restored to its default layout.')
}

function deleteCurrentPage() {
  if (!currentScene.value || currentScene.value.pages.length <= 1) {
    notificationsStore.error('Cannot Delete', 'A scene must have at least one page.')
    return
  }
  if (!currentPage.value) return
  if (!confirm(`Delete "${currentPage.value.name}"? This cannot be undone.`)) return
  dashboardStore.removePage(currentPageIndex.value)
  notificationsStore.success('Page Deleted', 'The page has been removed.')
}

function addPageToCurrentScene() {
  dashboardStore.addPage()
}

function updateGridRows(rows: number) {
  if (currentPage.value) {
    currentPage.value.grid_config.rows = rows
  }
}

function updateGridCols(cols: number) {
  if (currentPage.value) {
    currentPage.value.grid_config.cols = cols
  }
}

async function saveProfile() {
  await dashboardStore.saveProfile()
  notificationsStore.success('Profile Saved', 'All profile modifications stored.')
}

async function handleSaveProfileFromEditor() {
  await saveProfile()
}

async function createDefaultProfileForFirstTimeUser() {
  try {
    const defaultProfile = createDefaultProfile()
    const createdProfile = await profilesStore.createProfile({
      name: defaultProfile.name,
      description: defaultProfile.description,
      theme: defaultProfile.theme
    })

    if (createdProfile) {
      const updatedProfile = await profilesStore.updateProfile(createdProfile.id, {
        ...defaultProfile,
        id: createdProfile.id
      })

      if (updatedProfile) {
        dashboardStore.setProfile(updatedProfile)
      }
    }
  } catch (error) {
    console.error('Error creating default profile:', error)
  }
}

function nextScene() {
  if (!currentProfile.value || currentProfile.value.scenes.length <= 1) return
  const nextIdx = (currentSceneIndex.value + 1) % currentProfile.value.scenes.length
  setScene(currentProfile.value.scenes[nextIdx].id)
}

function previousScene() {
  if (!currentProfile.value || currentProfile.value.scenes.length <= 1) return
  const prevIdx = (currentSceneIndex.value - 1 + currentProfile.value.scenes.length) % currentProfile.value.scenes.length
  setScene(currentProfile.value.scenes[prevIdx].id)
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.ctrlKey || event.metaKey) {
    if (event.key === 'v' && clipboardButton.value) {
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

onMounted(async () => {
  // Load last used profile or first available profile
  const lastProfileId = localStorage.getItem('vdock_last_profile')
  let profileLoaded = false
  if (lastProfileId) {
    const profile = await profilesStore.getProfile(lastProfileId)
    if (profile) {
      dashboardStore.setProfile(profile)
      profileLoaded = true
    }
  }
  if (!profileLoaded) {
    await profilesStore.loadProfiles()
    if (profilesStore.profiles.length > 0) {
      const profile = await profilesStore.getProfile(profilesStore.profiles[0].id)
      if (profile) {
        dashboardStore.setProfile(profile)
        profileLoaded = true
      }
    }
  }
  if (!profileLoaded) {
    await createDefaultProfileForFirstTimeUser()
  }

  // Auto scene switching is bootstrapped once, globally, in App.vue —
  // registering it here too would leak a duplicate listener on every
  // Dashboard mount (see App.vue for the single owner).

  // Keyboard shortcut listener
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('focusin', handleGlobalFocus)

  // Idle timer for screensaver
  IDLE_EVENTS.forEach(ev => document.addEventListener(ev, resetIdleTimer, { passive: true }))
  resetIdleTimer()

  // Picks up settings/profile changes made in a separate Settings tab as
  // soon as that tab is closed, without waiting for a manual refresh.
  stopVdockRefreshListener = listenForVdockRefreshRequests()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('focusin', handleGlobalFocus)

  // Idle timer cleanup
  IDLE_EVENTS.forEach(ev => document.removeEventListener(ev, resetIdleTimer))
  if (idleTimer) clearTimeout(idleTimer)

  stopVdockRefreshListener?.()
})

watch(currentProfile, (profile) => {
  if (profile) {
    localStorage.setItem('vdock_last_profile', profile.id)
  }
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  box-sizing: border-box;
}

.dashboard-bg-transparent {
  background: transparent !important;
}

.deck-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s var(--ease-io);
}

.main-content.with-sidebar {
  margin-right: 0; /* Decomposed sidebar handles its own layout next to grid inside flex container */
}

.main-content.with-docked-sidebar {
  margin-left: 0;
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
  font-size: clamp(3.20rem, 2vw + 2.00rem, 4.80rem);
  opacity: 0.5;
}

.action-toast {
  position: fixed;
  bottom: var(--spacing-lg);
  right: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.3s var(--ease-out);
  z-index: 1000;
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

.global-onscreen-keypad {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100vw;
  z-index: 2000;
}

/* ── Page slide transitions ── */
.page-slide-left-enter-active,
.page-slide-left-leave-active,
.page-slide-right-enter-active,
.page-slide-right-leave-active {
  transition: transform 0.34s var(--ease-io), opacity 0.34s ease;
  will-change: transform;
}

.page-slide-left-enter-from {
  transform: translateX(34%);
  opacity: 0;
}
.page-slide-left-leave-to {
  transform: translateX(-34%);
  opacity: 0;
}

.page-slide-right-enter-from {
  transform: translateX(-34%);
  opacity: 0;
}
.page-slide-right-leave-to {
  transform: translateX(34%);
  opacity: 0;
}

/* Responsive .deck-main at <768px — sidebar becomes bottom drawer */
@media (max-width: 768px) {
  .deck-main {
    flex-direction: column;
  }

  .main-content {
    flex: 1;
  }
}

/* Dashboard grid layout */
.dashboard-layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
  grid-template-columns: auto 1fr;
  grid-template-rows: auto 1fr auto;
  height: 100vh;
  width: 100vw;
}

@media (max-width: 480px) {
  .dashboard-layout {
    grid-template-areas:
      "header"
      "main"
      "footer";
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
}
</style>
