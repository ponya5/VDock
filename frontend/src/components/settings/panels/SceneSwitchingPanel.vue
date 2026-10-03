<template>
    <section class="panel" id="auto-switch">
      <div class="panel-head"><h2>Auto scene switching</h2><span class="hint">Scenes follow the app in focus.</span></div>
      <div class="panel-body">
        <div class="row">
          <div class="row-text">
            <span class="label">Enable auto switching</span>
            <p>Switch scenes when monitored apps become active.</p>
          </div>
          <div class="row-control">
            <label class="switch"><span class="sr-only">Enable auto switching</span><input type="checkbox" :checked="autoSwitchingEnabled" @change="toggleAutoSwitching" /><span class="track"></span></label>
          </div>
        </div>
        <div v-if="autoSwitchingEnabled" class="row row-status-row">
          <div class="auto-switch-status">
            <FontAwesomeIcon :icon="['fas', 'circle-check']" class="status-icon success" />
            <span>Monitoring active application</span>
          </div>
        </div>
      </div>
    </section>

    <section class="panel" id="running-apps">
      <div class="panel-head">
        <h2>Running applications</h2>
        <span class="hint">Periodically detected apps — powers the live scene dots and this list.</span>
        <span class="spacer"></span>
        <button v-if="settingsStore.appScanningEnabled" type="button" class="btn sm" @click="refreshRunningApps">
          <FontAwesomeIcon :icon="['fas', 'sync']" :spin="loadingApps" /> Refresh
        </button>
      </div>
      <div class="panel-body">
        <div class="row">
          <div class="row-text">
            <span class="label">Enable app scanning</span>
            <p>Detect running apps so scenes can follow them.</p>
          </div>
          <div class="row-control">
            <label class="switch"><span class="sr-only">Enable app scanning</span><input type="checkbox" :checked="settingsStore.appScanningEnabled" @change="toggleAppScanning" /><span class="track"></span></label>
          </div>
        </div>
      </div>
      <div class="panel-body flush app-list-body">
        <div v-if="!settingsStore.appScanningEnabled" class="empty-state">
          <FontAwesomeIcon :icon="['fas', 'desktop']" /><p>App scanning is disabled</p>
        </div>
        <template v-else>
          <div v-if="runningApps.length > 0" class="app-toolbar">
            <div class="app-search">
              <FontAwesomeIcon :icon="['fas', 'search']" class="app-search-icon" />
              <input
                v-model="appSearch"
                type="text"
                class="app-search-input"
                placeholder="Filter apps — try 'terminal', 'vscode', 'git'"
              />
              <button v-if="appSearch" class="app-search-clear" title="Clear filter" @click="appSearch = ''">
                <FontAwesomeIcon :icon="['fas', 'times']" />
              </button>
            </div>
            <span v-if="appSearch" class="app-count">{{ filteredApps.length }} of {{ runningApps.length }}</span>
          </div>
          <div v-if="loadingApps" class="loading-state">
            <FontAwesomeIcon :icon="['fas', 'spinner']" spin /><span>Loading applications...</span>
          </div>
          <div v-else-if="runningApps.length === 0" class="empty-state">
            <FontAwesomeIcon :icon="['fas', 'desktop']" /><p>No applications detected</p>
            <button class="btn sm" @click="refreshRunningApps">Refresh</button>
          </div>
          <div v-else class="app-integration-list">
            <div class="list-header">
              <span>Application</span><span>Status</span><span>Scene</span><span>Actions</span>
            </div>
            <div v-if="filteredApps.length === 0" class="empty-state app-filter-empty">
              <FontAwesomeIcon :icon="['fas', 'search']" /><p>No apps match "{{ appSearch }}"</p>
            </div>
            <div v-for="app in filteredApps" :key="app.exe" class="app-item" :class="{ 'app-item--dev': appTier(app) < 2 }">
              <div class="app-info">
                <FontAwesomeIcon :icon="['fas', 'window-maximize']" class="app-icon" />
                <div class="app-details">
                  <span class="app-name">{{ app.name }}</span>
                  <span class="app-exe">{{ app.exe }}</span>
                </div>
                <span v-if="appBadge(app)" class="app-badge" :class="{ 'app-badge--profile': appTier(app) === 0 }">{{ appBadge(app) }}</span>
              </div>
              <div class="app-status">
                <label class="switch"><span class="sr-only">Integrate {{ app.name }}</span><input type="checkbox" :checked="isAppIntegrationEnabled(app.exe)" @change="toggleAppIntegration(app)" /><span class="track"></span></label>
                <span class="status-text">{{ isAppIntegrationEnabled(app.exe) ? 'On' : 'Off' }}</span>
              </div>
              <div class="app-scene">
                <select v-if="isAppIntegrationEnabled(app.exe)" :value="getAppScene(app.exe)" @change="updateAppScene(app.exe, ($event.target as HTMLSelectElement).value)" class="select select-sm">
                  <option value="">Create New Scene</option>
                  <option v-for="scene in availableScenes" :key="scene.id" :value="scene.id">{{ scene.name }}</option>
                </select>
                <span v-else class="scene-placeholder">—</span>
              </div>
              <div class="app-actions">
                <button v-if="isAppIntegrationEnabled(app.exe)" class="btn-icon" @click="$emit('manage-shortcuts', app)" title="Manage Shortcuts"><FontAwesomeIcon :icon="['fas', 'cog']" /></button>
                <button v-if="isAppIntegrationEnabled(app.exe) && !getAppScene(app.exe)" class="btn-icon btn-icon-primary" @click="createSceneForApp(app)" title="Create Scene"><FontAwesomeIcon :icon="['fas', 'plus']" /></button>
              </div>
            </div>
          </div>
          <div v-if="appIntegrations.length > 0" class="integration-summary">
            <FontAwesomeIcon :icon="['fas', 'circle-info']" />
            <span>{{ appIntegrations.length }} app{{ appIntegrations.length > 1 ? 's' : '' }} integrated</span>
          </div>
        </template>
      </div>
    </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import apiClient from '@/api/client'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import { fetchAppProfiles, hasAppShortcuts, topAppShortcuts, type AppProfileDto } from '@/api/appProfiles'
