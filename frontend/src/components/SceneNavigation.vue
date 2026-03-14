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

.scene-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  outline: none;
  cursor: pointer;
  height: 44px;
  padding: 0 var(--spacing-lg);
  background: transparent;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
  font-size: clamp(0.75rem, 1vw + 0.5rem, 0.9rem);
  font-weight: 600;
  color: var(--color-text-secondary);
  white-space: nowrap;
  min-width: 0;
}

.scene-tab:hover {
  border-color: rgba(255, 255, 255, 0.3);
  color: var(--color-text);
  background: rgba(255, 255, 255, 0.05);
}

.scene-tab.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(52, 152, 219, 0.12);
}

.scene-tab:active {
  transform: scale(0.96);
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
  background: transparent;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
  color: var(--color-text-secondary);
}

.add-scene-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(52, 152, 219, 0.12);
}

.add-scene-btn:active {
  transform: scale(0.94);
}

.scene-edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
  background: transparent;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  color: var(--color-text-secondary);
}

.scene-edit-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(52, 152, 219, 0.12);
}

.scene-edit-btn:active {
  transform: scale(0.94);
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
