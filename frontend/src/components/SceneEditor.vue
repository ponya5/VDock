<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal scene-editor">
      <div class="modal-header">
        <h2>{{ isEditing ? 'Edit Scene' : 'Create Scene' }}</h2>
        <button class="close-btn" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>Scene Name</label>
          <input 
            v-model="editedScene.name" 
            type="text" 
            class="input" 
            placeholder="Enter scene name"
            maxlength="50"
          />
        </div>

        <div class="form-group">
          <label>Scene Icon (Optional)</label>
          <div class="icon-input-group">
            <input 
              v-model="editedScene.icon" 
              type="text" 
              class="input" 
              placeholder="fas fa-home"
              style="flex: 1"
            />
            <button class="btn btn-secondary" @click="showIconPicker = true">
              <FontAwesomeIcon :icon="['fas', 'icons']" /> Pick Icon
            </button>
          </div>
          <p class="form-help">FontAwesome icon class (e.g., fas fa-home)</p>
        </div>

        <div class="form-group">
          <label>Scene Color</label>
          <div class="color-picker-section">
            <div class="current-color" :style="{ backgroundColor: editedScene.color || '#3498db' }">
              <input 
                v-model="editedScene.color" 
                type="color" 
                class="color-input"
                @input="updateSceneColor"
              />
            </div>
            <div class="color-palette">
              <div 
                v-for="color in colorPalette" 
                :key="color"
                class="color-swatch"
                :class="{ active: editedScene.color === color }"
                :style="{ backgroundColor: color }"
                @click="selectColor(color)"
                :title="color"
              ></div>
            </div>
          </div>
        </div>

        <div v-if="isEditing" class="form-group">
          <label class="checkbox-label">
            <input v-model="editedScene.isActive" type="checkbox" />
            <span>Set as Active Scene</span>
          </label>
        </div>
      </div>

      <div class="modal-footer">
        <button 
          v-if="isEditing" 
          class="btn btn-danger" 
          @click="deleteScene"
        >
          <FontAwesomeIcon :icon="['fas', 'trash']" /> Delete Scene
        </button>
        <div class="footer-spacer"></div>
        <button class="btn btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="handleSave">Save</button>
      </div>
    </div>

    <IconPicker 
      v-if="showIconPicker" 
      @select="handleIconSelect" 
      @close="showIconPicker = false" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Scene } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import IconPicker from './IconPicker.vue'

interface Props {
  scene?: Scene
  isEditing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditing: false
})

const emit = defineEmits<{
  save: [scene: Scene]
  delete: [sceneId: string]
  close: []
}>()

const showIconPicker = ref(false)

// Initialize edited scene
const editedScene = ref<Scene>(props.scene ? { ...props.scene } : {
  id: `scene_${Date.now()}`,
  name: 'New Scene',
  icon: '',
  color: '#3498db',
  pages: [],
  isActive: false
})

// Color palette for scene colors
const colorPalette = ref([
  '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c',
  '#34495e', '#e67e22', '#95a5a6', '#f1c40f', '#e91e63', '#673ab7',
  '#795548', '#607d8b', '#ff5722', '#4caf50', '#2196f3', '#ff9800',
  '#9c27b0', '#00bcd4', '#8bc34a', '#ffc107', '#ff6b6b', '#4ecdc4',
  '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'
])

function selectColor(color: string) {
  editedScene.value.color = color
}

function updateSceneColor(event: Event) {
  const target = event.target as HTMLInputElement
  editedScene.value.color = target.value
}

function handleIconSelect(icon: string) {
  editedScene.value.icon = icon
  showIconPicker.value = false
}

function handleSave() {
  // Validate scene name
  if (!editedScene.value.name.trim()) {
    alert('Please enter a scene name')
    return
  }

  emit('save', editedScene.value)
}

function deleteScene() {
  if (confirm(`Are you sure you want to delete "${editedScene.value.name}"? This action cannot be undone.`)) {
    emit('delete', editedScene.value.id)
  }
}
</script>

<style scoped>
.scene-editor {
  width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.footer-spacer {
  flex: 1;
}

.form-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  margin-bottom: 0;
}

.icon-input-group {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

/* Color Picker Styles */
.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.current-color {
  width: 60px;
  height: 40px;
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.color-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0;
}

.color-palette {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--spacing-xs);
  max-width: 300px;
}

.color-swatch {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.color-swatch:hover {
  transform: scale(1.1);
  border-color: var(--color-primary);
}

.color-swatch.active {
  border-color: var(--color-primary);
  border-width: 3px;
  box-shadow: 0 0 0 2px var(--color-primary-light);
}
</style>
