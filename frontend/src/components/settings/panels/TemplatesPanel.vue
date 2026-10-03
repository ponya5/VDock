<template>
  <div class="content">
    <div class="col">
      <section
        v-for="category in templateCategories"
        :key="category.id"
        class="panel template-category"
      >
        <button class="panel-head category-header" type="button" @click="toggleCategory(category.id)" :aria-expanded="expandedCategories.includes(category.id)">
          <h2><FontAwesomeIcon :icon="category.icon" class="category-icon" /> {{ category.name }}</h2>
          <span class="hint">{{ category.templates.length }} template{{ category.templates.length === 1 ? '' : 's' }}</span>
          <span class="spacer"></span>
          <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="category-chevron" :class="{ 'chevron-open': expandedCategories.includes(category.id) }" />
        </button>
        <Collapse :open="expandedCategories.includes(category.id)">
          <div class="panel-body pad">
            <div class="template-grid">
              <div v-for="template in category.templates" :key="template.id" class="template-card">
                <div class="template-card-header" :style="{ borderLeftColor: template.color }">
                  <div class="template-icon-wrap" :style="{ background: template.color + '22' }">
                    <img v-if="template.logo" :src="template.logo" :alt="template.name" class="template-logo-img" />
                    <FontAwesomeIcon v-else :icon="template.icon" :style="{ color: template.color }" />
                  </div>
                  <div class="template-info">
                    <span class="template-name">{{ template.name }}</span>
                    <span class="template-desc">{{ template.description }}</span>
                  </div>
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm template-path-btn"
                    :class="{ 'path-set': appPaths[templateAppKey(template)] }"
                    :title="appPaths[templateAppKey(template)] ? `Executable: ${appPaths[templateAppKey(template)]}` : 'Set the app executable path'"
                    aria-haspopup="dialog"
                    @click="openPathEditor = template.id"
                  >
                    <FontAwesomeIcon :icon="['fas', 'cog']" />
                  </button>
                  <button class="btn primary sm template-add-btn" :disabled="addingTemplate === template.id" @click="addTemplateAsScene(template)">
                    <FontAwesomeIcon :icon="addingTemplate === template.id ? ['fas', 'spinner'] : ['fas', 'plus']" :spin="addingTemplate === template.id" />
                    {{ addingTemplate === template.id ? 'Adding…' : 'Add Scene' }}
                  </button>
                </div>
                <div class="template-buttons-preview">
                  <span v-for="btn in template.buttons.slice(0, 8)" :key="btn.label" class="template-btn-chip"
                    :style="{ background: btn.style?.backgroundColor ? btn.style.backgroundColor + '33' : template.color + '22', borderColor: btn.style?.backgroundColor ?? template.color }">
                    <FontAwesomeIcon :icon="btn.icon" :style="{ color: btn.style?.backgroundColor ?? template.color }" />
                    {{ btn.label }}
                  </span>
                  <span v-if="template.buttons.length > 8" class="template-btn-chip template-btn-more">+{{ template.buttons.length - 8 }} more</span>
                </div>
              </div>
            </div>
          </div>
        </Collapse>
      </section>
    </div>

    <div v-if="pathEditorTemplate" class="modal-overlay" @click.self="openPathEditor = ''">
      <div class="modal app-path-modal" role="dialog" aria-modal="true" :aria-label="`${pathEditorTemplate.name} executable path`">
        <div class="modal-header">
          <h2>{{ pathEditorTemplate.name }} executable</h2>
          <button type="button" class="close-btn" aria-label="Close" @click="openPathEditor = ''">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>
        <AppPathEditor
          class="settings-isolate"
          :app-key="templateAppKey(pathEditorTemplate)"
          :label="pathEditorTemplate.name"
          @close="openPathEditor = ''"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Collapse from '@/components/Collapse.vue'
import { templateCategories, type AppTemplate } from '@/data/appTemplates'
import type { Scene, Button } from '@/types'
import AppPathEditor from '@/components/AppPathEditor.vue'
import { appPaths, templateAppKey } from '@/api/appPaths'

const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()

const expandedCategories = ref<string[]>([])
const addingTemplate = ref<string | null>(null)

