<template>
  <div class="asset-picker-overlay" @click.self="emit('close')">
    <div class="asset-picker">
      <div class="asset-picker-header">
        <h2>{{ title }}</h2>
        <button class="close-btn" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="asset-picker-toolbar">
        <div class="search-section">
          <div class="search-input-container">
            <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search assets..." 
              class="search-input"
            />
            <button 
              v-if="searchQuery" 
              @click="searchQuery = ''"
              class="clear-search-btn"
            >
              <FontAwesomeIcon :icon="['fas', 'times']" />
            </button>
          </div>
        </div>

        <div class="filter-section">
          <select v-model="selectedCategory" class="category-select">
            <option value="">All Categories</option>
            <option 
              v-for="category in nonEmptyCategories" 
              :key="category.id" 
              :value="category.id"
            >
              {{ category.name }}
            </option>
          </select>
        </div>

        <div class="view-options">
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'grid' }"
            @click="viewMode = 'grid'"
            title="Grid View"
          >
            <FontAwesomeIcon :icon="['fas', 'th']" />
          </button>
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
            title="List View"
          >
            <FontAwesomeIcon :icon="['fas', 'list']" />
          </button>
        </div>
      </div>

      <div class="asset-picker-content">
        <div class="categories-sidebar" v-if="!searchQuery">
          <div class="category-list">
            <button 
              class="category-item" 
              :class="{ active: selectedCategory === '' }"
              @click="selectedCategory = ''"
            >
              <FontAwesomeIcon :icon="['fas', 'star']" />
              <span>All Assets</span>
              <span class="asset-count">{{ totalAssets }}</span>
            </button>
            <button 
              v-for="category in nonEmptyCategories" 
              :key="category.id"
              class="category-item" 
              :class="{ active: selectedCategory === category.id }"
              @click="selectedCategory = category.id"
            >
              <FontAwesomeIcon :icon="getCategoryIcon(category.id)" />
              <span>{{ category.name }}</span>
              <span class="asset-count">{{ category.assets.length }}</span>
            </button>
          </div>
        </div>

        <div class="assets-main" :class="{ 'full-width': searchQuery }">
          <div v-if="loading" class="loading-state">
            <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
            <p>Loading assets...</p>
          </div>

          <div v-else-if="filteredAssets.length === 0" class="empty-state">
            <FontAwesomeIcon :icon="['fas', 'search']" />
            <p>No assets found</p>
            <span v-if="searchQuery">Try adjusting your search terms</span>
          </div>

          <div v-else class="assets-grid" :class="viewMode">
            <div 
              v-for="asset in paginatedAssets" 
              :key="asset.id"
              class="asset-item"
              :class="{ selected: selectedAsset?.id === asset.id }"
              @click="selectAsset(asset)"
              @dblclick="confirmSelection"
            >
              <div class="asset-preview">
                <FontAwesomeIcon v-if="asset.type === 'icon' && asset.format === 'fontawesome'"
                  :icon="asset.icon"
                  :style="{ color: asset.color }"
                  class="asset-icon"
                />
                <div v-else-if="asset.type === 'background' && asset.format === 'css'"
                  class="gradient-preview"
                  :style="{ background: asset.css }"
                ></div>
                <img v-else-if="asset.thumbnail" 
                  :src="asset.thumbnail" 
                  :alt="asset.name"
                  class="asset-image"
                />
                <div v-else class="asset-placeholder">
                  <FontAwesomeIcon :icon="getAssetTypeIcon(asset.type)" />
                </div>
              </div>
              
              <div class="asset-info">
                <h4 class="asset-name">{{ asset.name }}</h4>
                <div class="asset-tags">
                  <span 
                    v-for="tag in asset.tags.slice(0, 3)" 
                    :key="tag"
                    class="asset-tag"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="totalPages > 1" class="pagination">
            <button 
              class="pagination-btn" 
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              <FontAwesomeIcon :icon="['fas', 'chevron-left']" />
            </button>
            
            <span class="pagination-info">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            
            <button 
              class="pagination-btn" 
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              <FontAwesomeIcon :icon="['fas', 'chevron-right']" />
            </button>
          </div>
        </div>
      </div>

      <div class="asset-picker-footer">
        <div class="selected-asset-info">
          <div v-if="selectedAsset" class="selected-preview">
            <FontAwesomeIcon v-if="selectedAsset.type === 'icon' && selectedAsset.format === 'fontawesome'"
              :icon="selectedAsset.icon"
              :style="{ color: selectedAsset.color }"
              class="selected-icon"
            />
            <div v-else-if="selectedAsset.type === 'background' && selectedAsset.format === 'css'"
              class="selected-gradient"
              :style="{ background: selectedAsset.css }"
            ></div>
            <div class="selected-details">
              <h4>{{ selectedAsset.name }}</h4>
              <p>{{ selectedAsset.category }}</p>
            </div>
          </div>
          <div v-else class="no-selection">
            <p>Select an asset to continue</p>
          </div>
        </div>

        <div class="action-buttons">
          <button class="btn btn-secondary" @click="emit('close')">
            Cancel
          </button>
          <button 
            class="btn btn-primary" 
            :disabled="!selectedAsset"
            @click="confirmSelection"
          >
            Select Asset
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { assetManager, type AssetMetadata, type AssetCategory } from '@/utils/assetManager'

