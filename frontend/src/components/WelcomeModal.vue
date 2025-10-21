<template>
  <div class="modal-overlay welcome-overlay">
    <div class="welcome-modal modal">
      <div class="modal-header">
        <h1>
          <FontAwesomeIcon :icon="['fas', 'rocket']" />
          Welcome to VDock!
        </h1>
      </div>

      <div class="modal-body">
        <div class="welcome-content">
          <p class="welcome-text">
            Your virtual stream deck is ready to use! Get started quickly with a pre-configured template,
            or create your own custom layout from scratch.
          </p>

          <div class="options-grid">
            <div
              class="option-card"
              :class="{ selected: selectedOption === 'template' }"
              @click="selectedOption = 'template'"
            >
              <div class="option-icon">
                <FontAwesomeIcon :icon="['fas', 'layer-group']" />
              </div>
              <h3>Start from Template</h3>
              <p>Choose from pre-made scenes with essential controls</p>
              <div class="option-check">
                <FontAwesomeIcon :icon="['fas', 'check-circle']" v-if="selectedOption === 'template'" />
              </div>
            </div>

            <div
              class="option-card"
              :class="{ selected: selectedOption === 'blank' }"
              @click="selectedOption = 'blank'"
            >
              <div class="option-icon">
                <FontAwesomeIcon :icon="['fas', 'plus-circle']" />
              </div>
              <h3>Start Blank</h3>
              <p>Create your own custom layout from the ground up</p>
              <div class="option-check">
                <FontAwesomeIcon :icon="['fas', 'check-circle']" v-if="selectedOption === 'blank'" />
              </div>
            </div>
          </div>

          <!-- Template Preview (if template option selected) -->
          <div v-if="selectedOption === 'template'" class="template-preview-section">
            <h3>Popular Templates:</h3>
            <div class="quick-templates">
              <div
                v-for="template in quickTemplates"
                :key="template.id"
                class="quick-template"
                :class="{ selected: selectedTemplateId === template.id }"
                @click="selectedTemplateId = template.id"
              >
                <div class="quick-icon" :style="{ backgroundColor: template.color }">
                  <FontAwesomeIcon :icon="['fas', template.icon]" />
                </div>
                <div class="quick-info">
                  <strong>{{ template.name }}</strong>
                  <span>{{ template.button_count }} buttons</span>
                </div>
              </div>
            </div>

            <button class="browse-more-btn" @click="showFullGallery = true">
              <FontAwesomeIcon :icon="['fas', 'th']" />
              Browse All Templates
            </button>
          </div>

          <div class="welcome-features">
            <h3>What You Can Do:</h3>
            <ul>
              <li>
                <FontAwesomeIcon :icon="['fas', 'keyboard']" />
                <span>Create hotkeys and keyboard shortcuts</span>
              </li>
              <li>
                <FontAwesomeIcon :icon="['fas', 'robot']" />
                <span>Automate tasks with macros</span>
              </li>
              <li>
                <FontAwesomeIcon :icon="['fas', 'volume-up']" />
                <span>Control media and system volume</span>
              </li>
              <li>
                <FontAwesomeIcon :icon="['fas', 'rocket']" />
                <span>Launch applications instantly</span>
              </li>
              <li>
                <FontAwesomeIcon :icon="['fas', 'gauge']" />
                <span>Monitor system performance</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('skip')">
          Skip for Now
        </button>
        <button
          class="btn btn-primary"
          @click="handleContinue"
          :disabled="!selectedOption"
        >
          <FontAwesomeIcon :icon="['fas', 'arrow-right']" />
          Continue
        </button>
      </div>
    </div>

    <!-- Full Template Gallery -->
    <TemplateGallery
      v-if="showFullGallery"
      @close="showFullGallery = false"
      @apply="handleTemplateApplied"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import TemplateGallery from './TemplateGallery.vue'
import apiClient from '@/api/client'
import { useNotificationsStore } from '@/stores/notifications'

const emit = defineEmits<{
  skip: []
  continue: [option: 'template' | 'blank', templateId?: string]
  templateApplied: [scene: any]
}>()

const notificationsStore = useNotificationsStore()

const selectedOption = ref<'template' | 'blank' | null>(null)
const selectedTemplateId = ref<string>('template-welcome')
const quickTemplates = ref<any[]>([])
const showFullGallery = ref(false)

async function loadQuickTemplates() {
  try {
    const response = await apiClient.get('/templates/list')
    if (response.data.success) {
      const allTemplates: any[] = []
      const cats = response.data.categories
      
      for (const categoryId in cats) {
        allTemplates.push(...cats[categoryId])
      }
      
      // Show only essentials and development templates as quick options
      quickTemplates.value = allTemplates
        .filter(t => t.category === 'essentials' || t.category === 'development')
        .slice(0, 3)
    }
  } catch (error) {
    console.error('Failed to load quick templates:', error)
  }
}

function handleContinue() {
  if (selectedOption.value === 'template') {
    emit('continue', 'template', selectedTemplateId.value)
  } else {
    emit('continue', 'blank')
  }
}

function handleTemplateApplied(scene: any) {
  emit('templateApplied', scene)
}

onMounted(() => {
  loadQuickTemplates()
})
</script>

<style scoped>
.welcome-overlay {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
}

.welcome-modal {
  width: 90vw;
  max-width: 800px;
  max-height: 90vh;
}

.modal-header h1 {
  margin: 0;
  font-size: 2rem;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.modal-header h1 svg {
  color: var(--color-primary);
}

.welcome-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.welcome-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
  text-align: center;
  margin: 0;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
}

.option-card {
  position: relative;
  padding: var(--spacing-xl);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  cursor: pointer;
  transition: all var(--transition-normal);
  text-align: center;
}

.option-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.option-card.selected {
  border-color: var(--color-primary);
  background: rgba(var(--color-primary-rgb), 0.1);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.2);
}

.option-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  border-radius: var(--radius-full);
  font-size: 2.5rem;
  color: white;
}

.option-card h3 {
  margin: 0 0 var(--spacing-sm);
  font-size: 1.3rem;
  color: var(--color-text);
}

.option-card p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.option-check {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  font-size: 1.5rem;
  color: var(--color-primary);
}

.template-preview-section {
  padding: var(--spacing-lg);
  background: var(--color-background);
  border-radius: var(--radius-lg);
}

.template-preview-section h3 {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text);
}

.quick-templates {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.quick-template {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-template:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-hover);
}

.quick-template.selected {
  border-color: var(--color-primary);
  background: rgba(var(--color-primary-rgb), 0.1);
}

.quick-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 1.5rem;
  color: white;
}

.quick-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quick-info strong {
  color: var(--color-text);
  font-size: 1rem;
}

.quick-info span {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.browse-more-btn {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.browse-more-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
}

.welcome-features {
  padding: var(--spacing-lg);
  background: rgba(var(--color-primary-rgb), 0.05);
  border-radius: var(--radius-lg);
  border-left: 3px solid var(--color-primary);
}

.welcome-features h3 {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text);
}

.welcome-features ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.welcome-features li {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  color: var(--color-text-secondary);
}

.welcome-features li svg {
  color: var(--color-primary);
  font-size: 1.2rem;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

@media (max-width: 768px) {
  .welcome-modal {
    width: 100vw;
    height: 100vh;
    max-width: none;
    max-height: none;
    border-radius: 0;
  }

  .options-grid {
    grid-template-columns: 1fr;
  }

  .modal-header h1 {
    font-size: 1.5rem;
  }
}
</style>

