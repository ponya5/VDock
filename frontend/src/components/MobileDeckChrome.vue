<template>
  <!-- Dedicated mobile chrome: a single slim bar that puts the two actions
       a phone deck actually needs — switching scenes and flipping pages —
       one tap away, with everything else behind an overflow menu. No
       configuration affordances on this surface (DL-061). -->
  <header class="mobile-chrome">
    <div
      ref="railRef"
      class="mc-scene-rail"
      :class="{ 'wipe-next': wipeDir === 'next', 'wipe-prev': wipeDir === 'prev' }"
      role="radiogroup"
      aria-label="Scene selector"
    >
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
        :class="{
          'is-active': i === currentSceneIndex,
          'agent-waiting': sceneWaiting(scene),
          'seg-sweep-out': sweep?.out === i,
          'seg-sweep-in': sweep?.in === i,
          'seg-sweep-back': sweepBack?.idx === i,
        }"
        :style="segmentSwipeStyle(i)"
        @click="selectScene(i)"
      >
        <img
          v-if="segLogo(scene)"
          :src="segLogo(scene)!"
          class="mc-seg-logo"
          alt=""
          aria-hidden="true"
        />
        <FontAwesomeIcon v-else-if="scene.icon" :icon="parseIcon(scene.icon)" class="mc-seg-icon" />
        <span class="mc-seg-label">{{ scene.name }}</span>
        <span
          v-if="sceneAppIsLive(scene, appIntegrations) || sceneWaiting(scene)"
          class="mc-live"
          :class="{ 'agent-waiting': sceneWaiting(scene) }"
          :title="sceneWaiting(scene) ? `${scene.name}'s agent is waiting for input` : `${scene.name}'s app is running`"
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
         fresh off a QR-code scan and has never seen this bar before.

         Hidden entirely once already running standalone (launched from an
         iOS Home Screen icon or an installed PWA) — there's no browser
         chrome left to hide in that case (DL-067 second follow-up). -->
    <div v-if="!isStandalone" class="mc-fullscreen-wrap">
      <div
        v-if="!isFullscreen && showFullscreenCallout"
        class="mc-fullscreen-callout"
        :class="{ 'mc-fullscreen-callout-persist': fullscreenUnsupported }"
        role="status"
      >
        {{ fullscreenUnsupported ? IOS_FULLSCREEN_CALLOUT : 'Tap for fullscreen' }}
        <span class="mc-fullscreen-callout-arrow" aria-hidden="true"></span>
      </div>
      <button
        type="button"
        class="mc-fullscreen-btn"
        :class="{ 'mc-suggest': !isFullscreen && suggestFullscreen }"
        :aria-label="fullscreenButtonLabel"
        :title="fullscreenButtonLabel"
        @click="onFullscreen"
      >
        <FontAwesomeIcon :icon="['fas', fullscreenButtonIcon]" />
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
        <span v-if="needsYou > 0" class="mc-more-badge" aria-hidden="true"></span>
      </button>
      <div v-if="menuOpen" class="mc-menu" role="menu">
        <button
          type="button"
          role="menuitem"
          class="mc-menu-item"
          data-testid="mc-menu-mission"
          @click="onMissionControl"
        >
          <FontAwesomeIcon :icon="['fas', 'satellite-dish']" />
          <span>Mission Control</span>
          <span v-if="needsYou > 0" class="mc-menu-count">{{ needsYou }}</span>
        </button>
        <button
          type="button"
          role="menuitem"
          class="mc-menu-item"
          data-testid="mc-menu-layout"
          @click="toggleLayout"
        >
          <FontAwesomeIcon :icon="['fas', 'table-cells-large']" />
          <span>Layout: {{ devicePrefs.layout === 'fit' ? 'Fit to screen' : 'As designed' }}</span>
        </button>
        <button
          type="button"
          role="menuitem"
          class="mc-menu-item"
          data-testid="mc-menu-keep-awake"
          @click="devicePrefs.keepAwake = !devicePrefs.keepAwake"
        >
          <FontAwesomeIcon :icon="['fas', 'lightbulb']" />
          <span class="mc-menu-label">
            Keep screen on: {{ devicePrefs.keepAwake ? 'On' : 'Off' }}
            <small v-if="keepAwakeNeedsApp" class="mc-menu-hint" data-testid="mc-keep-awake-hint">
              Needs the installed app or HTTPS (USE_SSL)
            </small>
          </span>
        </button>
        <button
          v-if="!isStandalone"
          type="button"
          role="menuitem"
          class="mc-menu-item"
          data-testid="mc-menu-install"
          @click="onInstall"
        >
          <FontAwesomeIcon :icon="['fas', 'square-plus']" />
          <span>Add to Home Screen</span>
        </button>
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

    <InstallSheet v-if="showInstall" @close="showInstall = false" />

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
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useElectron } from '@/composables/useElectron'
import { refreshVdock } from '@/composables/useVdockRefresh'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { useSettingsStore } from '@/stores/settings'
import { startAppDetection, stopAppDetection, sceneAppIsLive, sceneLogo, loadProfileMaps } from '@/services/appDetection'
import { initAgentState } from '@/services/agentState'
import { sceneAgentIsWaiting, sceneWaitingAgent } from '@/services/agentWaiting'
import { sceneSwipe } from '@/services/sceneSwipe'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'
import { useNeedsYouCount } from '@/composables/useNeedsYouCount'
import { useDevicePrefs } from '@/services/devicePrefs'
import { openMissionControl } from '@/services/missionControl'
import { supportsFullscreenApi, isRunningStandalone } from '@/utils/fullscreenSupport'
import { IOS_FULLSCREEN_CALLOUT } from '@/utils/installCopy'
import InstallSheet from '@/components/InstallSheet.vue'
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
const needsYou = useNeedsYouCount()
const devicePrefs = useDevicePrefs()
const { quitApp, isElectron, toggleFullscreen: toggleElectronFullscreen, isFullscreen: getElectronFullscreen } = useElectron()