import type { RunningApp, Scene, Button } from '@/types'
import { appIdForExe } from '@/data/appBackgrounds'
import { useAppIntegrations, setAppIntegrations, setAutoSceneSwitching } from '@/composables/useAppIntegrations'
import { getAppScene, createButtonFromShortcut } from '@/composables/useAppShortcutScenes'

defineEmits<{ (e: 'manage-shortcuts', app: RunningApp): void }>()

const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()

const runningApps = ref<RunningApp[]>([])
const loadingApps = ref(false)
const appIntegrations = useAppIntegrations()
const autoSwitchingEnabled = ref(localStorage.getItem('autoSceneSwitching') === 'true')
const appSearch = ref('')
const appProfiles = ref<AppProfileDto[]>([])
const appProfilesLoaded = ref(false)

// VDock is a development companion: dev tools sort above everything else.
// Tier 0 is stronger still — an exe with a backend app profile means VDock
// actually has keystroke actions for it.
const DEV_APP_EXES = new Set([
  'code.exe', 'code - insiders.exe', 'cursor.exe', 'devenv.exe', 'zed.exe',
  'rider64.exe', 'idea64.exe', 'webstorm64.exe', 'pycharm64.exe',
  'clion64.exe', 'goland64.exe', 'phpstorm64.exe', 'rubymine64.exe',
  'datagrip64.exe', 'rustrover64.exe', 'fleet64.exe', 'studio64.exe',
  'sublime_text.exe', 'notepad++.exe', 'neovide.exe',
  'windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe',
  'bash.exe', 'wsl.exe', 'wezterm-gui.exe', 'alacritty.exe', 'tabby.exe',
  'termius.exe', 'putty.exe',
  'gitkraken.exe', 'githubdesktop.exe', 'sourcetree.exe', 'fork.exe',
  'postman.exe', 'insomnia.exe', 'bruno.exe',
  'docker desktop.exe', 'com.docker.backend.exe', 'rancher desktop.exe',
  'podman.exe', 'dbeaver.exe', 'mongodbcompass.exe',
  'node.exe', 'python.exe', 'pythonw.exe', 'devtunnel.exe',
])

// Friendly queries -> exes, so "terminal" finds Windows Terminal, etc.
const APP_ALIASES: Record<string, string[]> = {
  vscode: ['code.exe', 'code - insiders.exe'],
  'vs code': ['code.exe', 'code - insiders.exe'],
  'visual studio code': ['code.exe'],
  'visual studio': ['devenv.exe'],
  terminal: ['windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe', 'wezterm-gui.exe', 'alacritty.exe', 'tabby.exe'],
  claude: ['windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe'],
  browser: ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe'],
  git: ['gitkraken.exe', 'githubdesktop.exe', 'sourcetree.exe', 'fork.exe'],
  github: ['githubdesktop.exe'],
  docker: ['docker desktop.exe', 'com.docker.backend.exe', 'rancher desktop.exe'],
  jetbrains: ['idea64.exe', 'webstorm64.exe', 'pycharm64.exe', 'rider64.exe', 'clion64.exe', 'goland64.exe', 'phpstorm64.exe'],
  editor: ['code.exe', 'cursor.exe', 'sublime_text.exe', 'notepad++.exe', 'devenv.exe', 'zed.exe'],
}

const appProfileByExe = computed(() => {
  const map = new Map<string, AppProfileDto>()
  for (const profile of appProfiles.value) {
    for (const exe of profile.exes) {
      const key = exe.toLowerCase()
      if (!map.has(key)) map.set(key, profile)
    }
  }
  return map
})

function appTier(app: RunningApp): number {
  const exe = app.exe.toLowerCase()
  if (appProfileByExe.value.has(exe)) return 0
  if (DEV_APP_EXES.has(exe)) return 1
  return 2
}

