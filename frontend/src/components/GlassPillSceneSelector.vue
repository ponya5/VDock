<template>
  <div class="glass-pill-scene-selector">
    <!-- pill container -->
    <div role="radiogroup" aria-label="Scene selector" class="pill-container" ref="pillRef">
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
      </button>

      <!-- One edit badge per scene, anchored to that scene's own segment so
           it's unambiguous which pencil edits which scene (previously these
           were a detached row of identical icons with no visual link to the
           scene they belonged to). -->
      <div v-if="isEditMode" class="edit-badges">
        <button
          v-for="(scene, i) in scenes"
          :key="`edit-${scene.id}`"
          class="scene-edit-badge"
          :style="{ left: `${(i + 1) * segmentPercent}%` }"
          @click.stop="$emit('edit-scene', scene)"
          :aria-label="`Edit ${scene.name}`"
          title="Edit scene"
        >
          <FontAwesomeIcon :icon="['fas', 'pen']" />
        </button>
      </div>
    </div>

    <button v-if="isEditMode" class="edit-btn add-btn" @click="$emit('add-scene')" aria-label="Add scene">
      <FontAwesomeIcon :icon="['fas', 'plus']" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'

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
}

.pill-container {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--glass-bg, rgba(0,0,0,0.25));
  backdrop-filter: blur(var(--glass-blur, 14px));
  -webkit-backdrop-filter: blur(var(--glass-blur, 14px));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  border-radius: 1rem;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 4px;
  /* fallback for non-dark themes */
  --fallback-bg: var(--color-surface, rgba(255,255,255,0.1));
}

.pill-container::-webkit-scrollbar { display: none; }

.glider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  background: linear-gradient(135deg, rgba(52,152,219,0.35), rgba(52,152,219,0.7));
  box-shadow: 0 0 18px rgba(52,152,219,0.45), inset 0 0 10px rgba(255,255,255,0.15);
  border-radius: calc(1rem - 4px);
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
  /* Bigger touch target than a typical tab bar — these are tapped often on
     touch panels, so err on the side of generous rather than compact. */
  min-height: 56px;
  min-width: 96px;
  padding: 10px 18px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, rgba(255,255,255,0.7));
  font-size: clamp(0.78rem, 0.9vw + 0.5rem, 1rem);
  font-weight: 600;
  cursor: pointer;
  border-radius: calc(1rem - 4px);
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-badges {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
}

.scene-edit-badge {
  position: absolute;
  /* Kept inside the pill: overflow-x:auto on .pill-container also clips
     vertically, so a negative top cut the badge in half. */
  top: 2px;
  transform: translateX(-100%);
  width: 34px;
  height: 34px;
  margin-left: -4px;
  /* Real touch target in edit mode; capped so it can't swallow the whole
     segment on tablet mode. */
  width: max(34px, calc(44px * min(var(--touch-multiplier, 1), 1.25)));
  height: max(34px, calc(44px * min(var(--touch-multiplier, 1), 1.25)));
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 2px solid rgba(0, 0, 0, 0.35);
  background: var(--color-primary, #007aff);
  color: #fff;
  font-size: calc(0.75rem * min(var(--touch-multiplier, 1), 1.25));
  cursor: pointer;
  pointer-events: auto;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  transition: transform 0.15s ease, background 0.15s ease;
}

.scene-edit-badge:hover {
  background: var(--color-primary-dark, #005fcc);
  transform: translateX(-100%) scale(1.08);
}

.scene-edit-badge:active {
  transform: translateX(-100%) scale(0.94);
}

.edit-btn.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  min-height: 48px;
  flex-shrink: 0;
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  background: var(--glass-bg, rgba(0,0,0,0.15));
  color: var(--color-text-secondary);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.edit-btn.add-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
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
</style>
