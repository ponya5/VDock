<template>
  <div class="glass-pill-scene-selector">
    <!-- pill container -->
    <div
      role="radiogroup"
      aria-label="Scene selector"
      class="pill-container"
      :class="{ 'pill-edit': isEditMode, 'wipe-next': wipeDir === 'next', 'wipe-prev': wipeDir === 'prev' }"
      ref="pillRef"
    >
      <!-- glider (absolute positioned, behind segments) -->
      <div class="glider" :style="gliderStyle"></div>

      <!-- one segment per scene -->
      <button
        v-for="(scene, i) in scenes"
        :key="scene.id"
        ref="segmentRefs"
        role="radio"
        :aria-checked="i === currentSceneIndex ? 'true' : 'false'"
        :tabindex="i === focusedIndex ? 0 : -1"
        class="segment"
        :class="{
          'is-active': i === currentSceneIndex,
          'agent-waiting': sceneWaiting(scene),
          'seg-sweep-out': sweep?.out === i,
          'seg-sweep-in': sweep?.in === i,
          'seg-sweep-back': sweepBack?.idx === i,
        }"
        :style="segmentSwipeStyle(i)"
        @click="selectScene(i)"
        @keydown="onKeyDown($event, i)"
      >
        <FontAwesomeIcon v-if="scene.icon" :icon="parseIcon(scene.icon)" class="segment-icon" />
        <span class="segment-label">{{ scene.name }}</span>
        <!-- Green dot when the scene's app is actually running — so a Claude
             scene pill means "buttons will reach a live session", not just
             "this scene exists". A waiting agent upgrades it to a brighter
             pulse and rings the whole pill, so a session idle on another
             scene still reaches the user (DL-080 follow-up). -->
        <span
          v-if="sceneAppIsLive(scene, appIntegrations) || sceneWaiting(scene)"
          class="app-live-dot"
          :class="{ 'agent-waiting-dot': sceneWaiting(scene) }"
          :title="sceneWaiting(scene) ? `${scene.name}'s agent is waiting for input` : `${scene.name}'s app is running`"
        ></span>
        <!-- Edit pencil on the ACTIVE pill only, parked in a lane reserved by
             its edit-mode padding-right — anchored to the real segment edge,
             never covers the label, and only widens one pill (per-scene
             badges on every pill pushed the row into horizontal scroll on
             the narrow 1024px header). Tap another pill to move the pencil. -->
        <span
          v-if="isEditMode && i === currentSceneIndex"
          class="scene-edit-badge"
          role="button"
          tabindex="0"
          :aria-label="`Edit ${scene.name}`"
          title="Edit scene"
          @click.stop="$emit('edit-scene', scene)"
          @keydown.enter.stop.prevent="$emit('edit-scene', scene)"
          @keydown.space.stop.prevent="$emit('edit-scene', scene)"
        >
          <FontAwesomeIcon :icon="['fas', 'pen']" />
        </span>
      </button>
    </div>

    <button v-if="isEditMode" class="edit-btn add-btn" @click="$emit('add-scene')" aria-label="Add scene">
      <FontAwesomeIcon :icon="['fas', 'plus']" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'
import { startAppDetection, stopAppDetection, sceneAppIsLive, loadProfileMaps } from '@/services/appDetection'
import { initAgentState } from '@/services/agentState'
import { sceneAgentIsWaiting } from '@/services/agentWaiting'
import { sceneSwipe } from '@/services/sceneSwipe'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { useSettingsStore } from '@/stores/settings'

const appIntegrations = useAppIntegrations()
const settingsStore = useSettingsStore()

// Poll only while app scanning is enabled — the setting gates both the
// 10s detected-profiles scan and the live dots it feeds.
watch(() => settingsStore.appScanningEnabled,
  enabled => (enabled ? startAppDetection() : stopAppDetection()),
  { immediate: true })

interface Props {
  scenes: Scene[]
  currentSceneIndex: number
  isEditMode: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  // Emits the scene id (not the index) so the single handler chain in
  // DashboardView.setScene — also used by swipe-to-switch — is the only
  // place that resolves a scene reference to a store index.
  'scene-change': [sceneId: string]
  'add-scene': []
  'edit-scene': [scene: Scene]
}>()