// DL-084 app-path editors — which card / launch-paths row is open.
const openPathEditor = ref('')
const pathEditorTemplate = computed(() => {
  if (!openPathEditor.value) return null
  for (const cat of templateCategories) {
    const found = cat.templates.find((t) => t.id === openPathEditor.value)
    if (found) return found
  }
  return null
})

function toggleCategory(id: string) {
  const index = expandedCategories.value.indexOf(id)
  if (index === -1) {
    expandedCategories.value.push(id)
  } else {
    expandedCategories.value.splice(index, 1)
  }
}

async function addTemplateAsScene(template: AppTemplate) {
  const profile = dashboardStore.currentProfile
  if (!profile) { notificationsStore.error('No profile', 'Load a profile first.'); return }
  addingTemplate.value = template.id
  try {
    const buttons: Button[] = template.buttons.map((b, index) => ({
      id: `button-${Date.now()}-${index}`,
      label: b.label, icon: b.icon, icon_type: 'fontawesome', action: b.action as Button['action'], shape: 'rounded',
      position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
      style: { backgroundColor: b.style?.backgroundColor ?? template.color, textColor: b.style?.textColor ?? '#ffffff' },
      tooltip: b.tooltip ?? b.label, enabled: true
    }))
    const newScene: Scene = {
      id: `scene-${Date.now()}`, name: template.name, icon: template.icon[1] ?? 'layer-group',
      color: template.color, pages: [{ id: `page-${Date.now()}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
      appId: template.id, autoCreated: false
    }
    dashboardStore.addScene(newScene)
    notificationsStore.success('Scene added', `"${template.name}" scene added to your dashboard.`)
  } finally { addingTemplate.value = null }
}
</script>

<style scoped>
.template-category {
  margin-bottom: var(--spacing-md); }
.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: transparent;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  font-size: clamp(13px, 0.8vw + 10px, 16px);
  font-weight: 600;
  min-height: 44px;
  transition: background-color 0.12s ease;
}
@media (hover: hover) and (pointer: fine) {
  .category-header:hover { background-color: rgba(255, 255, 255, 0.02); }
  .template-card:hover { box-shadow: var(--glass-glow, 0 0 20px rgba(52,152,219,0.2)); }
}
.category-header:active { background-color: rgba(255, 255, 255, 0.035); }
.category-header:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
.category-icon { color: var(--color-primary, #3498db); }
.category-chevron {
  color: var(--color-text-secondary);
  transition: transform 200ms var(--ease-out);
}
.category-chevron.chevron-open { transform: rotate(180deg); }
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}
.template-card {
  border: 1px solid var(--glass-border, var(--color-border));
  border-radius: var(--radius-md);
  overflow: hidden;
  background: rgba(0,0,0,0.15);
  transition: box-shadow var(--transition-fast);
}
.template-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 3px solid transparent;
}
.template-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.template-logo-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}
.template-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.template-name {
  font-size: clamp(12px, 0.7vw + 9px, 14px);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.template-desc {
  font-size: clamp(10px, 0.5vw + 8px, 12px);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.template-add-btn {
  flex-shrink: 0;
  min-height: 32px;
}
.template-path-btn {
  flex-shrink: 0;
  min-height: 32px;
  min-width: 32px;
  padding: 0 8px;
}
.template-path-btn.path-set {
  color: #34d399;
  border-color: rgba(52, 211, 153, 0.5);
}
.app-path-modal {
  width: 520px;
  padding: var(--spacing-lg) var(--spacing-xl);
}
.app-path-modal .modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}
.app-path-modal .modal-header h2 {
  margin: 0;
  font-size: clamp(16px, 1.2vw + 12px, 20px);
}
.app-path-modal .close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  min-height: 36px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}
.app-path-modal .close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}
.template-buttons-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: var(--spacing-xs) var(--spacing-md) var(--spacing-sm);
}
.template-btn-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid;
  font-size: clamp(10px, 0.5vw + 8px, 11px);
  white-space: nowrap;
}
.template-btn-more {
  background: transparent !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-secondary);
}
.category-header {
  touch-action: manipulation; }
@media (prefers-reduced-motion: reduce) {
  .category-header {
    transition: none; }
}
</style>
