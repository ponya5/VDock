<template>
  <teleport to="body">
    <transition name="quick-search-fade">
      <div v-if="isOpen" class="quick-search-overlay" @click="close">
        <div class="quick-search-modal" @click.stop>
          <div class="search-header">
            <div class="search-icon">
              <FontAwesomeIcon :icon="['fas', 'magnifying-glass']" />
            </div>
            <input
              ref="searchInput"
              v-model="query"
              type="text"
              placeholder="Search buttons, actions, scenes..."
              class="search-input"
              @keydown.down.prevent="selectNext"
              @keydown.up.prevent="selectPrevious"
              @keydown.enter="executeSelected"
              @keydown.esc="close"
            />
            <button class="close-btn" @click="close" title="Close (Esc)">
              <FontAwesomeIcon :icon="['fas', 'xmark']" />
            </button>
          </div>

          <div class="search-results" v-if="results.length > 0">
            <div
              v-for="(result, index) in results"
              :key="result.id"
              :class="['result-item', { selected: index === selectedIndex }]"
              @click="execute(result)"
              @mouseenter="selectedIndex = index"
            >
              <div class="result-icon" :style="{ backgroundColor: result.color }">
                <FontAwesomeIcon v-if="result.iconType === 'fontawesome'" :icon="result.icon" />
                <img v-else-if="result.iconUrl" :src="result.iconUrl" alt="" class="custom-icon" />
                <FontAwesomeIcon v-else :icon="['fas', 'square']" />
              </div>
              <div class="result-info">
                <div class="result-title">{{ result.label }}</div>
                <div class="result-meta">
                  <span class="result-scene">{{ result.sceneName }}</span>
                  <span class="result-separator">•</span>
                  <span class="result-action">{{ result.actionType }}</span>
                </div>
              </div>
              <div class="result-shortcut">
                <kbd>Enter</kbd>
              </div>
            </div>
          </div>

          <div class="search-empty" v-else-if="query.length > 0">
            <FontAwesomeIcon :icon="['fas', 'inbox']" />
            <p>No results found for "{{ query }}"</p>
          </div>

          <div class="search-footer">
            <div class="search-tips">
              <span class="tip"><kbd>↑</kbd><kbd>↓</kbd> Navigate</span>
              <span class="tip"><kbd>Enter</kbd> Execute</span>
              <span class="tip"><kbd>Esc</kbd> Close</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import type { Button } from '@/types'

interface SearchResult {
  id: string
  label: string
  sceneName: string
  sceneId: string
  pageId: string
  actionType: string
  icon: any
  iconType: string
  iconUrl?: string
  color: string
  button: Button
}

const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()

const isOpen = ref(false)
const query = ref('')
const selectedIndex = ref(0)
const searchInput = ref<HTMLInputElement>()

// Build searchable index from all buttons
const searchableButtons = computed(() => {
  const buttons: SearchResult[] = []
  const profile = dashboardStore.activeProfile

  if (!profile) return buttons

  profile.scenes.forEach(scene => {
    scene.pages.forEach(page => {
      page.buttons.forEach(button => {
        buttons.push({
          id: button.id,
          label: button.label || 'Unnamed',
          sceneName: scene.name,
          sceneId: scene.id,
          pageId: page.id,
          actionType: button.action?.type || 'none',
          icon: button.icon,
          iconType: button.icon_type || 'fontawesome',
          iconUrl: button.icon_url,
          color: button.style.backgroundColor || '#667eea',
          button
        })
      })
    })
  })

  return buttons
})

// Filter results based on query
const results = computed(() => {
  if (!query.value.trim()) return []

  const searchTerm = query.value.toLowerCase()
  
  return searchableButtons.value
    .filter(item => {
      return (
        item.label.toLowerCase().includes(searchTerm) ||
        item.sceneName.toLowerCase().includes(searchTerm) ||
        item.actionType.toLowerCase().includes(searchTerm)
      )
    })
    .slice(0, 10) // Limit to 10 results
})

// Reset selection when results change
watch(results, () => {
  selectedIndex.value = 0
})

function open() {
  isOpen.value = true
  query.value = ''
  selectedIndex.value = 0
  
  nextTick(() => {
    searchInput.value?.focus()
  })
}

function close() {
  isOpen.value = false
  query.value = ''
  selectedIndex.value = 0
}

function selectNext() {
  if (selectedIndex.value < results.value.length - 1) {
    selectedIndex.value++
  }
}

function selectPrevious() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--
  }
}

function executeSelected() {
  if (results.value.length > 0) {
    execute(results.value[selectedIndex.value])
  }
}

async function execute(result: SearchResult) {
  close()

  try {
    // Switch to the scene if needed
    if (dashboardStore.activeSceneId !== result.sceneId) {
      dashboardStore.setActiveScene(result.sceneId)
      await nextTick()
    }

    // Execute the button action
    if (result.button.action) {
      const actionResult = await dashboardStore.executeAction(
        dashboardStore.activeProfileId,
        result.button.action
      )

      if (actionResult.success) {
        notificationsStore.success(
          'Action Executed',
          `"${result.label}" executed successfully`
        )
      } else {
        notificationsStore.error(
          'Action Failed',
          actionResult.message,
          actionResult.data?.details
        )
      }
    } else {
      notificationsStore.warning(
        'No Action',
        `Button "${result.label}" has no action configured`
      )
    }
  } catch (error: any) {
    notificationsStore.error(
      'Execution Error',
      'Failed to execute action',
      error.message
    )
  }
}

// Keyboard shortcut listener
function handleKeydown(e: KeyboardEvent) {
  // Ctrl+K or Cmd+K
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    if (isOpen.value) {
      close()
    } else {
      open()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// Expose open method for parent components
defineExpose({
  open,
  close
})
</script>

<style scoped>
.quick-search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 9999;
  animation: fadeIn 0.2s ease-out;
}

.quick-search-modal {
  width: 90%;
  max-width: 600px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideDown 0.3s ease-out;
}

.search-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background);
}

.search-icon {
  color: var(--color-text-secondary);
  font-size: 1.2rem;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1rem;
  color: var(--color-text);
  outline: none;
  padding: 0.5rem 0;
}

.search-input::placeholder {
  color: var(--color-text-secondary);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--color-surface);
  color: var(--color-text);
}

.search-results {
  max-height: 400px;
  overflow-y: auto;
  padding: var(--spacing-xs);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover,
.result-item.selected {
  background: var(--color-background);
}

.result-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: white;
  flex-shrink: 0;
}

.custom-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}

.result-separator {
  opacity: 0.5;
}

.result-shortcut {
  opacity: 0.6;
}

.search-empty {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.search-empty svg {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.search-footer {
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
}

.search-tips {
  display: flex;
  gap: var(--spacing-md);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.tip {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

kbd {
  padding: 0.2rem 0.4rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  font-size: 0.7rem;
  font-family: monospace;
  color: var(--color-text);
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.quick-search-fade-enter-active,
.quick-search-fade-leave-active {
  transition: opacity 0.2s;
}

.quick-search-fade-enter-from,
.quick-search-fade-leave-to {
  opacity: 0;
}

/* Scrollbar */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
}

/* Responsive */
@media (max-width: 767px) {
  .quick-search-modal {
    width: 95%;
    max-width: none;
  }

  .search-results {
    max-height: 300px;
  }

  .result-meta {
    font-size: 0.7rem;
  }
}
</style>

