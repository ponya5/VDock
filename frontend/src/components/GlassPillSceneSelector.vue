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

      <!-- edit controls -->
      <div v-if="isEditMode" class="edit-controls">
        <button class="edit-btn add-btn" @click="$emit('add-scene')" aria-label="Add scene">
          <FontAwesomeIcon :icon="['fas', 'plus']" />
        </button>
        <button
          v-for="(scene, i) in scenes"
          :key="`edit-${scene.id}`"
          class="edit-btn per-scene-btn"
          @click.stop="$emit('edit-scene', scene)"
          :aria-label="`Edit ${scene.name}`"
        >
          <FontAwesomeIcon :icon="['fas', 'pen']" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'
import { vibrate } from '@/utils/haptics'
import { useDashboardStore } from '@/stores/dashboard'

interface Props {
  scenes: Scene[]
  currentSceneIndex: number
  isEditMode: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'scene-change': [index: number]
  'add-scene': []
  'edit-scene': [scene: Scene]
}>()

const dashboardStore = useDashboardStore()
const pillRef = ref<HTMLElement | null>(null)
const segmentRefs = ref<HTMLElement[]>([])
const disableAnimation = ref(false)
const focusedIndex = ref(0)

const segmentWidth = computed(() => `${100 / Math.max(props.scenes.length, 1)}%`)

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
  dashboardStore.setScene(index)
  emit('scene-change', index)
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
  gap: 6px;
  min-height: 44px;
  min-width: 80px;
  padding: 6px 14px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, rgba(255,255,255,0.7));
  font-size: clamp(0.65rem, 0.8vw + 0.4rem, 0.85rem);
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

.segment-icon { flex-shrink: 0; }

.segment-label {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-controls {
  display: flex;
  gap: 4px;
  margin-left: 4px;
  flex-shrink: 0;
}

.edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  background: var(--glass-bg, rgba(0,0,0,0.15));
  color: var(--color-text-secondary);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.edit-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .segment-label {
    max-width: 72px;
  }
}

@media (max-width: 480px) {
  .segment-icon { display: none; }
  .segment { min-width: 56px; padding: 6px 8px; }
}
</style>
