<template>
  <div class="dashboard-view" :class="[dashboardBackgroundClass, { mobile: isMobileViewport }]" :style="dashboardBackgroundStyle">
    <!-- Dedicated slim chrome on phones: scene rail + page steppers only.
         The desktop header/footer don't mount on mobile at all (DL-063). -->
    <MobileDeckChrome
      v-if="isMobileViewport"
      :scenes="currentProfile?.scenes || []"
      :current-scene-index="currentSceneIndex"
      :total-pages="showsMobileAgentConsole ? 1 : currentScene?.pages.length || 1"
      :current-page-index="currentPageIndex"
      @set-scene="setScene"
      @previous-page="previousPage"
      @next-page="nextPage"
    />

    <!-- Decomposed Header component -->
    <DeckHeader
      v-else
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
      @import-scene="importScene"
      @set-page="setPage"
      @previous-page="previousPage"
      @next-page="nextPage"
    />

    <main class="deck-main" :style="mainStyle">
      <!-- Docked Sidebar -->
      <DockedSidebar
        v-slot:default
        v-if="settingsStore.dockedSidebarEnabled && currentPage && !isMobileViewport"
        :docked-buttons="currentProfile?.dockedButtons || []"
        :grid-rows="currentPage.grid_config.rows"
        :is-edit-mode="isEditMode"
        :show-labels="settingsStore.showLabels"
        :show-tooltips="settingsStore.showTooltips"
        :button-size="settingsStore.buttonSize * settingsStore.touchModeMultiplier"
        @button-click="handleButtonClick"
        @press="handleButtonPress"
        @release="handleButtonRelease"
        @button-release="handleButtonRelease"
        @button-edit="handleButtonEdit"
        @button-copy="handleButtonCopy"
        @button-delete="handleDockedButtonDelete"
        @button-drop="handleDockedButtonDrop"
        @placeholder-click="onDockedPlaceholderClick"
      />
      
      <div ref="mainContentRef" class="main-content" :class="{ 'with-sidebar': isEditMode, 'with-docked-sidebar': settingsStore.dockedSidebarEnabled && !isMobileViewport }">
        <!-- DL-082: the pane is keyed on the scene id, so a scene change
             remounts this subtree inside the wipe Transition — the old
             scene cross-dissolves out while the new one dissolves in,
             both live during the swap. Page flips keep the same key, so
             DeckGrid's own staggered transition still runs for those
             (and a fresh mount never double-fires it on a scene switch). -->
        <Transition :name="sceneTransitionName">
          <div v-if="currentPage" :key="currentScene?.id" class="scene-pane">
            <MobileAgentConsole v-if="showsMobileAgentConsole" :scene="currentScene" />
            <template v-else>
              <AgentActionBar :scene="currentScene" />
              <div class="deck-grid-host">
                <DeckGrid
                  :page="currentPage"
                  :is-edit-mode="isEditMode"
                  :button-size="settingsStore.buttonSize * settingsStore.touchModeMultiplier"
                  :show-labels="settingsStore.showLabels"
                  :show-tooltips="settingsStore.showTooltips"
                  :compact="shouldUseCompactMode"
                  @button-click="handleButtonClick"
                  @button-press="handleButtonPress"
                  @button-release="handleButtonRelease"
                  @button-edit="handleButtonEdit"
                  @button-copy="handleButtonCopy"
                  @button-delete="handleButtonDelete"
                  @action-drop="handleActionDrop"
                  @placeholder-click="onPlaceholderClick"
                  @button-move="handleButtonMove"
                  @button-swap="handleButtonSwap"
                  @slider-expand="handleSliderExpand"
                  @slider-shrink="handleSliderShrink"
                  @double-tap="handleButtonClick"
                  @exit-edit-mode="dashboardStore.toggleEditMode"
                />
              </div>
            </template>
          </div>
        </Transition>
        <AgentWaitingGlow />

        <div v-if="!currentPage" class="no-profile">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" class="no-profile-icon" />
          <p>No profile loaded</p>
          <!-- Mobile never gets profile-management UI (DL-061) — this state
               means the desktop app hasn't set one up yet either, so send
               the user there instead of into a picker phones shouldn't have. -->
          <button v-if="!isMobileViewport" class="btn btn-primary" @click="router.push('/profiles')">
            Select Profile
          </button>
          <p v-else class="no-profile-hint">Set up a profile on the VDock desktop app first.</p>
        </div>
      </div>

      <!-- Decomposed Edit Sidebar component -->
      <EditSidebar
        v-if="isEditMode"
        v-model:action-search="actionSearch"
        :expanded-categories="effectiveExpandedCategories"
        :filtered-categories="filteredCategories"
        @toggle-category="toggleCategory"
        @select-action="selectAction"
        @close="closeSidebar"
      />
    </main>

    <!-- Decomposed Footer component — replaced by the page steppers in
         MobileDeckChrome on phones. Only mounts when it has content —
         edit controls (edit mode) or page dots (multi-page) — and slides
         up from below the viewport edge / down off it. Outside those
         states the grid reclaims the strip; the header reveal is a
         floating button now (DL-102), not footer content. -->
    <Transition name="footer-slide">
      <DeckFooter
        v-if="footerVisible"
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
    </Transition>

    <!-- DL-102: independent header reveal — a compact floating button, not
         a docked pill. Bottom-RIGHT: the docked sidebar owns the left edge
         and page dots/edit controls sit footer-left/center, so the right
         corner is the only spot that never collides. When the footer is
         mounted it lifts above the strip. Tap or swipe down reveals —
         the same gesture the header dismisses with (swipe up), reversed. -->
    <Transition name="reveal-fab">
      <button
        v-if="!isMobileViewport && !settingsStore.showHeader && !isEditMode"
        ref="revealFabRef"
        type="button"
        class="header-reveal-fab"
        :class="{ 'above-footer': footerVisible }"
        title="Swipe down or tap to show header"
        aria-label="Show header"
        @click="revealHeader"
      >
        <!-- Mini window-with-header glyph (DL-104): a tiny panel whose
             accent header band is what's summoned — reads as "drop the
             header down", not a generic arrow. The word sits on the
             button body so it can't be missed. -->
        <span class="fab-head" aria-hidden="true"></span>
        <span class="fab-body">
          <span class="fab-label">Header</span>
          <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="fab-caret" />
        </span>
      </button>
    </Transition>

    <!-- Screen Saver overlay — wrapped in a dissolve Transition (DL-003
         follow-up): it blooms in from center on idle, and evaporates
         edges-in back to the deck on dismiss. -->
    <Transition name="saver-dissolve">
      <ScreenSaver
        v-if="screensaverVisible"
        :visible="screensaverVisible"
        :layout-edit="screensaverLayoutEdit"
        @dismiss="dismissScreensaver"
        @save-layout="saveScreensaverLayout"
      />
    </Transition>

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

    <!-- Phones: the deck is landscape-only — portrait shows a rotate prompt -->
    <RotateToLandscape :portrait-allowed="screensaverVisible || showsMobileAgentConsole" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { LAST_PROFILE_STORAGE_KEY, useDashboardStore } from '@/stores/dashboard'