function appBadge(app: RunningApp): string | null {
  const exe = app.exe.toLowerCase()
  return appProfileByExe.value.get(exe)?.label ?? (DEV_APP_EXES.has(exe) ? 'Dev' : null)
}

const filteredApps = computed(() => {
  const query = appSearch.value.trim().toLowerCase()
  let list = runningApps.value
  if (query) {
    const aliases = APP_ALIASES[query] ?? []
    list = list.filter((app) => {
      const name = app.name.toLowerCase()
      const exe = app.exe.toLowerCase()
      return name.includes(query) || exe.includes(query) || aliases.includes(exe)
    })
  }
  return [...list].sort(
    (a, b) => appTier(a) - appTier(b) || a.name.localeCompare(b.name)
  )
})

const availableScenes = computed(() => {
  const profile = dashboardStore.currentProfile
  if (!profile) return []
  return (profile.scenes || []).map((scene: Scene) => ({ id: scene.id, name: scene.name }))
})

function toggleAppScanning() {
  settingsStore.appScanningEnabled = !settingsStore.appScanningEnabled
  if (settingsStore.appScanningEnabled) void refreshRunningApps()
  else runningApps.value = []
}

async function refreshRunningApps() {
  if (!settingsStore.appScanningEnabled) {
    runningApps.value = []
    return
  }
  loadingApps.value = true
  if (!appProfilesLoaded.value) {
    appProfilesLoaded.value = true
    fetchAppProfiles()
      .then((profiles) => { appProfiles.value = profiles })
      .catch(() => { appProfilesLoaded.value = false })
  }
  try {
    const response = await apiClient.get('/metrics/running-apps')
    runningApps.value = response.data.success ? (response.data.data ?? []) : []
    if (!response.data.success) {
      console.error('Failed to load running applications:', response.data.error)
    }
  } catch (error) {
    console.error('Failed to load running applications:', error)
    runningApps.value = []
  } finally {
    loadingApps.value = false
  }
}

function isAppIntegrationEnabled(appExe: string): boolean { return appIntegrations.value.some(i => i.appExe === appExe && i.enabled) }

function toggleAppIntegration(app: RunningApp) {
  const idx = appIntegrations.value.findIndex(i => i.appExe === app.exe)
  if (idx >= 0) { appIntegrations.value[idx].enabled = !appIntegrations.value[idx].enabled }
  else { appIntegrations.value.push({ appExe: app.exe, appName: app.name, sceneId: '', enabled: true, autoCreateScene: false }) }
  saveAppIntegrations()
}

function updateAppScene(appExe: string, sceneId: string) {
  const integration = appIntegrations.value.find(i => i.appExe === appExe)
  if (integration) { integration.sceneId = sceneId; saveAppIntegrations() }
}

async function createSceneForApp(app: RunningApp) {
  const profile = dashboardStore.currentProfile
  if (!profile) { notificationsStore.error('No profile', 'No profile loaded.'); return }
  const sceneName = app.name.replace('.exe', '')
  try {
    const profiles = await fetchAppProfiles()
    const topShortcuts = hasAppShortcuts(profiles, app.exe) ? topAppShortcuts(profiles, app.exe, 8) : []
    const buttons: Button[] = topShortcuts.map((shortcut, index) => createButtonFromShortcut(shortcut, index))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: sceneName, icon: 'window-maximize', color: '#3498db',
      pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
      triggeredByApp: app.exe, appId: appIdForExe(app.exe), autoCreated: true
    }
    dashboardStore.addScene(newScene)
    updateAppScene(app.exe, newScene.id)
    notificationsStore.success('Scene created', `"${sceneName}" created with ${buttons.length} shortcut buttons`)
  } catch { notificationsStore.error('Create failed', 'Failed to create scene') }
}

function saveAppIntegrations() {
  setAppIntegrations(appIntegrations.value)
  autoSceneSwitcher.updateIntegrations(appIntegrations.value)
}

// Actual scene-switching callback is owned by App.vue for the app's whole
// lifetime; this only flips the enabled state the singleton acts on.
async function toggleAutoSwitching() {
  const newValue = !autoSwitchingEnabled.value
  try {
    if (newValue) {
      autoSceneSwitcher.initialize(appIntegrations.value)
      const success = await autoSceneSwitcher.enable()
      if (success) { autoSwitchingEnabled.value = true; setAutoSceneSwitching(true) }
      else notificationsStore.error('Auto-switching', 'Failed to enable auto scene switching')
    } else {
      const success = await autoSceneSwitcher.disable()
      if (success) { autoSwitchingEnabled.value = false; setAutoSceneSwitching(false) }
      else notificationsStore.error('Auto-switching', 'Failed to disable auto scene switching')
    }
  } catch { notificationsStore.error('Auto-switching', 'Error toggling auto scene switching') }
}

onMounted(refreshRunningApps)
</script>