interface Props {
  type?: 'icon' | 'animation' | 'background'
  title?: string
  initialSelection?: AssetMetadata
}

const props = withDefaults(defineProps<Props>(), {
  type: 'icon',
  title: 'Select Asset'
})

const emit = defineEmits<{
  close: []
  select: [asset: AssetMetadata]
}>()

// State
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const selectedAsset = ref<AssetMetadata | null>(props.initialSelection || null)
const currentPage = ref(1)
const itemsPerPage = 24

// Data
const categories = ref<AssetCategory[]>([])
const allAssets = ref<AssetMetadata[]>([])

// Computed
const totalAssets = computed(() => allAssets.value.length)

// Filter out empty categories
const nonEmptyCategories = computed(() => {
  return categories.value.filter(category => category.assets.length > 0)
})

const filteredAssets = computed(() => {
  let assets = allAssets.value

  // Filter by type
  if (props.type) {
    assets = assets.filter(asset => asset.type === props.type)
  }

  // Filter by category
  if (selectedCategory.value) {
    assets = assets.filter(asset => asset.category === selectedCategory.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    assets = assets.filter(asset => 
      asset.name.toLowerCase().includes(query) ||
      asset.tags.some(tag => tag.toLowerCase().includes(query)) ||
      asset.category.toLowerCase().includes(query)
    )
  }

  return assets
})

const totalPages = computed(() => Math.ceil(filteredAssets.value.length / itemsPerPage))

const paginatedAssets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredAssets.value.slice(start, end)
})

// Methods
function getCategoryIcon(categoryId: string): string[] {
  if (categoryId.includes('system')) return ['fas', 'cog']
  if (categoryId.includes('media')) return ['fas', 'play']
  if (categoryId.includes('gaming')) return ['fas', 'gamepad']
  if (categoryId.includes('productivity')) return ['fas', 'briefcase']
  if (categoryId.includes('streaming')) return ['fas', 'broadcast-tower']
  if (categoryId.includes('social')) return ['fas', 'users']
  if (categoryId.includes('gradient')) return ['fas', 'palette']
  return ['fas', 'folder']
}

function getAssetTypeIcon(type: string): string[] {
  switch (type) {
    case 'icon': return ['fas', 'icons']
    case 'animation': return ['fas', 'film']
    case 'background': return ['fas', 'image']
    default: return ['fas', 'file']
  }
}

function selectAsset(asset: AssetMetadata) {
  selectedAsset.value = asset
}

