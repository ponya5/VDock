<template>
  <div 
    class="deck-grid" 
    :class="{ 'drag-over': isDragOver }"
    :style="gridStyle"
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
  >
    <DeckButton
      v-for="button in visibleButtons"
      :key="button.id"
      :button="button"
      :is-edit-mode="isEditMode"
      @click="handleButtonClick"
      @edit="handleButtonEdit"
      @delete="handleButtonDelete"
    />
    
    <!-- Button placeholders for empty slots -->
    <div
      v-for="placeholder in emptySlots"
      :key="`placeholder-${placeholder.row}-${placeholder.col}`"
      class="button-placeholder"
      :style="placeholderStyle"
      @click="handlePlaceholderClick(placeholder.row, placeholder.col)"
    >
      <FontAwesomeIcon :icon="['fas', 'plus']" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Button, Page } from '@/types'
import DeckButton from './DeckButton.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  page: Page
  isEditMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false
})

const emit = defineEmits<{
  buttonClick: [button: Button]
  buttonEdit: [button: Button]
  buttonDelete: [buttonId: string]
  swipeLeft: []
  swipeRight: []
  actionDrop: [action: any, position: { row: number; col: number }]
  placeholderClick: [position: { row: number; col: number }]
  buttonMove: [buttonId: string, newPosition: { row: number; col: number }]
}>()

const gridStyle = computed(() => {
  const { rows, cols } = props.page.grid_config
  return {
    display: 'grid',
    gridTemplateRows: `repeat(${rows}, 1fr)`,
    gridTemplateColumns: `repeat(${cols}, 1fr)`,
    gap: 'var(--spacing-sm)',
    width: '100%',
    height: '100%',
    padding: 'var(--spacing-md)'
  }
})

const visibleButtons = computed(() => {
  return props.page.buttons.filter(btn => btn.enabled)
})

const emptySlots = computed(() => {
  const { rows, cols } = props.page.grid_config
  const occupiedPositions = new Set()
  
  // Mark occupied positions
  visibleButtons.value.forEach(button => {
    const { row, col } = button.position
    occupiedPositions.add(`${row}-${col}`)
  })
  
  // Generate empty slots
  const slots = []
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      if (!occupiedPositions.has(`${row}-${col}`)) {
        slots.push({ row, col })
      }
    }
  }
  
  return slots
})

const placeholderStyle = computed(() => {
  const { rows, cols } = props.page.grid_config
  const buttonSize = Math.min(100 / Math.max(rows, cols), 80) // Dynamic sizing
  
  return {
    fontSize: `${buttonSize * 0.3}px`,
    minHeight: `${buttonSize}px`,
    minWidth: `${buttonSize}px`
  }
})

function handleButtonClick(button: Button) {
  emit('buttonClick', button)
}

function handleButtonEdit(button: Button) {
  emit('buttonEdit', button)
}

function handleButtonDelete(buttonId: string) {
  emit('buttonDelete', buttonId)
}

function handlePlaceholderClick(row: number, col: number) {
  if (props.isEditMode) {
    emit('placeholderClick', { row, col })
  }
}

// Touch gesture handling for page swiping
let touchStartX = 0
let touchStartY = 0
const isDragOver = ref(false)

function handleTouchStart(e: TouchEvent) {
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
}

function handleTouchEnd(e: TouchEvent) {
  if (!e.changedTouches.length) return
  
  const touchEndX = e.changedTouches[0].clientX
  const touchEndY = e.changedTouches[0].clientY
  
  const diffX = touchEndX - touchStartX
  const diffY = touchEndY - touchStartY
  
  // Only trigger if horizontal swipe is significant
  if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
    if (diffX > 0) {
      emit('swipeRight')
    } else {
      emit('swipeLeft')
    }
  }
}

// Drag and drop handlers
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'copy'
}

function handleDragEnter(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
  
  if (!props.isEditMode) return
  
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  // Calculate grid position
  const { rows, cols } = props.page.grid_config
  const cellWidth = rect.width / cols
  const cellHeight = rect.height / rows
  
  const col = Math.floor(x / cellWidth)
  const row = Math.floor(y / cellHeight)
  
  // Ensure position is within bounds
  if (row < 0 || row >= rows || col < 0 || col >= cols) return
  
  // Check for button drop first
  const buttonData = e.dataTransfer?.getData('application/vdock-button')
  if (buttonData) {
    try {
      const button = JSON.parse(buttonData)
      emit('buttonMove', button.id, { row, col })
      return
    } catch (error) {
      console.error('Error handling button drop:', error)
    }
  }
  
  // Check for action drop
  const actionData = e.dataTransfer?.getData('application/vdock-action')
  if (actionData) {
    try {
      const action = JSON.parse(actionData)
      emit('actionDrop', action, { row, col })
    } catch (error) {
      console.error('Error handling action drop:', error)
    }
  }
}
</script>

<style scoped>
.deck-grid {
  background-color: var(--color-background);
  user-select: none;
  touch-action: pan-y; /* Allow vertical scrolling but enable custom horizontal gestures */
  transition: all var(--transition-fast);
}

.deck-grid.drag-over {
  background-color: var(--color-primary-light);
  border: 2px dashed var(--color-primary);
}

.button-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-surface);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
  min-height: 60px;
  min-width: 60px;
}

.button-placeholder:hover {
  background-color: var(--color-surface-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: scale(1.05);
}

.button-placeholder:active {
  transform: scale(0.95);
}
</style>

