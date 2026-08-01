<template>
  <div v-if="visible" class="quick-add-overlay" @click.self="emit('close')">
    <div class="quick-add-modal card">
      <!-- Left Category Rail -->
      <aside class="category-rail">
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="category-tab"
          :class="{ active: activeCategory === cat.id }"
          @click="selectCategory(cat.id)"
          :title="cat.label"
        >
          <FontAwesomeIcon :icon="cat.icon" class="category-icon" />
          <span class="category-label">{{ cat.label }}</span>
        </button>
      </aside>

      <!-- Right Presets Area -->
      <main class="presets-panel">
        <header class="presets-header">
          <h2>Add Button Preset</h2>
          <button class="btn btn-icon btn-close" @click="emit('close')" title="Close">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </header>

        <!-- Presets Grid with Swipe Area -->
        <div ref="gridRef" class="presets-grid-container">
          <div v-if="pagePresets.length > 0" class="presets-grid">
            <button
              v-for="preset in pagePresets"
              :key="preset.name"
              class="preset-card touch-target"
              @click="handlePresetSelect(preset)"
              :style="{ '--preset-color': preset.brand.primary }"
            >
              <div class="preset-icon-wrapper">
                <img
                  v-if="preset.icon.type === 'logo'"
                  :src="`/logos/${preset.icon.value}`"
                  :alt="preset.name"
                  class="preset-logo"
                  @error="handleImgError"
                />
                <FontAwesomeIcon
                  v-else
                  :icon="preset.icon.value.split(':')"
                  class="preset-icon"
                />
              </div>
              <span class="preset-name">{{ preset.name }}</span>
            </button>
          </div>
          <div v-else class="empty-presets">
            <p>No presets found in this category.</p>
          </div>
        </div>

        <!-- Dot Indicators -->
        <footer v-if="totalPages > 1" class="presets-footer">
          <button
            v-for="p in totalPages"
            :key="p"
            class="dot-indicator"
            :class="{ active: currentPage === p - 1 }"
            @click="currentPage = p - 1"
            :aria-label="`Go to page ${p}`"
          />
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSwipe } from '@/composables/useGestures'
import { presetRegistry, getPresetsByCategory, presetToButton } from '@/data/presets'
import type { ButtonPreset, PresetCategory } from '@/data/presets/types'
import type { Button, ButtonPosition } from '@/types'

interface Props {
  visible: boolean
  position: ButtonPosition
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  select: [button: Button]
}>()

const activeCategory = ref<PresetCategory>('recent')
const currentPage = ref(0)
const recentPresets = ref<ButtonPreset[]>([])
const gridRef = ref<HTMLElement | null>(null)

const categories = [
  { id: 'recent', label: 'Recent', icon: ['fas', 'history'] },
  { id: 'ai', label: 'AI Tools', icon: ['fas', 'robot'] },
  { id: 'dev', label: 'Developer', icon: ['fas', 'code'] },
  { id: 'media', label: 'Media', icon: ['fas', 'music'] },
  { id: 'social', label: 'Social', icon: ['fas', 'comments'] },
  { id: 'news', label: 'News', icon: ['fas', 'newspaper'] },
  { id: 'system', label: 'System', icon: ['fas', 'sliders-h'] }
] as const

// Load recent presets from localStorage or fall back to system defaults
function loadRecent() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('vdock-recent-presets')
    if (stored) {
      try {
        const names = JSON.parse(stored) as string[]
        recentPresets.value = names
          .map(name => presetRegistry.find(p => p.name === name))
          .filter((p): p is ButtonPreset => !!p)
      } catch (e) {
        // Ignore parsing errors
      }
    }
  }
  // Default fallback seeds the recent list with popular presets
  if (recentPresets.value.length === 0) {
    recentPresets.value = presetRegistry.slice(0, 15)
  }
}

// Compute presets list for active category
const categoryPresets = computed(() => {
  if (activeCategory.value === 'recent') {
    return recentPresets.value
  }
  return getPresetsByCategory(presetRegistry, activeCategory.value)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(categoryPresets.value.length / 15))
})

const pagePresets = computed(() => {
  const start = currentPage.value * 15
  return categoryPresets.value.slice(start, start + 15)
})

function selectCategory(catId: PresetCategory) {
  activeCategory.value = catId
  currentPage.value = 0
}

function handlePresetSelect(preset: ButtonPreset) {
  // Update recent list in localStorage
  const filtered = recentPresets.value.filter(p => p.name !== preset.name)
  const updated = [preset, ...filtered].slice(0, 15)
  recentPresets.value = updated
  localStorage.setItem('vdock-recent-presets', JSON.stringify(updated.map(p => p.name)))

  const button = presetToButton(preset, props.position)
  emit('select', button)
}

function handleImgError(e: Event) {
  // If logo fails to load, replace image element with a generic icon dynamically
  const target = e.target as HTMLImageElement
  if (target) {
    target.style.display = 'none'
  }
}

// Wire swipe gesture for page navigation
useSwipe(gridRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'LEFT' && currentPage.value < totalPages.value - 1) {
      currentPage.value++
    } else if (direction === 'RIGHT' && currentPage.value > 0) {
      currentPage.value--
    }
  }
})

// Reload recents on modal visibility change
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadRecent()
    currentPage.value = 0
  }
})

onMounted(() => {
  loadRecent()
})
</script>

<style scoped>
.quick-add-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.quick-add-modal {
  display: flex;
  width: 85vw;
  max-width: 760px;
  height: 70vh;
  max-height: 480px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Category Sidebar Rail */
.category-rail {
  width: 140px;
  background-color: rgba(0, 0, 0, 0.15);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--spacing-sm) 0;
  overflow-y: auto;
  gap: var(--spacing-xs);
}

.category-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 64px; /* Touch target dimensions */
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: clamp(0.70rem, 1vw + 0.4rem, 0.85rem);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
}

.category-tab:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--color-text);
}

.category-tab.active {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--color-primary);
  border-left: 3px solid var(--color-primary);
}

.category-icon {
  font-size: 1.25rem;
}

/* Presets Container */
.presets-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
  overflow: hidden;
}

.presets-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
}

.presets-header h2 {
  font-size: clamp(1.10rem, 1.5vw + 0.8rem, 1.40rem);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.presets-grid-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
  flex: 1;
}

.preset-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  padding: var(--spacing-xs);
  gap: var(--spacing-xs);
  font-family: inherit;
  /* Min touch targets */
  min-height: 48px;
  min-width: 48px;
}

.preset-card:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: var(--preset-color, var(--color-primary));
  transform: translateY(-2px);
}

.preset-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 1.5rem;
  color: var(--preset-color, var(--color-text));
}

.preset-logo {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.preset-name {
  font-size: clamp(0.70rem, 1vw + 0.4rem, 0.80rem);
  color: var(--color-text);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.empty-presets {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--color-text-secondary);
}

/* Dots Indicators */
.presets-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding-top: var(--spacing-sm);
}

.dot-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-border);
  border: none;
  cursor: pointer;
  padding: 18px; /* Makes it 44x44px touch target */
  background-clip: content-box; /* Restricts the visual dot to the content box */
  box-sizing: content-box;
  transition: background-color 0.2s var(--ease-out);
}

.dot-indicator.active {
  background-color: var(--color-primary);
}
</style>
