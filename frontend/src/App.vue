<template>
  <div
    id="app"
    class="theme-dark"
    :data-ui-font="settingsStore.dashboardFont"
    :class="{
      'bg-animated': !isStandaloneSettings && settingsStore.background !== 'default',
      'settings-standalone-mode': isStandaloneSettings,
      'settings-route': route.path === '/settings',
    }"
  >
    <!-- Suspended while the screensaver covers the deck — an animated
         background under the opaque saver only burns frame budget. -->
    <BackgroundRenderer v-if="!isStandaloneSettings && !screensaverCovered" />
    <router-view />
    <!-- Toasts render in standalone settings too — the test buttons and
         layout editor live there and must surface results. -->
    <NotificationCenter v-if="showNotifications" />
    <ConfirmDialog />
    <!-- Tour lives above the router so it survives dashboard ↔ settings navigation -->
    <TutorialTour />
    <QuickDeckOverlay v-if="!isStandaloneSettings" />
    <AgentAlertOverlay />
    <AgentMissionControl v-if="!isStandaloneSettings" />
    <!-- The lock screen sits above everything, including standalone settings -->
    <AuthGate />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useDashboardStore } from '@/stores/dashboard'
import { useActionCatalogStore } from '@/stores/actionCatalog'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import NotificationCenter from '@/components/NotificationCenter.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import BackgroundRenderer from '@/components/backgrounds/BackgroundRenderer.vue'
import TutorialTour from '@/components/TutorialTour.vue'
import QuickDeckOverlay from '@/components/QuickDeckOverlay.vue'
import AgentAlertOverlay from '@/components/AgentAlertOverlay.vue'
import AgentMissionControl from '@/components/AgentMissionControl.vue'
import AuthGate from '@/components/AuthGate.vue'
import { probeAuth } from '@/services/auth'
import { useAgentAlerts } from '@/services/agentAlerts'
import { useToggleSync } from '@/services/toggleSync'
import { initTriggerEvents } from '@/services/triggerEvents'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import { useAppIntegrations, useAutoSceneSwitching } from '@/composables/useAppIntegrations'
import { isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import { screensaverCovered } from '@/services/screensaverState'

const route = useRoute()
const router = useRouter()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const dashboardStore = useDashboardStore()
const actionCatalogStore = useActionCatalogStore()

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

  // Auth before anything else that talks to the server (DL-126): when the
  // deck is locked the probe raises the gate and the calls below fail
  // quietly — a successful unlock reloads the page and starts clean.
  await probeAuth()

  await settingsStore.ensureSettingsLoaded()
  await settingsStore.loadServerConfig()

  // Load the action catalog before any button can be pressed: it decides which
  // action types are live widgets that must not dispatch.
  await actionCatalogStore.load()

  socketClient.connect()
  useAgentAlerts().init()
  initTriggerEvents()
  useToggleSync().init()
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
  // Integrations + the on/off flag live in the shared user settings, so this
  // reacts to edits made in Settings or on another device without a reload.
  const integrationsRef = useAppIntegrations()
  const autoSwitchRef = useAutoSceneSwitching()
  autoSceneSwitcher.onSceneSwitch((sceneId: string) => {
    const profile = dashboardStore.currentProfile
    if (!profile) return
    const idx = profile.scenes.findIndex(s => s.id === sceneId)
    if (idx >= 0) dashboardStore.setScene(idx)
  })
  const syncAutoSwitch = () => {
    autoSceneSwitcher.updateIntegrations(integrationsRef.value)
    if (autoSwitchRef.value) void autoSceneSwitcher.enable()
    else void autoSceneSwitcher.disable()
  }
  autoSceneSwitcher.initialize(integrationsRef.value)
  syncAutoSwitch()
  watch([integrationsRef, autoSwitchRef], syncAutoSwitch, { deep: true })
})

function handleBeforeUnload() {
  void settingsStore.flushSettingsToServer()
}

// In-window summon key — backtick toggles the quick-deck overlay. (Browsers
// can't own OS-global hotkeys; the Electron build adds Ctrl+Shift+D.)
function handleSummonKey(e: KeyboardEvent) {
  if (e.key !== '`' || isStandaloneSettings.value) return
  const target = e.target as HTMLElement | null
  if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
  e.preventDefault()
  window.dispatchEvent(new CustomEvent('vdock-quick-deck'))
}

onMounted(() => {
  window.addEventListener('keydown', handleSummonKey)
  // Tray "Settings" — navigate in place instead of reloading the SPA.
  ;(window as any).electron?.onNavigate?.((path: string) => {
    if (typeof path === 'string' && path.startsWith('/')) router.push(path)
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleSummonKey)
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
  height: 100dvh; /* iOS Safari dynamic toolbar — see DashboardView */
  overflow: hidden;
  /* clip = same visual crop but NOT a scroll container, so focusing an
     off-screen element (e.g. a toggled switch's hidden input) can't scroll the
     whole app out from under the viewport (DL-140 F/U2). */
  overflow: clip;
  background: var(--color-background);
  background-image: var(--app-backdrop);
  color: var(--color-text);
}

#app.bg-animated {
  background: transparent;
}

#app.settings-standalone-mode {
  background: var(--color-background, #0f1419);
}

/* DL-140: at ≤880px SettingsView switches to a body-scroll page (nav becomes
   a top strip, the dock pins bottom:0) — that only works if #app stops
   clipping at 100dvh, otherwise the whole page is unreachable below the fold
   and hidden-overflow scrolls leave stale paint. Scoped to the settings
   route so the fixed-viewport deck keeps its clip at the same widths. */
/* F/U: same release when the viewport is wide but short — the touch
   keyboard shrinks the layout viewport (interactive-widget=resizes-content)
   so 100dvh collapses even at desktop widths. */
@media (max-width: 880px), (max-height: 480px) {
  /* Two nested #app divs exist: the index.html mount point and this
     component's root — both carry the clip, so both must release it. */
  #app.settings-route,
  #app:has(> .settings-route) {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    overflow: visible;
  }
}
</style>