import { useActionCatalogStore } from '@/stores/actionCatalog'
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
import MobileDeckChrome from '@/components/MobileDeckChrome.vue'
import ScreenSaver from '@/components/ScreenSaver.vue'
import EditSidebar from '@/components/EditSidebar.vue'
import QuickAddPicker from '@/components/QuickAddPicker.vue'
import OnScreenKeypad from '@/components/OnScreenKeypad.vue'
import RotateToLandscape from '@/components/RotateToLandscape.vue'
import AgentActionBar from '@/components/AgentActionBar.vue'
import AgentWaitingGlow from '@/components/AgentWaitingGlow.vue'
import MobileAgentConsole from '@/components/MobileAgentConsole.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { createDefaultProfile } from '@/utils/defaultProfile'
import { useTutorial } from '@/services/tutorial'
import { openStandaloneSettings } from '@/utils/openStandaloneSettings'
import { backgroundClassFor, backgroundStyleFor } from '@/utils/backgroundStyle'
import { appBackgroundForScene } from '@/data/appBackgrounds'
import { loadProfileMaps, sceneAppProfile } from '@/services/appDetection'
import { agentStateEntry } from '@/services/agentState'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { useButtonActions } from '@/composables/useButtonActions'
import { listenForVdockRefreshRequests } from '@/composables/useVdockRefresh'
import { listenForUiCommands } from '@/composables/useUiCommands'
import { confirmDialog } from '@/composables/useConfirm'
import { useMobileViewport } from '@/utils/mobileViewport'
import { useSwipe } from '@/composables/useGestures'
import { sceneSwipe } from '@/services/sceneSwipe'
import type { ScreensaverLayout } from '@/utils/screensaverLayout'

const router = useRouter()
const dashboardStore = useDashboardStore()
const actionCatalogStore = useActionCatalogStore()
const profilesStore = useProfilesStore()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()

const editingScene = ref<Scene | null>(null)
let stopVdockRefreshListener: (() => void) | null = null
let stopUiCommandListener: (() => void) | null = null

