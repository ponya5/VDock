<template>
  <div ref="sidebarEl" class="docked-sidebar" :class="{ 'is-edit-mode': isEditMode, 'is-mobile': isMobile, 'is-narrow': isNarrow, 'is-open': sidebarOpen }" :style="{ width: isMobile ? '100vw' : sidebarWidth }">
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
      <button
        v-if="!props.showHeader"
        type="button"
        class="header-toggle-button"
        @click.stop="emit('toggleHeader')"
        title="Show header"
        aria-label="Show header"
      >
        <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
        <span>Show Header</span>
      </button>
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

    <!-- Weather card at the top of the docked column (per the 7-inch mockup).
         Hidden on the mobile bottom-bar layout and when weather hasn't
         resolved yet so an empty card never eats button space. -->
    <div v-if="!isMobile && weather" class="sidebar-weather-card">
      <FontAwesomeIcon :icon="weather.icon" class="weather-icon" />
      <div class="weather-info">
        <span class="weather-temp">{{ Math.round(weather.temperature) }}°</span>
        <span class="weather-desc">{{ weather.description }}</span>
        <span class="weather-loc">{{ weather.location }}</span>
      </div>
    </div>

    <p v-if="isEditMode && !isMobile" class="edit-hint">
      Drag to reorder. Tap the red minus to remove.
    </p>

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
            :button-size="buttonSize"
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
import { useWeather } from '@/composables/useWeather'

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
// 7" 1024x600 touch screen (spec 2): cap effective sidebar width so it
// doesn't eat the grid's horizontal space. Computed in JS (not CSS) so
// gridStyle's cell-height math below stays in sync with the real width.
const isCompactScreen = ref(
  typeof window !== 'undefined' ? window.innerWidth <= 1100 || window.innerHeight <= 650 : false
)
const sidebarOpen = ref(false)

// Free Open-Meteo weather for the mockup's top-of-sidebar card.
const { weather, start: startWeather, stop: stopWeather } = useWeather()

// Available vertical space for the button column itself (sidebar height minus
// its own padding), tracked so cell height can respond to the window/panel
// actually shrinking or growing instead of only reacting to width.
const sidebarEl = ref<HTMLElement | null>(null)
const availableHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 600)
let resizeObserver: ResizeObserver | null = null

const handleAvailableHeightResize = () => {
  if (sidebarEl.value) {
    availableHeight.value = sidebarEl.value.clientHeight
  }
}

const handleWindowResize = () => {
  isMobile.value = window.innerWidth < 768
  isNarrow.value = window.innerWidth < 480
  isCompactScreen.value = window.innerWidth <= 1100 || window.innerHeight <= 650
  handleAvailableHeightResize()
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleWindowResize)
  }
  // Tracks the sidebar's own box, so cell height also reacts to the header
  // being toggled or the docked panel switching to its mobile bottom-bar
  // layout — changes a window-resize listener alone would miss.
  if (typeof ResizeObserver !== 'undefined' && sidebarEl.value) {
    resizeObserver = new ResizeObserver(handleAvailableHeightResize)
    resizeObserver.observe(sidebarEl.value)
  }
  handleAvailableHeightResize()
  startWeather()
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleWindowResize)
  }
  resizeObserver?.disconnect()
  resizeObserver = null
  stopWeather()
})

// Use sidebar width from settings, capped on compact/7" screens (the mockup's
// column is 132px at 1024x600)
const effectiveSidebarWidth = computed(() => {
  // Compact cap raised 132→168: at 132px the weather card text and docked
  // button labels squeezed to near-unreadable sizes on the 7" panel; 168px
  // still leaves ~840px for the main grid at 1024x600.
  return isCompactScreen.value
    ? Math.min(settingsStore.dockedSidebarWidth, 168)
    : settingsStore.dockedSidebarWidth
})

const sidebarWidth = computed(() => {
  return `${effectiveSidebarWidth.value}px`
})

