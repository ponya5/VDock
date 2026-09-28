<script setup lang="ts">
/**
 * "Request a feature" dialog (About tab). Posts the message + an optional
 * pasted/picked image to /api/feedback — the backend stores a copy and
 * relays it to the maintainer's inbox. The destination address never
 * appears in the frontend.
 */
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import { useNotificationsStore } from '@/stores/notifications'

const emit = defineEmits<{ (e: 'close'): void }>()
const notifications = useNotificationsStore()

const MAX_MESSAGE = 4000
const MAX_IMAGE_BYTES = 2 * 1024 * 1024

const message = ref('')
const imageFile = ref<File | null>(null)
const imagePreview = ref('')
const imageError = ref('')
const sending = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const messageLeft = computed(() => MAX_MESSAGE - message.value.length)
const canSend = computed(
  () => message.value.trim().length > 0 && message.value.length <= MAX_MESSAGE && !sending.value
)

function setImage(file: File | null) {
  imageError.value = ''
  if (!file) return clearImage()
  if (!file.type.startsWith('image/')) {
    imageError.value = 'Only image files can be attached'
    return
  }
  if (file.size > MAX_IMAGE_BYTES) {
    imageError.value = 'Image too large — keep it under 2MB'
    return
  }
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function clearImage() {
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imageFile.value = null
  imagePreview.value = ''
}

function onPaste(e: ClipboardEvent) {
  const item = [...(e.clipboardData?.items ?? [])].find(i => i.type.startsWith('image/'))
  const file = item?.getAsFile()
  if (file) setImage(file)
}

function onPick(e: Event) {
  setImage((e.target as HTMLInputElement).files?.[0] ?? null)
  if (fileInput.value) fileInput.value.value = ''
}

async function send() {
  if (!canSend.value) return
  sending.value = true
  try {
    const form = new FormData()
    form.append('message', message.value.trim())
    if (imageFile.value) form.append('image', imageFile.value)
    const { data } = await apiClient.post('/feedback', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (data?.success) {
      notifications.success(
        'Request sent',
        data.emailed
          ? 'Thanks — the developer has been emailed.'
          : 'Saved — the developer will see it. (Email relay unavailable right now.)'
      )
      emit('close')
    } else {
      notifications.error('Not sent', data?.message || 'The request could not be sent.')
    }
  } catch (e: any) {
    notifications.error('Not sent', e?.response?.data?.message || 'The request could not be sent.')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal feature-request" role="dialog" aria-modal="true" aria-label="Request a feature">
      <div class="modal-header">
        <h2><FontAwesomeIcon :icon="['fas', 'lightbulb']" /> Request a feature</h2>
        <button type="button" class="close-btn" aria-label="Close" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <p class="hint">
        Describe the feature — it's emailed straight to the developer. Paste an image to attach a screenshot.
      </p>

      <textarea
        v-model="message"
        class="input textarea fr-textarea"
        rows="6"
        :maxlength="MAX_MESSAGE"
        placeholder="What would make VDock better for you?"
        @paste="onPaste"
      />
      <div class="fr-meta">
        <span v-if="imageError" class="fr-error">{{ imageError }}</span>
        <span class="fr-count" :class="{ warn: messageLeft < 200 }">{{ messageLeft }}</span>
      </div>

      <div v-if="imagePreview" class="fr-attachment">
        <img :src="imagePreview" alt="Attached screenshot" class="fr-thumb" />
        <div class="fr-attachment-info">
          <span class="fr-attachment-name">{{ imageFile?.name || 'Pasted image' }}</span>
          <span class="fr-attachment-size">{{ Math.round((imageFile?.size ?? 0) / 1024) }} KB</span>
        </div>
        <button type="button" class="btn btn-secondary btn-sm" @click="clearImage">
          <FontAwesomeIcon :icon="['fas', 'times']" /> Remove
        </button>
      </div>

      <input ref="fileInput" type="file" accept="image/*" class="fr-file" @change="onPick" />

      <div class="fr-actions">
        <button type="button" class="btn btn-secondary btn-sm" @click="fileInput?.click()">
          <FontAwesomeIcon :icon="['fas', 'image']" /> Attach image
        </button>
        <span class="fr-spacer" />
        <button type="button" class="btn btn-secondary" @click="emit('close')">Cancel</button>
        <button type="button" class="btn primary" :disabled="!canSend" @click="send">
          <FontAwesomeIcon :icon="['fas', sending ? 'spinner' : 'paper-plane']" :spin="sending" />
          {{ sending ? 'Sending…' : 'Send' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.feature-request {
  width: 560px;
  padding: var(--spacing-lg) var(--spacing-xl);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.modal-header h2 {
  margin: 0;
  font-size: clamp(16px, 1.2vw + 12px, 20px);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.close-btn {
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

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}

.hint {
  margin: 0 0 var(--spacing-md);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.fr-textarea {
  width: 100%;
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

/* iOS Safari force-zooms focused inputs under 16px. */
@media (pointer: coarse) {
  .fr-textarea {
    font-size: clamp(16px, 1rem, 18px);
  }
}

.fr-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  min-height: 18px;
}

.fr-error {
  font-size: 0.78rem;
  color: #f87171;
}

.fr-count {
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--color-text-secondary);
}

.fr-count.warn {
  color: var(--warn, #fbbf24);
}

.fr-attachment {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.15);
}

.fr-thumb {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.fr-attachment-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.fr-attachment-name {
  font-size: 0.8rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fr-attachment-size {
  font-size: 0.72rem;
  color: var(--color-text-secondary);
}

.fr-file {
  display: none;
}

.fr-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: var(--spacing-md);
  flex-wrap: wrap;
}

.fr-spacer {
  flex: 1;
}
</style>
