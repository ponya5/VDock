<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="template-gallery modal">
      <div class="modal-header">
        <h2>
          <FontAwesomeIcon :icon="['fas', 'layer-group']" />
          Scene Templates
        </h2>
        <button class="close-btn" @click="$emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="modal-body">
        <!-- Search and Filter -->
        <div class="gallery-controls">
          <div class="search-box">
            <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search templates..."
              class="search-input"
            />
          </div>

          <div class="category-filter">
            <button
              v-for="category in categories"
              :key="category.id"
              class="category-btn"
              :class="{ active: selectedCategory === category.id }"
              @click="selectedCategory = category.id"
            >
              <FontAwesomeIcon :icon="['fas', category.icon]" />
              {{ category.name }}
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
          <p>Loading templates...</p>
        </div>

        <!-- Templates Grid -->
        <div v-else-if="filteredTemplates.length > 0" class="templates-grid">
          <div
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            :class="{ selected: selectedTemplate?.id === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="card-header" :style="{ backgroundColor: template.color }">
              <FontAwesomeIcon :icon="['fas', template.icon]" class="template-icon" />
            </div>
            
            <div class="card-content">
              <h3>{{ template.name }}</h3>
              <p class="description">{{ template.description }}</p>
              
              <div class="card-meta">
                <span class="meta-item">
                  <FontAwesomeIcon :icon="['fas', 'grip']" />
                  {{ template.button_count }} buttons
                </span>
                <span class="meta-item">
                  <FontAwesomeIcon :icon="['fas', 'user']" />
                  {{ template.author }}
                </span>
              </div>
            </div>

            <div class="card-actions">
              <button
                class="btn btn-primary btn-sm"
                @click.stop="applyTemplate(template)"
              >
                <FontAwesomeIcon :icon="['fas', 'plus']" />
                Apply
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <FontAwesomeIcon :icon="['fas', 'inbox']" class="empty-icon" />
          <p>No templates found</p>
          <p class="help-text">Try adjusting your search or category filter</p>
        </div>
      </div>

      <!-- Template Preview (if selected) -->
      <div v-if="selectedTemplate" class="template-preview">
        <h3>{{ selectedTemplate.name }}</h3>
        <p>{{ selectedTemplate.description }}</p>
        
        <div class="preview-stats">
          <div class="stat">
            <strong>{{ selectedTemplate.button_count }}</strong>
            <span>Buttons</span>
          </div>
          <div class="stat">
            <strong>{{ selectedTemplate.version }}</strong>
            <span>Version</span>
          </div>
          <div class="stat">
            <strong>{{ categoryName(selectedTemplate.category) }}</strong>
            <span>Category</span>
          </div>
        </div>

        <div class="preview-actions">
          <button class="btn btn-primary" @click="applyTemplate(selectedTemplate)">
            <FontAwesomeIcon :icon="['fas', 'check']" />
            Apply Template
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import { useNotificationsStore } from '@/stores/notifications'

const emit = defineEmits<{
  close: []
  apply: [scene: any]
}>()

const notificationsStore = useNotificationsStore()

const loading = ref(true)
const templates = ref<any[]>([])
const categories = ref<any[]>([])
const selectedCategory = ref('all')
const searchQuery = ref('')
const selectedTemplate = ref<any>(null)

const filteredTemplates = computed(() => {
  let filtered = templates.value

  // Filter by category
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(t => t.category === selectedCategory.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }

  return filtered
})

function categoryName(categoryId: string): string {
  const category = categories.value.find(c => c.id === categoryId)
  return category ? category.name : categoryId
}

function selectTemplate(template: any) {
  selectedTemplate.value = template
}

async function applyTemplate(template: any) {
  try {
    const response = await apiClient.post(`/templates/${template.id}/apply`)
    
    if (response.data.success) {
      notificationsStore.success(
        'Template Applied',
        `Scene "${template.name}" has been created successfully!`
      )
      emit('apply', response.data.scene)
      emit('close')
    } else {
      notificationsStore.error(
        'Failed to Apply Template',
        response.data.error || 'Unknown error occurred'
      )
    }
  } catch (error: any) {
    notificationsStore.error(
      'Failed to Apply Template',
      error.message || 'Could not apply the template'
    )
  }
}

async function loadTemplates() {
  try {
    loading.value = true
    
    // Load templates
    const templatesResponse = await apiClient.get('/templates/list')
    if (templatesResponse.data.success) {
      // Flatten categories into a single array
      const allTemplates: any[] = []
      const cats = templatesResponse.data.categories
      
      for (const categoryId in cats) {
        allTemplates.push(...cats[categoryId])
      }
      
      templates.value = allTemplates
    }
    
    // Load categories
    const categoriesResponse = await apiClient.get('/templates/categories')
    if (categoriesResponse.data.success) {
      categories.value = [
        { id: 'all', name: 'All', icon: 'th', description: 'All templates' },
        ...categoriesResponse.data.categories
      ]
    }
  } catch (error: any) {
    notificationsStore.error(
      'Failed to Load Templates',
      error.message || 'Could not load template gallery'
    )
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-gallery {
  width: 90vw;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.gallery-controls {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.search-box {
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
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-sm) 3rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.category-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.875rem;
}

.category-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
}

.category-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  gap: var(--spacing-md);
  font-size: 1.5rem;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.template-card {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  flex-direction: column;
}

.template-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.template-card.selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.2);
}

.card-header {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
}

.template-icon {
  font-size: 3rem;
  color: white;
}

.card-content {
  padding: var(--spacing-md);
  flex: 1;
}

.card-content h3 {
  margin: 0 0 var(--spacing-xs);
  font-size: 1.1rem;
  color: var(--color-text);
}

.description {
  margin: 0 0 var(--spacing-md);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.card-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.card-actions {
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl) * 2;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.3;
  margin-bottom: var(--spacing-lg);
}

.help-text {
  font-size: 0.875rem;
  margin-top: var(--spacing-xs);
}

.template-preview {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
}

.template-preview h3 {
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text);
}

.preview-stats {
  display: flex;
  gap: var(--spacing-lg);
  margin: var(--spacing-lg) 0;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.stat strong {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.stat span {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.preview-actions {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-lg);
}

@media (max-width: 768px) {
  .template-gallery {
    width: 100vw;
    height: 100vh;
    max-width: none;
    max-height: none;
    border-radius: 0;
  }

  .templates-grid {
    grid-template-columns: 1fr;
  }

  .category-filter {
    overflow-x: auto;
    flex-wrap: nowrap;
  }
}
</style>

