<template>
  <div class="deck-header-wrapper" :class="{ 'header-hidden': !settingsStore.showHeader }">
    <!-- Reveal trigger area (visible when header is hidden) -->
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
    <header v-else class="deck-header dashboard-header">
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

        <div class="header-right">
          <button
            class="btn-fullscreen btn-12 animate-tap"
            @click="handleToggleFullscreen"
            :title="isFullscreenActive ? 'Exit full screen' : 'Enter full screen'"
            :aria-label="isFullscreenActive ? 'Exit full screen' : 'Enter full screen'"
          >
            <span>
              <FontAwesomeIcon :icon="['fas', isFullscreenActive ? 'compress' : 'expand']" />
              {{ isFullscreenActive ? 'Exit' : 'Full Screen' }}
            </span>
          </button>
          <div class="header-right-separator"></div>
          <button
            class="btn-hide-header btn-12 animate-tap"
            @click="settingsStore.showHeader = false"
            title="Hide header"
            aria-label="Hide header"
          >
            <div>
              <span><FontAwesomeIcon :icon="['fas', 'eye-slash']" /> Hide</span>
            </div>
          </button>
          <div class="header-right-separator"></div>
          <button class="btn-12 animate-tap" @click="emit('navigateProfiles')" title="Profiles">
            <span><FontAwesomeIcon :icon="['fas', 'users']" /> Profiles</span>
          </button>
          <button
            :class="['btn-12 animate-tap', { 'edit-active': isEditMode }]"
            @click="emit('toggleEdit')"
            title="Toggle Edit Mode"
          >
            <span><FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" /> {{ isEditMode ? 'View' : 'Edit' }}</span>
          </button>
          <button class="btn-12 animate-tap" @click="emit('navigateSettings')" title="Settings">
            <span><FontAwesomeIcon :icon="['fas', 'cog']" /> Settings</span>
          </button>
        </div>
      </div>
    </header>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import GlassPillSceneSelector from './GlassPillSceneSelector.vue'
import PageNavigation from './PageNavigation.vue'
import { useSettingsStore } from '@/stores/settings'
import { useSwipe } from '@/composables/useGestures'
import { useElectron } from '@/composables/useElectron'
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
const { toggleFullscreen, isFullscreen } = useElectron()
const triggerRef = ref<HTMLElement | null>(null)
const isFullscreenActive = ref(false)

async function refreshFullscreenState() {
  isFullscreenActive.value = await isFullscreen()
}

async function handleToggleFullscreen() {
  isFullscreenActive.value = await toggleFullscreen()
}

function handleFullscreenChange() {
  refreshFullscreenState()
}

onMounted(() => {
  refreshFullscreenState()
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})

function revealHeader() {
  settingsStore.showHeader = true
}

// Support swipe down gesture on the trigger area to reveal header
useSwipe(triggerRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'DOWN') {
      revealHeader()
    }
  }
})
</script>

<style scoped>
.deck-header-wrapper {
  width: 100%;
  z-index: 100;
  transition: transform 0.3s var(--ease-io);
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
  height: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  cursor: pointer;
  z-index: 110;
}

.reveal-handle {
  width: 60px;
  height: 6px;
  background-color: rgba(255, 255, 255, 0.25);
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: background-color 0.2s var(--ease-out);
}

.header-reveal-trigger:hover .reveal-handle {
  background-color: var(--color-primary, #007aff);
}

.animate-tap {
  min-height: 44px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Thin header shell (spec 4.7) */
.deck-header {
  position: relative;
  width: 100%;
  min-height: 56px;
  padding: 0.4rem 1rem;
  box-sizing: border-box;
  overflow: hidden;
}

/* Replace the dated glossy .btn-12 look with the app's dark-glass language
   (matches .pill-container in GlassPillSceneSelector.vue) — scoped to this
   header only, .btn-12 isn't used anywhere else. */
.header-right .btn-12 {
  padding: 0.5rem 0.9rem;
  min-height: 36px;
  background: var(--glass-bg, rgba(0, 0, 0, 0.25));
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.12));
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0;
  text-shadow: none;
  box-shadow: none;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.header-right .btn-12:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}

.header-right .btn-12:active:not(:disabled),
.header-right .btn-12:focus:not(:disabled) {
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.4);
}

.header-right .btn-12.edit-active {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.35), rgba(52, 152, 219, 0.7));
  border-color: rgba(52, 152, 219, 0.6);
  color: #fff;
  box-shadow: 0 0 18px rgba(52, 152, 219, 0.45);
}

.header-background {
  position: absolute;
  inset: 0;
  background: var(--glass-bg, rgba(0, 0, 0, 0.25));
  backdrop-filter: blur(20px);
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
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1 1 auto;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.profile-avatar-container {
  position: relative;
  width: 44px;
  height: 44px;
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
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  font-size: 1.1rem;
}

.avatar-status-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #2ecc71;
  border: 2px solid rgba(0, 0, 0, 0.4);
}

.profile-title-inline {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.header-right-separator {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  margin: 0 0.25rem;
}

@media (max-width: 640px) {
  .profile-title-inline {
    display: none;
  }
  .header-center {
    display: none;
  }
}

@media (max-width: 1100px), (max-height: 650px) {
  .deck-header {
    min-height: calc(56px * var(--touch-multiplier, 1));
    padding: calc(0.4rem * var(--touch-multiplier, 1)) calc(0.75rem * var(--touch-multiplier, 1));
  }

  .header-right .btn-12 {
    min-height: max(44px, calc(36px * var(--touch-multiplier, 1)));
    padding: calc(0.55rem * var(--touch-multiplier, 1)) calc(0.85rem * var(--touch-multiplier, 1));
    font-size: calc(0.85rem * var(--touch-multiplier, 1));
  }

  .header-right-separator {
    height: calc(24px * var(--touch-multiplier, 1));
  }

  .profile-avatar-container {
    width: max(44px, calc(36px * var(--touch-multiplier, 1)));
    height: max(44px, calc(36px * var(--touch-multiplier, 1)));
  }

  .profile-title-inline {
    font-size: calc(1rem * var(--touch-multiplier, 1));
    max-width: 140px;
  }
}
</style>