// Composables logic
const {
  editingButton,
  clipboardButton,
  selectedAction,
  actionResult,
  showActionResult,
  handleButtonClick,
  handleButtonPress,
  handleButtonRelease,
  handleButtonEdit,
  handleButtonCopy,
  handleButtonDelete,
  handleButtonMove,
  handleButtonSwap,
  handleSliderExpand,
  handleSliderShrink,
  handleActionDrop,
  handlePlaceholderClick,
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
const tour = useTutorial()
// True while the screensaver is showing its drag/resize layout editor —
// reached via the 'screensaver_layout_edit' ui_command from Settings.
const screensaverLayoutEdit = ref(false)
let idleTimer: ReturnType<typeof setTimeout> | null = null

const IDLE_EVENTS = ['pointermove', 'pointerdown', 'keydown'] as const

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer)
  const timeoutMs = settingsStore.screensaverTimeout * 1000
  if (timeoutMs <= 0) return
  idleTimer = setTimeout(() => {
    // Never cover the walkthrough with the screensaver — an open tour is
    // active engagement even without pointer events.
    if (!tour.state.active) screensaverVisible.value = true
  }, timeoutMs)
}

function dismissScreensaver() {
  screensaverVisible.value = false
  screensaverLayoutEdit.value = false
  resetIdleTimer()
}

// Tour ↔ screensaver mutex: starting the tour dismisses the screensaver;
// the screensaver appearing (idle timer is guarded, but ui_commands can
// force it) ends the tour so bubbles never float over the saver.
watch(() => tour.state.active, (active) => {
  if (active && screensaverVisible.value) dismissScreensaver()
})
watch(screensaverVisible, (visible) => {
  if (visible && tour.state.active) tour.finish()
})