// The desktop pill owns this watcher — on mobile it doesn't mount, so the
// rail starts detection itself or the live dots never light up.
watch(() => settingsStore.appScanningEnabled,
  enabled => (enabled ? startAppDetection() : stopAppDetection()),
  { immediate: true })

// Same waiting-agent feed the desktop rail uses (idempotent): the phone's
// scene segments flag an idle agent on another scene too.
onMounted(() => {
  initAgentState()
  void loadProfileMaps()
})

/** DL-080 follow-up: this scene's agent sits idle, waiting for input. */
const waitingAlertsOn = computed(() => settingsStore.agentWaitingGlowEnabled !== false)

function sceneWaiting(scene: Scene): boolean {
  return waitingAlertsOn.value && sceneAgentIsWaiting(scene, appIntegrations.value)
}

/** Gallery logo for the scene's app, or null → the FA icon renders. */
function segLogo(scene: Scene): string | null {
  return sceneLogo(scene, appIntegrations.value)
}

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
  scrollWaitingIntoView()
  if (typeof ResizeObserver !== 'undefined' && railRef.value) {
    railObserver = new ResizeObserver(() => measureGlider())
    railObserver.observe(railRef.value)
  }
})

/* DL-080 follow-up #4: the rail is horizontally scrollable, so a waiting
   scene's glowing segment can sit entirely off-screen — the frame flashes
   "something waits" while the *where* stays invisible. When a waiting
   scene's segment is clipped, smooth-scroll it into
   view once per waiting episode (`sceneId:entry.ts`, the same episode key
   the snooze dismissal uses). Applies to the active scene too — the
   glider only re-scrolls it into view on scene *change*. Marked before
   the scroll so a user who then scrolls away is never fought; a fresh
   `ready` event is a new episode. */
const waitingRailKey = computed(() =>
  props.scenes
    .map(s => {
      const w = sceneWaitingAgent(s, appIntegrations.value)
      return w ? `${s.id}:${w.entry.ts}` : ''
    })
    .join(','),
)
const autoScrolledWaits = new Set<string>()

function scrollWaitingIntoView() {
  const rail = railRef.value
  if (!rail || !waitingAlertsOn.value) return
  const liveKeys = new Set(waitingRailKey.value.split(',').filter(Boolean))
  for (const k of autoScrolledWaits) {
    if (!liveKeys.has(k)) autoScrolledWaits.delete(k)
  }
  for (const [i, scene] of props.scenes.entries()) {
    if (!sceneWaiting(scene)) continue
    const key = `${scene.id}:${sceneWaitingAgent(scene, appIntegrations.value)?.entry.ts ?? 0}`
    if (autoScrolledWaits.has(key)) continue
    const el = segmentRefs.value?.[i]
    if (!el) continue
    autoScrolledWaits.add(key)
    const clipped =
      el.offsetLeft < rail.scrollLeft - 1 ||
      el.offsetLeft + el.offsetWidth > rail.scrollLeft + rail.clientWidth + 1
    if (clipped) {
      const instant = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      el.scrollIntoView({ behavior: instant ? 'auto' : 'smooth', block: 'nearest', inline: 'nearest' })
    }
    break
  }
}

