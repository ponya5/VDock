<template>
  <div class="media-picker">
    <div class="file-input-container">
      <input
        ref="fileInput"
        type="file"
        :accept="acceptedTypes"
        @change="handleFileSelect"
        class="file-input"
        style="display: none"
      />
      <button
        type="button"
        class="btn btn-secondary"
        @click="triggerFileSelect"
        :disabled="uploading"
      >
        <FontAwesomeIcon :icon="['fas', 'upload']" />
        {{ uploading ? 'Uploading...' : 'Upload Media File' }}
      </button>
    </div>

    <div v-if="uploadedMedia" class="uploaded-media">
      <div class="media-preview">
        <img
          v-if="uploadedMedia.media_type === 'image' || uploadedMedia.media_type === 'gif'"
          :src="uploadedMedia.url"
          :alt="uploadedMedia.filename"
          class="preview-image"
        />
        <video
          v-else-if="uploadedMedia.media_type === 'video'"
          :src="uploadedMedia.url"
          class="preview-video"
          muted
          loop
          autoplay
        />
      </div>
      <div class="media-info">
        <p class="filename">{{ uploadedMedia.filename }}</p>
        <p class="file-size">{{ formatFileSize(uploadedMedia.file_size) }}</p>
        <p class="media-type">{{ uploadedMedia.media_type.toUpperCase() }}</p>
      </div>
      <button
        type="button"
        class="btn btn-danger btn-sm"
        @click="removeMedia"
        title="Remove media"
      >
        <FontAwesomeIcon :icon="['fas', 'trash']" />
      </button>
    </div>

    <div v-if="error" class="error-message">
      <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
      {{ error }}
    </div>

    <div class="upload-info">
      <p class="info-text">
        <FontAwesomeIcon :icon="['fas', 'info-circle']" />
        Supported formats: GIF, MP4, WebM, MOV, AVI, PNG, JPG, JPEG
      </p>
      <p class="info-text">
        <FontAwesomeIcon :icon="['fas', 'weight-hanging']" />
        Maximum file size: 5MB
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'

interface Props {
  modelValue?: {
    url: string
    type: string
  } | null
  profileId: string
}

interface Emits {
  (e: 'update:modelValue', value: { url: string; type: string } | null): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const error = ref('')
const uploadedMedia = ref<{
  filename: string
  url: string
  media_type: string
  file_size: number
} | null>(null)

const acceptedTypes = '.gif,.mp4,.webm,.mov,.avi,.png,.jpg,.jpeg'

function triggerFileSelect() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return

  error.value = ''
  
  // Client-side validation
  const allowedTypes = ['image/gif', 'image/png', 'image/jpeg', 'image/jpg', 'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo']
  const allowedExtensions = ['.gif', '.png', '.jpg', '.jpeg', '.mp4', '.webm', '.mov', '.avi']
  
  // Check file type
  const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!allowedExtensions.includes(fileExt)) {
    error.value = 'Invalid file type. Allowed: GIF, PNG, JPG, JPEG, MP4, WebM, MOV, AVI'
    return
  }
  
  // Check file size (5MB limit)
  const maxSize = 5 * 1024 * 1024 // 5MB in bytes
  if (file.size > maxSize) {
    error.value = `File too large. Maximum size is 5MB, got ${(file.size / (1024 * 1024)).toFixed(1)}MB`
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('profile_id', props.profileId)

    const response = await apiClient.post('/upload/media', formData)

    if (response.data.success) {
      uploadedMedia.value = {
        filename: response.data.filename,
        url: response.data.url,
        media_type: response.data.media_type,
        file_size: response.data.file_size
      }

      emit('update:modelValue', {
        url: response.data.url,
        type: response.data.media_type
      })
    } else {
      error.value = response.data.error || 'Upload failed'
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Upload failed'
  } finally {
    uploading.value = false
    // Reset file input
    if (target) target.value = ''
  }
}

function removeMedia() {
  uploadedMedia.value = null
  emit('update:modelValue', null)
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Initialize with existing value
if (props.modelValue) {
  uploadedMedia.value = {
    filename: props.modelValue.url.split('/').pop() || 'media',
    url: props.modelValue.url,
    media_type: props.modelValue.type,
    file_size: 0 // We don't have this info from existing data
  }
}
</script>

<style scoped>
.media-picker {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.file-input-container {
  display: flex;
  justify-content: center;
}

.uploaded-media {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--color-surface-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.media-preview {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background-color: var(--color-surface);
}

.preview-image,
.preview-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-info {
  flex: 1;
  min-width: 0;
}

.filename {
  font-weight: 500;
  margin: 0 0 var(--spacing-xs) 0;
  word-break: break-all;
}

.file-size,
.media-type {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.error-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background-color: var(--color-error-bg);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}

.upload-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-text {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.75rem;
}

.btn-danger {
  background-color: var(--color-error);
  color: white;
  border: none;
}

.btn-danger:hover {
  background-color: var(--color-error-dark);
}
</style>
