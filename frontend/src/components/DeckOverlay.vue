<template>
  <div 
    v-if="active && !isReduced"
    ref="containerRef"
    class="ambient-overlay-container"
    :class="mode"
    @mousedown="handleTap"
    @touchstart="handleTap"
  >
    <!-- Full-bleed mode: single overlay cover -->
    <div 
      v-if="mode === 'full-bleed'"
      class="ambient-overlay-inner"
      :class="`overlay-${style}`"
    />

    <!-- Keys mode: overlay per button slot -->
    <div 
      v-else
      class="ambient-overlay-grid"
      :style="gridStyle"
    >
      <div 
        v-for="button in buttons"
        :key="button.id"
        class="ambient-overlay-cell"
        :style="getCellStyle(button)"
      >
        <div 
          class="ambient-overlay-inner"
          :class="`overlay-${style}`"
          :style="getInnerStyle(button)"
        />
      </div>
    </div>

    <!-- Tap Ripples -->
    <div 
      v-for="ripple in ripples"
      :key="ripple.id"
      class="tap-ripple"
      :style="{ left: `${ripple.x}px`, top: `${ripple.y}px` }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Button } from '@/types'

interface Props {
  active: boolean
  style: string
  mode?: 'keys' | 'full-bleed'
  rows: number
  cols: number
  buttons: Button[]
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'keys'
})

const containerRef = ref<HTMLElement | null>(null)
const gridWidth = ref(0)
const gridHeight = ref(0)
const ripples = ref<{ id: number; x: number; y: number }[]>([])
const isReduced = ref(
  typeof window !== 'undefined' && 
  window.matchMedia && 
  window.matchMedia('(prefers-reduced-motion: reduce)').matches
)
let rippleId = 0

// Grid layout styles matching the parent grid
const gridStyle = computed(() => ({
  display: 'grid',
  gridTemplateRows: `repeat(${props.rows}, minmax(0, 1fr))`,
  gridTemplateColumns: `repeat(${props.cols}, minmax(0, 1fr))`,
  gap: 'var(--spacing-xs)',
  width: '100%',
  height: '100%',
  padding: 'var(--spacing-md)'
}))

// Position cell at correct row/col in the grid
function getCellStyle(button: Button) {
  const { position = { row: 0, col: 0 }, size = { rows: 1, cols: 1 } } = button
  return {
    gridRow: `${position.row + 1} / span ${size.rows}`,
    gridColumn: `${position.col + 1} / span ${size.cols}`
  }
}

// Compute negative offset for cell to align child animation
function getInnerStyle(button: Button) {
  if (gridWidth.value === 0 || gridHeight.value === 0) return {}

  const { position = { row: 0, col: 0 } } = button
  
  // Padding is 1rem (16px) on each side = 32px total
  const paddingTotal = 32
  const gapSize = 4 // var(--spacing-xs) is 0.25rem = 4px
  
  const contentWidth = gridWidth.value - paddingTotal
  const contentHeight = gridHeight.value - paddingTotal
  
  const cellW = (contentWidth - (props.cols - 1) * gapSize) / props.cols
  const cellH = (contentHeight - (props.rows - 1) * gapSize) / props.rows
  
  const offsetX = -position.col * (cellW + gapSize) - 16 // Account for grid left padding (16px)
  const offsetY = -position.row * (cellH + gapSize) - 16 // Account for grid top padding (16px)

  return {
    width: `${gridWidth.value}px`,
    height: `${gridHeight.value}px`,
    transform: `translate(${offsetX}px, ${offsetY}px)`
  }
}

function handleTap(e: MouseEvent | TouchEvent) {
  if (!containerRef.value) return
  
  const rect = containerRef.value.getBoundingClientRect()
  let clientX = 0
  let clientY = 0

  if ('touches' in e) {
    if (e.touches.length === 0) return
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }

  const x = clientX - rect.left
  const y = clientY - rect.top

  const id = rippleId++
  ripples.value.push({ id, x, y })

  // Remove ripple after animation finishes (600ms)
  setTimeout(() => {
    ripples.value = ripples.value.filter(r => r.id !== id)
  }, 600)
}

let resizeObserver: ResizeObserver | null = null
let reducedMotionCleanup: (() => void) | null = null

onMounted(() => {
  if (containerRef.value) {
    gridWidth.value = containerRef.value.clientWidth
    gridHeight.value = containerRef.value.clientHeight

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          gridWidth.value = entry.contentRect.width
          gridHeight.value = entry.contentRect.height
        }
      })
      resizeObserver.observe(containerRef.value)
    }
  }

  // Handle prefers-reduced-motion media query listener
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    isReduced.value = mediaQuery.matches
    
    const handler = (event: MediaQueryListEvent) => {
      isReduced.value = event.matches
    }
    
    mediaQuery.addEventListener('change', handler)
    reducedMotionCleanup = () => mediaQuery.removeEventListener('change', handler)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  reducedMotionCleanup?.()
})
</script>

<style scoped>
.ambient-overlay-grid {
  width: 100%;
  height: 100%;
}
</style>
