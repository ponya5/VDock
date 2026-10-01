<template>
  <div class="deck-header-wrapper" :class="{ 'header-hidden': !settingsStore.showHeader }">
    <!-- While the header is hidden the reveal pill lives docked inside
         DeckFooter (in-flow chrome — a floating pill always overlapped
         the grid or the footer's page dots; DL-014 follow-up). This
         Transition now animates the header alone: it slides down in on
         reveal while the footer pill slides down out of its slot, and on
         collapse the header slides up away while the pill rises into
         place (DL-014 addendum #3). -->
    <Transition name="hdr-reveal">
      <!-- Main Header -->
      <header v-if="settingsStore.showHeader" ref="headerRef" class="deck-header dashboard-header">
      <div class="header-background"></div>
      <div class="header-content">
        <div class="header-left">
          <div class="profile-avatar-container">
            <img
              v-if="currentProfile?.avatar && !avatarBroken"
              :key="currentProfile.avatar"
              :src="currentProfile.avatar"
              :alt="currentProfile.name"
              class="profile-avatar enhanced-avatar"
              @error="avatarBroken = true"
              @load="avatarBroken = false"
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
            <!-- DL-134: Profiles/Settings are reachable here on mobile too —
                 the header only mounts on mobile after a deliberate reveal,
                 so the DL-061 "no config affordances" surface rule doesn't
                 apply to it. Edit stays gated: toggleEditMode is blocked on
                 mobile upstream, so the button would be dead. -->
            <button class="btn-icon-circle animate-tap" @click="emit('navigateProfiles')" title="Profiles" aria-label="Profiles">
              <FontAwesomeIcon :icon="['fas', 'users']" />
            </button>
            <button
              v-if="!isMobileViewport"
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
      <!-- Auto-hide countdown chip: the 4px line alone never told the user
           how long they had. Gradient-border pill (star/glow layers behind
           the face) with live seconds; a tap pins the header open — the
           collapse handle/swipe still works from pinned. -->
      <button
        type="button"
        class="autohide-pill"
        :class="{ pinned: autohidePaused }"
        :title="autohidePaused ? 'Header pinned — tap to resume auto-hide' : `Header hides in ${secondsLeft}s — tap to keep it open`"
        :aria-label="autohidePaused ? 'Header pinned — tap to resume auto-hide' : `Header hides in ${secondsLeft} seconds — tap to keep it open`"
        @click="toggleAutohidePin"
      >
        <span class="pill-stars" aria-hidden="true"></span>
        <span class="pill-glow" aria-hidden="true">
          <span class="pill-circle"></span>
          <span class="pill-circle"></span>
        </span>
        <span class="pill-face">
          <FontAwesomeIcon :icon="['fas', autohidePaused ? 'thumbtack' : 'clock']" class="pill-icon" />
          <span class="pill-secs">{{ autohidePaused ? 'Pinned' : `${secondsLeft}s` }}</span>
        </span>
      </button>
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
    </Transition>

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
import { useMobileViewport } from '@/utils/mobileViewport'
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
  setScene: [sceneId: string]
  addScene: []
  editScene: [scene: Scene]
  setPage: [index: number]
  previousPage: []
  nextPage: []
}>()

const settingsStore = useSettingsStore()
// Phones hide the config entries (profiles / edit mode / settings) — the
// deck is a pure control surface on small screens.
const { isMobileViewport } = useMobileViewport()
const { quitApp, isElectron, toggleFullscreen: toggleElectronFullscreen, isFullscreen: getElectronFullscreen } = useElectron()
const headerRef = ref<HTMLElement | null>(null)
const progressWidth = ref(100)
const isFullscreen = ref(typeof document !== 'undefined' && !!document.fullscreenElement)
const isRefreshing = ref(false)
// Broken avatar files (e.g. deleted uploads) otherwise paint the alt text
// over the icon row — fall back to the placeholder glyph instead.
const avatarBroken = ref(false)

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
// Refs mirror the tick for the countdown pill's face.
const secondsLeft = ref(5)
const autohidePaused = ref(false)
const AUTOHIDE_MS = 5000
const TICK_MS = 50

function toggleAutohidePin() {
  autohidePaused.value = !autohidePaused.value
  if (autohidePaused.value) {
    stopAutohide()
  } else {
    // Resume from where it paused rather than restarting at 5s —
    // unpinning should not silently grant a fresh window.
    startAutohide(autohideRemainingMs)
  }
}

function collapseHeader() {
  stopAutohide()
  autohidePaused.value = false
  settingsStore.showHeader = false
}

// Short viewports (landscape phones): a 164px header leaves the deck
// unusable, so it starts hidden — the reveal tab/swipe-down still works.
// If WE hid it, rotating back to a tall viewport restores it; an explicit
// user hide stays hidden.
const SHORT_VIEWPORT_PX = 480
let userRevealedOnShort = false
let autoHidOnShort = false

function autoHideOnShortViewport() {
  if (window.innerHeight < SHORT_VIEWPORT_PX) {
    if (!userRevealedOnShort && settingsStore.showHeader) {
      settingsStore.showHeader = false
      autoHidOnShort = true
    }
  } else if (autoHidOnShort && !settingsStore.showHeader) {
    settingsStore.showHeader = true
    autoHidOnShort = false
  }
}

function startAutohide(fromMs: number = AUTOHIDE_MS) {
  stopAutohide()
  autohideRemainingMs = fromMs
  secondsLeft.value = Math.ceil(autohideRemainingMs / 1000)
  progressWidth.value = (autohideRemainingMs / AUTOHIDE_MS) * 100
  autohideTimer = setInterval(() => {
    autohideRemainingMs -= TICK_MS
    secondsLeft.value = Math.max(0, Math.ceil(autohideRemainingMs / 1000))
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
    // A reveal while the viewport is short counts as an explicit user
    // reveal — auto-hide won't re-engage for it. Set here (not in a
    // click handler) so every reveal path marks it, including the
    // footer-docked pill. The height guard keeps a reveal on a tall
    // viewport from pinning the flag forever.
    if (window.innerHeight < SHORT_VIEWPORT_PX) {
      userRevealedOnShort = true
    }
    startAutohide()
  } else {
    stopAutohide()
    autohidePaused.value = false
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
  window.addEventListener('resize', autoHideOnShortViewport)
  autoHideOnShortViewport()
  // Mounting with the header already revealed (mobile reveal mounts this
  // component only when showHeader is on — the showHeader watcher misses
  // the transition) still gets the countdown, matching a watched reveal.
  if (settingsStore.showHeader) {
    startAutohide()
  }
  getElectronFullscreen().then((value) => {
    isFullscreen.value = value
  })
})

onUnmounted(() => {
  stopAutohide()
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('resize', autoHideOnShortViewport)
})
</script>

<style scoped>
/* DL-104: the header is an overlay shade, not a flow strip — anchored to
   .dashboard-view (position:relative) so it slides down over the grid and
   the deck's height never reflows when it opens/closes. The mobile header
   already overlays the same way. */
.deck-header-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  /* Above the docked sidebar (z-100) — an open header shades the whole
     deck, sidebar included. Below the narrow-mode sidebar drawer (999),
     toasts (1000) and modals (2000). DL-104 follow-up. */
  z-index: 200;
}

/* Redundant with the overlay (the wrapper no longer has flow height at
   all) but kept: the leave transition's choreography comments reference
   the collapsed wrapper, and it documents the zero-height invariant. */
.header-hidden {
  height: 0;
  overflow: visible;
}

.reveal-handle {
  width: 96px;
  height: 10px;
  margin-top: 6px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

/* Show/hide choreography (DL-014 addendum #3): the header slides down in
   on reveal and up away on hide; the footer-docked reveal pill animates
   in the same direction from its own Transition in DeckFooter, so the
   handoff still reads as one motion. The leaving header rides on
   .header-hidden's height:0 + overflow:visible — the grid reclaims the
   space instantly, no end-of-leave jump. */
.hdr-reveal-enter-active,
.hdr-reveal-leave-active {
  transition: transform 0.55s var(--ease-io, cubic-bezier(0.4, 0, 0.2, 1));
  will-change: transform;
}

/* While leaving, the grid has already reclaimed the header's space
   (.header-hidden → height:0) — keep the sliding header above it. */
.deck-header.hdr-reveal-leave-active {
  z-index: 100;
}

.deck-header.hdr-reveal-enter-from,
.deck-header.hdr-reveal-leave-to {
  transform: translateY(-102%);
}

@media (prefers-reduced-motion: reduce) {
  .hdr-reveal-enter-active,
  .hdr-reveal-leave-active {
    transition: none;
  }
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
  /* Grows with touch mode so the taller icon buttons keep breathing room on
     small panels instead of clipping. */
  min-height: calc(64px * var(--touch-multiplier, 1) + 26px);
  padding: 10px 16px 18px 16px;
  box-sizing: border-box;
  overflow: visible;
  touch-action: pan-x;
}

.header-background {
  position: absolute;
  inset: 0;
  background: rgba(10, 8, 32, 0.66);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  z-index: 0;
}

.header-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: calc(68px * var(--touch-multiplier, 1));
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
  /* Keep the action buttons above the scene pill's positioned segments so
     they always win hit-testing if the pill ever overflows. */
  position: relative;
  z-index: 5;
}

.header-actions-group {
  display: flex;
  align-items: center;
  gap: calc(0.6rem * min(var(--touch-multiplier, 1), 1.25));
}

.header-exit-group {
  margin-left: 1.75rem;
  padding-left: 1.75rem;
  border-left: 1px solid rgba(255, 255, 255, 0.18);
}

.profile-avatar-container {
  position: relative;
  width: calc(56px * min(var(--touch-multiplier, 1), 1.2));
  height: calc(56px * min(var(--touch-multiplier, 1), 1.2));
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
  background: #3ddc84;
  border: 2px solid #17133f;
}

.animate-tap {
  touch-action: manipulation;
  min-width: 44px;
  min-height: 44px;
  /* Touch mode enlarges the floor; the plain 44px lines above stay as the
     baseline for engines without max()/var(). */
  min-width: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
}

/* Large circular icon buttons — 56px base per the mockup, capped hard below
   the full multiplier so a row of them still leaves room for the scene pill
   on a 1024px panel at touch-friendly scale. */
.btn-icon-circle {
  width: calc(56px * min(var(--touch-multiplier, 1), 1.25));
  height: calc(56px * min(var(--touch-multiplier, 1), 1.25));
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
  font-size: calc(clamp(1.2rem, 2vw, 1.5rem) * var(--touch-multiplier, 1));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease;
  touch-action: manipulation;
  flex-shrink: 0;
}

.btn-icon-circle:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.18);
}

