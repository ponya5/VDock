<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="shortcut-manager modal">
      <div class="modal-header">
        <div class="header-title">
          <FontAwesomeIcon :icon="['fas', 'keyboard']" />
          <h2>{{ appName }} Shortcuts</h2>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="manager-content">
        <!-- Search Bar -->
        <div class="search-section">
          <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="Search shortcuts..."
            autofocus
          />
        </div>

        <!-- Category Tabs -->
        <div class="category-tabs">
          <button
            class="category-tab"
            :class="{ active: selectedCategory === 'all' }"
            @click="selectedCategory = 'all'"
          >
            All ({{ allShortcuts.length }})
          </button>
          <button
            v-for="category in categories"
            :key="category"
            class="category-tab"
            :class="{ active: selectedCategory === category }"
            @click="selectedCategory = category"
          >
            {{ categoryLabels[category] }} ({{ getShortcutsByCategory(category).length }})
          </button>
        </div>

        <!-- Shortcuts List -->
        <div class="shortcuts-list">
          <div
            v-for="shortcut in filteredShortcuts"
            :key="shortcut.name"
            class="shortcut-item"
          >
            <div class="shortcut-info">
              <div class="shortcut-name">{{ shortcut.name }}</div>
              <div class="shortcut-description">{{ shortcut.description }}</div>
              <div class="shortcut-keys">
                <kbd v-for="(key, index) in shortcut.keys" :key="index" class="key">
                  {{ key }}
                </kbd>
              </div>
            </div>
            <button
              class="btn btn-primary btn-sm add-btn"
              @click="addShortcutToScene(shortcut)"
              title="Add to scene"
            >
              <FontAwesomeIcon :icon="['fas', 'plus']" />
              Add
            </button>
          </div>

          <div v-if="filteredShortcuts.length === 0" class="empty-state">
            <FontAwesomeIcon :icon="['fas', 'search']" />
            <p>No shortcuts found</p>
          </div>
        </div>

        <!-- Manual Shortcut Creator -->
        <div class="manual-creator">
          <button
            class="btn btn-secondary"
            @click="showManualCreator = !showManualCreator"
          >
            <FontAwesomeIcon :icon="['fas', showManualCreator ? 'minus' : 'plus']" />
            Create Custom Shortcut
          </button>

          <div v-if="showManualCreator" class="creator-form">
            <div class="form-group">
              <label>Shortcut Name</label>
              <input
                v-model="customShortcut.name"
                type="text"
                class="input"
                placeholder="e.g., My Custom Action"
              />
            </div>
            <div class="form-group">
              <label>Keys</label>
              <div class="keys-input">
                <div
                  v-for="(key, index) in customShortcut.keys"
                  :key="index"
                  class="key-tag"
                >
                  <kbd>{{ key }}</kbd>
                  <button
                    class="remove-key"
                    @click="removeKey(index)"
                  >
                    <FontAwesomeIcon :icon="['fas', 'times']" />
                  </button>
                </div>
                <input
                  v-model="newKey"
                  type="text"
                  class="key-input"
                  placeholder="Press key..."
                  @keydown="captureKey"
                />
              </div>
              <p class="form-help">Click input and press keys to add them</p>
            </div>
            <div class="form-group">
              <label>Description</label>
              <input
                v-model="customShortcut.description"
                type="text"
                class="input"
                placeholder="What does this shortcut do?"
              />
            </div>
            <button
              class="btn btn-primary"
              :disabled="!customShortcut.name || customShortcut.keys.length === 0"
              @click="addCustomShortcut"
            >
              <FontAwesomeIcon :icon="['fas', 'check']" />
              Add Custom Shortcut
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  getShortcutsForApp,
  getCategoriesForApp,
  getAppName,
  type AppShortcut
} from '@/data/appShortcuts'

interface Props {
  appExe: string
  sceneId: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  addShortcut: [shortcut: AppShortcut]
}>()

const searchQuery = ref('')
const selectedCategory = ref<string>('all')
const showManualCreator = ref(false)
const newKey = ref('')

const customShortcut = ref<Partial<AppShortcut>>({
  name: '',
  keys: [],
  description: '',
  category: 'general'
})

const allShortcuts = computed(() => getShortcutsForApp(props.appExe))
const categories = computed(() => getCategoriesForApp(props.appExe))
const appName = computed(() => getAppName(props.appExe))

