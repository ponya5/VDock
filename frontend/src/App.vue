<template>
  <div id="app" class="theme-dark">
    <router-view />
    <NotificationCenter v-if="showNotifications" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import NotificationCenter from '@/components/NotificationCenter.vue'

const route = useRoute()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

// Theme is fixed to dark mode

// Don't show notifications on login page
const showNotifications = computed(() => route.path !== '/login')

onMounted(() => {
  // Initialize API client with notifications store
  apiClient.setNotificationsStore(notificationsStore)
  
  // Check for saved auth token
  authStore.initAuth()
  
  // Initialize socket connection if authenticated
  if (authStore.isAuthenticated && authStore.token) {
    socketClient.connect(authStore.token)
  }
  
  // Show welcome notification for first time users
  const hasSeenWelcome = localStorage.getItem('vdock_welcome_shown')
  if (!hasSeenWelcome && route.path === '/') {
    setTimeout(() => {
      notificationsStore.info(
        'Welcome to VDock!',
        'Your virtual stream deck is ready. Click "Help" in the dashboard for a quick start guide.',
        { duration: 10000 }
      )
      localStorage.setItem('vdock_welcome_shown', 'true')
    }, 2000)
  }
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
}

#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-background);
  color: var(--color-text);
}
</style>