const gridStyle = computed(() => {
  const gap = 8
  // Sidebar chrome above the grid: own padding + header row + weather card
  // (~150px) + edit hint (~34px) when those are rendered.
  let paddingBlock = 32
  if (!isMobile.value && weather.value) paddingBlock += 150
  if (props.isEditMode && !isMobile.value) paddingBlock += 34
  const rows = Math.max(props.gridRows, 1)

  // User-configured height, scaled by the global button-size setting, but
  // capped so `rows` of them (plus gaps/padding) never exceed the sidebar's
  // actual available height — otherwise a tall stack just overflows and has
  // to scroll instead of fitting the panel it's in.
  const desiredCellHeight = settingsStore.dockedButtonHeight * props.buttonSize
  const maxTotalCellHeight = availableHeight.value - paddingBlock - gap * (rows - 1)
  const maxCellHeight = Math.max(40, maxTotalCellHeight / rows)
  const cellHeight = Math.min(desiredCellHeight, maxCellHeight)

  return {
    display: 'grid',
    gridTemplateColumns: '1fr',
    gridTemplateRows: `repeat(${rows}, ${cellHeight}px)`,
    gap: `${gap}px`,
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
  const newWidth = Math.max(80, Math.min(360, startWidth.value + delta))
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
  /* Faint glass tint keeps the background continuous while grounding the
     column on bright wallpapers; the divider is a two-tone seam — a dark
     edge plus an inner light line — so it reads on light AND dark
     backgrounds (a plain white hairline vanished on light ones). */
  background: rgba(10, 8, 32, 0.16);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-right: 1px solid rgba(0, 0, 0, 0.35);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.16);
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
  box-shadow: none;
  border-top: 1px solid rgba(0, 0, 0, 0.35);
  background: rgba(10, 8, 32, 0.66);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
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
  padding: var(--spacing-touch-sm, var(--spacing-sm));
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background-color var(--transition-fast), cursor var(--transition-fast);
}

/* Removed clickable-header styles as we now use a proper button */

.sidebar-header h3 {
  font-size: clamp(0.70rem, 2vw + 0.42rem, 1.00rem);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 0;
}

/* Weather card — the mockup's top-of-column tile. Centered vertical stack:
   the compact column is only ~140px of content, so left-aligned text read
   cramped and tiny on the 7" panel — center everything and size it up. */
.sidebar-weather-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  margin: 12px 12px 0;
  padding: 16px 10px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.weather-icon {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(74, 163, 255, 0.18);
  color: #7dbcff;
  font-size: clamp(1.30rem, 2vw + 0.90rem, 1.60rem);
}

.weather-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  max-width: 100%;
  line-height: 1.2;
}

.weather-temp {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: clamp(1.90rem, 4vw + 1.10rem, 2.50rem);
  color: #eef2fa;
  line-height: 1.05;
}

.weather-desc {
  font-size: clamp(0.80rem, 2vw + 0.50rem, 0.95rem);
  color: var(--color-text-secondary);
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.weather-loc {
  font-size: clamp(0.72rem, 2vw + 0.44rem, 0.85rem);
  color: rgba(255, 255, 255, 0.55);
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.edit-hint {
  margin: 8px 14px 0;
  font-size: 0.72rem;
  line-height: 1.35;
  color: var(--color-text-secondary);
}

.header-toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-touch-xs, var(--spacing-xs));
  flex: 1;
  min-width: 0;
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  padding: var(--spacing-touch-sm, var(--spacing-sm));
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  font-family: inherit;
  font-size: calc(clamp(0.60rem, 2vw + 0.38rem, 0.90rem) * min(var(--touch-multiplier, 1), 1.25));
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  touch-action: manipulation;
}

.header-toggle-button:hover {
  background: #1f6fd1;
  border-color: #1f6fd1;
}

.header-toggle-button svg {
  font-size: calc(clamp(0.64rem, 2vw + 0.40rem, 0.96rem) * min(var(--touch-multiplier, 1), 1.4));
  flex-shrink: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  min-width: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  background-color: #1f6fd1;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
  color: white;
  font-size: calc(clamp(0.60rem, 2vw + 0.38rem, 0.90rem) * min(var(--touch-multiplier, 1), 1.4));
  touch-action: manipulation;
  flex-shrink: 0;
}

.add-btn:hover {
  background: #2a80e0;
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
  background-color: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.34);
  border-radius: 18px;
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
    background: rgba(10, 8, 32, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(0, 0, 0, 0.35);
    box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.16);
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
