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
        <!-- Upload Custom Avatar Section -->
        <div class="upload-section">
          <h3>Upload Custom Avatar</h3>
          <div class="upload-area">
            <input 
              ref="fileInput"
              type="file" 
              accept="image/png,image/jpeg,image/jpg,image/gif"
              @change="handleFileUpload"
              style="display: none"
            />
            <button class="btn btn-primary upload-btn" @click="triggerFileInput">
              <FontAwesomeIcon :icon="['fas', 'upload']" />
              Upload Photo
            </button>
            <p class="upload-help">PNG, JPG, GIF - Max 5MB</p>
          </div>
          
          <div v-if="uploadedAvatar" class="uploaded-preview">
            <img :src="uploadedAvatar.url" alt="Uploaded avatar" class="uploaded-image" />
            <button class="btn btn-sm btn-danger" @click="removeUploadedAvatar">
              <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
            </button>
          </div>
        </div>

        <div class="divider">
          <span>OR CHOOSE FROM PRESETS</span>
        </div>

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
const uploadedAvatar = ref<Avatar | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

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
  // Clear uploaded avatar selection if selecting preset
  if (uploadedAvatar.value && avatar.id !== uploadedAvatar.value.id) {
    // Keep uploaded avatar but mark preset as selected
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  // Validate file type
  if (!file.type.match(/^image\/(png|jpeg|jpg|gif)$/)) {
    alert('Please upload a valid image file (PNG, JPG, or GIF)')
    return
  }
  
  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('File size must be less than 5MB')
    return
  }
  
  try {
    // Create FormData for upload
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', 'avatar')
    
    // Upload to backend
    const response = await apiClient.post('/upload/icon', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      const uploadedUrl = response.data.url
      
      // Create avatar object
      uploadedAvatar.value = {
        id: 'custom-uploaded',
        name: 'Custom Avatar',
        url: uploadedUrl,
        type: 'image',
        category: 'custom'
      }
      
      // Auto-select the uploaded avatar
      selectedAvatar.value = uploadedAvatar.value
    } else {
      alert('Failed to upload avatar: ' + (response.data.error || 'Unknown error'))
    }
  } catch (error: any) {
    console.error('Avatar upload error:', error)
    alert('Failed to upload avatar: ' + (error.message || 'Network error'))
  }
  
  // Reset file input
  if (target) {
    target.value = ''
  }
}

function removeUploadedAvatar() {
  uploadedAvatar.value = null
  if (selectedAvatar.value?.id === 'custom-uploaded') {
    selectedAvatar.value = null
  }
}

function confirmSelection() {
  // Prioritize uploaded avatar if selected
  const avatarToSelect = selectedAvatar.value || uploadedAvatar.value
  
  if (avatarToSelect) {
    emit('select', avatarToSelect)
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

/* Upload Section Styles */
.upload-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 2px dashed var(--color-border);
}

.upload-section h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text);
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.upload-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.uploaded-preview {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-md);
}

.uploaded-image {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-full);
  object-fit: cover;
  border: 2px solid var(--color-primary);
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: var(--spacing-lg) 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--color-border);
}

.divider span {
  padding: 0 var(--spacing-md);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.btn-sm {
  font-size: 0.75rem;
  padding: var(--spacing-xs) var(--spacing-sm);
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover {
  background-color: #dc2626;
}
</style>
