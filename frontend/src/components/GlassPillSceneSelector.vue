<template>
  <div class="glass-pill-scene-selector">
    <!-- pill container -->
    <div role="radiogroup" aria-label="Scene selector" class="pill-container" :class="{ 'pill-edit': isEditMode }" ref="pillRef">
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
        :class="{ 'is-active': i === currentSceneIndex }"
        @click="selectScene(i)"
        @keydown="onKeyDown($event, i)"
      >
        <FontAwesomeIcon v-if="scene.icon" :icon="parseIcon(scene.icon)" class="segment-icon" />
        <span class="segment-label">{{ scene.name }}</span>
        <!-- Green dot when the scene's app is actually running — so a Claude
             scene pill means "buttons will reach a live session", not just
             "this scene exists". -->
        <span
          v-if="sceneAppIsLive(scene, appIntegrations)"
          class="app-live-dot"
          :title="`${scene.name}'s app is running`"
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
import { startAppDetection, sceneAppIsLive } from '@/services/appDetection'
import { useAppIntegrations } from '@/composables/useAppIntegrations'

const appIntegrations = useAppIntegrations()

// Poll once per mounted selector — startAppDetection is idempotent.
onMounted(startAppDetection)

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

@media (prefers-reduced-motion: reduce) {
  .app-live-dot { animation: none; }
}
</style>
