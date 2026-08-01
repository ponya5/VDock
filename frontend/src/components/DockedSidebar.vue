<template>
  <div class="docked-sidebar" :class="{ 'is-edit-mode': isEditMode, 'is-mobile': isMobile, 'is-narrow': isNarrow, 'is-open': sidebarOpen }" :style="{ width: isMobile ? '100vw' : sidebarWidth }">
    <div
      v-if="isEditMode"
      class="resize-handle"
      @mousedown="startResize"
      title="Drag to resize"
    ></div>
    <div
      class="sidebar-header"
      @click="!props.showHeader && emit('toggleHeader')"
    >
      <div v-if="!props.showHeader" class="header-toggle-button">
        <FontAwesomeIcon :icon="['fas', 'chevron-up']" />
        <span>Docked Buttons</span>
      </div>
      <h3 v-else>Docked Buttons</h3>
      <button
        v-if="isEditMode"
        class="add-btn"
        @click.stop="handleAddButton"
        title="Add Docked Button"
      >
        <FontAwesomeIcon :icon="['fas', 'plus']" />
      </button>
    </div>

    <button v-if="isNarrow" class="sidebar-close-btn" @click="toggleSidebar">
      <FontAwesomeIcon :icon="['fas', 'times']" />
    </button>

    <div
      class="sidebar-grid"
      :style="gridStyle"
    >
      <!-- Render grid slots -->
      <template v-for="row in gridRows" :key="`row-${row}`">
        <template v-for="col in gridCols" :key="`slot-${row}-${col}`">
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
            @long-press="handleButtonEdit"
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

  <button
    v-if="isNarrow && !sidebarOpen"
    class="sidebar-toggle-btn"
    @click="toggleSidebar"
    aria-label="Open sidebar"
  >
    <FontAwesomeIcon :icon="['fas', 'bars']" />
  </button>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { Button } from '@/types'
import DeckButton from './DeckButton.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSettingsStore } from '@/stores/settings'

interface Props {
  dockedButtons: Button[]
  gridRows: number
  isEditMode?: boolean
  showLabels?: boolean
  showTooltips?: boolean
  buttonSize?: number
  showHeader?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false,
  showLabels: true,
  showTooltips: true,
  buttonSize: 1.0,
  showHeader: true
})

const emit = defineEmits<{
  buttonClick: [button: Button]
  buttonEdit: [button: Button]
  buttonCopy: [button: Button]
  buttonDelete: [buttonId: string]
  buttonDrop: [event: DragEvent, position: { row: number; col: number }]
  addButton: [position: { row: number; col: number }]
  placeholderClick: [position: { row: number; col: number }]
  toggleHeader: []
}>()

const gridCols = 1 // Docked sidebar is always 1 column
const dragOverSlot = ref<{ row: number; col: number } | null>(null)
const settingsStore = useSettingsStore()
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 768 : false)
const isNarrow = ref(typeof window !== 'undefined' ? window.innerWidth < 480 : false)
const sidebarOpen = ref(false)

const handleWindowResize = () => {
  isMobile.value = window.innerWidth < 768
  isNarrow.value = window.innerWidth < 480
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleWindowResize)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleWindowResize)
  }
})

// Use sidebar width from settings
const sidebarWidth = computed(() => {
  return `${settingsStore.dockedSidebarWidth}px`
})

const gridStyle = computed(() => {
  // Calculate cell height based on sidebar width
  // Make buttons roughly square based on the sidebar width
  const cellWidth = settingsStore.dockedSidebarWidth - 32 // Subtract padding
  const baseCellHeight = cellWidth * props.buttonSize

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

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

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

// Resize functionality
function startResize(event: MouseEvent) {
  if (!props.isEditMode) return

  isResizing.value = true
  startX.value = event.clientX
  startWidth.value = settingsStore.dockedSidebarWidth

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(event: MouseEvent) {
  if (!isResizing.value) return

  const delta = event.clientX - startX.value
  const newWidth = Math.max(80, Math.min(300, startWidth.value + delta))
  settingsStore.dockedSidebarWidth = newWidth
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}
</script>

<style scoped>
.docked-sidebar {
  height: 100%;
  background: var(--glass-bg, rgba(255, 255, 255, 0.05));
  backdrop-filter: var(--glass-blur, blur(10px));
  -webkit-backdrop-filter: var(--glass-blur, blur(10px));
  border-right: 2px solid var(--color-primary);
  box-shadow: var(--glass-shadow);
  display: flex;
  flex-direction: column;
  transition: none; /* Disable transition during resize */
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}

.docked-sidebar.is-mobile {
  position: fixed;
  bottom: 0;
  left: 0;
  height: 80px;
  width: 100vw !important;
  border-right: none;
  border-top: 2px solid var(--color-primary);
  flex-direction: row;
  z-index: 999;
}

.docked-sidebar.is-mobile .sidebar-grid {
  display: flex !important;
  flex-direction: row !important;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 8px !important;
  width: 100vw;
}

.docked-sidebar.is-mobile .sidebar-header {
  display: none;
}

.resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  cursor: col-resize;
  z-index: 101;
  background-color: transparent;
  transition: background-color var(--transition-fast);
}

.resize-handle:hover {
  background-color: var(--color-primary);
  opacity: 0.5;
}

.resize-handle::before {
  content: '';
  position: absolute;
  top: 0;
  right: -4px;
  width: 12px;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface);
  transition: background-color var(--transition-fast), cursor var(--transition-fast);
}

/* Removed clickable-header styles as we now use a proper button */

.sidebar-header h3 {
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.header-toggle-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  animation: button-pulse 2s ease-in-out infinite;
}

.header-toggle-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: button-pulse-hover 1s ease-in-out infinite;
}

.header-toggle-button svg {
  font-size: clamp(0.64rem, 2vw + 0.40rem, 0.96rem);
}

@keyframes button-pulse {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), 0 0 0 0 rgba(102, 126, 234, 0.4);
  }
  50% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), 0 0 0 8px rgba(102, 126, 234, 0.1);
  }
}

@keyframes button-pulse-hover {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), 0 0 0 0 rgba(102, 126, 234, 0.6);
  }
  50% {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), 0 0 0 12px rgba(102, 126, 234, 0.2);
  }
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
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
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
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
  color: var(--color-text-secondary);
  opacity: 0.5;
}

.docked-placeholder.drag-over .placeholder-icon {
  color: var(--color-primary);
  opacity: 1;
}

/* Narrow overlay mode */
@media (max-width: 480px) {
  .docked-sidebar.is-narrow {
    position: fixed;
    top: 0;
    left: -100%;
    height: 100vh;
    width: 200px !important;
    z-index: 999;
    transition: left 0.2s ease;
    border-right: 2px solid var(--color-primary);
    border-top: none;
    flex-direction: column;
  }

  .docked-sidebar.is-narrow.is-open {
    left: 0;
  }
}

.sidebar-toggle-btn {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  z-index: 200;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid var(--glass-border, rgba(255,255,255,0.12));
  background: var(--glass-bg, rgba(0,0,0,0.4));
  backdrop-filter: blur(8px);
  color: var(--color-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.sidebar-close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
}

.sidebar-close-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}
</style>
