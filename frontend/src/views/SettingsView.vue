<template>
  <div class="settings-app">
    <aside class="nav">
      <div class="nav-brand">
        <span class="nav-mark"><img :src="'/assets/branding/vdock-logo.jpg'" alt="" class="nav-mark-img" /></span>
        <span class="nav-name">VDock</span>
      </div>
      <div class="nav-search">
        <FontAwesomeIcon :icon="['fas', 'magnifying-glass']" class="nav-search-icon" />
        <label class="sr-only" for="setting-search">Find a setting</label>
        <input
          id="setting-search"
          v-model="settingsSearch"
          type="search"
          placeholder="Find a setting…"
          autocomplete="off"
          @keydown.esc="settingsSearch = ''"
        />
        <div v-if="settingsSearch" class="nav-results">
          <button
            v-for="match in searchMatches"
            :key="match.label"
            type="button"
            class="nav-result"
            @click="jumpToSearchResult(match)"
          >
            <FontAwesomeIcon :icon="match.icon" class="nav-result-icon" />
            <span class="nav-result-label">{{ match.label }}</span>
            <span class="nav-result-crumb">{{ searchEntryCrumb(match) }}</span>
          </button>
          <div v-if="!searchMatches.length" class="nav-results-empty">No matching settings</div>
        </div>
      </div>
      <nav class="nav-scroll" aria-label="Settings sections">
        <div v-for="s in NAV_SECTIONS" :key="s.id" class="nav-group" :class="{ 'nav-group-help-start': s.id === 'about' }">
          <button
            type="button"
            class="nav-item nav-rail-item"
            :aria-current="section === s.id ? 'page' : undefined"
            :data-tour="s.tour"
            @click="selectSection(s.id)"
          >
            <FontAwesomeIcon :icon="s.icon" />
            <span>{{ s.name }}</span>
          </button>
        </div>
        <div class="nav-group">
          <button
            type="button"
            class="nav-item nav-rail-item"
            data-tour="nav-guide"
            title="Open the guide in a new window"
            @click="openGuide"
          >
            <FontAwesomeIcon :icon="['fas', 'circle-question']" />
            <span>Guide</span>
            <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" class="nav-item-ext" />
          </button>
        </div>
      </nav>
    </aside>

    <main ref="mainEl" class="main">
      <header class="topbar">
        <div class="topbar-text">
          <p class="crumb">{{ topbarMeta.crumb }}</p>
          <h1>{{ topbarMeta.title }}</h1>
          <p>{{ topbarMeta.blurb }}</p>
        </div>
        <div class="topbar-actions">
          <button
            v-if="section === 'appearance'"
            type="button"
            class="btn ghost sm"
            @click="resetAppearanceSection"
          >
            <FontAwesomeIcon :icon="['fas', 'rotate-left']" /> Reset section
          </button>
          <template v-if="isButtonsPage">
            <span class="topbar-divider" aria-hidden="true"></span>
            <span v-if="buttonPageDirty" class="draft-chip"><span class="draft-dot" aria-hidden="true"></span>Draft not applied</span>
            <button
              type="button"
              class="btn primary sm"
              :disabled="applyingButtonBehaviour"
              @click="applyButtonBehaviourToAll"
            >
              <FontAwesomeIcon :icon="['fas', applyingButtonBehaviour ? 'spinner' : 'floppy-disk']" :spin="applyingButtonBehaviour" />
              {{ applyingButtonBehaviour ? 'Applying…' : 'Save & Apply to all keys' }}
            </button>
          </template>
          <button
            v-else-if="!activePage.autosaves"
            type="button"
            class="btn primary sm"
            title="Save settings and refresh the dashboard"
            @click="applyToDashboard"
          >
            <FontAwesomeIcon :icon="['fas', 'check']" /> Apply
          </button>
          <button type="button" class="btn ghost sm" @click="handleSettingsBack">
            <FontAwesomeIcon :icon="['fas', isStandaloneSettings ? 'xmark' : 'arrow-left']" />
            {{ isStandaloneSettings ? 'Close' : 'Back' }}
          </button>
        </div>
      </header>

        <div v-if="activeSection.pages.length > 1" class="subtab-bar" role="tablist" :aria-label="`${topbarMeta.title} sections`">
          <button
            v-for="p in activeSection.pages" :key="p.id"
            type="button" role="tab" class="subtab"
            :aria-selected="page === p.id"
            :data-tour="p.tour"
            @click="selectPage(p.id)"
          >{{ p.name }}</button>
        </div>

        <!-- Each page lists its panels in the settings registry; panels that are bare
             sections get the shared content column here. -->
        <div v-if="pageIsStacked" class="content">
          <div class="col">
            <component :is="PANELS[name]" v-for="name in activePage.panels" :key="name" v-bind="panelBindings[name]" />
          </div>
        </div>
        <template v-else>
          <component :is="PANELS[name]" v-for="name in activePage.panels" :key="name" v-bind="panelBindings[name]" />
        </template>

    </main>

    <SiteFooter class="settings-dock settings-isolate" />

    <FeatureRequestModal v-if="showFeatureRequest" class="settings-isolate" @close="showFeatureRequest = false" />

    <McpInfoModal v-if="mcpHelpOpen" :endpoint="mcpEndpoint" class="settings-isolate" @close="mcpHelpOpen = false" />

    <!-- Shortcut Manager Modal -->
    <AppShortcutManager
      v-if="showShortcutManager"
      class="settings-isolate"
      :app-exe="selectedAppForShortcuts?.exe || ''"
      :scene-id="getAppScene(selectedAppForShortcuts?.exe || '')"
      @close="showShortcutManager = false"
      @add-shortcut="handleAddShortcut"
    />

    <!-- Live screensaver layout editor — mounted in THIS window so Customize
         Layout works whether or not a deck window is reachable. Save writes
         settings.screensaverLayout, which syncs to every connected window. -->
    <Teleport to="body">
      <ScreenSaver
        v-if="screensaverLayoutEditOpen"
        :visible="true"
        :layout-edit="true"
        @dismiss="screensaverLayoutEditOpen = false"
        @save-layout="onSaveScreensaverLayout"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { LAST_PROFILE_STORAGE_KEY, useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { useSettingsNavigation } from '@/composables/useSettingsNavigation'
import { NAV_SECTIONS, findPage, findSection, searchSettings, type SearchEntry } from '@/settings/registry'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import ScreenSaver from '@/components/ScreenSaver.vue'
import type { ScreensaverLayout } from '@/utils/screensaverLayout'
import DeckButton from '@/components/DeckButton.vue'
import ButtonDesignPicker from '@/components/ButtonDesignPicker.vue'
import SettingResetButton from '@/components/SettingResetButton.vue'
import Collapse from '@/components/Collapse.vue'
import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'
import AppShortcutManager from '@/components/AppShortcutManager.vue'
import type { AppShortcut } from '@/api/appProfiles'
import type { RunningApp, Button } from '@/types'
import { isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import { refreshVdock, requestVdockRefresh } from '@/composables/useVdockRefresh'
import { useAppIntegrations, reloadAppIntegrations } from '@/composables/useAppIntegrations'
import { getAppScene, createButtonFromShortcut } from '@/composables/useAppShortcutScenes'
import { sliderFill } from '@/utils/sliderFill'
import { useBackgroundPreview } from '@/composables/useBackgroundPreview'
import SiteFooter from '@/components/SiteFooter.vue'
import FeatureRequestModal from '@/components/FeatureRequestModal.vue'
import TriggersPanel from '@/components/settings/TriggersPanel.vue'
// Cascade order matters (equal-specificity ties): view-level child components above,
// then the shared settings styles, then the panels whose scoped rules refine them.
import '@/assets/styles/settings.css'
import OverviewPanel from '@/components/settings/panels/OverviewPanel.vue'
import AccountsPanel from '@/components/settings/panels/AccountsPanel.vue'
import AboutPanel from '@/components/settings/panels/AboutPanel.vue'
import ConnectPanel from '@/components/settings/panels/ConnectPanel.vue'
import SecurityPanel from '@/components/settings/panels/SecurityPanel.vue'
import PortsPanel from '@/components/settings/panels/PortsPanel.vue'
import StartupPanel from '@/components/settings/panels/StartupPanel.vue'
import NotificationsPanel from '@/components/settings/panels/NotificationsPanel.vue'
import McpPanel from '@/components/settings/panels/McpPanel.vue'
import AgentAlertsPanel from '@/components/settings/panels/AgentAlertsPanel.vue'
import RecentActionsPanel from '@/components/settings/panels/RecentActionsPanel.vue'
import SceneSwitchingPanel from '@/components/settings/panels/SceneSwitchingPanel.vue'
import ScreensaverPanel from '@/components/settings/panels/ScreensaverPanel.vue'
import AppearanceBackground from '@/components/settings/panels/AppearanceBackground.vue'
import AppearanceLayout from '@/components/settings/panels/AppearanceLayout.vue'
import AppearanceButtons from '@/components/settings/panels/AppearanceButtons.vue'
import LogsPanel from '@/components/settings/panels/LogsPanel.vue'
import TemplatesPanel from '@/components/settings/panels/TemplatesPanel.vue'
import McpInfoModal from '@/components/settings/McpInfoModal.vue'
import { loadAppPaths } from '@/api/appPaths'
const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()
const profilesStore = useProfilesStore()
const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const isStandaloneSettings = computed(() => isStandaloneSettingsRoute(route))

// Opens the real screensaver in drag/resize edit mode — mounted inside this
// window so it always works: the previous design sent a ui_command to the
// deck window, which silently did nothing when no deck window was mounted or
// reachable (e.g. settings opened standalone on the panel itself).
const screensaverLayoutEditOpen = ref(false)

function onSaveScreensaverLayout(layout: ScreensaverLayout, target: 'widgets' | 'spectrum' = 'widgets') {
  // Assigning the store ref persists through the settings watch → local +
  // server sync, so the deck window picks the arrangement up live.
  // DL-142: each saver type has its own layout.
  settingsStore.setScreensaverLayout(target, layout)
  screensaverLayoutEditOpen.value = false
  notificationsStore.success('Layout saved', 'The new widget arrangement is applied on the deck.')
}

function handleSettingsBack() {
  if (isStandaloneSettings.value) {
    // The main dashboard runs in a different tab/window here, so ask it to
    // refresh itself instead of calling refreshVdock() directly.
    requestVdockRefresh()
    window.close()
    return
  }

  // Settings changes made via direct API calls (templates, integrations,
  // shortcuts, etc.) don't all flow through the reactive settings store, so
  // re-sync everything from the backend when returning to the dashboard.
  void refreshVdock()
  router.push('/')
}

const { mcpEndpoint } = useServerConfig()
const mcpHelpOpen = ref(false)

const mainEl = ref<HTMLElement | null>(null)
const { section, page, activeSection, activePage, selectSection, selectPage, go } = useSettingsNavigation(mainEl)

const topbarMeta = computed(() => ({
  crumb: activeSection.value.pages.length > 1 ? `${activeSection.value.name} · ${activePage.value.name}` : activeSection.value.name,
  title: activePage.value.title,
  blurb: activePage.value.blurb,
}))

// Registry pages name their panels; this maps those names to components.
const PANELS: Record<string, Component> = {
  OverviewPanel, AccountsPanel,
  AppearanceButtons, AppearanceLayout, AppearanceBackground, ScreensaverPanel,
  SceneSwitchingPanel, AgentAlertsPanel, NotificationsPanel, TriggersPanel, McpPanel,
  TemplatesPanel, ConnectPanel, SecurityPanel, PortsPanel,
  LogsPanel, StartupPanel, RecentActionsPanel, AboutPanel,
}
// Panels that are bare sections (no content column of their own).
const STACKED_PANELS = new Set([
  'SceneSwitchingPanel', 'AgentAlertsPanel', 'NotificationsPanel', 'TriggersPanel', 'McpPanel',
  'StartupPanel', 'RecentActionsPanel',
])
const pageIsStacked = computed(() => activePage.value.panels.every((name) => STACKED_PANELS.has(name)))

// Sample button for the live preview card — never persisted, just rendered
// through the real DeckButton component so the preview matches actual
// dashboard rendering exactly. Initialized from the persisted defaults so the
// picker still shows the last-applied style when the tab is reopened.
const previewAnimation = ref(settingsStore.buttonDefaultAnimation)
const previewIconLoop = ref(settingsStore.buttonDefaultIconLoop)
const previewEffect = ref(settingsStore.buttonDefaultEffect)

// Preview rails show exactly what the dashboard would (see useBackgroundPreview).
const { previewBackgroundClass, previewBackgroundStyle } = useBackgroundPreview()

// DL-054: the redesign's save bar. Settings autosave on every change, so the
// only real dirty state is the Buttons page's design draft — the three
// motion/effect defaults preview locally until committed to the store.
const isButtonsPage = computed(() => section.value === 'appearance' && page.value === 'buttons')
const buttonPageDirty = computed(() =>
  previewAnimation.value !== settingsStore.buttonDefaultAnimation ||
  previewIconLoop.value !== settingsStore.buttonDefaultIconLoop ||
  previewEffect.value !== settingsStore.buttonDefaultEffect
)

// Warn once per draft episode — the rewrite cost is the one fact the
// draft chip can't carry; a toast surfaces it at the moment it matters
// instead of as permanent page chrome (DL-095 follow-up).
let draftToastShown = false
watch(buttonPageDirty, (dirty) => {
  if (dirty && !draftToastShown) {
    draftToastShown = true
    notificationsStore.warning(
      'Draft changes',
      'Motion and key design stay drafts until Save & Apply — which rewrites every existing key, including per-key customisation.',
      { duration: 7000, important: true }
    )
  } else if (!dirty) {
    draftToastShown = false
  }
})
function revertButtonDefaults() {
  previewAnimation.value = settingsStore.buttonDefaultAnimation
  previewIconLoop.value = settingsStore.buttonDefaultIconLoop
  previewEffect.value = settingsStore.buttonDefaultEffect
}
async function applyToDashboard() {
  settingsStore.saveSettings()
  try {
    // Drain the debounced PUT so the toast means the server has the values.
    await settingsStore.flushSettingsToServer()
  } catch (err: any) {
    notificationsStore.error('Apply failed', err?.message || 'Settings could not be saved to the server.')
    return
  }
  requestVdockRefresh()
  // `important` so it still shows under the default "errors only" toast level
  // — Apply is an explicit action and deserves explicit feedback.
  notificationsStore.success('Applied', 'Settings saved and the dashboard was refreshed.', {
    important: true,
    duration: 2000,
  })
}

// Topbar "Reset section" — restores the current Appearance page's settings to
// defaults. Drafted button defaults are reset in the store too so the dirty
// state clears with everything else.
function resetAppearanceSection() {
  const D = SETTINGS_DEFAULTS
  switch (page.value) {
    case 'buttons':
      settingsStore.touchMode = D.touchMode
      settingsStore.buttonSize = D.buttonSize
      settingsStore.buttonTransparency = D.buttonTransparency
      settingsStore.animationsEnabled = D.animationsEnabled
      settingsStore.editModeWiggle = D.editModeWiggle
      settingsStore.tiltEffectEnabled = D.tiltEffectEnabled
      settingsStore.showLabels = D.showLabels
      settingsStore.showTooltips = D.showTooltips
      settingsStore.pressSoundEnabled = D.pressSoundEnabled
      settingsStore.pressSoundStyle = D.pressSoundStyle
      settingsStore.buttonDefaultAnimation = D.buttonDefaultAnimation
      settingsStore.buttonDefaultIconLoop = D.buttonDefaultIconLoop
      settingsStore.buttonDefaultEffect = D.buttonDefaultEffect
      revertButtonDefaults()
      break
    case 'layout':
      settingsStore.dashboardFont = D.dashboardFont
      settingsStore.dockedSidebarEnabled = D.dockedSidebarEnabled
      settingsStore.dockedSidebarWidth = D.dockedSidebarWidth
      settingsStore.dockedButtonHeight = D.dockedButtonHeight
      break
    case 'background':
      settingsStore.background = D.background
      break
    case 'screensaver':
      settingsStore.screensaverTimeout = D.screensaverTimeout
      settingsStore.screensaverWidgets = [...D.screensaverWidgets]
      settingsStore.screensaverWeatherSize = D.screensaverWeatherSize
      settingsStore.screensaverWidgetSize = D.screensaverWidgetSize
      settingsStore.screensaverBackground = D.screensaverBackground
      settingsStore.screensaverStyle = D.screensaverStyle
      settingsStore.spectrumSkin = D.spectrumSkin
      settingsStore.spectrumShuffle = D.spectrumShuffle
      settingsStore.spectrumShuffleMinutes = D.spectrumShuffleMinutes
      settingsStore.spectrumMediaBar = D.spectrumMediaBar
      break
  }
  notificationsStore.success('Section reset', 'Defaults restored for this section.')
}

const applyingButtonBehaviour = ref(false)

// "Save & Apply to all keys" — commits the draft (preview refs) as the
// persisted defaults AND rewrites every existing key (DL-031 follow-up:
// the draft-only path looked identical to a real apply, so picks
// never reached the deck). The dirty-watch toast states the per-key
// customisation cost.
async function applyButtonBehaviourToAll() {
  applyingButtonBehaviour.value = true
  try {
    settingsStore.buttonDefaultAnimation = previewAnimation.value
    settingsStore.buttonDefaultIconLoop = previewIconLoop.value
    settingsStore.buttonDefaultEffect = previewEffect.value
    settingsStore.saveSettings()

    // Standalone Settings windows start with no profile in the dashboard
    // store — without this, applyGlobalButtonStyle silently no-ops while
    // the toast claims success.
    await ensureProfileLoaded()
    if (!dashboardStore.currentProfile) {
      notificationsStore.error('Failed to apply', 'No profile is loaded — nothing to apply the design to.')
      return
    }

    const saved = await dashboardStore.applyGlobalButtonStyle({
      animation: previewAnimation.value,
      iconLoop: previewIconLoop.value,
      effect: previewEffect.value
    })
    if (!saved) {
      notificationsStore.error('Failed to apply', dashboardStore.lastProfileSaveError || 'The profile could not be saved — your buttons were not changed.')
      return
    }

    // Refresh THIS window first: BroadcastChannel never delivers to its own
    // sender, so requestVdockRefresh alone leaves a same-window dashboard on
    // whatever object it renders (stale profile ref = old design). The
    // reload below re-fetches the just-saved profile, so there's no race.
    await refreshVdock()

    // If Settings is open in a separate window/tab (e.g. via "Open in
    // browser"), tell the dashboard window to refresh itself as well.
    requestVdockRefresh()

    notificationsStore.success('Button style applied', 'Animation, icon motion, and effect applied to every button on your dashboard.')
  } catch (err: any) {
    notificationsStore.error('Failed to apply', err?.message || 'Could not apply the button style to all buttons.')
  } finally {
    applyingButtonBehaviour.value = false
  }
}

// The grid stepper needs a loaded profile — standalone Settings windows start
// with none, so fetch it when the Buttons tab is opened (or already active).
watch(isButtonsPage, (onButtons) => {
  if (onButtons) void ensureProfileLoaded()
}, { immediate: true })

const appIntegrations = useAppIntegrations()
const showShortcutManager = ref(false)
const showFeatureRequest = ref(false)
const selectedAppForShortcuts = ref<RunningApp | null>(null)

const settingsSearch = ref('')
const searchMatches = computed(() => searchSettings(settingsSearch.value))

function openGuide() {
  // The guide is a standalone landing page (DL-132) — a new window so the
  // deck and the guide can sit side by side.
  window.open(`${window.location.origin}/guide`, '_blank', 'noopener')
}

function searchEntryCrumb(match: SearchEntry): string {
  if (match.section === 'guide') return 'Guide ↗ new window'
  const sec = findSection(match.section)!
  const pg = match.page ? findPage(sec, match.page) : undefined
  return pg && sec.pages.length > 1 ? `${sec.name} · ${pg.name}` : sec.name
}

function jumpToSearchResult(match: SearchEntry) {
  settingsSearch.value = ''
  if (match.section === 'guide') {
    openGuide()
    return
  }
  go({ section: match.section, page: match.page ?? findSection(match.section)!.pages[0].id, anchor: match.anchor })
}

function openShortcutManager(app: RunningApp) { selectedAppForShortcuts.value = app; showShortcutManager.value = true }

// Props and listeners the view wires into panels that need more than the stores.
const panelBindings = computed<Record<string, Record<string, unknown>>>(() => ({
  OverviewPanel: { onNavigate: go },
  AppearanceButtons: {
    animation: previewAnimation.value,
    'onUpdate:animation': (v: string) => { previewAnimation.value = v },
    iconLoop: previewIconLoop.value,
    'onUpdate:iconLoop': (v: string) => { previewIconLoop.value = v },
    effect: previewEffect.value,
    'onUpdate:effect': (v: string) => { previewEffect.value = v },
  },
  AppearanceBackground: { onOpenScreensaverBackground: () => go({ section: 'appearance', page: 'screensaver', anchor: 'ss-background' }) },
  ScreensaverPanel: { onCustomizeLayout: () => { screensaverLayoutEditOpen.value = true } },
  SceneSwitchingPanel: { onManageShortcuts: openShortcutManager },
  TriggersPanel: { class: 'settings-isolate' },
  McpPanel: { onShowHelp: () => { mcpHelpOpen.value = true } },
  AboutPanel: { onRequestFeature: () => { showFeatureRequest.value = true } },
}))

function handleAddShortcut(shortcut: AppShortcut) {
  const sceneId = getAppScene(selectedAppForShortcuts.value?.exe || '')
  if (!sceneId) { notificationsStore.error('No scene', 'Please create a scene first'); return }
  const profile = dashboardStore.currentProfile
  if (!profile) return
  const scene = profile.scenes.find(s => s.id === sceneId)
  if (!scene?.pages?.length) { notificationsStore.error('Scene missing', 'Scene not found'); return }
  const page = scene.pages[0]
  const buttons = page.buttons || []
  let emptySlot = null
  for (let row = 0; row < page.grid_config.rows && !emptySlot; row++) {
    for (let col = 0; col < page.grid_config.cols && !emptySlot; col++) {
      if (!buttons.some(b => b.position.row === row && b.position.col === col)) emptySlot = { row, col }
    }
  }
  if (!emptySlot) { notificationsStore.error('Scene full', 'No empty slots available in the scene'); return }
  const newButton = createButtonFromShortcut(shortcut, 0)
  newButton.position = emptySlot
  dashboardStore.addButton(newButton)
  showShortcutManager.value = false
  notificationsStore.success('Shortcut added', `"${shortcut.name}" added to scene`)
}

function loadAppIntegrations() {
  reloadAppIntegrations()
  autoSceneSwitcher.updateIntegrations(appIntegrations.value)
}

// Settings is normally opened from within the already-running dashboard,
// which has already loaded a profile into dashboardStore. But when opened as
// its own standalone browser tab it's a fresh app instance with no profile
// loaded at all, which left features like "Scene Background" permanently
// disabled (no current scene to override). Mirrors the profile-loading logic
// in DashboardView's onMounted.
async function ensureProfileLoaded() {
  if (dashboardStore.currentProfile) return

  const lastProfileId = localStorage.getItem(LAST_PROFILE_STORAGE_KEY)
  if (lastProfileId) {
    const profile = await profilesStore.getProfile(lastProfileId)
    if (profile) {
      dashboardStore.setProfile(profile)
      return
    }
  }

  await profilesStore.loadProfiles()
  if (profilesStore.profiles.length > 0) {
    const profile = await profilesStore.getProfile(profilesStore.profiles[0].id)
    if (profile) {
      dashboardStore.setProfile(profile)
    }
  }
}

onMounted(async () => {
  // 'guide' is no longer a tab — a stale ?tab=guide link still lands the
  // user on the guide page.
  if (route.query.tab === 'guide') openGuide()
  await ensureProfileLoaded()
  void settingsStore.loadServerConfig()
  void loadAppPaths()
  loadAppIntegrations()
})
</script>

