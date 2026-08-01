<template>
  <footer class="deck-footer" :class="{ 'edit-mode': isEditMode }">
    <!-- Left Side: Page Dots -->
    <div class="footer-left">
      <div v-if="totalPages > 1" class="page-dots">
        <button
          v-for="p in totalPages"
          :key="p"
          class="page-dot touch-target"
          :class="{ active: currentPageIndex === p - 1 }"
          @click="emit('setPage', p - 1)"
          :aria-label="`Go to page ${p}`"
        />
      </div>
    </div>

    <!-- Edit Mode controls (displayed in center during edit mode) -->
    <div v-if="isEditMode" class="footer-edit-section">
      <!-- Grid size controls -->
      <div class="grid-size-controls">
        <label>Grid:</label>
        <input
          :value="gridRows"
          @input="emit('updateRows', parseInt(($event.target as HTMLInputElement).value))"
          type="number"
          min="1"
          max="10"
          class="grid-input"
          title="Rows"
        />
        <span>×</span>
        <input
          :value="gridCols"
          @input="emit('updateCols', parseInt(($event.target as HTMLInputElement).value))"
          type="number"
          min="1"
          max="10"
          class="grid-input"
          title="Columns"
        />
      </div>

      <!-- Page actions -->
      <button class="btn btn-primary btn-sm touch-target" @click="emit('addPage')">
        <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Page
      </button>
      <button
        class="btn btn-danger btn-sm touch-target"
        @click="emit('deletePage')"
        :disabled="totalPages <= 1"
      >
        <FontAwesomeIcon :icon="['fas', 'trash']" /> Delete Page
      </button>
      <button class="btn btn-success btn-sm touch-target" @click="emit('saveProfile')">
        <FontAwesomeIcon :icon="['fas', 'save']" /> Save Profile
      </button>
    </div>

    <!-- Right Side: Scene Pills -->
    <div class="footer-right">
      <div v-if="scenes.length > 0" class="scene-pills">
        <button
          v-for="(scene, idx) in scenes"
          :key="scene.id"
          class="scene-pill touch-target"
          :class="{ active: currentSceneIndex === idx }"
          @click="emit('setScene', idx)"
        >
          <FontAwesomeIcon v-if="scene.icon" :icon="scene.icon.split(':')" class="scene-pill-icon" />
          <span>{{ scene.name }}</span>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'

interface Props {
  isEditMode: boolean
  totalPages: number
  currentPageIndex: number
  gridRows: number
  gridCols: number
  scenes: Scene[]
  currentSceneIndex: number
}

defineProps<Props>()
const emit = defineEmits<{
  setPage: [index: number]
  setScene: [index: number]
  addPage: []
  deletePage: []
  saveProfile: []
  updateRows: [rows: number]
  updateCols: [cols: number]
}>()
</script>

<style scoped>
.deck-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 52px;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: 0 var(--spacing-md);
  box-sizing: border-box;
  z-index: 90;
}

.footer-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.page-dots {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--color-border);
  border: none;
  cursor: pointer;
  padding: 17px; /* Makes it 44x44px touch target */
  background-clip: content-box;
  box-sizing: content-box;
  transition: all 0.2s var(--ease-out);
}

.page-dot.active {
  background-color: var(--color-primary);
  transform: scale(1.2);
}

.footer-edit-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 2;
  justify-content: center;
}

.grid-size-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.grid-input {
  width: 44px;
  height: 32px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  text-align: center;
  font-family: inherit;
  font-size: 0.9rem;
}

.footer-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
}

.scene-pills {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.scene-pill {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  padding: 0 var(--spacing-sm);
  min-height: 32px;
  min-width: 44px;
}

.scene-pill:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
}

.scene-pill.active {
  background-color: var(--color-primary);
  color: #ffffff;
  border-color: var(--color-primary);
}

.scene-pill-icon {
  font-size: 0.85rem;
}

.btn-sm {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