const categoryLabels: Record<string, string> = {
  general: 'General',
  editing: 'Editing',
  navigation: 'Navigation',
  search: 'Search',
  debug: 'Debug',
  view: 'View',
  terminal: 'Terminal',
  git: 'Git',
  refactor: 'Refactor'
}

const filteredShortcuts = computed(() => {
  let shortcuts = allShortcuts.value

  // Filter by category
  if (selectedCategory.value !== 'all') {
    shortcuts = shortcuts.filter(s => s.category === selectedCategory.value)
  }

  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    shortcuts = shortcuts.filter(s =>
      s.name.toLowerCase().includes(query) ||
      s.description.toLowerCase().includes(query) ||
      s.keys.some(k => k.toLowerCase().includes(query))
    )
  }

  return shortcuts
})

function getShortcutsByCategory(category: string) {
  return allShortcuts.value.filter(s => s.category === category)
}

function addShortcutToScene(shortcut: AppShortcut) {
  emit('addShortcut', shortcut)
}

function captureKey(event: KeyboardEvent) {
  event.preventDefault()
  
  const key = event.key
  
  // Normalize key names
  let normalizedKey = key
  if (key === 'Control') normalizedKey = 'Ctrl'
  if (key === 'Meta') normalizedKey = 'Win'
  if (key === ' ') normalizedKey = 'Space'
  
  // Avoid duplicates
  if (!customShortcut.value.keys!.includes(normalizedKey)) {
    customShortcut.value.keys!.push(normalizedKey)
  }
  
  newKey.value = ''
}

function removeKey(index: number) {
  customShortcut.value.keys!.splice(index, 1)
}

function addCustomShortcut() {
  if (!customShortcut.value.name || !customShortcut.value.keys || customShortcut.value.keys.length === 0) {
    return
  }

  const shortcut: AppShortcut = {
    name: customShortcut.value.name,
    keys: customShortcut.value.keys,
    description: customShortcut.value.description || '',
    category: customShortcut.value.category as any || 'general',
    priority: 5
  }

  emit('addShortcut', shortcut)

  // Reset form
  customShortcut.value = {
    name: '',
    keys: [],
    description: '',
    category: 'general'
  }
  showManualCreator.value = false
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.shortcut-manager {
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  background-color: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.header-title h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--color-text);
}

.header-title svg {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 1.5rem;
  padding: var(--spacing-xs);
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
}

.close-btn:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.manager-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.search-section {
  position: relative;
}

.search-icon {
  position: absolute;
  left: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-sm) calc(var(--spacing-md) * 2.5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text);
  font-size: 0.95rem;
  transition: all var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb, 74, 144, 226), 0.1);
}

.category-tabs {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.category-tab {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 0.875rem;
  font-weight: 500;
}

.category-tab:hover {
  background-color: var(--color-border);
  color: var(--color-text);
}

.category-tab.active {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  flex: 1;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  transition: all var(--transition-fast);
}

.shortcut-item:hover {
  background-color: var(--color-surface-hover);
  border-color: var(--color-primary);
  transform: translateX(2px);
}

.shortcut-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.shortcut-name {
  font-weight: 600;
  color: var(--color-text);
  font-size: 1rem;
}

.shortcut-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.shortcut-keys {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.key {
  padding: 2px 8px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  color: var(--color-text);
  box-shadow: 0 2px 0 var(--color-border);
}

.add-btn {
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  gap: var(--spacing-sm);
}

.empty-state svg {
  font-size: 3rem;
  opacity: 0.5;
}

.manual-creator {
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-lg);
}

.creator-form {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  font-weight: 500;
  color: var(--color-text);
  font-size: 0.875rem;
}

.form-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.keys-input {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  align-items: center;
}

.key-tag {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-surface);
  border-radius: var(--radius-sm);
}

.key-tag kbd {
  font-size: 0.75rem;
}

.remove-key {
  background: none;
  border: none;
  color: var(--color-error);
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  font-size: 0.75rem;
}

.remove-key:hover {
  opacity: 0.7;
}

.key-input {
  flex: 1;
  min-width: 100px;
  border: none;
  background: none;
  outline: none;
  color: var(--color-text);
  font-size: 0.875rem;
}
</style>

