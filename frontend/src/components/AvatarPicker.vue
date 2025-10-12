<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal avatar-picker">
      <div class="modal-header">
        <h2>Choose Avatar</h2>
        <button class="close-btn" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
          <span>Loading avatars...</span>
        </div>
        
        <div v-else class="avatars-grid">
          <div 
            v-for="avatar in avatars" 
            :key="avatar.id"
            :class="['avatar-item', { selected: selectedAvatar?.id === avatar.id }]"
            @click="selectAvatar(avatar)"
          >
            <div class="avatar-preview">
              <img 
                :src="avatar.url" 
                :alt="avatar.name"
                class="avatar-image"
              />
            </div>
            <span class="avatar-name">{{ avatar.name }}</span>
          </div>
        </div>

        <div v-if="selectedAvatar" class="selected-avatar-info">
          <h3>Selected: {{ selectedAvatar.name }}</h3>
          <div class="avatar-preview-large">
            <img 
              :src="selectedAvatar.url" 
              :alt="selectedAvatar.name"
              class="avatar-image-large"
            />
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emit('close')">Cancel</button>
        <button 
          class="btn btn-primary" 
          @click="confirmSelection"
          :disabled="!selectedAvatar"
        >
          Select Avatar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Avatar } from '@/assets/avatars'
import apiClient from '@/api/client'

interface Props {
  currentAvatar?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [avatar: Avatar]
  close: []
}>()

const selectedAvatar = ref<Avatar | null>(null)
const avatars = ref<Avatar[]>([])
const loading = ref(true)

async function loadAvatars() {
  try {
    loading.value = true
    // Create avatar list directly from known files
    const avatarList = []
    for (let i = 1; i <= 18; i++) {
      avatarList.push({
        id: `avatar-${i}`,
        name: `Avatar ${i}`,
        url: `/avatars/${i}.png`,
        type: 'image',
        category: 'characters'
      })
    }
    avatars.value = avatarList
  } catch (error) {
    console.error('Failed to load avatars:', error)
  } finally {
    loading.value = false
  }
}

function parseIcon(iconString: string) {
  const parts = iconString.split(' ')
  if (parts.length === 2) {
    return [parts[0], parts[1].replace('fa-', '')]
  }
  return ['fas', 'question']
}

function selectAvatar(avatar: Avatar) {
  selectedAvatar.value = avatar
}

function confirmSelection() {
  if (selectedAvatar.value) {
    emit('select', selectedAvatar.value)
  }
}

onMounted(() => {
  loadAvatars()
})
</script>

<style scoped>
.avatar-picker {
  width: 700px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}


.avatars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.avatar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  background-color: var(--color-surface);
}

.avatar-item:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.avatar-item.selected {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.avatar-preview {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-full);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-name {
  font-size: 0.75rem;
  text-align: center;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.selected-avatar-info {
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.selected-avatar-info h3 {
  font-size: 1rem;
  font-weight: bold;
  margin-bottom: var(--spacing-sm);
}

.avatar-preview-large {
  width: 100px;
  height: 100px;
  border-radius: var(--radius-full);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background);
  margin: 0 auto;
}

.avatar-image-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.loading-state svg {
  font-size: 2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}
</style>
