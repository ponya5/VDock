<template>
  <div id="app" :class="themeClass">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import socketClient from '@/api/socket'

const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const themeClass = computed(() => `theme-${settingsStore.currentTheme}`)

onMounted(() => {
  // Check for saved auth token
  authStore.initAuth()
  
  // Initialize socket connection if authenticated
  if (authStore.isAuthenticated && authStore.token) {
    socketClient.connect(authStore.token)
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

