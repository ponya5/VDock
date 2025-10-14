<template>
  <div class="docked-sidebar" :class="{ 'is-edit-mode': isEditMode }" :style="{ width: sidebarWidth }">
    <div class="sidebar-header">
      <h3>Docked Buttons</h3>
      <button 
        v-if="isEditMode" 
        class="add-btn" 
        @click="handleAddButton"
        title="Add Docked Button"
      >
        <FontAwesomeIcon :icon="['fas', 'plus']" />
      </button>
    </div>

    <div 
      class="sidebar-grid"
      :style="gridStyle"
    >
      <!-- Render grid slots -->
      <template v-for="row in gridRows" :key="`row-${row}`">
        <template v-for="col in gridCols" :key="`slot-${row}-${col}`">
          <!-- Existing button -->
          <DeckButton
            v-if="getButtonAt(row - 1, col - 1)"
            :button="getButtonAt(row - 1, col - 1)!"
            :is-edit-mode="isEditMode"
            :show-labels="showLabels"
            :show-tooltips="showTooltips"
            @click="handleButtonClick"
            @edit="handleButtonEdit"
            @copy="handleButtonCopy"
            @delete="handleButtonDelete"
          />
          
          <!-- Empty slot placeholder in edit mode -->
          <div
            v-else-if="isEditMode"
            class="docked-placeholder"
            @click="handlePlaceholderClick(row - 1, col - 1)"
            @dragover="handlePlaceholderDragOver"
            @drop="handlePlaceholderDrop($event, row - 1, col - 1)"
            @dragenter="handlePlaceholderDragEnter($event, row - 1, col - 1)"
            @dragleave="handlePlaceholderDragLeave($event, row - 1, col - 1)"
            :class="{ 'drag-over': isDragOverSlot(row - 1, col - 1) }"
          >
            <FontAwesomeIcon :icon="['fas', 'plus']" class="placeholder-icon" />
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Button } from '@/types'
import DeckButton from './DeckButton.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  dockedButtons: Button[]
  gridRows: number
  isEditMode?: boolean
  showLabels?: boolean
  showTooltips?: boolean
  buttonSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false,
  showLabels: true,
  showTooltips: true,
  buttonSize: 1.0
})

const emit = defineEmits<{
  buttonClick: [button: Button]
  buttonEdit: [button: Button]
  buttonCopy: [button: Button]
  buttonDelete: [buttonId: string]
  buttonDrop: [event: DragEvent, position: { row: number; col: number }]
  addButton: [position: { row: number; col: number }]
  placeholderClick: [position: { row: number; col: number }]
}>()

const gridCols = 1 // Docked sidebar is always 1 column
const dragOverSlot = ref<{ row: number; col: number } | null>(null)

// Calculate sidebar width based on button size
const sidebarWidth = computed(() => {
  // Match 5x5 grid button size - much smaller to avoid scrolling
  // For a 5x5 grid, buttons are typically 100-120px
  const baseButtonWidth = 110
  const scaledButtonWidth = baseButtonWidth * props.buttonSize
  const padding = 32 // Total horizontal padding (16px each side)
  const editModeExtra = props.isEditMode ? 20 : 0
  return `${scaledButtonWidth + padding + editModeExtra}px`
})

const gridStyle = computed(() => {
  // Set explicit cell heights to match 5x5 grid button size
  // Smaller buttons to prevent scrolling and match grid layout
  const baseCellHeight = 110 * props.buttonSize
  
  return {
    display: 'grid',
    gridTemplateColumns: '1fr',
    gridTemplateRows: `repeat(${props.gridRows}, ${baseCellHeight}px)`,
    gap: '8px',
    padding: '16px',
    height: '100%',
    overflow: 'auto'
  }
})

function getButtonAt(row: number, col: number): Button | undefined {
  return props.dockedButtons.find(
    b => b.position.row === row && b.position.col === col
  )
}

function isDragOverSlot(row: number, col: number): boolean {
  return dragOverSlot.value?.row === row && dragOverSlot.value?.col === col
}

function handleButtonClick(button: Button) {
  emit('buttonClick', button)
}

function handleButtonEdit(button: Button) {
  emit('buttonEdit', button)
}

function handleButtonCopy(button: Button) {
  emit('buttonCopy', button)
}

function handleButtonDelete(buttonId: string) {
  emit('buttonDelete', buttonId)
}

function handlePlaceholderDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

function handlePlaceholderDragEnter(event: DragEvent, row: number, col: number) {
  event.preventDefault()
  dragOverSlot.value = { row, col }
}

function handlePlaceholderDragLeave(event: DragEvent, row: number, col: number) {
  event.preventDefault()
  // Only clear if we're leaving the current drag-over slot
  if (dragOverSlot.value?.row === row && dragOverSlot.value?.col === col) {
    dragOverSlot.value = null
  }
}

function handlePlaceholderDrop(event: DragEvent, row: number, col: number) {
  console.log('DockedSidebar: drop at', row, col)
  event.preventDefault()
  event.stopPropagation()
  dragOverSlot.value = null
  
  emit('buttonDrop', event, { row, col })
}

function handleAddButton() {
  // Find first empty slot
  for (let row = 0; row < props.gridRows; row++) {
    for (let col = 0; col < gridCols; col++) {
      if (!getButtonAt(row, col)) {
        emit('addButton', { row, col })
        return
      }
    }
  }
}

function handlePlaceholderClick(row: number, col: number) {
  emit('placeholderClick', { row, col })
}
</script>

<style scoped>
.docked-sidebar {
  height: 100%;
  background-color: var(--color-surface-solid);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: all var(--transition-normal);
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface);
}

.sidebar-header h3 {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background-color: var(--color-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: white;
  font-size: 0.75rem;
}

.add-btn:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.sidebar-grid {
  flex: 1;
  overflow-y: auto;
}

.docked-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-surface);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 60px;
}

.docked-placeholder:hover {
  background-color: var(--color-surface-hover);
  border-color: var(--color-primary);
}

.docked-placeholder.drag-over {
  background-color: var(--color-primary-light);
  border-color: var(--color-primary);
  border-style: solid;
  transform: scale(1.05);
}

.placeholder-icon {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  opacity: 0.5;
}

.docked-placeholder.drag-over .placeholder-icon {
  color: var(--color-primary);
  opacity: 1;
}
</style>