watch(waitingRailKey, () => void nextTick().then(scrollWaitingIntoView))

/* --- DL-082: directional dissolve on scene switch -------------------------
   Same mechanism as the desktop GlassPillSceneSelector — see that file for
   the full technique. While a horizontal scene swipe tracks, the active
   segment dissolves 1:1 under the finger; on commit the outgoing segment
   finishes the wave (resuming from `--sweep-from`) and re-forms inactive,
   the incoming one dissolves in; on cancel the wipe reverses. */
interface SegSweep {
  out: number
  in: number
  dir: 'next' | 'prev'
  fromPos: number
  fromOp: number
}
const sweep = ref<SegSweep | null>(null)
const sweepBack = ref<{ idx: number; dir: 'next' | 'prev'; fromPos: number; fromOp: number } | null>(null)
let sweepTimer: ReturnType<typeof setTimeout> | null = null
let sweepBackTimer: ReturnType<typeof setTimeout> | null = null

function dragMaskPos(dir: 'next' | 'prev', progress: number): number {
  const travel = 55 * Math.min(progress, 1)
  return dir === 'next' ? 100 - travel : travel
}
function dragOpacity(progress: number): number {
  return 1 - 0.5 * Math.min(progress, 1)
}

const WIPE_GRADIENTS = {
  next: 'linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%)',
  prev: 'linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%)',
} as const

const wipeDir = computed(() =>
  sweep.value?.dir ?? sweepBack.value?.dir ?? (sceneSwipe.dragging ? sceneSwipe.dir : null),
)

const reduceMotion =
  typeof window !== 'undefined' &&
  (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false)

function segmentSwipeStyle(i: number): Record<string, string> | undefined {
  if (sweep.value && sweep.value.out === i) {
    return {
      '--sweep-from': `${sweep.value.fromPos}%`,
      '--sweep-from-op': String(sweep.value.fromOp),
    } as Record<string, string>
  }
  if (sweepBack.value && sweepBack.value.idx === i) {
    return {
      '--sweep-from': `${sweepBack.value.fromPos}%`,
      '--sweep-from-op': String(sweepBack.value.fromOp),
    } as Record<string, string>
  }
  if (!sceneSwipe.dragging || i !== props.currentSceneIndex) return undefined
  if (reduceMotion) {
    return { opacity: String(dragOpacity(sceneSwipe.progress)), transition: 'none' }
  }
  const grad = WIPE_GRADIENTS[sceneSwipe.dir]
  return {
    '-webkit-mask-image': grad,
    'mask-image': grad,
    '-webkit-mask-size': '250% 100%',
    'mask-size': '250% 100%',
    '-webkit-mask-position': `${dragMaskPos(sceneSwipe.dir, sceneSwipe.progress)}% 0`,
    'mask-position': `${dragMaskPos(sceneSwipe.dir, sceneSwipe.progress)}% 0`,
    opacity: String(dragOpacity(sceneSwipe.progress)),
    transition: 'none',
  }
}

watch(() => props.currentSceneIndex, (newIdx, oldIdx) => {
  if (newIdx === oldIdx) return
  const n = props.scenes.length
  const forward = (newIdx - oldIdx + n) % n
  const dir = forward <= n - forward ? 'next' : 'prev'
  const p = sceneSwipe.justSwiped ? Math.min(sceneSwipe.progress, 1) : 0
  sceneSwipe.justSwiped = false
  sweepBack.value = null
  sweep.value = {
    out: oldIdx,
    in: newIdx,
    dir,
    fromPos: dragMaskPos(dir, p),
    fromOp: dragOpacity(p),
  }
  if (sweepTimer) clearTimeout(sweepTimer)
  sweepTimer = setTimeout(() => { sweep.value = null }, 620)
})