function confirmSelection() {
  if (selectedAsset.value) {
    emit('select', selectedAsset.value)
  }
}

// Watch for search query changes to reset pagination
watch(searchQuery, () => {
  currentPage.value = 1
})

watch(selectedCategory, () => {
  currentPage.value = 1
})

// Initialize
onMounted(async () => {
  try {
    // Wait for asset manager to initialize
    await new Promise(resolve => setTimeout(resolve, 100))
    
    categories.value = assetManager.getCategories()
    allAssets.value = props.type ? 
      assetManager.getAssetsByType(props.type) : 
      Array.from(assetManager.getCategories()).flatMap(cat => cat.assets)
    
    loading.value = false
  } catch (error) {
    console.error('Failed to load assets:', error)
    loading.value = false
  }
})
</script>

<style scoped>
.asset-picker-overlay {
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
  animation: fadeIn var(--transition-fast);
}

.asset-picker {
  background-color: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  width: 90vw;
  height: 85vh;
  max-width: 1200px;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
  animation: slideUp var(--transition-normal);
  backdrop-filter: blur(20px);
}

.asset-picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.asset-picker-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.asset-picker-toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface);
}

.search-input-container {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: var(--spacing-sm);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) 2.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.clear-search-btn {
  position: absolute;
  right: var(--spacing-xs);
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
}

.clear-search-btn:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.category-select {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  color: var(--color-text);
  min-width: 150px;
}

.view-options {
  display: flex;
  gap: var(--spacing-xs);
}

.view-btn {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.view-btn:hover,
.view-btn.active {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.asset-picker-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.categories-sidebar {
  width: 250px;
  border-right: 1px solid var(--color-border);
  background-color: var(--color-surface);
  overflow-y: auto;
}

.category-list {
  padding: var(--spacing-sm);
}

.category-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  margin-bottom: var(--spacing-xs);
}

.category-item:hover,
.category-item.active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
}

.asset-count {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  background-color: var(--color-border);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.assets-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.assets-main.full-width {
  width: 100%;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: var(--spacing-md);
  color: var(--color-text-secondary);
}

.loading-state svg,
.empty-state svg {
  font-size: 3rem;
  opacity: 0.5;
}

.assets-grid {
  display: grid;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  overflow-y: auto;
  flex: 1;
}

.assets-grid.grid {
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
}

.assets-grid.list {
  grid-template-columns: 1fr;
}

.asset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.assets-grid.list .asset-item {
  flex-direction: row;
  text-align: left;
}

.asset-item:hover {
  border-color: var(--color-primary-light);
  background-color: var(--color-surface-hover);
  transform: translateY(-2px);
}

.asset-item.selected {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.asset-preview {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-sm);
  border-radius: var(--radius-sm);
  background-color: var(--color-background);
}

.assets-grid.list .asset-preview {
  margin-bottom: 0;
  margin-right: var(--spacing-md);
}

.asset-icon {
  font-size: 2rem;
}

.gradient-preview {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-sm);
}

.asset-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.asset-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  font-size: 1.5rem;
}

.asset-info {
  text-align: center;
  width: 100%;
}

.assets-grid.list .asset-info {
  text-align: left;
}

.asset-name {
  font-size: 0.85rem;
  font-weight: 500;
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--color-text);
}

.asset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  justify-content: center;
}

.assets-grid.list .asset-tags {
  justify-content: flex-start;
}

.asset-tag {
  font-size: 0.7rem;
  padding: 2px 6px;
  background-color: var(--color-border);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.pagination-btn {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background-color: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.asset-picker-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  background-color: var(--color-surface);
}

.selected-asset-info {
  flex: 1;
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.selected-icon {
  font-size: 2rem;
}

.selected-gradient {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
}

.selected-details h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text);
}

.selected-details p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.no-selection p {
  margin: 0;
  color: var(--color-text-secondary);
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-md);
}
</style>