.btn-icon-circle:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.24);
}

.btn-icon-circle:disabled {
  opacity: 0.65;
  cursor: wait;
}

.btn-icon-circle.btn-refresh:hover:not(:disabled) {
  background: rgba(74, 163, 255, 0.22);
  border-color: rgba(74, 163, 255, 0.55);
}

.btn-icon-circle.edit-active {
  background: #1f6fd1;
  border-color: #1f6fd1;
  box-shadow: 0 4px 12px rgba(31, 111, 209, 0.45);
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

/* Auto-hide countdown pill — gradient-border glass chip (animated
   border-clip trick), a drifting star layer and two blurred glow blobs
   behind the face. Bottom-right mirrors the reveal FAB's corner. Tap =
   pin the header open. */
.autohide-pill {
  position: absolute;
  bottom: 8px;
  right: 14px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  border: 2px solid transparent;
  background-image:
    linear-gradient(rgba(14, 12, 36, 0.88), rgba(14, 12, 36, 0.88)),
    linear-gradient(137.48deg, #ffdb3b 10%, #fe53bb 45%, #8f51ea 67%, #0044ff 87%);
  background-origin: border-box;
  background-clip: padding-box, border-box;
  background-size: 100% 100%, 300% 300%;
  animation: pill-border-sweep 5s ease infinite;
  overflow: hidden;
  color: #fff;
  font-size: calc(0.72rem * var(--touch-multiplier, 1));
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-user-select: none;
  user-select: none;
  transition: transform 0.18s cubic-bezier(0.23, 1, 0.32, 1);
}

@keyframes pill-border-sweep {
  0% { background-position: 0% 0%, 0% 50%; }
  50% { background-position: 0% 0%, 100% 50%; }
  100% { background-position: 0% 0%, 0% 50%; }
}

/* Star field — one grid of 1px dots drifting up by exactly one period
   (22px) per loop, so the wrap is seamless and transform-composited. */
.pill-stars {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  overflow: hidden;
  pointer-events: none;
}

.pill-stars::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: calc(100% + 22px);
  background-image: radial-gradient(#ffffff 1px, transparent 1.4px);
  background-size: 22px 22px;
  opacity: 0.26;
  animation: pill-stars-drift 3.6s linear infinite;
}

@keyframes pill-stars-drift {
  to { transform: translateY(-22px); }
}

.pill-glow {
  position: absolute;
  inset: 0;
  display: flex;
  pointer-events: none;
}

.pill-circle {
  width: 60%;
  height: 150%;
  margin-top: -6%;
  filter: blur(12px);
  animation: pill-glow-pulse 4s ease-in-out infinite;
}

.pill-circle:nth-of-type(1) { background: rgba(254, 83, 186, 0.5); }
.pill-circle:nth-of-type(2) { background: rgba(142, 81, 234, 0.55); }

@keyframes pill-glow-pulse {
  0%, 100% { transform: scale(0.8); }
  50% { transform: scale(1.08); }
}

.pill-face {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.pill-icon { font-size: 0.8em; opacity: 0.9; }
.pill-secs { min-width: 3.4ch; text-align: left; font-variant-numeric: tabular-nums; }

/* Pinned: the countdown is stopped, so the chip stops asking for
   attention — gradient freezes mid-sweep, glow dims. */
.autohide-pill.pinned {
  animation-play-state: paused;
}

.autohide-pill.pinned .pill-stars::before,
.autohide-pill.pinned .pill-circle {
  animation: none;
}

.autohide-pill.pinned .pill-circle { opacity: 0.4; }

@media (hover: hover) and (pointer: fine) {
  .autohide-pill:hover { transform: scale(1.06); }
}

.autohide-pill:active { transform: scale(0.96); }

@media (prefers-reduced-motion: reduce) {
  .autohide-pill,
  .autohide-pill .pill-stars::before,
  .autohide-pill .pill-circle {
    animation: none;
  }
}

/* Enhanced scene nav sizing */
.enhanced-scene-nav {
  --pill-height: calc(56px * var(--touch-multiplier, 1));
}

/* The 7-inch mockup drops the profile name — the avatar carries the context
   and the freed width goes to the scene pills. Kept in the DOM for a11y. */
.profile-title-inline {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  /* Sized to content — when there's no page nav it takes zero width instead
     of claiming an equal flex share and starving the scene pill. */
  flex: 0 1 auto;
  min-width: 0;
}

/* Exit confirmation modal */
.exit-confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  -webkit-backdrop-filter: blur(4px);
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