// The waiting-state feed is wired up here too (both calls are idempotent):
// the rail must flag waiting scenes even when no agent surface is mounted,
// which is exactly the off-scene case this cue exists for.
onMounted(() => {
  initAgentState()
  void loadProfileMaps()
})

/** DL-080 follow-up: does this scene's agent sit idle, waiting for input?
    Hidden in edit mode and with the waiting-glow setting, same as the
    viewport frame. */
const waitingAlertsOn = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false && !props.isEditMode
)

function sceneWaiting(scene: Scene): boolean {
  return waitingAlertsOn.value && sceneAgentIsWaiting(scene, appIntegrations.value)
}

const pillRef = ref<HTMLElement | null>(null)
const segmentRefs = ref<HTMLElement[]>([])
const disableAnimation = ref(false)
const focusedIndex = ref(0)

const segmentPercent = computed(() => 100 / Math.max(props.scenes.length, 1))
const segmentWidth = computed(() => `${segmentPercent.value}%`)

const gliderStyle = computed(() => {
  const safeIndex = Math.max(0, Math.min(props.currentSceneIndex, props.scenes.length - 1))
  return {
    width: segmentWidth.value,
    transform: `translateX(${safeIndex * 100}%)`,
    transition: disableAnimation.value ? 'none' : 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)'
  }
})

function selectScene(index: number) {
  if (index === props.currentSceneIndex) return
  vibrate(10)
  emit('scene-change', props.scenes[index].id)
}

function onKeyDown(event: KeyboardEvent, index: number) {
  const N = props.scenes.length
  if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    event.preventDefault()
    focusedIndex.value = (index + 1) % N
  } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    event.preventDefault()
    focusedIndex.value = (index - 1 + N) % N
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    selectScene(index)
  }
}

function parseIcon(iconValue: unknown) {
  return normalizeFaIcon(iconValue)
}

watch(focusedIndex, async (newIdx) => {
  await nextTick()
  if (segmentRefs.value[newIdx]) {
    (segmentRefs.value[newIdx] as HTMLElement).focus()
  }
})

watch(() => props.scenes.length, () => {
  disableAnimation.value = true
  nextTick(() => { disableAnimation.value = false })
})

/* --- DL-082: directional dissolve on scene switch -------------------------
   Two phases sharing one mask technique: the gradient is 250% wide so
   animating mask-position sweeps a soft edge across the segment.
   - While the user drags a horizontal scene swipe, the ACTIVE segment
     dissolves 1:1 with the finger (inline style, transition:none).
   - On commit the outgoing segment finishes the sweep via a keyframe that
     resumes from the finger's release position (`--sweep-from`), then
     re-reveals in place as a now-inactive button; the incoming segment
     dissolves in. On cancel a short keyframe wipes the mask back.
   Mask gradients: "out" dissolves the wave-front edge first; "in" reveals
   it — both travel the sweep direction (next = L→R, prev = R→L). */
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

/** Drag progress → the mask-position the live dissolve left the segment at
    (matches the keyframes' 100→0 / 0→100 travel, capped mid-way so the
    button never fully vanishes before the swipe commits). */
function dragMaskPos(dir: 'next' | 'prev', progress: number): number {
  const travel = 55 * Math.min(progress, 1)
  return dir === 'next' ? 100 - travel : travel
}
function dragOpacity(progress: number): number {
  return 1 - 0.5 * Math.min(progress, 1)
}

/** Outgoing-wave gradient — the edge the wave reaches first is
    transparent: transparent-left sweeps L→R, black-left sweeps R→L. */
const WIPE_GRADIENTS = {
  next: 'linear-gradient(to right, transparent 0%, transparent 42%, #000 58%, #000 100%)',
  prev: 'linear-gradient(to right, #000 0%, #000 42%, transparent 58%, transparent 100%)',
} as const

/** Direction class for the container — the committed sweep wins, then a
    cancel recovery, then the live drag. */
const wipeDir = computed(() =>
  sweep.value?.dir ?? sweepBack.value?.dir ?? (sceneSwipe.dragging ? sceneSwipe.dir : null),
)

const reduceMotion =
  typeof window !== 'undefined' &&
  (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false)

