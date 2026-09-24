<template>
  <!-- Dedicated mobile chrome: a single slim bar that puts the two actions
       a phone deck actually needs — switching scenes and flipping pages —
       one tap away, with everything else behind an overflow menu. No
       configuration affordances on this surface (DL-061). -->
  <header class="mobile-chrome">
    <div ref="railRef" class="mc-scene-rail" role="radiogroup" aria-label="Scene selector">
      <!-- Measured glider: sized from the active segment's real box so it
           stays aligned once the rail scrolls (a %-of-container glider
           misplaces under overflow). -->
      <span class="mc-glider" :style="gliderStyle" aria-hidden="true"></span>
      <button
        v-for="(scene, i) in scenes"
        :key="scene.id"
        ref="segmentRefs"
        type="button"
        role="radio"
        :aria-checked="i === currentSceneIndex ? 'true' : 'false'"
        :tabindex="i === currentSceneIndex ? 0 : -1"
        class="mc-seg"
        :class="{ 'is-active': i === currentSceneIndex }"
        @click="selectScene(i)"
      >
        <FontAwesomeIcon v-if="scene.icon" :icon="parseIcon(scene.icon)" class="mc-seg-icon" />
        <span class="mc-seg-label">{{ scene.name }}</span>
        <span
          v-if="sceneAppIsLive(scene, appIntegrations)"
          class="mc-live"
          :title="`${scene.name}'s app is running`"
        ></span>
      </button>
    </div>

    <div v-if="totalPages > 1" class="mc-pages">
      <button type="button" class="mc-page-btn" aria-label="Previous page" @click="emit('previousPage')">
        <FontAwesomeIcon :icon="['fas', 'chevron-left']" />
      </button>
      <span class="mc-page-ind">{{ currentPageIndex + 1 }}/{{ totalPages }}</span>
      <button type="button" class="mc-page-btn" aria-label="Next page" @click="emit('nextPage')">
        <FontAwesomeIcon :icon="['fas', 'chevron-right']" />
      </button>
    </div>

    <!-- Fullscreen is promoted out of the overflow menu (DL-067): most
         mobile browsers refuse an unprompted requestFullscreen() call, so
         this needs to be a one-tap, hard-to-miss target rather than
         something buried behind ⋮. It pulses until the user has either
         entered fullscreen or dismissed the suggestion once this visit.
         The callout bubble (DL-067 follow-up) spells it out in words for
         the first few seconds — mainly for a phone that just landed here
         fresh off a QR-code scan and has never seen this bar before. -->
    <div class="mc-fullscreen-wrap">
      <div v-if="!isFullscreen && showFullscreenCallout" class="mc-fullscreen-callout" role="status">
        Tap for fullscreen
        <span class="mc-fullscreen-callout-arrow" aria-hidden="true"></span>
      </div>
      <button
        type="button"
        class="mc-fullscreen-btn"
        :class="{ 'mc-suggest': !isFullscreen && suggestFullscreen }"
        :aria-label="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
        :title="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
        @click="onFullscreen"
      >
        <FontAwesomeIcon :icon="['fas', isFullscreen ? 'compress' : 'expand']" />
      </button>
    </div>

    <div ref="menuWrapRef" class="mc-more-wrap">
      <button
        type="button"
        class="mc-more-btn"
        aria-label="More actions"
        :aria-expanded="menuOpen ? 'true' : 'false'"
        @click="menuOpen = !menuOpen"
      >
        <FontAwesomeIcon :icon="['fas', 'ellipsis-vertical']" />
      </button>
      <div v-if="menuOpen" class="mc-menu" role="menu">
        <button type="button" role="menuitem" class="mc-menu-item" @click="onRefresh">
          <FontAwesomeIcon :icon="['fas', 'rotate-right']" :spin="isRefreshing" />
          <span>Refresh</span>
        </button>
        <button type="button" role="menuitem" class="mc-menu-item mc-menu-danger" @click="onExit">
          <FontAwesomeIcon :icon="['fas', 'power-off']" />
          <span>Exit VDock</span>
        </button>
      </div>
    </div>

    <!-- Exit confirmation (same flow as the desktop header). -->
    <div v-if="showExitConfirm" class="mc-confirm-overlay" @click.self="cancelExit">
      <div class="mc-confirm-dialog" role="alertdialog" aria-modal="true" aria-label="Exit VDock">
        <div class="mc-confirm-icon">
          <FontAwesomeIcon :icon="['fas', 'power-off']" />
        </div>
        <h3>Exit VDock?</h3>
        <p>This will close the application.</p>
        <div class="mc-confirm-actions">
          <button type="button" class="mc-confirm-btn" @click="cancelExit">Cancel</button>
          <button type="button" class="mc-confirm-btn mc-confirm-danger" @click="confirmExit">Exit</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useElectron } from '@/composables/useElectron'
