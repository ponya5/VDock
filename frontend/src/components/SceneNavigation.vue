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
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--spacing-xs);
  border: 1px solid var(--color-border);
}

.scene-tab-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.scene-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
  font-size: 1rem;
  font-weight: 500;
  white-space: nowrap;
  min-width: 0;
  min-height: 44px;
}

.scene-tab:hover {
  background-color: var(--color-surface-hover);
  color: var(--color-text);
}

.scene-tab.active {
  color: white;
  box-shadow: var(--shadow-sm);
  opacity: 1;
}

.scene-tab.active:hover {
  opacity: 0.9;
}

.scene-icon {
  font-size: 1.1rem;
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
  width: 40px;
  height: 40px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
  font-size: 1rem;
}

.add-scene-btn:hover {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.scene-edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  opacity: 0.8;
}

.scene-edit-btn:hover {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  opacity: 1;
}

/* Responsive design */
@media (max-width: 768px) {
  .scene-name {
    max-width: 80px;
  }
  
  .scene-tab {
    padding: var(--spacing-xs) var(--spacing-sm);
  }
}
</style>
