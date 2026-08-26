<template>
  <div
    id="app"
    class="theme-dark"
    :class="{
      'bg-animated': !isStandaloneSettings && settingsStore.backgroundPreference !== 'none',
      'settings-standalone-mode': isStandaloneSettings,
    }"
  >
    <BackgroundRenderer v-if="!isStandaloneSettings" />
    <router-view />
    <NotificationCenter v-if="showNotifications && !isStandaloneSettings" />
    <UserGuideModal v-if="settingsStore.showHelpGuide" @close="settingsStore.showHelpGuide = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useDashboardStore } from '@/stores/dashboard'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import NotificationCenter from '@/components/NotificationCenter.vue'
import BackgroundRenderer from '@/components/backgrounds/BackgroundRenderer.vue'
import UserGuideModal from '@/components/UserGuideModal.vue'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import { isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import type { AppIntegration } from '@/types'

const route = useRoute()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const dashboardStore = useDashboardStore()

const isStandaloneSettings = computed(() => isStandaloneSettingsRoute(route))

watch(isStandaloneSettings, (standalone) => {
  document.title = standalone ? 'VDock Settings' : 'VDock - Virtual Stream Deck'
}, { immediate: true })

// Theme is fixed to dark mode

const showNotifications = ref(true)
let stopLiveSettingsSync: (() => void) | undefined

onMounted(async () => {
  window.addEventListener('beforeunload', handleBeforeUnload)

  apiClient.setNotificationsStore(notificationsStore)

  await settingsStore.loadSettingsFromServer()
  await settingsStore.loadServerConfig()

  socketClient.connect()
  stopLiveSettingsSync = settingsStore.initLiveSync()

  // Show welcome notification for first time users
  const hasSeenWelcome = localStorage.getItem('vdock_welcome_shown')
  if (!hasSeenWelcome && route.path === '/' && !isStandaloneSettings.value) {
    setTimeout(() => {
      notificationsStore.info(
        'Welcome to VDock!',
        'Your virtual stream deck is ready. Find "Help & Guide" in Settings for a quick start guide.',
        { duration: 10000 }
      )
      localStorage.setItem('vdock_welcome_shown', 'true')
    }, 2000)
  }

  // Single, app-lifetime owner of auto scene switching. Registering this
  // per-route (Dashboard/Settings) instead caused a leaked listener on every
  // Dashboard remount and a dead listener whenever Settings unmounted.
  const storedIntegrations = localStorage.getItem('appIntegrations')
  const storedAutoSwitch = localStorage.getItem('autoSceneSwitching')
  if (storedAutoSwitch === 'true' && storedIntegrations) {
    try {
      const integrations: AppIntegration[] = JSON.parse(storedIntegrations)
      autoSceneSwitcher.initialize(integrations)
      autoSceneSwitcher.onSceneSwitch((sceneId: string) => {
        const profile = dashboardStore.currentProfile
        if (!profile) return
        const idx = profile.scenes.findIndex(s => s.id === sceneId)
        if (idx >= 0) dashboardStore.setScene(idx)
      })
      autoSceneSwitcher.enable()
    } catch {
      // ignore malformed localStorage state
    }
  }
})

function handleBeforeUnload() {
  void settingsStore.flushSettingsToServer()
}

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  stopLiveSettingsSync?.()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0a0a0a;
}

#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-background);
  color: var(--color-text);
}

#app.bg-animated {
  background: transparent;
}

#app.settings-standalone-mode {
  background: var(--color-background, #0f1419);
}
</style>