import { refreshVdock } from '@/composables/useVdockRefresh'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { useSettingsStore } from '@/stores/settings'
import { startAppDetection, stopAppDetection, sceneAppIsLive } from '@/services/appDetection'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'
import type { Scene } from '@/types'

interface Props {
  scenes: Scene[]
  currentSceneIndex: number
  totalPages: number
  currentPageIndex: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  setScene: [sceneId: string]
  previousPage: []
  nextPage: []
}>()

const appIntegrations = useAppIntegrations()
const settingsStore = useSettingsStore()
const { quitApp, isElectron, toggleFullscreen: toggleElectronFullscreen, isFullscreen: getElectronFullscreen } = useElectron()

// The desktop pill owns this watcher — on mobile it doesn't mount, so the
// rail starts detection itself or the live dots never light up.
watch(() => settingsStore.appScanningEnabled,
  enabled => (enabled ? startAppDetection() : stopAppDetection()),
  { immediate: true })

function parseIcon(iconValue: unknown) {
  return normalizeFaIcon(iconValue)
}

function selectScene(index: number) {
  if (index === props.currentSceneIndex) return
  vibrate(10)
  emit('setScene', props.scenes[index].id)
}

// --- Measured glider -----------------------------------------------------------
// Positions come from the active segment's offset box inside the scroll
// content, so the indicator tracks correctly no matter how far the rail
// is scrolled. Re-measured on scene/list changes and rail resizes.
const railRef = ref<HTMLElement | null>(null)
const segmentRefs = ref<HTMLElement[]>([])
const gliderStyle = ref<Record<string, string>>({ opacity: '0' })

async function measureGlider() {
  await nextTick()
  const el = segmentRefs.value?.[props.currentSceneIndex]
  if (!el || !railRef.value) {
    gliderStyle.value = { opacity: '0' }
    return
  }
  gliderStyle.value = {
    transform: `translateX(${el.offsetLeft}px)`,
    width: `${el.offsetWidth}px`,
    opacity: '1',
  }
  // A scene change from anywhere (rail tap, page swipe) keeps the active
  // segment visible — nearest-edge scroll, no jarring jumps.
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
}

let railObserver: ResizeObserver | null = null
watch(() => [props.currentSceneIndex, props.scenes.length], measureGlider)
onMounted(() => {
  measureGlider()
  if (typeof ResizeObserver !== 'undefined' && railRef.value) {
    railObserver = new ResizeObserver(() => measureGlider())
    railObserver.observe(railRef.value)
  }
})

// --- Overflow menu --------------------------------------------------------------
const menuOpen = ref(false)
const menuWrapRef = ref<HTMLElement | null>(null)

function onDocPointerDown(e: PointerEvent) {
  if (menuOpen.value && menuWrapRef.value && !menuWrapRef.value.contains(e.target as Node)) {
    menuOpen.value = false
  }
}
document.addEventListener('pointerdown', onDocPointerDown)

const isFullscreen = ref(typeof document !== 'undefined' && !!document.fullscreenElement)
const isRefreshing = ref(false)
const showExitConfirm = ref(false)
// Pulses the fullscreen button until the user acts on it once this visit —
// most mobile browsers block the unattended auto-fullscreen attempt below,
// so this is the actual, reliable way in for most phones.
const suggestFullscreen = ref(true)
// Spells the pulse out in words for a few seconds, then fades — a silent
// pulsing border is easy to miss on a phone screen someone is seeing for
// the first time right after scanning the connect QR code.
const showFullscreenCallout = ref(true)
let fullscreenCalloutTimer: ReturnType<typeof setTimeout> | null = null

