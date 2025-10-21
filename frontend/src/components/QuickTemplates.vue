<template>
  <div class="quick-templates">
    <div class="templates-header">
      <h3>
        <FontAwesomeIcon :icon="['fas', 'bolt']" />
        Quick Templates
      </h3>
      <button class="collapse-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Expand' : 'Collapse'">
        <FontAwesomeIcon :icon="['fas', collapsed ? 'chevron-down' : 'chevron-up']" />
      </button>
    </div>

    <div v-if="!collapsed" class="templates-content">
      <div class="category-tabs">
        <button
          v-for="category in categories"
          :key="category.id"
          :class="['category-tab', { active: activeCategory === category.id }]"
          @click="activeCategory = category.id"
        >
          <FontAwesomeIcon :icon="category.icon" />
          {{ category.name }}
        </button>
      </div>

      <div class="templates-grid">
        <button
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
          @click="emit('apply-template', template)"
          :title="template.description"
        >
          <div class="template-icon" :style="{ backgroundColor: template.style?.backgroundColor || '#667eea' }">
            <FontAwesomeIcon :icon="template.icon" :style="{ color: template.style?.textColor || '#ffffff' }" />
          </div>
          <div class="template-info">
            <div class="template-name">{{ template.name }}</div>
            <div class="template-desc">{{ template.description }}</div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { BUTTON_TEMPLATES, TEMPLATE_CATEGORIES, type ButtonTemplate } from '@/data/buttonTemplates'

const emit = defineEmits<{
  (e: 'apply-template', template: ButtonTemplate): void
}>()

const collapsed = ref(false)
const activeCategory = ref('media')
const categories = TEMPLATE_CATEGORIES

const filteredTemplates = computed(() => {
  return BUTTON_TEMPLATES.filter(t => t.category === activeCategory.value)
})
</script>

<style scoped>
.quick-templates {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
  overflow: hidden;
}

.templates-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  cursor: pointer;
}

.templates-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.collapse-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.templates-content {
  padding: var(--spacing-md);
}

.category-tabs {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.category-tab {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--color-text);
}

.category-tab:hover {
  background: var(--color-surface);
  border-color: var(--color-primary);
}

.category-tab.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
  max-height: 300px;
  overflow-y: auto;
  padding-right: var(--spacing-xs);
}

.template-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--color-primary);
}

.template-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-desc {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Scrollbar styling */
.templates-grid::-webkit-scrollbar {
  width: 6px;
}

.templates-grid::-webkit-scrollbar-track {
  background: var(--color-background);
  border-radius: var(--radius-sm);
}

.templates-grid::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

.templates-grid::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
}

/* Responsive */
@media (max-width: 767px) {
  .templates-grid {
    grid-template-columns: 1fr;
    max-height: 200px;
  }

  .category-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    scrollbar-width: thin;
  }

  .category-tab {
    white-space: nowrap;
  }
}
</style>