/** Live dissolve style while a horizontal scene swipe tracks the finger. */
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
  // Reduced motion keeps the fade, drops the travelling mask edge.
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
  // A committed swipe keeps `progress` at its release value, so the sweep
  // keyframe resumes the dissolve right where the finger left off.
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
  // Gesture released below the commit threshold → `justSwiped` stays false
  // and no index change follows: play the wipe backwards so the segment
  // re-forms instead of snapping back to full opacity.
  if (dragging || sceneSwipe.justSwiped || sceneSwipe.progress === 0) return
  const i = props.currentSceneIndex
  const dir = sceneSwipe.dir
  sweepBack.value = {
    idx: i,
    dir,
    fromPos: dragMaskPos(dir, sceneSwipe.progress),
    fromOp: dragOpacity(sceneSwipe.progress),
  }
  if (sweepBackTimer) clearTimeout(sweepBackTimer)
  sweepBackTimer = setTimeout(() => { sweepBack.value = null }, 320)
})
</script>

<style scoped>
.glass-pill-scene-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  /* Let the flex item shrink below its content width so the pill scrolls
     internally instead of overflowing across the header's right-side
     buttons when many scenes are present. */
  min-width: 0;
  max-width: 100%;
}

.pill-container {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  -webkit-backdrop-filter: blur(var(--glass-blur, 14px));
  backdrop-filter: blur(var(--glass-blur, 14px));
  -webkit-backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 18px;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 4px;
}

.pill-container::-webkit-scrollbar { display: none; }

/* Edit mode: the ACTIVE segment reserves a badge-width lane at its right
   edge so its pencil sits in its own space instead of covering the label.
   Only the active pill gets a pencil (and the widening) — one badge per
   pill pushed the row into horizontal scroll on the narrow 1024px header,
   and a header-height badge strip was rejected because it pushes the
   dashboard grid down and clips the bottom row on a 600px-tall panel. */
.pill-container.pill-edit .segment.is-active {
  /* Badge capped at 44px so it stays inside a ~48-60px pill (the uncapped
     touch-scaled 55px badge spilled past the pill edges). */
  --pill-badge: clamp(34px, calc(44px * var(--touch-multiplier, 1)), 44px);
  min-width: calc(96px + var(--pill-badge) + 14px);
  padding-right: calc(var(--pill-badge) + 12px);
}

.glider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  background: #1f6fd1;
  box-shadow: 0 4px 12px rgba(31, 111, 209, 0.45);
  border-radius: 14px;
  z-index: 1;
  will-change: transform;
  pointer-events: none;
}

.segment {
  -webkit-user-select: none;
  user-select: none;
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  /* Generous touch target — these are tapped often on touch panels. */
  min-height: 48px;
  min-width: 96px;
  padding: 10px 14px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, rgba(255,255,255,0.7));
  font-size: clamp(14px, 1vw + 8px, 18px);
  font-weight: 500;
  cursor: pointer;
  border-radius: 14px;
  transition: color 0.2s ease;
  white-space: nowrap;
}

.segment:active {
  transform: scale(0.96);
  transition: transform 80ms ease;
}

