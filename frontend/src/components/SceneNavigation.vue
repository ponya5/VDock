<template>
  <div class="scene-nav-wrapper">
    <!-- Glass radio group pill -->
    <div
      class="glass-radio-group"
      role="radiogroup"
      :aria-label="'Scene selector'"
      :style="{ '--scene-count': scenes.length }"
    >
      <!-- Animated glider -->
      <div class="glass-glider" :style="gliderStyle" aria-hidden="true"></div>

      <template v-for="(scene, index) in scenes" :key="scene.id">
        <input
          type="radio"
          :id="`scene-radio-${scene.id}`"
          :name="`scene-group-${groupId}`"
          :value="index"
          :checked="index === currentSceneIndex"
          class="scene-radio-input"
          @change="setScene(index)"
        />
        <label
          :for="`scene-radio-${scene.id}`"
          class="scene-radio-label"
          :class="{ active: index === currentSceneIndex }"
        >
          <FontAwesomeIcon v-if="scene.icon" :icon="scene.icon" class="scene-label-icon" />
          <span class="scene-label-text">{{ scene.name }}</span>

          <!-- Edit button overlaid on label in edit mode -->
          <button
            v-if="isEditMode"
            class="scene-inline-edit"
            @click.prevent.stop="editScene(scene)"
            :title="`Edit ${scene.name}`"
            tabindex="-1"
          >
            <FontAwesomeIcon :icon="['fas', 'edit']" />
          </button>
        </label>
      </template>
    </div>

    <!-- Add scene button — outside the pill -->
    <button
      v-if="isEditMode"
      class="add-scene-btn"
      @click="addScene"
      title="Add Scene"
    >
      <FontAwesomeIcon :icon="['fas', 'plus']" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Scene } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  scenes: Scene[]
  currentSceneIndex: number
  isEditMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false
})

const emit = defineEmits<{
  setScene: [index: number]
  addScene: []
  editScene: [scene: Scene]
}>()

// Unique group id to avoid radio name collisions if component is mounted multiple times
const groupId = Math.random().toString(36).slice(2, 8)

// Disable spring animation briefly when scene count changes (avoids glider flying across)
const disableAnimation = ref(false)
watch(
  () => props.scenes.length,
  () => {
    disableAnimation.value = true
    setTimeout(() => { disableAnimation.value = false }, 50)
  }
)

const gliderStyle = computed(() => {
  const n = props.scenes.length || 1
  return {
    width: `calc(100% / ${n})`,
    transform: `translateX(${props.currentSceneIndex * 100}%)`,
    transition: disableAnimation.value ? 'none' : 'transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56)',
  }
})

function setScene(index: number) {
  emit('setScene', index)
}

function addScene() {
  emit('addScene')
}

function editScene(scene: Scene) {
  emit('editScene', scene)
}
</script>

<style scoped>
/* ── wrapper ── */
.scene-nav-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── glass pill container ── */
.glass-radio-group {
  position: relative;
  display: flex;
  align-items: stretch;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  overflow: hidden;
  min-height: 44px;
}

/* ── hidden radio inputs ── */
.scene-radio-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

/* ── labels ── */
.scene-radio-label {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-width: 72px;
  padding: 0.55rem 1.2rem;
  font-size: clamp(0.65rem, 0.7vw + 0.45rem, 0.85rem);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  z-index: 1;
  transition: color 0.25s ease;
  /* ensure touch target height */
  min-height: 44px;
}

.scene-radio-label.active {
  color: #fff;
}

.scene-radio-label:hover:not(.active) {
  color: rgba(255, 255, 255, 0.8);
}

.scene-label-icon {
  font-size: 0.8em;
  flex-shrink: 0;
}

.scene-label-text {
  /* truncate long names */
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── inline edit button ── */
.scene-inline-edit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-left: 0.2rem;
  padding: 0;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 0.6rem;
  flex-shrink: 0;
  transition: background 0.15s ease, color 0.15s ease;
}

.scene-inline-edit:hover {
  background: rgba(52, 152, 219, 0.35);
  color: #fff;
  border-color: rgba(52, 152, 219, 0.6);
}

/* ── animated glider ── */
.glass-glider {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: calc(1rem - 1px);
  background: linear-gradient(
    135deg,
    rgba(52, 152, 219, 0.35),
    rgba(52, 152, 219, 0.7)
  );
  box-shadow:
    0 0 18px rgba(52, 152, 219, 0.45),
    inset 0 0 10px rgba(255, 255, 255, 0.15);
  z-index: 0;
  pointer-events: none;
}

/* ── add scene button ── */
.add-scene-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: clamp(0.75rem, 1vw + 0.4rem, 0.95rem);
  transition: all 0.2s ease;
}

.add-scene-btn:hover {
  border-color: rgba(52, 152, 219, 0.6);
  color: #3498db;
  background: rgba(52, 152, 219, 0.12);
}

.add-scene-btn:active {
  transform: scale(0.92);
}

/* ── responsive ── */
@media (max-width: 480px) {
  .scene-radio-label {
    min-width: 56px;
    padding: 0.5rem 0.8rem;
  }

  .scene-label-text {
    max-width: 60px;
  }
}
</style>
