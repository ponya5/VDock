<template>
  <div class="actions-sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-header">
      <h2>Button Actions</h2>
      <button class="close-btn" @click="emit('close')">
        <FontAwesomeIcon :icon="['fas', 'times']" />
      </button>
    </div>

    <div class="search-box">
      <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search actions..."
        class="search-input"
      />
    </div>

    <div class="actions-list">
      <p v-if="catalog.isLoading" class="catalog-state">Loading actions...</p>

      <p v-else-if="catalog.error" class="catalog-state catalog-error">
        {{ catalog.error }}
        <button class="retry-btn" @click="catalog.load(true)">Retry</button>
      </p>

      <p v-else-if="!visibleCategories.length" class="catalog-state">
        No actions match "{{ searchQuery }}".
      </p>

      <div
        v-for="category in visibleCategories"
        :key="category.id"
        class="action-category"
      >
        <button class="category-header" @click="toggleCategory(category.id)">
          <FontAwesomeIcon
            :icon="isExpanded(category.id) ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']"
          />
          <span>{{ category.label }}</span>
          <span class="count">({{ category.actions.length }})</span>
        </button>

        <div v-show="isExpanded(category.id)" class="category-items">
          <button
            v-for="action in category.actions"
            :key="action.id"
            class="action-item"
            :class="{ 'is-unavailable': action.unavailable_reason }"
            :title="action.unavailable_reason || action.description"
            :disabled="!!action.unavailable_reason"
            @click="selectAction(action)"
          >
            <FontAwesomeIcon :icon="action.icon" />
            <span>{{ action.label }}</span>
            <FontAwesomeIcon
              v-if="action.unavailable_reason"
              :icon="['fas', 'circle-exclamation']"
              class="unavailable-icon"
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// The action list is built from the backend action catalog
// (GET /api/actions/catalog), not from hardcoded markup.
//
// This file used to hardcode 46 selectAction('...') strings, 22 of which named
// an action type ActionExecutor had no handler for, so those buttons failed on
// press. Most were not missing features: `volume_up`, `media_play_pause` and
// `screenshot` were already implemented, but they are `cross_platform` configs
// rather than action types, and the sidebar emitted them as bare types. The
// catalog encodes that distinction, so emitting a spec now carries both the
// action_type and the default_config it needs.
import { ref, computed, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useActionCatalogStore, type ActionSpec } from '@/stores/actionCatalog'

interface Props {
  isOpen?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
  selectAction: [action: ActionSpec]
}>()

const catalog = useActionCatalogStore()
const searchQuery = ref('')

// Categories the user has collapsed. Defaulting to expanded means a newly
// added category is visible without touching this component.
const collapsedCategories = ref<string[]>([])

onMounted(() => {
  catalog.load()
})

/** Categories with their matching actions, empty ones dropped. */
const visibleCategories = computed(() =>
  catalog.populatedCategories
    .map((category) => ({
      ...category,
      actions: catalog
        .actionsInCategory(category.id)
        .filter((action) => catalog.matches(action, searchQuery.value))
    }))
    .filter((category) => category.actions.length > 0)
)

function isExpanded(categoryId: string): boolean {
  // While searching, show every category that still has matches.
  if (searchQuery.value.trim()) return true
  return !collapsedCategories.value.includes(categoryId)
}

function toggleCategory(categoryId: string) {
  const index = collapsedCategories.value.indexOf(categoryId)
  if (index >= 0) {
    collapsedCategories.value.splice(index, 1)
  } else {
    collapsedCategories.value.push(categoryId)
  }
}

function selectAction(action: ActionSpec) {
  if (action.unavailable_reason) return
  emit('selectAction', action)
}
</script>

<style scoped>
.actions-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background: linear-gradient(180deg, #2d1b4e 0%, #1a0d2e 100%);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
}

.actions-sidebar.is-open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: clamp(1.20rem, 2vw + 0.75rem, 1.80rem);
  font-weight: 700;
  color: white;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: clamp(1.20rem, 2vw + 0.75rem, 1.80rem);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color 0.2s;
}

.close-btn:hover {
  color: white;
}

.search-box {
  position: relative;
  padding: var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-icon {
  position: absolute;
  left: calc(var(--spacing-md) + 12px);
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.5);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  color: white;
  font-size: clamp(0.72rem, 2vw + 0.45rem, 1.08rem);
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: var(--color-primary);
}

.actions-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.action-category {
  margin-bottom: var(--spacing-xs);
}

.category-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-height: 52px;
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: clamp(0.76rem, 2vw + 0.47rem, 1.14rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.category-header:hover {
  background: rgba(255, 255, 255, 0.1);
}

.category-header .count {
  margin-left: auto;
  font-size: clamp(0.68rem, 2vw + 0.42rem, 1.02rem);
  color: rgba(255, 255, 255, 0.6);
}

.category-items {
  padding: var(--spacing-xs) 0;
  padding-left: var(--spacing-md);
}

.action-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  min-height: 52px;
  padding: var(--spacing-md);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.9);
  font-size: clamp(0.72rem, 2vw + 0.45rem, 1.08rem);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.action-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(4px);
}

.action-item svg {
  width: 22px;
  flex-shrink: 0;
  color: var(--color-primary);
}

/* Scrollbar styling */
.actions-list::-webkit-scrollbar {
  width: 8px;
}

.actions-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.actions-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.actions-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.catalog-state {
  padding: var(--spacing-lg);
  color: rgba(255, 255, 255, 0.6);
  font-size: clamp(0.85rem, 1vw + 0.5rem, 1rem);
  text-align: center;
}

.catalog-error {
  color: #ff9b9b;
}

.retry-btn {
  display: block;
  margin: var(--spacing-sm) auto 0;
  padding: var(--spacing-xs) var(--spacing-md);
  min-height: 44px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  color: white;
  cursor: pointer;
}

.action-item.is-unavailable {
  opacity: 0.45;
  cursor: not-allowed;
}

.unavailable-icon {
  margin-left: auto;
  color: #ffc107;
}
</style>