function saveScreensaverLayout(layout: ScreensaverLayout) {
  // Assigning the store ref persists through the settings watch → local +
  // server sync.
  settingsStore.screensaverLayout = layout
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
  // Inputs built for the device's own keyboard (the phone console composer)
  // would get the keypad stacked on top of it.
  if (target?.closest('[data-native-keyboard]')) return
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

// Sidebar categories state — categories start collapsed so the sidebar
// opens as a compact category index; a click drills into one.
const actionSearch = ref('')
const expandedCategories = ref<string[]>([])

const actionCategories = ref([
  {
    id: 'quick-launch',
    name: 'Quick Launch',
    icon: ['fas', 'rocket'],
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
    icon: ['fas', 'desktop'],
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
    icon: ['fas', 'volume-high'],
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
    icon: ['fas', 'music'],
    actions: [
      { id: 'play-pause', name: 'Play/Pause', icon: ['fas', 'play'] },
      { id: 'next-track', name: 'Next Track', icon: ['fas', 'forward'] },
      { id: 'prev-track', name: 'Previous Track', icon: ['fas', 'backward'] },
      { id: 'stop', name: 'Stop', icon: ['fas', 'stop'] }
    ]
  },
  {
    id: 'window-management',
    name: 'Windows',
    icon: ['fas', 'window-restore'],
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
    icon: ['fas', 'globe'],
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
    icon: ['fas', 'keyboard'],
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
    icon: ['fas', 'chart-line'],
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
    icon: ['fas', 'clock'],
    actions: [
      { id: 'time_world_clock', name: 'World Time', icon: ['fas', 'globe'] },
      { id: 'time_timer', name: 'Timer', icon: ['fas', 'stopwatch'] },
      { id: 'time_countdown', name: 'Countdown', icon: ['fas', 'hourglass-half'] }
    ]
  },
  {
    id: 'weather',
    name: 'Weather',
    icon: ['fas', 'cloud-sun'],
    actions: [
      { id: 'weather', name: 'Weather', icon: ['fas', 'cloud-sun'] }
    ]
  },
  {
    id: 'navigation',
    name: 'Navigation',
    icon: ['fas', 'compass'],
    actions: [
      { id: 'next-page', name: 'Next Page', icon: ['fas', 'arrow-right'] },
      { id: 'previous-page', name: 'Previous Page', icon: ['fas', 'arrow-left'] },
      { id: 'home-page', name: 'Home Page', icon: ['fas', 'home'] }
    ]
  },
  {
    id: 'streaming',
    name: 'Streaming (OBS)',
    icon: ['fas', 'video'],
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
    icon: ['fas', 'puzzle-piece'],
    actions: [
      { id: 'custom-icon', name: 'Custom Icon', icon: ['fas', 'image'] },
      { id: 'custom-gif', name: 'Custom GIF', icon: ['fas', 'film'] },
      { id: 'custom-video', name: 'Custom Video', icon: ['fas', 'video'] },
      { id: 'custom-sound', name: 'Custom Sound', icon: ['fas', 'volume-up'] }
    ]
  }
])

/**
 * Categories contributed by the backend action catalog (AI Assistants,
 * Developer, and anything an integration pack adds).
 *
 * The hardcoded list above only covers presetRegistry entries, so without this
 * the Claude, Cursor, Copilot and GitHub actions were reachable only from the
 * button editor's "Browse Button Actions" panel -- the main sidebar offered 71
 * items and none of them. Only categories the hardcoded list does not already
 * cover are appended, so nothing appears twice.
 */
/**
 * Names the hardcoded list already offers, so a catalog entry for the same
 * thing is not listed twice.
 *
 * Deduplicating by name rather than by category matters: excluding whole
 * categories hid genuinely new actions that happen to share a category with
 * existing ones -- `http_request` sits in "Web & Apps" and the window
 * management entries in "System", and both would have been dropped.
 */
const hardcodedActionNames = computed(
  () => new Set(
    actionCategories.value.flatMap(c => c.actions.map(a => a.name.toLowerCase()))
  )
)

const catalogCategories = computed(() => {
  const alreadyListed = hardcodedActionNames.value

  return actionCatalogStore.populatedCategories
    .map(category => ({
      id: `catalog-${category.id}`,
      name: category.label,
      icon: category.icon,
      actions: actionCatalogStore
        .actionsInCategory(category.id)
        .filter(spec => !alreadyListed.has(spec.label.toLowerCase()))
        .map(spec => ({
          id: spec.id,
          name: spec.label,
          icon: spec.icon,
          // Marks this as a catalog entry so resolveButtonForAction builds the
          // button from the spec (type *and* config) instead of guessing.
          catalogId: spec.id,
          unavailableReason: spec.unavailable_reason
        }))
    }))
    .filter(category => category.actions.length > 0)
})

/**
 * Hardcoded categories first, with catalog entries merged into the category of
 * the same name, and genuinely new categories (AI Assistants, Developer)
 * appended. Merging rather than appending keeps one "Web & Apps" section
 * instead of two that differ only in contents.
 */
/** Catalog category name -> the hardcoded section it belongs in. */
const CATEGORY_ALIASES: Record<string, string> = {
  'text & clipboard': 'text & input',
  'system metrics': 'monitor metrics',
  time: 'time & date',
  streaming: 'streaming (obs)',
  custom: 'custom media'
}

const allCategories = computed(() => {
  const merged = actionCategories.value.map(category => ({ ...category }))
  const byName = new Map(merged.map(c => [c.name.toLowerCase(), c]))
  const appended: typeof merged = []

  for (const category of catalogCategories.value) {
    const key = category.name.toLowerCase()
    const existing = byName.get(key) ?? byName.get(CATEGORY_ALIASES[key] ?? '')
    if (existing) {
      existing.actions = [...existing.actions, ...category.actions]
    } else {
      appended.push(category as (typeof merged)[number])
    }
  }

  return [...merged, ...appended]
})

const filteredCategories = computed(() => {
  if (!actionSearch.value) return allCategories.value
  const query = actionSearch.value.toLowerCase()
  return allCategories.value.map(category => ({
    ...category,
    actions: category.actions.filter(action =>
      action.name.toLowerCase().includes(query)
    )
  })).filter(category => category.actions.length > 0)
})

// What EditSidebar renders as open: while a search is active every matching
// category expands so results aren't hidden inside collapsed groups.
const effectiveExpandedCategories = computed(() =>
  actionSearch.value.trim()
    ? filteredCategories.value.map(category => category.id)
    : expandedCategories.value
)

const currentProfile = computed(() => dashboardStore.currentProfile)
const currentScene = computed(() => dashboardStore.currentScene)
const currentPage = computed(() => dashboardStore.currentPage)
const currentSceneIndex = computed(() => dashboardStore.currentSceneIndex)
const currentPageIndex = computed(() => dashboardStore.currentPageIndex)
const isEditMode = computed(() => dashboardStore.isEditMode)
// DL-102: the footer only earns its strip for real content — edit controls
// or multi-page dots. The header reveal floats independently and lifts
// above the strip via .above-footer whenever this is true.
const footerVisible = computed(() =>
  !isMobileViewport.value && (isEditMode.value || (currentScene.value?.pages.length || 1) > 1)
)
// Phones: hide the docked sidebar (config-bound dead width), let the
// header overlay instead of squeezing the deck, and reserve a slim top
// strip so the header-reveal pill never sits on buttons.
const { isMobileViewport } = useMobileViewport()

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

// Background preferences
const appIntegrations = useAppIntegrations()

// Phones get a portrait console instead of the grid on agent scenes (DL-065).
const showsMobileAgentConsole = computed(() => {
  const scene = currentScene.value
  if (!isMobileViewport.value || !scene || isEditMode.value) return false
  return Boolean(sceneAppProfile(scene, appIntegrations.value)?.state_actions)
})

// A reply or permission prompt reaching the phone console is what the user
// is waiting for, so it wakes the screen like a touch would.
const mobileConsoleConversationKey = computed(() => {
  const scene = currentScene.value
  if (!showsMobileAgentConsole.value || !scene) return null
  const entry = agentStateEntry(sceneAppProfile(scene, appIntegrations.value)?.status_source)
  return entry ? [entry.state, entry.prompt, entry.reply].join('\u0000') : null
})
watch(mobileConsoleConversationKey, (conversationKey) => {
  if (conversationKey) dismissScreensaver()
})
// The scene slot resolves to the user's explicit override first; absent that,
// an app-associated scene falls back to its bundled app wallpaper.
const effectiveSceneBackground = computed(() => {
  const scene = currentScene.value
  if (!scene) return undefined
  if (scene.background) return scene.background
  const appDefault = appBackgroundForScene(scene, appIntegrations.value)
  return appDefault ? { type: 'image' as const, image: appDefault.image } : undefined
})
const dashboardBackgroundClass = computed(() =>
  backgroundClassFor(settingsStore.background, effectiveSceneBackground.value, currentPage.value?.background)
)
const dashboardBackgroundStyle = computed(() =>
  backgroundStyleFor(settingsStore.background, effectiveSceneBackground.value)
)
// `mainStyle` exists only to paint a page-level background on <main>. It must
// never fall through to backgroundStyleFor's global-image branch — that
// backdrop is already painted on .dashboard-view via dashboardBackgroundStyle,
// and painting it again here double-paints the image with a different
// cover-cropped rect, producing a visible seam at the header boundary.
const mainStyle = computed(() =>
  currentPage.value?.background
    ? backgroundStyleFor(settingsStore.background, undefined, currentPage.value.background)
    : {}
)

const shouldUseCompactMode = computed(() => {
  if (!currentPage.value) return false
  return currentPage.value.buttons.some(button => {
    const actionType = button.action?.type
    return actionType === 'weather' || 
           actionType === 'time_world_clock' || 
           actionType === 'time_timer' ||
           actionType === 'time_stopwatch' ||
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
    // DL-082: pick the dissolve direction from the shortest path between
    // indexes so rail clicks, steppers, and swipes all wipe the right way.
    const n = currentProfile.value?.scenes.length ?? 0
    if (n > 1 && idx !== currentSceneIndex.value) {
      const forward = (idx - currentSceneIndex.value + n) % n
      sceneTransitionName.value =
        forward <= n - forward ? 'scene-wipe-next' : 'scene-wipe-prev'
    }
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

function importScene(scene: Scene) {
  dashboardStore.addScene(scene)
  notificationsStore.success('Scene imported', `"${scene.name}" added to this profile.`)
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

async function deleteCurrentPage() {
  if (!currentScene.value || currentScene.value.pages.length <= 1) {
    notificationsStore.error('Cannot Delete', 'A scene must have at least one page.')
    return
  }
  if (!currentPage.value) return
  const ok = await confirmDialog({
    title: `Delete "${currentPage.value.name}"?`,
    message: 'This page and its buttons will be removed. This cannot be undone.',
    confirmLabel: 'Delete',
  })
  if (!ok) return
  dashboardStore.removePage(currentPage.value.id)
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

// DL-082 — horizontal (and vertical) swipes anywhere over the content area
// switch scenes: the single listener covers the deck grid, the agent action
// bar, and the mobile agent console, which had no swipe surface at all.
// While a horizontal swipe tracks, the shared `sceneSwipe` state lets the
// scene rails dissolve the active segment 1:1 under the finger.
const mainContentRef = ref<HTMLElement | null>(null)
const sceneTransitionName = ref('scene-wipe-next')
const revealFabRef = ref<HTMLElement | null>(null)

function revealHeader() {
  settingsStore.showHeader = true
}

// Swipe down on the reveal button reveals too — the same gesture the
// header dismisses with (swipe up) in reverse.
useSwipe(revealFabRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'DOWN') revealHeader()
  }
})
let sceneSwipeArmed = false
let swipeAxisBlocked = { horizontal: false, vertical: false }

/** Whether the swipe's start target can natively scroll on an axis — if
    so the gesture on that axis belongs to the scroller, not to scene
    switching (e.g. an overflowing compact grid or a scrollable pane). */
function scrollableAxes(el0: HTMLElement | null): { horizontal: boolean; vertical: boolean } {
  const blocked = { horizontal: false, vertical: false }
  let el = el0
  while (el && el !== mainContentRef.value && !(blocked.horizontal && blocked.vertical)) {
    const style = getComputedStyle(el)
    if ((style.overflowX === 'auto' || style.overflowX === 'scroll') && el.scrollWidth > el.clientWidth)
      blocked.horizontal = true
    if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight)
      blocked.vertical = true
    el = el.parentElement
  }
  return blocked
}

useSwipe(mainContentRef, {
  threshold: 50,
  onSwipeStart: (e) => {
    sceneSwipeArmed =
      !isEditMode.value &&
      (currentProfile.value?.scenes.length ?? 0) > 1 &&
      !(e.target as HTMLElement).closest(
        'input, textarea, select, [contenteditable="true"], .agent-target-popover, .onscreen-keypad, .slider-face'
      )
    swipeAxisBlocked = sceneSwipeArmed
      ? scrollableAxes(e.target as HTMLElement)
      : { horizontal: true, vertical: true }
    sceneSwipe.dragging = false
    sceneSwipe.progress = 0
  },
  onSwipe: (direction, progress) => {
    const horizontal = direction === 'LEFT' || direction === 'RIGHT'
    if (!sceneSwipeArmed || !horizontal || swipeAxisBlocked.horizontal) {
      if (sceneSwipe.dragging) { sceneSwipe.dragging = false; sceneSwipe.progress = 0 }
      return
    }
    sceneSwipe.dragging = true
    sceneSwipe.dir = direction === 'LEFT' ? 'next' : 'prev'
    sceneSwipe.progress = progress
  },
  onSwipeEnd: (direction) => {
    const horizontal = direction === 'LEFT' || direction === 'RIGHT'
    const blocked = horizontal ? swipeAxisBlocked.horizontal : swipeAxisBlocked.vertical
    if (sceneSwipeArmed && !blocked) {
      if (horizontal) {
        sceneSwipe.justSwiped = true
        if (direction === 'LEFT') nextScene()
        else previousScene()
      } else if (direction === 'UP') {
        nextScene()
      } else if (direction === 'DOWN') {
        previousScene()
      }
    }
    sceneSwipe.dragging = false
    sceneSwipeArmed = false
  },
  onSwipeCancel: () => {
    // Below-threshold release / pointercancel: the rails read
    // `dragging=false` and transition the segment back to full opacity.
    sceneSwipe.dragging = false
    sceneSwipeArmed = false
  }
})

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

    // Edit-mode undo/redo — the store keeps profile history but nothing
    // triggered it. Ctrl+Z splits a mistaken slider merge, restores a
    // deleted button, etc. saveProfile keeps disk in sync like every
    // other mutation.
    const key = event.key.toLowerCase()
    if (isEditMode.value && (key === 'z' || key === 'y')) {
      event.preventDefault()
      if (key === 'z' && !event.shiftKey && dashboardStore.canUndo) {
        dashboardStore.undo()
        dashboardStore.saveProfile()
      } else if ((key === 'y' || (key === 'z' && event.shiftKey)) && dashboardStore.canRedo) {
        dashboardStore.redo()
        dashboardStore.saveProfile()
      }
    }
  }
}

onMounted(async () => {
  // Fetch app-profile metadata (state_actions, prompt_command, …) up front
  // instead of waiting for AgentActionBar/MobileAgentConsole to mount and
  // request it themselves. With app scanning off (the default) nothing else
  // triggers this fetch, so `showsMobileAgentConsole` could otherwise stay
  // false — grid buttons but no agent controls on a phone — until whichever
  // surface happens to mount first pulls it in on its own. See DL-065
  // follow-up.
  void loadProfileMaps()

  // Load the profile every device should land on. The server-persisted
  // `activeProfileId` (set by `setProfile` on every device, DL-061
  // follow-up) is checked first so a phone connecting for the first time
  // opens the SAME profile the desktop is already using, instead of this
  // per-browser localStorage cache (kept as a fallback for the offline/
  // settings-fetch-failed case) or, worse, falling all the way through to
  // "first profile on the backend" or bootstrapping a brand new one.
  await settingsStore.ensureSettingsLoaded()
  const lastProfileId = settingsStore.activeProfileId || localStorage.getItem(LAST_PROFILE_STORAGE_KEY)
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

  // First-run bubble tutorial (or a "Launch Tutorial" request from Settings).
  // `settingsStore.ensureSettingsLoaded()` already resolved above (before the
  // profile load), so `tutorialCompleted` is guaranteed to hold its real
  // server value here rather than the `ref(false)` default.
  //
  // Skipped entirely on phones (DL-061 follow-up): the tour's first step
  // navigates to '/profiles' to walk through profile selection — a screen
  // mobile has no business showing (DL-061, "mobile = control surface
  // only") — and every phone connecting to an already-set-up desktop has
  // already had that walkthrough there.
  if (!isMobileViewport.value) {
    // Delayed so the deck renders before the tour starts measuring targets.
    setTimeout(() => tour.consumePendingOrFirstRun(), 800)
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

  // UI commands from other windows (e.g. "Test Screensaver" in Settings).
  // Setting the flag directly means the preview also works when
  // screensaverTimeout is 0 (screensaver disabled).
  stopUiCommandListener = listenForUiCommands((command) => {
    if (command === 'show_screensaver') {
      screensaverVisible.value = true
    }
    if (command === 'screensaver_layout_edit') {
      screensaverLayoutEdit.value = true
      screensaverVisible.value = true
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('focusin', handleGlobalFocus)

  // Idle timer cleanup
  IDLE_EVENTS.forEach(ev => document.removeEventListener(ev, resetIdleTimer))
  if (idleTimer) clearTimeout(idleTimer)

  stopVdockRefreshListener?.()
  stopUiCommandListener?.()
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  position: relative; /* anchor for the mobile overlay header */
  width: 100vw;
  height: 100vh;
  /* iOS Safari: 100vh covers the collapsing URL bar, hiding bottom
     chrome; dvh tracks the real visible height (ignored pre-15.4). */
  height: 100dvh;
  overflow: hidden;
  box-sizing: border-box;
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
  position: relative; /* anchors the leaving scene-pane during a wipe */
  /* Scene swipes live here (DL-082): vertical pans stay native scroll,
     horizontal is ours; contain stops Chrome-Android pull-to-refresh
     from stealing the gesture mid-swipe. */
  touch-action: pan-y;
  overscroll-behavior-y: contain;
  transition: all 0.3s var(--ease-io);
}

/* DL-082 — keyed scene pane + directional dissolve.
   The wipe is a travelling soft mask edge: mask-image is a 250%-wide
   gradient (transparent band on one side, opaque on the other) and
   mask-position sweeps across, combined with an opacity fade and a small
   translateX drift in the travel direction. "next" (swipe-left / index+)
   sweeps L→R — the outgoing scene dissolves from its leading left edge;
   "prev" sweeps R→L. Both panes run simultaneously (default mode): the
   leaving pane goes absolute + topmost so its dissolve reads over the
   incoming scene. */
.scene-pane {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.scene-wipe-next-enter-active,
.scene-wipe-next-leave-active,
.scene-wipe-prev-enter-active,
.scene-wipe-prev-leave-active {
  transition:
    -webkit-mask-position 0.42s var(--ease-io),
    mask-position 0.42s var(--ease-io),
    opacity 0.42s var(--ease-io),
    transform 0.42s var(--ease-io);
  will-change: transform, opacity;
}

.scene-wipe-next-leave-active,
.scene-wipe-prev-leave-active {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}

/* next: wave travels L→R */
.scene-wipe-next-enter-active {
  -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
  mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
  -webkit-mask-size: 250% 100%;
  mask-size: 250% 100%;
}
.scene-wipe-next-enter-from {
  -webkit-mask-position: 100% 0;
  mask-position: 100% 0;
  opacity: 0.4;
  transform: translateX(28px);
}
.scene-wipe-next-enter-to {
  -webkit-mask-position: 0% 0;
  mask-position: 0% 0;
}
.scene-wipe-next-leave-active {
  -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
  mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
  -webkit-mask-size: 250% 100%;
  mask-size: 250% 100%;
}
.scene-wipe-next-leave-from {
  -webkit-mask-position: 100% 0;
  mask-position: 100% 0;
}
.scene-wipe-next-leave-to {
  -webkit-mask-position: 0% 0;
  mask-position: 0% 0;
  opacity: 0;
  transform: translateX(-28px);
}

/* prev: wave travels R→L (mirrored gradients, reversed sweep) */
.scene-wipe-prev-enter-active {
  -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
  mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
  -webkit-mask-size: 250% 100%;
  mask-size: 250% 100%;
}
.scene-wipe-prev-enter-from {
  -webkit-mask-position: 0% 0;
  mask-position: 0% 0;
  opacity: 0.4;
  transform: translateX(-28px);
}
.scene-wipe-prev-enter-to {
  -webkit-mask-position: 100% 0;
  mask-position: 100% 0;
}
.scene-wipe-prev-leave-active {
  -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
  mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
  -webkit-mask-size: 250% 100%;
  mask-size: 250% 100%;
}
.scene-wipe-prev-leave-from {
  -webkit-mask-position: 0% 0;
  mask-position: 0% 0;
}
.scene-wipe-prev-leave-to {
  -webkit-mask-position: 100% 0;
  mask-position: 100% 0;
  opacity: 0;
  transform: translateX(28px);
}

@media (prefers-reduced-motion: reduce) {
  .scene-wipe-next-enter-active,
  .scene-wipe-next-leave-active,
  .scene-wipe-prev-enter-active,
  .scene-wipe-prev-leave-active {
    transition: opacity 0.2s ease;
    -webkit-mask-image: none;
    mask-image: none;
    transform: none;
  }
  .scene-wipe-next-enter-from,
  .scene-wipe-prev-enter-from {
    transform: none;
    opacity: 0.4;
  }
}

/* DL-003 follow-up — screensaver fade. Was a mask-size dissolve; animating
   a mask on a full-viewport layer over a WebGL bg (Prismatic Burst)
   re-rasterized the mask every frame — read as flicker. Composited
   opacity+transform only: the GPU handles it and no paint runs. Enter
   fades in drifting down from a faint zoom; leave is the time-reverse. */
.saver-dissolve-enter-active {
  animation: saver-in 0.45s var(--ease-out) both;
}
.saver-dissolve-leave-active {
  pointer-events: none; /* a dissolving saver must not eat the tap's follow-ups */
  animation: saver-out 0.3s var(--ease-out) both;
}
@keyframes saver-in {
  from {
    opacity: 0;
    transform: scale(1.025);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes saver-out {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(1.025);
  }
}

@media (prefers-reduced-motion: reduce) {
  .saver-dissolve-enter-active {
    animation: saver-fade-in 0.25s ease both;
  }
  .saver-dissolve-leave-active {
    animation: saver-fade-out 0.25s ease both;
  }
}
@keyframes saver-fade-in {
  from { opacity: 0; }
}
@keyframes saver-fade-out {
  to { opacity: 0; }
}

/* The grid is height: 100% of its parent; this host gives it only the space
   left under the agent action bar instead of the whole column. */
.deck-grid-host {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
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

.no-profile-hint {
  max-width: 260px;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.no-profile-icon {
  font-size: clamp(3.20rem, 2vw + 2.00rem, 4.80rem);
  opacity: 0.5;
}

/* DL-102 + DL-104: floating header reveal — a mini "window" whose accent
   header band is the thing being summoned (reference: a form with a green
   header). Bottom-right because the left edge belongs to the docked
   sidebar and the footer's left/center to page dots and edit controls.
   Glass chrome, translucent enough that the corner tile it grazes stays
   readable; ≥44px touch floor on both axes. */
.header-reveal-fab {
  position: fixed;
  right: var(--spacing-touch-md, var(--spacing-md));
  bottom: var(--spacing-touch-md, var(--spacing-md));
  width: max(92px, calc(92px * min(var(--touch-multiplier, 1), 1.4)));
  height: max(58px, calc(58px * min(var(--touch-multiplier, 1), 1.4)));
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(10, 8, 32, 0.66);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  opacity: 0.8;
  transition: opacity 0.2s ease, transform 0.2s ease, bottom 0.3s var(--ease-io, ease);
  z-index: 95;
  touch-action: none;
  -webkit-user-select: none;
  user-select: none;
  animation: fab-breathe 3s ease-in-out infinite;
}

/* The accent "header" band across the top of the mini window — the part
   the button summons. It bobs down a couple px on a loop: a tactile
   "the header drops" hint legible where hover never fires. */
.fab-head {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(180deg, #40B3A2 0%, #2e8b7d 100%);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.25) inset;
  animation: fab-head-drop 2.6s ease-in-out infinite;
}

@keyframes fab-head-drop {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(2px); }
}

/* Body row under the band: the label names the control, the caret is
   the pull-down cue. */
.fab-body {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  top: 40%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.fab-label {
  color: rgba(255, 255, 255, 0.95);
  font-size: calc(0.86rem * min(var(--touch-multiplier, 1), 1.4));
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1;
}

.fab-caret {
  color: rgba(255, 255, 255, 0.9);
  font-size: calc(0.95rem * min(var(--touch-multiplier, 1), 1.4));
}

.header-reveal-fab.above-footer {
  bottom: calc(max(44px, calc(56px * var(--touch-multiplier, 1))) + 10px);
}

.header-reveal-fab:hover,
.header-reveal-fab:focus-visible,
.header-reveal-fab:active {
  opacity: 1;
  transform: scale(1.08);
}

/* A soft periodic ring keeps the control discoverable on touchscreens,
   where hover never fires — a bare icon button would read as decoration. */
@keyframes fab-breathe {
  0%, 100% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35), 0 0 0 0 rgba(255, 255, 255, 0.18); }
  50% { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35), 0 0 0 6px rgba(255, 255, 255, 0); }
}

.reveal-fab-enter-active,
.reveal-fab-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.reveal-fab-enter-from,
.reveal-fab-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (prefers-reduced-motion: reduce) {
  .header-reveal-fab,
  .fab-head { animation: none; transition: none; }
  .reveal-fab-enter-active,
  .reveal-fab-leave-active { transition: none; }
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
  height: 100dvh;
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
