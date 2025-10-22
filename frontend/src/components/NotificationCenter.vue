<template>
  <div class="notification-center">
    <!-- Notification Bell Icon -->
    <button 
      class="notification-bell"
      :class="{ 'has-unread': notificationsStore.unreadCount > 0 }"
      @click="togglePanel"
      title="Notifications"
    >
      <FontAwesomeIcon :icon="['fas', 'bell']" />
      <span v-if="notificationsStore.unreadCount > 0" class="badge">
        {{ notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount }}
      </span>
    </button>
    
    <!-- Notification Panel -->
    <Transition name="panel">
      <div v-if="showPanel" class="notification-panel" @click.stop>
        <div class="panel-header">
          <h3>Notifications</h3>
          <div class="header-actions">
            <button
              v-if="notificationsStore.notifications.length > 0"
              class="action-btn"
              @click="notificationsStore.markAllAsRead"
              title="Mark all as read"
            >
              <FontAwesomeIcon :icon="['fas', 'check-double']" />
            </button>
            <button
              v-if="notificationsStore.notifications.length > 0"
              class="action-btn"
              @click="notificationsStore.downloadLogs"
              title="Export logs"
            >
              <FontAwesomeIcon :icon="['fas', 'download']" />
            </button>
            <button
              class="action-btn"
              @click="togglePanel"
              title="Close"
            >
              <FontAwesomeIcon :icon="['fas', 'times']" />
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <div class="panel-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab-btn"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
            <span v-if="getTabCount(tab.id) > 0" class="tab-count">
              {{ getTabCount(tab.id) }}
            </span>
          </button>
        </div>
        
        <!-- Notification List -->
        <div class="panel-content">
          <div v-if="filteredNotifications.length === 0" class="empty-state">
            <FontAwesomeIcon :icon="['fas', 'inbox']" class="empty-icon" />
            <p>No notifications</p>
          </div>
          
          <div v-else class="notification-list">
            <div
              v-for="notification in filteredNotifications"
              :key="notification.id"
              class="notification-item"
              :class="[
                `item-${notification.type}`,
                { 'unread': !notification.read }
              ]"
              @click="markAsRead(notification.id)"
            >
              <div class="item-icon">
                <FontAwesomeIcon :icon="getNotificationIcon(notification.type)" />
              </div>
              
              <div class="item-content">
                <div class="item-header">
                  <h4 class="item-title">{{ notification.title }}</h4>
                  <span class="item-time">{{ formatTime(notification.timestamp) }}</span>
                </div>
                <p class="item-message">{{ notification.message }}</p>
                
                <div v-if="notification.details" class="item-details">
                  <button
                    class="details-toggle"
                    @click.stop="toggleDetails(notification.id)"
                  >
                    <FontAwesomeIcon 
                      :icon="['fas', expandedDetails.has(notification.id) ? 'chevron-up' : 'chevron-down']" 
                    />
                    {{ expandedDetails.has(notification.id) ? 'Hide' : 'Show' }} Details
                  </button>
                  <pre v-if="expandedDetails.has(notification.id)" class="details-text">{{ notification.details }}</pre>
                </div>
                
                <div v-if="notification.actions" class="item-actions">
                  <button
                    v-for="(action, index) in notification.actions"
                    :key="index"
                    class="action-btn-item"
                    :class="{ 'primary': action.primary }"
                    @click.stop="handleAction(action, notification.id)"
                  >
                    {{ action.label }}
                  </button>
                </div>
              </div>
              
              <button
                v-if="notification.dismissible"
                class="item-dismiss"
                @click.stop="notificationsStore.dismiss(notification.id)"
                title="Dismiss"
              >
                <FontAwesomeIcon :icon="['fas', 'times']" />
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="filteredNotifications.length > 0" class="panel-footer">
          <button class="clear-btn" @click="handleClearAll">
            Clear All
          </button>
        </div>
      </div>
    </Transition>
    
    <!-- Toast Container -->
    <div class="toast-container">
      <NotificationToast
        v-for="toast in notificationsStore.toasts"
        :key="toast.id"
        :notification="toast"
        @dismiss="notificationsStore.dismiss"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useNotificationsStore } from '@/stores/notifications'
import type { NotificationAction } from '@/stores/notifications'
import NotificationToast from './NotificationToast.vue'

const notificationsStore = useNotificationsStore()
const showPanel = ref(false)
const activeTab = ref('all')
const expandedDetails = ref(new Set<string>())

