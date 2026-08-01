<template>
  <div 
    class="deck-grid" 
    ref="gridRef"
    :class="{ 'drag-over': isDragOver }"
    :style="gridStyle"
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
      :show-labels="showLabels"
      :show-tooltips="showTooltips"
      :compact="compact"
      :grid-index="button.position.row * renderedPage.grid_config.cols + button.position.col"
      :class="cellClasses[`${button.position.row}-${button.position.col}`]"
      @click="handleButtonClick"
      @edit="handleButtonEdit"
      @copy="handleButtonCopy"
      @delete="handleButtonDelete"
      @double-tap="handleButtonDoubleTap"
      @long-press="handleButtonLongPress"
    />
    
    <!-- Button placeholders for empty slots - only show in edit mode or when receiving long-press -->
    <div
      v-for="placeholder in emptySlots"
      :key="`placeholder-${placeholder.row}-${placeholder.col}`"
      class="button-placeholder"
      :class="[
        { 
          'is-edit-mode': isEditMode,
          'is-highlighted': highlightedSlot?.row === placeholder.row && highlightedSlot?.col === placeholder.col
        },
        cellClasses[`${placeholder.row}-${placeholder.col}`]
      ]"
      :style="placeholderStyle"
      @click="handlePlaceholderClick(placeholder.row, placeholder.col)"
      @touchstart="handlePlaceholderTouchStart(placeholder.row, placeholder.col)"
      @touchend="handlePlaceholderTouchEnd(placeholder.row, placeholder.col)"
      @mousedown="handlePlaceholderTouchStart(placeholder.row, placeholder.col)"
      @mouseup="handlePlaceholderTouchEnd(placeholder.row, placeholder.col)"
      @mouseleave="handlePlaceholderTouchEnd(placeholder.row, placeholder.col)"
      @dragover="handlePlaceholderDragOver"
      @dragenter="(e) => handlePlaceholderDragEnter(e, placeholder)"
      @dragleave="(e) => handlePlaceholderDragLeave(e, placeholder)"
    >
      <FontAwesomeIcon :icon="['fas', 'plus']" />
    </div>

    <!-- Ambient Deck Overlay -->
    <DeckOverlay
      v-if="dashboardStore.currentScene?.overlay_style && dashboardStore.currentScene.overlay_style !== 'none'"
      :active="true"
      :style="dashboardStore.currentScene.overlay_style"
      :mode="dashboardStore.currentScene.overlay_mode || 'keys'"
      :rows="renderedPage.grid_config.rows"
      :cols="renderedPage.grid_config.cols"
      :buttons="visibleButtons"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Button, Page } from '@/types'
import DeckButton from './DeckButton.vue'
import DeckOverlay from './DeckOverlay.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSwipe, usePinch, useLongPress } from '@/composables/useGestures'
import { useParallax } from '@/composables/useParallax'
import { useGridTransition } from '@/composables/useGridTransition'
import { useDashboardStore } from '@/stores/dashboard'

interface Props {
  page: Page
  isEditMode?: boolean
  buttonSize?: number
  showLabels?: boolean
  showTooltips?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false,
  buttonSize: 1.0,
  showLabels: true,
  showTooltips: true,
  compact: false
})

const emit = defineEmits<{
  buttonClick: [button: Button]
  buttonEdit: [button: Button]
  buttonCopy: [button: Button]
  buttonDelete: [buttonId: string]
  swipeLeft: []
  swipeRight: []
  swipeUp: []
  swipeDown: []
  actionDrop: [action: any, position: { row: number; col: number }]
  placeholderClick: [position: { row: number; col: number }]
  placeholderLongPress: [position: { row: number; col: number }]
  buttonMove: [buttonId: string, newPosition: { row: number; col: number }]
  doubleTap: [button: Button]
  longPress: [button: Button]
}>()

const gridRef = ref<HTMLElement | null>(null)
const dashboardStore = useDashboardStore()

const renderedPage = ref<Page>({ ...props.page })
const { cellClasses, triggerTransition } = useGridTransition()

// Watch page.id and animate staggered grid transitions
watch(() => props.page.id, async (newVal, oldVal) => {
  if (newVal === oldVal) return

  const scene = dashboardStore.currentScene
  const transitionStyle = scene?.transition_style || 'light-bar'
  const staggerOrder = scene?.stagger_order || 'by-column'
  const rows = props.page.grid_config.rows
  const cols = props.page.grid_config.cols

  await triggerTransition(rows, cols, staggerOrder, transitionStyle, () => {
    renderedPage.value = props.page
  })
})

// Deep watch props.page to sync updates (e.g. edits) when ID doesn't change
watch(() => props.page, (newPage) => {
  if (newPage.id === renderedPage.value.id) {
    renderedPage.value = newPage
  }
}, { deep: true })

const { tiltX, tiltY } = useParallax(gridRef)

const pinchScale = ref(1)
usePinch(gridRef, {
  onPinch: (scale) => {
    pinchScale.value = Math.max(0.5, Math.min(2.0, scale))
  }
})

useSwipe(gridRef, {
  threshold: 50,
  onSwipeEnd: (direction) => {
    if (direction === 'LEFT') emit('swipeLeft')
    if (direction === 'RIGHT') emit('swipeRight')
    if (direction === 'UP') emit('swipeUp')
    if (direction === 'DOWN') emit('swipeDown')
  }
})

