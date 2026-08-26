<template>
  <div class="deck-header-wrapper" :class="{ 'header-hidden': !settingsStore.showHeader }">
    <!-- Reveal trigger area (visible when header is hidden). Large + mostly
         transparent hit-target so it's easy to grab with a swipe or tap
         without needing pixel-perfect precision. -->
    <div
      v-if="!settingsStore.showHeader"
      ref="triggerRef"
      class="header-reveal-trigger"
      @click="revealHeader"
      title="Swipe down or tap to show header"
    >
      <div class="reveal-handle"></div>
    </div>

    <!-- Main Header -->
    <header v-else ref="headerRef" class="deck-header dashboard-header">
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
          <GlassPillSceneSelector
            v-if="currentProfile && currentProfile.scenes.length > 0"
            :scenes="currentProfile.scenes"
            :current-scene-index="currentSceneIndex"
            :is-edit-mode="isEditMode"
            @scene-change="emit('setScene', $event)"
            @add-scene="emit('addScene')"
            @edit-scene="emit('editScene', $event)"
            class="enhanced-scene-nav"
          />
        </div>

        <div class="header-center">
          <PageNavigation
            v-if="currentScene && currentScene.pages.length > 1"
            :pages="currentScene.pages"
            :current-page="currentPageIndex"
            @previous="emit('previousPage')"
            @next="emit('nextPage')"
            @go-to="emit('setPage', $event)"
            class="enhanced-page-nav"
          />
        </div>

        <div class="header-right" @pointerdown="resetAutohide">
          <div class="header-actions-group">
            <button class="btn-icon-circle animate-tap" @click="emit('navigateProfiles')" title="Profiles" aria-label="Profiles">
              <FontAwesomeIcon :icon="['fas', 'users']" />
            </button>
            <button
              :class="['btn-icon-circle animate-tap', { 'edit-active': isEditMode }]"
              @click="emit('toggleEdit')"
              title="Toggle Edit Mode"
              aria-label="Toggle Edit Mode"
            >
              <FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" />
            </button>
            <button
              class="btn-icon-circle animate-tap"
              @click="toggleFullscreen"
              :title="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
              :aria-label="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
            >
              <FontAwesomeIcon :icon="['fas', isFullscreen ? 'compress' : 'expand']" />
            </button>
            <button class="btn-icon-circle animate-tap" @click="emit('navigateSettings')" title="Settings" aria-label="Settings">
              <FontAwesomeIcon :icon="['fas', 'cog']" />
            </button>
            <button
              class="btn-icon-circle animate-tap btn-refresh"
              title="Refresh VDock"
              aria-label="Refresh VDock"
              :disabled="isRefreshing"
              @click="handleRefreshVdock"
            >
              <FontAwesomeIcon :icon="['fas', 'rotate-right']" :spin="isRefreshing" />
            </button>
          </div>
          <div class="header-exit-group">
            <button
              class="btn-icon-circle animate-tap btn-exit"
              title="Exit VDock"
              aria-label="Exit VDock"
              @click="handleExitApp"
            >
              <FontAwesomeIcon :icon="['fas', 'power-off']" />
            </button>
          </div>
        </div>
      </div>
      <div class="autohide-progress" :style="{ width: progressWidth + '%' }"></div>
      <!-- Visible collapse affordance — mirrors the reveal handle so hiding the
           header (swipe up) isn't only discoverable via an invisible gesture -->
      <button
        class="header-collapse-handle"
        @click="collapseHeader"
        title="Swipe up or tap to hide header"
        aria-label="Hide header"
      >
        <div class="reveal-handle"></div>
      </button>
    </header>

    <!-- Confirmation modal for exiting the app -->
    <Teleport to="body">
      <div v-if="showExitConfirm" class="exit-confirm-overlay" @click.self="cancelExitApp">
        <div class="exit-confirm-dialog" role="alertdialog" aria-modal="true">
          <div class="exit-confirm-icon">
            <FontAwesomeIcon :icon="['fas', 'power-off']" />
          </div>
          <h3>Exit VDock?</h3>
          <p>This will close the VDock application window.</p>
          <div class="exit-confirm-actions">
            <button class="btn btn-secondary" @click="cancelExitApp">Cancel</button>
            <button class="btn btn-danger" @click="confirmExitApp">Exit</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import GlassPillSceneSelector from './GlassPillSceneSelector.vue'
import PageNavigation from './PageNavigation.vue'
import { useSettingsStore } from '@/stores/settings'
import { useElectron } from '@/composables/useElectron'
import { useSwipe } from '@/composables/useGestures'
import { refreshVdock } from '@/composables/useVdockRefresh'
import type { Profile, Scene } from '@/types'

