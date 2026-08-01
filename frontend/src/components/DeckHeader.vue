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
          <SceneNavigation
            v-if="currentProfile && currentProfile.scenes.length > 0"
            :scenes="currentProfile.scenes"
            :current-scene-index="currentSceneIndex"
            :is-edit-mode="isEditMode"
            @set-scene="emit('setScene', $event)"
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
            class="btn-hide-header"
            @click="settingsStore.showHeader = false"
            title="Hide header"
            aria-label="Hide header"
          >
            <div>
              <span><FontAwesomeIcon :icon="['fas', 'eye-slash']" /> Hide</span>
            </div>
          </button>
          <button class="btn-12 animate-tap" @click="emit('showHelp')" title="Help & Guide">
            <span><FontAwesomeIcon :icon="['fas', 'question-circle']" /> Help</span>
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
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import SceneNavigation from './SceneNavigation.vue'
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
  showHelp: []
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
</style>