.segment.is-active {
  color: var(--color-text, #fff);
}

.segment-icon {
  flex-shrink: 0;
  font-size: 1.1em;
}

.segment-label {
  max-width: 112px;
  /* min-width:0 lets the flex item shrink below its content width so the
     edit-mode badge lane can reclaim space without the label overflowing
     into it — ellipsis kicks in instead. */
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* The badge now lives inside its own .segment (positioned by `right`), so the
   old overlay layer is gone — see the template note. */


.scene-edit-badge {
  position: absolute;
  /* Inside the segment's reserved padding lane, vertically centered on the
     pill — never overlaps the icon/label. */
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  /* Real touch target; --pill-badge caps at 44px so it stays inside the
     pill (set on .segment.is-active in edit mode; 44px fallback otherwise). */
  width: var(--pill-badge, 44px);
  height: var(--pill-badge, 44px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 2px solid #fff;
  background: #1f6fd1;
  color: #fff;
  font-size: calc(0.75rem * min(var(--touch-multiplier, 1), 1.25));
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(8, 6, 30, 0.4);
  transition: transform 0.15s ease, background 0.15s ease;
}

.scene-edit-badge:hover {
  background: var(--color-primary-dark, #005fcc);
  transform: translateY(-50%) scale(1.08);
}

.scene-edit-badge:active {
  transform: translateY(-50%) scale(0.94);
}

.edit-btn.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  min-height: 48px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-secondary);
  border-radius: 14px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.edit-btn.add-btn:hover {
  border-color: #4aa3ff;
  color: #7dbcff;
  background: rgba(74, 163, 255, 0.16);
}

@media (max-width: 768px) {
  .segment-label {
    max-width: 84px;
  }
}

@media (max-width: 480px) {
  .segment-icon { display: none; }
  .segment { min-width: 64px; padding: 10px 10px; }
}

/* DL-033 — green "app is running" dot on the scene pill's top-right corner.
   pointer-events:none so it never eats the pill's click or the edit badge. */
.app-live-dot {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #30d158;
  box-shadow: 0 0 6px 1px rgba(48, 209, 88, 0.55);
  pointer-events: none;
  animation: app-live-pulse 2.4s ease-in-out infinite;
}

@keyframes app-live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

/* Agent waiting for input — a FILLED, pulsing segment says WHICH scene's
   agent wants a prompt while the user sits on another scene. Outlines
   alone were invisible on a 7" panel (DL-080 follow-up #3). */
.segment.agent-waiting {
  background: rgba(34, 197, 94, 0.16);
  box-shadow:
    inset 0 0 0 3px rgba(34, 197, 94, 0.95),
    0 0 14px rgba(34, 197, 94, 0.5);
  animation: segment-waiting-pulse 1.6s ease-in-out infinite;
}

@keyframes segment-waiting-pulse {
  0%, 100% {
    background: rgba(34, 197, 94, 0.16);
    box-shadow:
      inset 0 0 0 3px rgba(34, 197, 94, 0.95),
      0 0 12px rgba(34, 197, 94, 0.5);
  }
  50% {
    background: rgba(34, 197, 94, 0.38);
    box-shadow:
      inset 0 0 0 3px #86efac,
      0 0 26px rgba(34, 197, 94, 0.85),
      0 0 6px rgba(134, 239, 172, 0.7);
  }
}

.app-live-dot.agent-waiting-dot {
  width: 12px;
  height: 12px;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.9), 0 0 0 3px rgba(34, 197, 94, 0.35);
  animation: app-live-waiting-pulse 1.2s ease-in-out infinite;
}

@keyframes app-live-waiting-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.75; transform: scale(1.5); }
}

/* DL-082 — directional dissolve on the scene buttons. The mask gradient is
   250% wide: sweeping mask-position carries a soft transparent band across
   the segment. `next` (swipe-left / index forward) travels L→R, `prev`
   R→L. The outgoing segment dissolves out then re-forms in place as the
   now-inactive button — starting from `--sweep-from` so a committed swipe
   continues seamlessly from the drag-tracked position. */
.pill-container.wipe-next .segment.seg-sweep-out {
  animation: seg-wipe-out-next 0.55s var(--ease-io) both;
}
.pill-container.wipe-next .segment.seg-sweep-in {
  animation: seg-wipe-in-next 0.4s var(--ease-out) 0.05s both;
}
.pill-container.wipe-next .segment.seg-sweep-back {
  animation: seg-wipe-back-next 0.28s var(--ease-out) both;
}
.pill-container.wipe-prev .segment.seg-sweep-out {
  animation: seg-wipe-out-prev 0.55s var(--ease-io) both;
}
.pill-container.wipe-prev .segment.seg-sweep-in {
  animation: seg-wipe-in-prev 0.4s var(--ease-out) 0.05s both;
}
.pill-container.wipe-prev .segment.seg-sweep-back {
  animation: seg-wipe-back-prev 0.28s var(--ease-out) both;
}

/* next — wave travels L→R: out uses the transparent-left gradient
   (position 100%→0% dissolves the left edge first), the re-form and the
   incoming segment use the black-left gradient (same sweep reveals the
   left edge first). */
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

/* prev — wave travels R→L: mirrored gradients, position sweep 0%→100%. */
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
  .app-live-dot { animation: none; }
  .segment.agent-waiting { animation: none; }
  .app-live-dot.agent-waiting-dot { animation: none; }
  .segment.seg-sweep-out,
  .segment.seg-sweep-in,
  .segment.seg-sweep-back { animation: none; }
}
</style>
