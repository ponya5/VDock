<template>
  <div 
    class="notification-toast" 
    :class="[`toast-${notification.type}`, { 'toast-dismissing': isDismissing }]"
    @mouseenter="pauseAutoDismiss"
    @mouseleave="resumeAutoDismiss"
  >
    <div class="toast-icon">
      <FontAwesomeIcon :icon="getIcon()" />
    </div>
    
    <div class="toast-content">
      <div class="toast-header">
        <h4 class="toast-title">{{ notification.title }}</h4>
        <button 
          v-if="notification.dismissible"
          class="toast-close"
          @click="handleDismiss"
          title="Dismiss"
        >
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>
      
      <p class="toast-message">{{ notification.message }}</p>
      
      <div v-if="notification.details" class="toast-details">
        <button 
          class="details-toggle"
          @click="showDetails = !showDetails"
        >
          <FontAwesomeIcon :icon="['fas', showDetails ? 'chevron-up' : 'chevron-down']" />
          {{ showDetails ? 'Hide' : 'Show' }} Details
        </button>
        <pre v-if="showDetails" class="details-content">{{ notification.details }}</pre>
      </div>
      
      <div v-if="notification.actions && notification.actions.length > 0" class="toast-actions">
        <button
          v-for="(action, index) in notification.actions"
          :key="index"
          class="toast-action-btn"
          :class="{ 'primary': action.primary }"
          @click="handleAction(action)"
        >
          {{ action.label }}
        </button>
      </div>
    </div>
    
    <div v-if="notification.duration > 0" class="toast-progress">
      <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Notification, NotificationAction } from '@/stores/notifications'
import { useNotificationsStore } from '@/stores/notifications'

interface Props {
  notification: Notification
}

const props = defineProps<Props>()
const emit = defineEmits<{
  dismiss: [id: string]
}>()

const notificationsStore = useNotificationsStore()
const showDetails = ref(false)
const isDismissing = ref(false)
const progress = ref(100)
let progressInterval: number | null = null
let autoDismissTimeout: number | null = null
let isPaused = ref(false)
let remainingTime = ref(props.notification.duration)
let lastTime = Date.now()

function getIcon() {
  switch (props.notification.type) {
    case 'success':
      return ['fas', 'check-circle']
    case 'error':
      return ['fas', 'times-circle']
    case 'warning':
      return ['fas', 'exclamation-triangle']
    case 'info':
      return ['fas', 'info-circle']
    default:
      return ['fas', 'bell']
  }
}

function handleDismiss() {
  isDismissing.value = true
  setTimeout(() => {
    notificationsStore.markAsRead(props.notification.id)
    emit('dismiss', props.notification.id)
  }, 300) // Match animation duration
}

function handleAction(action: NotificationAction) {
  action.handler()
  handleDismiss()
}

function pauseAutoDismiss() {
  isPaused.value = true
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  if (autoDismissTimeout) {
    clearTimeout(autoDismissTimeout)
    autoDismissTimeout = null
    // Calculate remaining time
    const elapsed = Date.now() - lastTime
    remainingTime.value = Math.max(0, remainingTime.value - elapsed)
  }
}

function resumeAutoDismiss() {
  isPaused.value = false
  if (props.notification.duration > 0 && remainingTime.value > 0) {
    lastTime = Date.now()
    startProgress()
  }
}

function startProgress() {
  if (props.notification.duration <= 0) return
  
  const interval = 50 // Update every 50ms
  const totalSteps = remainingTime.value / interval
  let currentStep = 0
  
  progressInterval = window.setInterval(() => {
    currentStep++
    progress.value = Math.max(0, 100 - (currentStep / totalSteps) * 100)
    
    if (currentStep >= totalSteps) {
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      handleDismiss()
    }
  }, interval)
}

onMounted(() => {
  if (props.notification.duration > 0) {
    lastTime = Date.now()
    startProgress()
  }
})

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  if (autoDismissTimeout) {
    clearTimeout(autoDismissTimeout)
  }
})
</script>

<style scoped>
.notification-toast {
  position: relative;
  width: 400px;
  max-width: 90vw;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  animation: slideIn 0.3s ease-out;
  border-left: 4px solid;
  backdrop-filter: blur(10px);
}

.notification-toast.toast-dismissing {
  animation: slideOut 0.3s ease-out forwards;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
    max-height: 200px;
    margin-bottom: var(--spacing-sm);
  }
  to {
    transform: translateX(100%);
    opacity: 0;
    max-height: 0;
    margin-bottom: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
}

.toast-success {
  border-left-color: var(--color-success);
}

.toast-error {
  border-left-color: var(--color-error);
}

.toast-warning {
  border-left-color: var(--color-warning);
}

.toast-info {
  border-left-color: var(--color-info);
}

.toast-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  font-size: 1.2rem;
}

.toast-success .toast-icon {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-success);
}

.toast-error .toast-icon {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.toast-warning .toast-icon {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.toast-info .toast-icon {
  background: rgba(59, 130, 246, 0.1);
  color: var(--color-info);
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.toast-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
}

.toast-close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.toast-close:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.toast-message {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.toast-details {
  margin-top: var(--spacing-sm);
}

.details-toggle {
  background: transparent;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 4px;
}

.details-toggle:hover {
  background: var(--color-surface-hover);
}

.details-content {
  margin: var(--spacing-xs) 0 0;
  padding: var(--spacing-sm);
  background: var(--color-background);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 150px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
}

.toast-actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
}

.toast-action-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toast-action-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
}

.toast-action-btn.primary {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.toast-action-btn.primary:hover {
  background: var(--color-primary-dark);
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
}

.progress-bar {
  height: 100%;
  transition: width 0.05s linear;
}

.toast-success .progress-bar {
  background: var(--color-success);
}

.toast-error .progress-bar {
  background: var(--color-error);
}

.toast-warning .progress-bar {
  background: var(--color-warning);
}

.toast-info .progress-bar {
  background: var(--color-info);
}

/* Responsive */
@media (max-width: 768px) {
  .notification-toast {
    width: calc(100vw - 32px);
    max-width: none;
  }
}
</style>