watch(() => sceneSwipe.dragging, (dragging) => {
  if (dragging || sceneSwipe.justSwiped || sceneSwipe.progress === 0) return
  const dir = sceneSwipe.dir
  sweepBack.value = {
    idx: props.currentSceneIndex,
    dir,
    fromPos: dragMaskPos(dir, sceneSwipe.progress),
    fromOp: dragOpacity(sceneSwipe.progress),
  }
  if (sweepBackTimer) clearTimeout(sweepBackTimer)
  sweepBackTimer = setTimeout(() => { sweepBack.value = null }, 320)
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

// Already running without browser chrome (launched from an iOS Home Screen
// icon, or an installed PWA elsewhere) — nothing left for this control to
// toggle. Computed once per mount; it can't change while the page is open.
const isStandalone = isRunningStandalone()

// Screen Wake Lock only exists in a secure context, and a deck on plain
// http://192.168.x.x is not one (HTTPS via USE_SSL, or the installed app, fixes it).
const keepAwakeNeedsApp = !window.isSecureContext
const showInstall = ref(false)

function onInstall() {
  menuOpen.value = false
  showInstall.value = true
}

// iPhone Safari never implements the Fullscreen API (see fullscreenSupport.ts)
// — Electron always has its own native call, so only a plain browser tab
// without the DOM API is actually stuck.
const fullscreenUnsupported = !isElectron() && !supportsFullscreenApi()

const fullscreenButtonLabel = computed(() => {
  if (fullscreenUnsupported) return 'Add to Home Screen for fullscreen'
  return isFullscreen.value ? 'Exit fullscreen' : 'Enter fullscreen'
})
const fullscreenButtonIcon = computed(() => {
  if (fullscreenUnsupported) return 'arrow-up-right-from-square'
  return isFullscreen.value ? 'compress' : 'expand'
})

function handleFullscreenChange() {
  if (!isElectron()) isFullscreen.value = !!document.fullscreenElement
}

watch(isFullscreen, (fullscreen) => {
  if (fullscreen) showFullscreenCallout.value = false
})

async function onFullscreen() {
  menuOpen.value = false
  suggestFullscreen.value = false

  // No successful `requestFullscreen()` will ever fire on this platform, so
  // there's no event to dismiss the callout on its own — toggle it as the
  // button's whole job instead of attempting (and silently failing) the
  // same dead API call every other branch below relies on.
  if (fullscreenUnsupported) {
    showFullscreenCallout.value = !showFullscreenCallout.value
    return
  }

  showFullscreenCallout.value = false
  try {
    isFullscreen.value = await toggleElectronFullscreen()
  } catch (err) {
    console.error('Failed to toggle fullscreen:', err)
  }
}

function onMissionControl() {
  menuOpen.value = false
  openMissionControl()
}

// Device-local (DL-147): never part of the synced settings, so flipping it
// on a phone does not touch the desktop or any other device.
function toggleLayout() {
  devicePrefs.layout = devicePrefs.layout === 'fit' ? 'designed' : 'fit'
  menuOpen.value = false
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

  // iPhone Safari has no Fullscreen API to attempt at all — skip straight
  // to leaving the "Add to Home Screen" callout up (dismissed only by the
  // user tapping the button) rather than racing it against the 6-second
  // timer below, which exists for the "tap the button" case this isn't.
  if (fullscreenUnsupported) return

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
  -webkit-backdrop-filter: blur(14px);
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
  -webkit-user-select: none;
  user-select: none;
  position: relative;
  z-index: 2;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 72px;
  min-height: 48px;
  padding: 8px 12px;
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

/* App logo (DL-086) — smaller than desktop's 26px but still legible on a
   phone rail. */
.mc-seg-logo {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  object-fit: contain;
  border-radius: 5px;
}

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

/* Agent waiting — the whole segment fills green and pulses so the idle
   agent's scene is findable from any other scene on a small screen —
   a 2 px outline alone was invisible at 7" (DL-080 follow-up #3). */
.mc-seg.agent-waiting {
  background: rgba(34, 197, 94, 0.16);
  box-shadow:
    inset 0 0 0 3px rgba(34, 197, 94, 0.95),
    0 0 14px rgba(34, 197, 94, 0.5);
  animation: mc-waiting-pulse 1.6s ease-in-out infinite;
}

@keyframes mc-waiting-pulse {
  0%, 100% {
    background: rgba(34, 197, 94, 0.16);
    box-shadow:
      inset 0 0 0 3px rgba(34, 197, 94, 0.95),
      0 0 12px rgba(34, 197, 94, 0.5);
  }
  50% {
    background: rgba(34, 197, 94, 0.4);
    box-shadow:
      inset 0 0 0 3px #86efac,
      0 0 26px rgba(34, 197, 94, 0.85),
      0 0 6px rgba(134, 239, 172, 0.7);
  }
}

.mc-live.agent-waiting {
  width: 12px;
  height: 12px;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.9), 0 0 0 3px rgba(34, 197, 94, 0.35);
  animation: mc-live-waiting-pulse 1.2s ease-in-out infinite;
}

@keyframes mc-live-waiting-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.75; transform: scale(1.5); }
}

/* DL-082 — directional dissolve on the scene segments (same technique as
   the desktop pill rail): 250%-wide mask gradients swept via
   mask-position; `next` travels L→R, `prev` R→L; the outgoing segment
   re-forms as the now-inactive button, cancelled swipes wipe back. */
