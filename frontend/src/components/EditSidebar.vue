<template>
  <aside class="edit-sidebar card">
    <div class="sidebar-header">
      <h3>Button Actions</h3>
      <button class="btn btn-sm btn-secondary touch-target" @click="emit('close')" title="Close Sidebar">
        <FontAwesomeIcon :icon="['fas', 'times']" />
      </button>
    </div>

    <div class="sidebar-content">
      <div class="search-section">
        <input 
          :value="actionSearch"
          @input="emit('update:actionSearch', ($event.target as HTMLInputElement).value)"
          type="text" 
          placeholder="Search actions..." 
          class="search-input"
        />
      </div>

      <div class="categories-section">
        <div 
          v-for="(category, index) in filteredCategories" 
          :key="category.id"
          class="category-group"
        >
          <div 
            class="category-header" 
            @click="emit('toggleCategory', category.id)"
          >
            <div class="category-title">
              <FontAwesomeIcon 
                :icon="['fas', expandedCategories.includes(category.id) ? 'chevron-down' : 'chevron-right']" 
              />
              <span>{{ category.name }}</span>
            </div>
            <div class="category-controls" v-if="!actionSearch" @click.stop>
              <button 
                class="btn-control touch-target" 
                @click="emit('moveCategoryUp', index)"
                :disabled="index === 0"
                title="Move Up"
              >
                <FontAwesomeIcon :icon="['fas', 'chevron-up']" />
              </button>
              <button 
                class="btn-control touch-target" 
                @click="emit('moveCategoryDown', index)"
                :disabled="index === filteredCategories.length - 1"
                title="Move Down"
              >
                <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
              </button>
            </div>
          </div>

          <div 
            v-show="expandedCategories.includes(category.id)"
            class="category-actions"
          >
            <div 
              v-for="action in category.actions" 
              :key="action.id"
              :ref="(element) => setActionItemRef(action.id, element as Element | null)"
              class="action-item touch-target"
              draggable="true"
              @dragstart="handleDragStart($event, action)"
              @dragend="emit('dragend')"
              @click="handleActionClick(action)"
            >
              <FontAwesomeIcon :icon="normalizeFaIcon(action.icon)" class="action-icon" />
              <span class="action-name">{{ action.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useTouchActionDrag } from '@/composables/useTouchActionDrag'
import { normalizeFaIcon } from '@/utils/normalizeFaIcon'

interface Props {
  actionSearch: string
  expandedCategories: string[]
  filteredCategories: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:actionSearch': [value: string]
  toggleCategory: [id: string]
  moveCategoryUp: [index: number]
  moveCategoryDown: [index: number]
  selectAction: [action: any]
  dragend: []
  close: []
}>()

const { bindTouchDragSource, isTouchDragActive } = useTouchActionDrag()
const actionItemRefs = ref<Map<string, HTMLElement>>(new Map())
const suppressNextClick = ref(false)
const touchCleanupHandlers: Array<() => void> = []

function handleTouchDropComplete() {
  suppressNextClick.value = true
  emit('dragend')
}

function setActionItemRef(actionId: string, element: Element | null) {
  if (element instanceof HTMLElement) {
    actionItemRefs.value.set(actionId, element)
  } else {
    actionItemRefs.value.delete(actionId)
  }
}

function handleDragStart(event: DragEvent, action: any) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vdock-action', JSON.stringify(action))
    event.dataTransfer.effectAllowed = 'copy'
  }
}

function handleActionClick(action: any) {
  if (suppressNextClick.value || isTouchDragActive()) {
    suppressNextClick.value = false
    return
  }

  emit('selectAction', action)
}

function registerTouchDragSources() {
  touchCleanupHandlers.forEach((cleanup) => cleanup())
  touchCleanupHandlers.length = 0

  props.filteredCategories.forEach((category) => {
    category.actions.forEach((action: any) => {
      const actionElement = actionItemRefs.value.get(action.id)
      if (!actionElement) return

      const cleanup = bindTouchDragSource(
        actionElement,
        { type: 'action', data: action },
        350
      )
      touchCleanupHandlers.push(cleanup)
    })
  })
}

onMounted(async () => {
  await nextTick()
  registerTouchDragSources()
  document.addEventListener('vdock-touch-drop-complete', handleTouchDropComplete)
})

onUnmounted(() => {
  touchCleanupHandlers.forEach((cleanup) => cleanup())
  document.removeEventListener('vdock-touch-drop-complete', handleTouchDropComplete)
})

watch(
  () => props.filteredCategories,
  async () => {
    await nextTick()
    registerTouchDragSources()
  },
  { deep: true }
)
</script>

<style scoped>
.edit-sidebar {
  width: 280px;
  background-color: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
  z-index: 80;
}

.action-item {
  touch-action: none;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-section {
  padding: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.search-input {
  width: 100%;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.9rem;
}

.categories-section {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm) 0;
}

.category-group {
  margin-bottom: var(--spacing-xs);
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  user-select: none;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text);
  transition: background-color 0.2s var(--ease-out);
}

.category-header:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.category-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.category-controls {
  display: flex;
  gap: 4px;
}

.btn-control {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-xs);
  transition: all 0.2s var(--ease-out);
  min-height: 44px; /* Touch target size */
  min-width: 44px;
}

.btn-control:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
}

.btn-control:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.category-actions {
  padding: var(--spacing-xs) var(--spacing-md);
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  background-color: rgba(0, 0, 0, 0.1);
}

.action-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: grab;
  user-select: none;
  font-size: 0.8rem;
  transition: all 0.2s var(--ease-out);
  min-height: 44px;
}

.action-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: var(--color-primary);
}

.action-icon {
  color: var(--color-primary);
  font-size: 0.9rem;
}
</style>