function handleFullscreenChange() {
  if (!isElectron()) isFullscreen.value = !!document.fullscreenElement
}

watch(isFullscreen, (fullscreen) => {
  if (fullscreen) showFullscreenCallout.value = false
})

async function onFullscreen() {
  menuOpen.value = false
  suggestFullscreen.value = false
  showFullscreenCallout.value = false
  try {
    isFullscreen.value = await toggleElectronFullscreen()
  } catch (err) {
    console.error('Failed to toggle fullscreen:', err)
  }
}

async function onRefresh() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await refreshVdock()
  } finally {
    isRefreshing.value = false
    menuOpen.value = false
  }
}

function onExit() {
  menuOpen.value = false
  showExitConfirm.value = true
}

function cancelExit() {
  showExitConfirm.value = false
}

async function confirmExit() {
  showExitConfirm.value = false
  try {
    const handled = await quitApp()
    if (!handled) {
      window.alert('VDock is running in a browser tab and cannot close itself. Please close this browser tab/window manually.')
    }
  } catch (error) {
    console.error('Failed to quit VDock:', error)
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)

  // Best-effort: browsers only honor requestFullscreen() with a recent user
  // gesture, so this silently no-ops on most phone browsers (Safari,
  // Chrome without prior site permission) and only actually lands in
  // contexts that allow it (Electron, an installed PWA that already has
  // fullscreen permission). The pulsing button above is the fallback that
  // always works.
  if (!isFullscreen.value) {
    toggleElectronFullscreen()
      .then(result => { isFullscreen.value = result })
      .catch(() => { /* expected on most mobile browsers — button covers it */ })
  }

  fullscreenCalloutTimer = setTimeout(() => { showFullscreenCallout.value = false }, 6000)
})
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('pointerdown', onDocPointerDown)
  railObserver?.disconnect()
  if (fullscreenCalloutTimer) clearTimeout(fullscreenCalloutTimer)
})
</script>

<style scoped>
.mobile-chrome {
  position: relative;
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 56px;
  flex-shrink: 0;
  padding: 6px 8px;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* --- Scene rail ---------------------------------------------------------- */
.mc-scene-rail {
  position: relative;
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: stretch;
  gap: 2px;
  padding: 4px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  overflow-x: auto;
  scrollbar-width: none;
}
.mc-scene-rail::-webkit-scrollbar { display: none; }

.mc-glider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 0;
  width: 0;
  border-radius: 12px;
  background: #1f6fd1;
  box-shadow: 0 4px 12px rgba(31, 111, 209, 0.45);
  transition:
    transform 0.25s cubic-bezier(0.23, 1, 0.32, 1),
    width 0.25s cubic-bezier(0.23, 1, 0.32, 1),
    opacity 0.15s ease;
  pointer-events: none;
  z-index: 1;
}

.mc-seg {
  position: relative;
  z-index: 2;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 72px;
  min-height: 44px;
  padding: 6px 12px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-secondary, rgba(255, 255, 255, 0.7));
  font-size: clamp(0.72rem, 0.5rem + 1.2vw, 0.95rem);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.2s ease;
}
.mc-seg:active {
  transform: scale(0.96);
  transition: transform 80ms ease;
}
.mc-seg.is-active { color: #fff; }

.mc-seg-icon { flex-shrink: 0; }

.mc-seg-label {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mc-live {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d058;
  box-shadow: 0 0 6px rgba(52, 208, 88, 0.8);
}

/* --- Page steppers --------------------------------------------------------- */
.mc-pages {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 2px;
}
.mc-page-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: clamp(0.8rem, 0.6rem + 0.8vw, 1rem);
  cursor: pointer;
}
.mc-page-btn:active { transform: scale(0.94); }
.mc-page-ind {
  min-width: 34px;
  text-align: center;
  font-size: clamp(0.68rem, 0.55rem + 0.7vw, 0.85rem);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.6);
}

