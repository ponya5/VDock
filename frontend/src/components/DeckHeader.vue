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
          <button class="btn-icon-circle animate-tap" @click="emit('navigateSettings')" title="Settings" aria-label="Settings">
            <FontAwesomeIcon :icon="['fas', 'cog']" />
          </button>
        </div>
      </div>
      <div class="autohide-progress" :style="{ width: progressWidth + '%' }"></div>
    </header>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import GlassPillSceneSelector from './GlassPillSceneSelector.vue'
import PageNavigation from './PageNavigation.vue'
import { useSettingsStore } from '@/stores/settings'
import { useSwipe } from '@/composables/useGestures'
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
const triggerRef = ref<HTMLElement | null>(null)
const progressWidth = ref(100)

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
  transition: background-color 0.2s ease;
}

.header-reveal-trigger:hover .reveal-handle,
.header-reveal-trigger:active .reveal-handle {
  background-color: var(--color-primary, #007aff);
}

.deck-header {
  position: relative;
  width: 100%;
  min-height: 90px;
  padding: 0.6rem 1rem;
  box-sizing: border-box;
  overflow: visible;
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
  gap: 0.6rem;
  flex-shrink: 0;
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

.btn-icon-circle.edit-active {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.35), rgba(52, 152, 219, 0.7));
  border-color: rgba(52, 152, 219, 0.65);
  box-shadow: 0 0 18px rgba(52, 152, 219, 0.4);
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
</style>