const gridStyle = computed(() => {
  const { rows, cols } = renderedPage.value.grid_config
  const transformScale = props.buttonSize * pinchScale.value
  
  return {
    display: 'grid',
    gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
    gap: 'var(--spacing-xs)', // Always show small spacing between buttons
    width: '100%',
    height: '100%',
    padding: 'var(--spacing-md)',
    transform: `scale(${transformScale}) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg)`,
    transformOrigin: 'center'
  }
})

const visibleButtons = computed(() => {
  return renderedPage.value.buttons.filter(btn => btn.enabled)
})

const emptySlots = computed(() => {
  const { rows, cols } = renderedPage.value.grid_config
  const occupiedPositions = new Set()
  
  // Mark occupied positions (including multi-cell buttons) - only count enabled buttons
  renderedPage.value.buttons.filter(btn => btn.enabled).forEach(button => {
    const { row, col } = button.position
    const { rows: buttonRows, cols: buttonCols } = button.size
    
    // Mark all cells occupied by this button
    for (let r = row; r < row + buttonRows; r++) {
      for (let c = col; c < col + buttonCols; c++) {
        occupiedPositions.add(`${r}-${c}`)
      }
    }
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
  const { rows, cols } = renderedPage.value.grid_config
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

function handleButtonCopy(button: Button) {
  emit('buttonCopy', button)
}

function handleButtonDelete(buttonId: string) {
  emit('buttonDelete', buttonId)
}

function handleButtonDoubleTap(button: Button) {
  emit('doubleTap', button)
}

function handleButtonLongPress(button: Button) {
  emit('longPress', button)
}


const isDragOver = ref(false)
const highlightedSlot = ref<{ row: number; col: number } | null>(null)

// Drag and drop handlers
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  // Don't stop propagation - let the event bubble to parent containers like DockedSidebar
  e.dataTransfer!.dropEffect = 'copy'
}

function handleDragEnter(e: DragEvent) {
  e.preventDefault()
  // Don't stop propagation - let the event bubble to parent containers like DockedSidebar
  isDragOver.value = true
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  // Don't stop propagation - let the event bubble to parent containers like DockedSidebar
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
  highlightedSlot.value = null
  
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
      e.stopPropagation() // Only stop propagation if we handled the drop
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
      e.stopPropagation() // Only stop propagation if we handled the drop
    } catch (error) {
      console.error('Error handling action drop:', error)
    }
  }
}

function handlePlaceholderDragOver(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
}

function handlePlaceholderClick(row: number, col: number) {
  if (props.isEditMode) {
    emit('placeholderClick', { row, col })
  }
}

// Since useLongPress is attached via ref/element usually, we'll manually watch placeholders,
// but for simplicity in a v-for list, we'll implement a basic inline long-press timeout 
// for the empty slots when NOT in edit mode to trigger edit mode.
let placeholderTimeouts: Record<string, NodeJS.Timeout> = {}
function handlePlaceholderDragEnter(e: DragEvent, placeholder: { row: number; col: number }) {
  e.preventDefault()
  e.stopPropagation()
  highlightedSlot.value = placeholder
}

function handlePlaceholderDragLeave(e: DragEvent, placeholder: { row: number; col: number }) {
  e.preventDefault()
  e.stopPropagation()
  if (highlightedSlot.value?.row === placeholder.row && highlightedSlot.value?.col === placeholder.col) {
    highlightedSlot.value = null
  }
}

// Emulate long press for placeholders
function handlePlaceholderTouchStart(row: number, col: number) {
  if (props.isEditMode) return;
  const key = `${row}-${col}`;
  placeholderTimeouts[key] = setTimeout(() => {
    emit('placeholderLongPress', { row, col })
  }, 500)
}

function handlePlaceholderTouchEnd(row: number, col: number) {
  const key = `${row}-${col}`;
  if (placeholderTimeouts[key]) {
    clearTimeout(placeholderTimeouts[key]);
    delete placeholderTimeouts[key];
  }
}
</script>

<style scoped>
.deck-grid {
  background-color: transparent;
  user-select: none;
  touch-action: pan-y; /* Allow vertical scrolling but enable custom horizontal gestures */
  transition: all var(--transition-fast);
  margin: 0 auto;
  max-width: 100vw;
  max-height: 100%;
}

.deck-grid.drag-over {
  background-color: var(--color-primary-light);
  border: 2px dashed var(--color-primary);
}

.button-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: 2px dashed transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: transparent;
  min-height: 60px;
  min-width: 60px;
}

.button-placeholder.is-edit-mode {
  border-color: var(--color-primary-light);
  background-color: rgba(var(--color-primary-rgb, 74, 144, 226), 0.05);
  color: var(--color-text-secondary);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 1px 3px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.button-placeholder:hover {
  background-color: var(--color-surface-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: scale(1.05);
  box-shadow: 
    0 4px 15px rgba(0, 0, 0, 0.12),
    0 2px 5px rgba(0, 0, 0, 0.08),
    0 0 15px rgba(var(--color-primary-rgb, 74, 144, 226), 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.button-placeholder.is-highlighted {
  background-color: rgba(var(--color-primary-rgb, 74, 144, 226), 0.2);
  border-color: var(--color-primary);
  border-style: solid;
  color: var(--color-primary);
  transform: scale(1.08);
  box-shadow: 
    0 0 20px rgba(var(--color-primary-rgb, 74, 144, 226), 0.5),
    0 6px 20px rgba(0, 0, 0, 0.15),
    0 3px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.button-placeholder:active {
  transform: scale(0.95);
  box-shadow: 
    0 1px 4px rgba(0, 0, 0, 0.1),
    0 0 2px rgba(0, 0, 0, 0.05),
    inset 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>

