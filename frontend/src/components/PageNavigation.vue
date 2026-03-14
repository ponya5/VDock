<template>
  <div class="page-navigation">
    <button 
      class="nav-btn"
      :disabled="currentPage === 0"
      @click="emit('previous')"
      title="Previous Page"
    >
      <FontAwesomeIcon :icon="['fas', 'chevron-left']" />
    </button>

    <div class="page-indicators">
      <button
        v-for="(page, index) in pages"
        :key="page.id"
        class="page-indicator"
        :class="{ active: index === currentPage }"
        @click="emit('goTo', index)"
        :title="page.name"
      >
        <span>{{ index + 1 }}</span>
      </button>
    </div>

    <button 
      class="nav-btn"
      :disabled="currentPage === pages.length - 1"
      @click="emit('next')"
      title="Next Page"
    >
      <FontAwesomeIcon :icon="['fas', 'chevron-right']" />
    </button>

    <div v-if="showPageName" class="page-name">
      {{ pages[currentPage]?.name || '' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Page } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  pages: Page[]
  currentPage: number
  showPageName?: boolean
}

withDefaults(defineProps<Props>(), {
  showPageName: true
})

const emit = defineEmits<{
  previous: []
  next: []
  goTo: [index: number]
}>()
</script>

<style scoped>
.page-navigation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
}

.nav-btn,
.page-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  cursor: pointer;
  background: transparent;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.nav-btn {
  width: 44px;
  height: 44px;
  font-size: clamp(0.80rem, 1vw + 0.5rem, 1rem);
}

.nav-btn:hover:not(:disabled),
.page-indicator:hover {
  border-color: rgba(255, 255, 255, 0.3);
  color: var(--color-text);
  background: rgba(255, 255, 255, 0.05);
}

.nav-btn:active,
.page-indicator:active {
  transform: scale(0.94);
}

.page-indicator.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(52, 152, 219, 0.12);
}

.nav-btn:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.page-indicators {
  display: flex;
  gap: var(--spacing-xs);
}

.page-indicator {
  width: 36px;
  height: 36px;
  font-size: clamp(0.70rem, 1vw + 0.44rem, 0.85rem);
}

.page-name {
  font-weight: 600;
  color: var(--color-text);
  margin-left: var(--spacing-md);
  font-size: clamp(0.75rem, 1vw + 0.5rem, 0.9rem);
}
</style>

