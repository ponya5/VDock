<template>
  <div 
    class="deck-grid" 
    :style="gridStyle"
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
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
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Button, Page } from '@/types'
import DeckButton from './DeckButton.vue'

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

function handleButtonClick(button: Button) {
  emit('buttonClick', button)
}

function handleButtonEdit(button: Button) {
  emit('buttonEdit', button)
}

function handleButtonDelete(buttonId: string) {
  emit('buttonDelete', buttonId)
}

// Touch gesture handling for page swiping
let touchStartX = 0
let touchStartY = 0

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
</script>

<style scoped>
.deck-grid {
  background-color: var(--color-background);
  user-select: none;
  touch-action: pan-y; /* Allow vertical scrolling but enable custom horizontal gestures */
}
</style>

