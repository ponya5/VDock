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
        <div class="search-box">
          <FontAwesomeIcon :icon="['fas', 'magnifying-glass']" class="search-icon" />
          <input
            :value="actionSearch"
            @input="emit('update:actionSearch', ($event.target as HTMLInputElement).value)"
            type="text"
            placeholder="Search actions..."
            class="search-input"
          />
        </div>
      </div>

      <div class="categories-section">
        <div
          v-for="category in filteredCategories"
          :key="category.id"
          class="category-group"
          :style="{ '--cat-accent': catAccent(category.id) }"
        >
          <!-- DL-097: the row itself toggles (there are no expand/collapse or
               reorder buttons); icon chip + full name + count + chevron. -->
          <div
            class="category-header"
            :class="{ open: expandedCategories.includes(category.id) }"
            role="button"
            tabindex="0"
            :aria-expanded="expandedCategories.includes(category.id)"
            @click="emit('toggleCategory', category.id)"
            @keydown.enter.prevent="emit('toggleCategory', category.id)"
            @keydown.space.prevent="emit('toggleCategory', category.id)"
          >
            <span class="category-icon">
              <FontAwesomeIcon :icon="normalizeFaIcon(category.icon)" />
            </span>
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">{{ category.actions.length }}</span>
            <FontAwesomeIcon
              :icon="['fas', 'chevron-down']"
              class="category-chevron"
              :class="{ open: expandedCategories.includes(category.id) }"
            />
          </div>

          <!-- Collapse keeps items mounted (visibility, not v-if) so the
               touch-drag bindings registered at mount stay live. -->
          <Collapse :open="expandedCategories.includes(category.id)">
            <div class="category-actions">
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
          </Collapse>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Collapse from '@/components/Collapse.vue'
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
  selectAction: [action: any]
  dragend: []
  close: []
}>()

/* DL-097: per-category accent hue drives the icon chip, the open row's
   border/background tint and the items' left rail, so each section reads
   as its own colour-coded group like the deck buttons. Catalog-appended
   categories (catalog-*) get their own entries; unknown ids fall back to
   the deck's primary blue. */
const CATEGORY_ACCENTS: Record<string, string> = {
  'quick-launch': '#f5a623',
  'system': '#9aa5b1',
  'audio': '#2dd4bf',
  'media': '#a78bfa',
  'window-management': '#38bdf8',
  'web': '#4aa3ff',
  'text': '#fb7185',
  'metrics': '#34d399',
  'time': '#fb923c',
  'weather': '#22d3ee',
  'navigation': '#818cf8',
  'streaming': '#f87171',
  'custom': '#e879f9',
  'catalog-ai': '#c084fc',
  'catalog-dev': '#4ade80',
  'catalog-sliders': '#14b8a6'
}
const DEFAULT_ACCENT = '#4aa3ff'

function catAccent(id: string) {
  return CATEGORY_ACCENTS[id] ?? DEFAULT_ACCENT
}

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
  /* Widens with touch mode so scaled-up rows keep room for action labels on
     small panels. The multiplier is capped (unlike rows/fonts) because this
     sidebar shares the row with the deck grid rather than overlaying it. */
  width: min(92vw, calc(280px * min(var(--touch-multiplier, 1), 1.5)));
  background: rgba(10, 8, 32, 0.66);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
  z-index: 80;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-touch-sm, var(--spacing-sm)) var(--spacing-touch-md, var(--spacing-md));
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header h3 {
  margin: 0;
  /* Capped below the full multiplier so the title fits on one line next to
     the close button instead of wrapping underneath it. */
  font-size: calc(1rem * min(var(--touch-multiplier, 1), 1.25));
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.sidebar-header .btn {
  /* Icon-only close: square compact padding so it doesn't hog the header
     line (btn-sm's horizontal spacing-md made it pill-wide). */
  padding: 4px;
  flex-shrink: 0;
  min-height: 44px;
  min-width: 44px;
  /* Same cap as the title: an icon-only close button doesn't need the full
     2x tablet floor to stay tappable. */
  min-height: max(var(--min-touch-target, 44px), calc(44px * min(var(--touch-multiplier, 1), 1.25)));
  min-width: max(var(--min-touch-target, 44px), calc(44px * min(var(--touch-multiplier, 1), 1.25)));
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-section {
  padding: var(--spacing-touch-sm, var(--spacing-sm));
  border-bottom: 1px solid var(--color-border);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: calc(12px * var(--touch-multiplier, 1));
  color: var(--color-text-secondary);
  font-size: calc(0.8rem * min(var(--touch-multiplier, 1), 1.3));
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--spacing-touch-xs, var(--spacing-xs)) var(--spacing-touch-sm, var(--spacing-sm));
  padding-left: calc(34px * var(--touch-multiplier, 1));
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-family: inherit;
  font-size: calc(0.9rem * var(--touch-multiplier, 1));
  transition: border-color 0.2s var(--ease-out), box-shadow 0.2s var(--ease-out);
}

.search-input:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(74, 163, 255, 0.28);
}