/* --- Fullscreen (promoted out of the overflow menu, DL-067) --------------- */
.mc-fullscreen-wrap {
  position: relative;
  flex: 0 0 auto;
}

.mc-fullscreen-callout {
  position: absolute;
  top: calc(100% + 10px);
  right: -6px;
  z-index: 61;
  padding: 6px 12px;
  border-radius: 10px;
  background: #1f6fd1;
  color: #fff;
  font-size: clamp(0.68rem, 0.55rem + 0.6vw, 0.8rem);
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 8px 20px rgba(31, 111, 209, 0.5);
  animation: mc-fullscreen-callout-fade 6s ease forwards;
  pointer-events: none;
}
.mc-fullscreen-callout-arrow {
  position: absolute;
  top: -5px;
  right: 14px;
  width: 10px;
  height: 10px;
  background: #1f6fd1;
  transform: rotate(45deg);
}

@keyframes mc-fullscreen-callout-fade {
  0%, 75% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-4px); }
}

.mc-fullscreen-btn {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: clamp(0.85rem, 0.65rem + 0.9vw, 1.05rem);
  cursor: pointer;
}
.mc-fullscreen-btn:active { transform: scale(0.94); }

.mc-fullscreen-btn.mc-suggest {
  border-color: #1f6fd1;
  background: rgba(31, 111, 209, 0.28);
  color: #fff;
  animation: mc-fullscreen-pulse 1.6s ease-in-out infinite;
}

@keyframes mc-fullscreen-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(31, 111, 209, 0.55); }
  50% { box-shadow: 0 0 0 8px rgba(31, 111, 209, 0); }
}

/* --- Overflow menu ---------------------------------------------------------- */
.mc-more-wrap { position: relative; flex: 0 0 auto; }
.mc-more-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: clamp(0.85rem, 0.65rem + 0.9vw, 1.05rem);
  cursor: pointer;
}
.mc-more-btn:active { transform: scale(0.94); }

.mc-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 176px;
  padding: 6px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(24, 24, 40, 0.92);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  z-index: 60;
}
.mc-menu-item {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(255, 255, 255, 0.88);
  font-size: clamp(0.78rem, 0.65rem + 0.7vw, 0.95rem);
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}
.mc-menu-item:active { background: rgba(255, 255, 255, 0.1); }
.mc-menu-item > svg { width: 16px; color: rgba(255, 255, 255, 0.6); }
.mc-menu-danger { color: #ff8a80; }
.mc-menu-danger > svg { color: #ff8a80; }

/* --- Exit confirmation -------------------------------------------------------- */
.mc-confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}
.mc-confirm-dialog {
  min-width: 260px;
  max-width: 340px;
  padding: 24px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(24, 24, 40, 0.96);
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}
.mc-confirm-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 82, 82, 0.15);
  color: #ff8a80;
  font-size: clamp(1rem, 0.8rem + 1vw, 1.3rem);
}
.mc-confirm-dialog h3 {
  margin: 0 0 6px;
  font-size: clamp(0.95rem, 0.8rem + 0.8vw, 1.15rem);
  color: #fff;
}
.mc-confirm-dialog p {
  margin: 0 0 18px;
  font-size: clamp(0.75rem, 0.65rem + 0.6vw, 0.9rem);
  color: rgba(255, 255, 255, 0.6);
}
.mc-confirm-actions { display: flex; gap: 10px; justify-content: center; }
.mc-confirm-btn {
  min-height: 44px;
  min-width: 96px;
  padding: 10px 18px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
  font-size: clamp(0.78rem, 0.65rem + 0.7vw, 0.95rem);
  font-weight: 600;
  cursor: pointer;
}
.mc-confirm-btn:active { transform: scale(0.96); }
.mc-confirm-danger {
  background: rgba(255, 82, 82, 0.18);
  border-color: rgba(255, 82, 82, 0.4);
  color: #ff8a80;
}

@media (prefers-reduced-motion: reduce) {
  .mc-fullscreen-btn.mc-suggest { animation: none !important; }
  .mc-fullscreen-callout { animation: none !important; opacity: 1; }
}
</style>