interface Props {
  currentProfile: Profile | null
  currentScene: Scene | null
  currentSceneIndex: number
  currentPageIndex: number
  isEditMode: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  toggleEdit: []
  navigateSettings: []
  navigateProfiles: []
  setScene: [index: number]
  addScene: []
  editScene: [scene: Scene]
  setPage: [index: number]
  previousPage: []
  nextPage: []
}>()

const settingsStore = useSettingsStore()
const { quitApp, isElectron, toggleFullscreen: toggleElectronFullscreen, isFullscreen: getElectronFullscreen } = useElectron()
const triggerRef = ref<HTMLElement | null>(null)
const headerRef = ref<HTMLElement | null>(null)
const progressWidth = ref(100)
const isFullscreen = ref(typeof document !== 'undefined' && !!document.fullscreenElement)
const isRefreshing = ref(false)

// In the Electron shell, fullscreen is a native window property controlled
// via IPC and doesn't fire the DOM `fullscreenchange` event, so it can't be
// tracked that way. In a plain browser tab we fall back to the DOM
// Fullscreen API and its change event instead.
function handleFullscreenChange() {
  if (!isElectron()) {
    isFullscreen.value = !!document.fullscreenElement
  }
}

async function toggleFullscreen() {
  try {
    isFullscreen.value = await toggleElectronFullscreen()
  } catch (err) {
    console.error('Failed to toggle fullscreen:', err)
  }
}

const showExitConfirm = ref(false)

function handleExitApp() {
  // Pause the auto-hide countdown while the confirmation dialog is open so
  // the header can't disappear behind it.
  stopAutohide()
  showExitConfirm.value = true
}

function cancelExitApp() {
  showExitConfirm.value = false
  startAutohide()
}

async function confirmExitApp() {
  showExitConfirm.value = false
  try {
    const quitHandledNatively = await quitApp()
    if (!quitHandledNatively) {
      // Running in a plain browser tab: window.close() is ignored by
      // browsers for tabs not opened via script, so let the user know they
      // need to close it themselves instead of leaving them guessing.
      window.alert('VDock is running in a browser tab and cannot close itself. Please close this browser tab/window manually.')
    }
  } catch (error) {
    console.error('Failed to quit VDock:', error)
  }
}

async function handleRefreshVdock() {
  if (isRefreshing.value) {
    return
  }

  isRefreshing.value = true
  try {
    await refreshVdock()
  } finally {
    isRefreshing.value = false
  }
}
let autohideTimer: ReturnType<typeof setInterval> | null = null
let autohideRemainingMs = 5000
const AUTOHIDE_MS = 5000
const TICK_MS = 50

function revealHeader() {
  settingsStore.showHeader = true
}

function collapseHeader() {
  stopAutohide()
  settingsStore.showHeader = false
}

function startAutohide() {
  stopAutohide()
  autohideRemainingMs = AUTOHIDE_MS
  progressWidth.value = 100
  autohideTimer = setInterval(() => {
    autohideRemainingMs -= TICK_MS
    progressWidth.value = Math.max(0, (autohideRemainingMs / AUTOHIDE_MS) * 100)
    if (autohideRemainingMs <= 0) {
      stopAutohide()
      settingsStore.showHeader = false
    }
  }, TICK_MS)
}

function stopAutohide() {
  if (autohideTimer) {
    clearInterval(autohideTimer)
    autohideTimer = null
  }
}

function resetAutohide() {
  autohideRemainingMs = AUTOHIDE_MS
  progressWidth.value = 100
}

watch(() => settingsStore.showHeader, (visible) => {
  if (visible) {
    startAutohide()
  } else {
    stopAutohide()
  }
})

// Support swipe down gesture on the trigger area to reveal header
useSwipe(triggerRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'DOWN') {
      revealHeader()
    }
  }
})

// Support swipe up gesture on the header to dismiss
useSwipe(headerRef, {
  threshold: 40,
  onSwipeEnd: (direction) => {
    if (direction === 'UP') {
      stopAutohide()
      settingsStore.showHeader = false
    }
  }
})

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  getElectronFullscreen().then((value) => {
    isFullscreen.value = value
  })
})

