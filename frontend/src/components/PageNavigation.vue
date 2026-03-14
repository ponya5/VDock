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

/* Uiverse lenfear23 — shared mixin via class */
.nav-btn,
.page-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  cursor: pointer;
  background-image: linear-gradient(to top, #D8D9DB 0%, #fff 80%, #FDFDFD 100%);
  border-radius: 30px;
  border: 1px solid #8F9092;
  transition: all 0.2s ease;
  font-weight: 600;
  color: #606060;
  text-shadow: 0 1px #fff;
}

.nav-btn {
  width: 44px;
  height: 44px;
  font-size: clamp(0.80rem, 1vw + 0.5rem, 1rem);
}

.nav-btn:hover:not(:disabled),
.page-indicator:hover {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 3px 3px #CECFD1;
}

.nav-btn:active,
.page-indicator:active,
.page-indicator.active {
  box-shadow:
    0 4px 3px 1px #FCFCFC,
    0 6px 8px #D6D7D9,
    0 -4px 4px #CECFD1,
    0 -6px 4px #FEFEFE,
    inset 0 0 5px 3px #999,
    inset 0 0 30px #aaa;
  color: #333;
}

.nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
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