.mc-scene-rail.wipe-next .mc-seg.seg-sweep-out {
  animation: seg-wipe-out-next 0.55s var(--ease-io) both;
}
.mc-scene-rail.wipe-next .mc-seg.seg-sweep-in {
  animation: seg-wipe-in-next 0.4s var(--ease-out) 0.05s both;
}
.mc-scene-rail.wipe-next .mc-seg.seg-sweep-back {
  animation: seg-wipe-back-next 0.28s var(--ease-out) both;
}
.mc-scene-rail.wipe-prev .mc-seg.seg-sweep-out {
  animation: seg-wipe-out-prev 0.55s var(--ease-io) both;
}
.mc-scene-rail.wipe-prev .mc-seg.seg-sweep-in {
  animation: seg-wipe-in-prev 0.4s var(--ease-out) 0.05s both;
}
.mc-scene-rail.wipe-prev .mc-seg.seg-sweep-back {
  animation: seg-wipe-back-prev 0.28s var(--ease-out) both;
}

@keyframes seg-wipe-out-next {
  0% {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: var(--sweep-from, 100%) 0;
    mask-position: var(--sweep-from, 100%) 0;
    opacity: var(--sweep-from-op, 1);
  }
  42% {
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 0;
  }
  55% {
    -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 0;
  }
  100% {
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 1;
  }
}
@keyframes seg-wipe-in-next {
  0% {
    -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 0;
  }
  100% {
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 1;
  }
}
@keyframes seg-wipe-back-next {
  0% {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: var(--sweep-from, 100%) 0;
    mask-position: var(--sweep-from, 100%) 0;
    opacity: var(--sweep-from-op, 1);
  }
  100% {
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 1;
  }
}
@keyframes seg-wipe-out-prev {
  0% {
    -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: var(--sweep-from, 0%) 0;
    mask-position: var(--sweep-from, 0%) 0;
    opacity: var(--sweep-from-op, 1);
  }
  42% {
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 0;
  }
  55% {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 0;
  }
  100% {
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 1;
  }
}
@keyframes seg-wipe-in-prev {
  0% {
    -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    mask-image: linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 0;
  }
  100% {
    -webkit-mask-position: 100% 0;
    mask-position: 100% 0;
    opacity: 1;
  }
}
@keyframes seg-wipe-back-prev {
  0% {
    -webkit-mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    mask-image: linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%);
    -webkit-mask-size: 250% 100%;
    mask-size: 250% 100%;
    -webkit-mask-position: var(--sweep-from, 0%) 0;
    mask-position: var(--sweep-from, 0%) 0;
    opacity: var(--sweep-from-op, 1);
  }
  100% {
    -webkit-mask-position: 0% 0;
    mask-position: 0% 0;
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mc-seg.agent-waiting { animation: none; }
  .mc-live.agent-waiting { animation: none; }
  .mc-seg.seg-sweep-out,
  .mc-seg.seg-sweep-in,
  .mc-seg.seg-sweep-back { animation: none; }
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
  max-width: min(260px, 80vw);
  padding: 6px 12px;
  border-radius: 10px;
  background: #1f6fd1;
  color: #fff;
  font-size: clamp(0.68rem, 0.55rem + 0.6vw, 0.8rem);
  font-weight: 600;
  white-space: normal;
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

/* iPhone Safari has no successful requestFullscreen() to dismiss this on —
   it stays up until the user taps the button again, so skip the timed
   fade the pulsing-button case relies on (DL-067 second follow-up). */
.mc-fullscreen-callout-persist {
  animation: none;
  opacity: 1;
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
  position: relative;
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

/* Something needs you (permission prompt / prompted idle agent): a dot on
   the menu button, and the count next to Mission Control inside it. */
.mc-more-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f5a524;
  box-shadow: 0 0 0 2px rgba(24, 24, 40, 0.92);
}
.mc-menu-count {
  margin-left: auto;
  min-width: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(245, 165, 36, 0.2);
  color: #ffd89e;
  font-size: 0.8rem;
  font-weight: 700;
  text-align: center;
}

.mc-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 176px;
  padding: 6px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(24, 24, 40, 0.92);
  -webkit-backdrop-filter: blur(18px);
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
.mc-menu-label { display: flex; flex-direction: column; gap: 2px; }
.mc-menu-hint { font-size: 0.7rem; font-weight: 400; color: rgba(255, 255, 255, 0.5); }
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
  -webkit-backdrop-filter: blur(4px);
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