onUnmounted(() => {
  stopAutohide()
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
.deck-header-wrapper {
  width: 100%;
  z-index: 100;
}

.header-hidden {
  height: 0;
  overflow: visible;
}

.header-reveal-trigger {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  /* Large, fully-transparent hit area so a swipe-down or tap from anywhere
     near the top edge reliably reveals the header, without needing to hit a
     thin sliver of the screen. Only the small handle pill is ever visible. */
  height: 84px;
  background: transparent;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  cursor: pointer;
  touch-action: none;
  z-index: 110;
}

.reveal-handle {
  width: 96px;
  height: 10px;
  margin-top: 6px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.header-reveal-trigger:hover .reveal-handle,
.header-reveal-trigger:active .reveal-handle {
  background-color: var(--color-primary, #007aff);
  transform: scaleX(1.08);
}

.header-collapse-handle {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: center;
  width: 120px;
  height: 18px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  z-index: 2;
}

.header-collapse-handle .reveal-handle {
  margin-top: 0;
}

.header-collapse-handle:hover .reveal-handle,
.header-collapse-handle:active .reveal-handle {
  background-color: var(--color-primary, #007aff);
  transform: scaleX(1.08);
}

.deck-header {
  position: relative;
  width: 100%;
  min-height: 90px;
  padding: 0.6rem 1rem;
  box-sizing: border-box;
  overflow: visible;
  touch-action: pan-x;
}

.header-background {
  position: absolute;
  inset: 0;
  background: rgba(8, 8, 28, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 0;
}

.header-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 68px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0;
  flex-shrink: 0;
}

.header-actions-group {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.header-exit-group {
  margin-left: 1.75rem;
  padding-left: 1.75rem;
  border-left: 1px solid rgba(255, 255, 255, 0.18);
}

.profile-avatar-container {
  position: relative;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
}

.profile-avatar,
.profile-avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}

.profile-avatar {
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.profile-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.13);
  border: 2px solid rgba(255, 255, 255, 0.28);
  color: #fff;
  font-size: 1.5rem;
}

.avatar-status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #2ecc71;
  border: 2px solid rgba(0, 0, 0, 0.5);
}

.animate-tap {
  touch-action: manipulation;
  min-width: 44px;
  min-height: 44px;
}

/* Large circular icon buttons */
.btn-icon-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease;
  touch-action: manipulation;
  flex-shrink: 0;
}

.btn-icon-circle:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
}

.btn-icon-circle:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.22);
}

.btn-icon-circle:disabled {
  opacity: 0.65;
  cursor: wait;
}

.btn-icon-circle.btn-refresh:hover:not(:disabled) {
  background: rgba(52, 152, 219, 0.22);
  border-color: rgba(52, 152, 219, 0.55);
}

.btn-icon-circle.edit-active {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.35), rgba(52, 152, 219, 0.7));
  border-color: rgba(52, 152, 219, 0.65);
  box-shadow: 0 0 18px rgba(52, 152, 219, 0.4);
}

.btn-icon-circle.btn-exit {
  color: #fff;
  background: rgba(220, 53, 69, 0.38);
  border-color: rgba(220, 53, 69, 0.82);
  box-shadow: 0 0 14px rgba(220, 53, 69, 0.22);
}

.btn-icon-circle.btn-exit:hover:not(:disabled) {
  background: rgba(220, 53, 69, 0.58);
  border-color: rgba(255, 120, 130, 0.95);
}

.btn-icon-circle.btn-exit:active:not(:disabled) {
  background: rgba(185, 40, 55, 0.72);
}

/* Auto-hide countdown bar */
.autohide-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--color-primary, #007aff), rgba(0, 122, 255, 0.25));
  border-radius: 0 2px 2px 0;
  transition: width 0.1s linear;
  pointer-events: none;
}

/* Enhanced scene nav sizing */
.enhanced-scene-nav {
  --pill-height: 56px;
}

.profile-title-inline {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1 1 auto;
}

/* Exit confirmation modal */
.exit-confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.exit-confirm-dialog {
  width: min(360px, 90vw);
  background: rgba(20, 20, 32, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 1.75rem 1.5rem;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.exit-confirm-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 0.75rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #fff;
  background: rgba(220, 53, 69, 0.35);
  border: 2px solid rgba(220, 53, 69, 0.75);
}

.exit-confirm-dialog h3 {
  margin: 0 0 0.4rem;
  color: #fff;
  font-size: 1.15rem;
}

.exit-confirm-dialog p {
  margin: 0 0 1.4rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.exit-confirm-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.exit-confirm-actions .btn {
  flex: 1;
  padding: 0.65rem 1rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.exit-confirm-actions .btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #fff;
}

.exit-confirm-actions .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.exit-confirm-actions .btn-danger {
  background: rgba(220, 53, 69, 0.85);
  color: #fff;
}

.exit-confirm-actions .btn-danger:hover {
  background: rgba(220, 53, 69, 1);
}
</style>