const tabs = [
  { id: 'all', label: 'All' },
  { id: 'error', label: 'Errors' },
  { id: 'warning', label: 'Warnings' },
  { id: 'info', label: 'Info' }
]

const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') {
    return notificationsStore.notifications
  }
  return notificationsStore.getNotificationsByType(activeTab.value as any)
})

function getTabCount(tabId: string): number {
  if (tabId === 'all') {
    return notificationsStore.unreadCount
  }
  return notificationsStore.getNotificationsByType(tabId as any)
    .filter(n => !n.read).length
}

function togglePanel() {
  showPanel.value = !showPanel.value
}

function markAsRead(id: string) {
  notificationsStore.markAsRead(id)
}

function toggleDetails(id: string) {
  if (expandedDetails.value.has(id)) {
    expandedDetails.value.delete(id)
  } else {
    expandedDetails.value.add(id)
  }
}

function handleAction(action: NotificationAction, notificationId: string) {
  action.handler()
  notificationsStore.dismiss(notificationId)
}

function handleClearAll() {
  if (confirm('Are you sure you want to clear all notifications?')) {
    notificationsStore.dismissAll()
  }
}

function getNotificationIcon(type: string) {
  switch (type) {
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

function formatTime(timestamp: Date): string {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'Just now'
}

// Close panel when clicking outside
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.notification-center')) {
    showPanel.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-bell {
  position: relative;
  background: transparent;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  font-size: 1.1rem;
}

.notification-bell:hover {
  background: var(--color-surface-hover);
}

.notification-bell.has-unread {
  color: var(--color-primary);
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--color-error);
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 5px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 1;
}

.notification-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 400px;
  max-width: 90vw;
  max-height: 600px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
  backdrop-filter: blur(20px);
}

.panel-enter-active,
.panel-leave-active {
  transition: all 0.2s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.panel-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--color-text);
}

.header-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.action-btn {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.panel-tabs {
  display: flex;
  gap: 4px;
  padding: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tab-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.tab-btn.active {
  background: var(--color-primary);
  color: white;
}

.tab-count {
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.tab-btn.active .tab-count {
  background: rgba(255, 255, 255, 0.3);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  max-height: 450px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.3;
  margin-bottom: var(--spacing-md);
}

.notification-list {
  padding: var(--spacing-xs);
}

.notification-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--color-background);
  border-left: 3px solid transparent;
}

.notification-item:hover {
  background: var(--color-surface-hover);
}

.notification-item.unread {
  background: rgba(var(--color-primary-rgb, 102, 126, 234), 0.05);
}

.notification-item.item-error {
  border-left-color: var(--color-error);
}

.notification-item.item-warning {
  border-left-color: var(--color-warning);
}

.notification-item.item-info {
  border-left-color: var(--color-info);
}

.notification-item.item-success {
  border-left-color: var(--color-success);
}

.item-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  font-size: 1rem;
}

.item-error .item-icon {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.item-warning .item-icon {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.item-info .item-icon {
  background: rgba(59, 130, 246, 0.1);
  color: var(--color-info);
}

.item-success .item-icon {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-success);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 4px;
}

.item-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-time {
  flex-shrink: 0;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.item-message {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.item-details {
  margin-top: var(--spacing-xs);
}

.details-toggle {
  background: transparent;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all var(--transition-fast);
}

.details-toggle:hover {
  text-decoration: underline;
}

.details-text {
  margin: var(--spacing-xs) 0 0;
  padding: var(--spacing-sm);
  background: var(--color-background);
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 100px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
}

.item-actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
}

.action-btn-item {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn-item:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
}

.action-btn-item.primary {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.item-dismiss {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all var(--transition-fast);
}

.notification-item:hover .item-dismiss {
  opacity: 1;
}

.item-dismiss:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.panel-footer {
  padding: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.clear-btn {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  transition: all var(--transition-fast);
  width: 100%;
}

.clear-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-error);
  color: var(--color-error);
}

.toast-container {
  position: fixed;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  pointer-events: none;
}

.toast-container > * {
  pointer-events: all;
}

@media (max-width: 768px) {
  .notification-panel {
    position: fixed;
    top: auto;
    bottom: 0;
    right: 0;
    left: 0;
    width: 100%;
    max-width: none;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }
  
  .toast-container {
    left: var(--spacing-md);
    right: var(--spacing-md);
    top: var(--spacing-md);
  }
}
</style>

