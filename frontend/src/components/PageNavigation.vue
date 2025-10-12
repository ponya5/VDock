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
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.nav-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 1.25rem;
}

.nav-btn:hover:not(:disabled) {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-indicators {
  display: flex;
  gap: var(--spacing-xs);
}

.page-indicator {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background-color: var(--color-surface);
  border: 2px solid var(--color-border);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-indicator:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-indicator.active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  font-weight: bold;
}

.page-name {
  font-weight: 600;
  color: var(--color-text);
  margin-left: var(--spacing-md);
}
</style>

