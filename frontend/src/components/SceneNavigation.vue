<template>
  <div class="scene-navigation">
    <div class="scene-tabs">
      <div
        v-for="(scene, index) in scenes"
        :key="scene.id"
        class="scene-tab-container"
      >
        <button
          :class="['scene-tab', { active: index === currentSceneIndex }]"
          :style="{ 
            backgroundColor: scene.color || '#3498db',
            transform: `scale(${scene.buttonSize || 1.0})`
          }"
          @click="setScene(index)"
          :title="scene.name"
        >
          <FontAwesomeIcon 
            v-if="scene.icon" 
            :icon="scene.icon" 
            class="scene-icon"
          />
          <span class="scene-name">{{ scene.name }}</span>
        </button>
        
        <button
          v-if="isEditMode"
          class="scene-edit-btn"
          @click="editScene(scene)"
          :title="`Edit ${scene.name}`"
        >
          <FontAwesomeIcon :icon="['fas', 'edit']" />
        </button>
      </div>
      
      <button 
        v-if="isEditMode"
        class="add-scene-btn"
        @click="addScene"
        title="Add Scene"
      >
        <FontAwesomeIcon :icon="['fas', 'plus']" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Scene } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDashboardStore } from '@/stores/dashboard'

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

const dashboardStore = useDashboardStore()

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
.scene-navigation {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.scene-tabs {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs);
}

.scene-tab-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* Uiverse lenfear23 style */
.scene-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  outline: none;
  cursor: pointer;
  height: 44px;
  padding: 0 var(--spacing-lg);
  background-image: linear-gradient(to top, #D8D9DB 0%, #fff 80%, #FDFDFD 100%);
  border-radius: 30px;
  border: 1px solid #8F9092;
  transition: all 0.2s ease;
  font-size: clamp(0.75rem, 1vw + 0.5rem, 0.9rem);
  font-weight: 600;
  color: #606060;
  text-shadow: 0 1px #fff;
  white-space: nowrap;
  min-width: 0;
}

.scene-tab:hover {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 3px 3px #CECFD1;
}

.scene-tab:active,
.scene-tab.active {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 5px 3px #999,
    inset 0 0 30px #aaa;
  color: #333;
}

.scene-icon {
  font-size: clamp(0.75rem, 1vw + 0.5rem, 0.9rem);
  flex-shrink: 0;
}

.scene-name {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.add-scene-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  cursor: pointer;
  width: 44px;
  height: 44px;
  background-image: linear-gradient(to top, #D8D9DB 0%, #fff 80%, #FDFDFD 100%);
  border-radius: 30px;
  border: 1px solid #8F9092;
  transition: all 0.2s ease;
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
  color: #606060;
}

.add-scene-btn:hover {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 3px 3px #CECFD1;
}

.add-scene-btn:active {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 5px 3px #999,
    inset 0 0 30px #aaa;
}

.scene-edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
  background-image: linear-gradient(to top, #D8D9DB 0%, #fff 80%, #FDFDFD 100%);
  border-radius: 30px;
  border: 1px solid #8F9092;
  transition: all 0.2s ease;
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  color: #606060;
}

.scene-edit-btn:hover {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 3px 3px #CECFD1;
}

.scene-edit-btn:active {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 5px 3px #999,
    inset 0 0 30px #aaa;
}

@media (max-width: 768px) {
  .scene-name {
    max-width: 80px;
  }

  .scene-tab {
    padding: 0 var(--spacing-sm);
  }
}
</style>