.categories-section {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-touch-sm, var(--spacing-sm)) 0;
}

/* Wider scrollbar on touch panels so it can be dragged by finger. */
.categories-section::-webkit-scrollbar {
  width: calc(8px * var(--touch-multiplier, 1));
}

.categories-section::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.categories-section::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}

.category-group {
  margin-bottom: calc(4px * var(--touch-multiplier, 1));
  padding: 0 var(--spacing-touch-sm, var(--spacing-sm));
}

/* The whole row is the toggle — icon chip, full name, count, chevron. */
.category-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-touch-sm, var(--spacing-sm));
  padding: var(--spacing-touch-xs, var(--spacing-xs)) var(--spacing-touch-sm, var(--spacing-sm));
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  background-color: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: var(--radius-md);
  cursor: pointer;
  user-select: none;
  /* Capped so category names stay on one line at large touch scales. */
  font-size: calc(0.85rem * min(var(--touch-multiplier, 1), 1.3));
  font-weight: 600;
  color: var(--color-text);
  transition:
    background-color 0.2s var(--ease-out),
    border-color 0.2s var(--ease-out);
}

.category-header:hover {
  background-color: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.14);
}

.category-header:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Open rows take the category accent — tinted bg + border — so the active
   section is identifiable by colour, matching its icon chip. */
.category-header.open {
  background-color: rgba(255, 255, 255, 0.06);
  background-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 12%, transparent);
  border-color: rgba(255, 255, 255, 0.2);
  border-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 38%, transparent);
}

.category-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: calc(30px * min(var(--touch-multiplier, 1), 1.3));
  height: calc(30px * min(var(--touch-multiplier, 1), 1.3));
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  color: var(--cat-accent, #4aa3ff);
  background-color: rgba(255, 255, 255, 0.06);
  background-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 16%, transparent);
  font-size: calc(0.85rem * min(var(--touch-multiplier, 1), 1.3));
  transition: background-color 0.2s var(--ease-out);
}

.category-header.open .category-icon {
  background-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 26%, transparent);
}

.category-name {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-count {
  flex-shrink: 0;
  min-width: calc(22px * min(var(--touch-multiplier, 1), 1.3));
  padding: 1px calc(7px * var(--touch-multiplier, 1));
  border-radius: 999px;
  background-color: rgba(255, 255, 255, 0.08);
  color: var(--color-text-secondary);
  font-size: calc(0.7rem * min(var(--touch-multiplier, 1), 1.3));
  font-weight: 600;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* Single chevron rotated -90° when collapsed — transform transition
   instead of an icon swap (same pattern as Settings' chevron-open). */
.category-chevron {
  flex-shrink: 0;
  color: var(--color-text-secondary);
  font-size: calc(0.75rem * min(var(--touch-multiplier, 1), 1.3));
  transform: rotate(-90deg);
  transition: transform 0.25s var(--ease-out), color 0.2s var(--ease-out);
}

.category-chevron.open {
  transform: rotate(0deg);
  color: var(--cat-accent, var(--color-primary));
}

/* Items indent under a thin accent rail aligned to the icon chip centre,
   so they read as belonging to the category rather than a flat list. */
.category-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: calc(6px * var(--touch-multiplier, 1));
  padding: calc(6px * var(--touch-multiplier, 1)) var(--spacing-touch-sm, var(--spacing-sm)) calc(4px * var(--touch-multiplier, 1));
  margin-left: calc(15px * min(var(--touch-multiplier, 1), 1.3));
  border-left: 2px solid rgba(255, 255, 255, 0.08);
  border-left-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 30%, transparent);
}

.action-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-touch-sm, var(--spacing-sm));
  padding: var(--spacing-touch-xs, var(--spacing-xs)) var(--spacing-touch-sm, var(--spacing-sm));
  background-color: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  cursor: grab;
  user-select: none;
  touch-action: none;
  font-size: calc(0.8rem * var(--touch-multiplier, 1));
  transition:
    background-color 0.2s var(--ease-out),
    border-color 0.2s var(--ease-out);
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
}

.action-item:hover {
  background-color: rgba(255, 255, 255, 0.09);
  border-color: var(--color-primary);
  border-color: color-mix(in srgb, var(--cat-accent, #4aa3ff) 45%, transparent);
}

.action-icon {
  color: var(--cat-accent, #4aa3ff);
  opacity: 0.85;
  font-size: calc(0.9rem * var(--touch-multiplier, 1));
}
</style>
