import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useSettingsStore } from './settings'

export interface NotificationAction {
  label: string
  handler: () => void
  primary?: boolean
}

export interface Notification {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  title: string
  message: string
  details?: string
  actions?: NotificationAction[]
  duration: number
  dismissible: boolean
  timestamp: Date
  read: boolean
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const maxNotifications = 100 // Keep last 100 notifications
  
  // Computed
  const unreadCount = computed(() => 
    notifications.value.filter(n => !n.read).length
  )
  
  const errorCount = computed(() =>
    notifications.value.filter(n => n.type === 'error' && !n.read).length
  )
  
  const warningCount = computed(() =>
    notifications.value.filter(n => n.type === 'warning' && !n.read).length
  )
  
  const toasts = computed(() => {
    const settingsStore = useSettingsStore()
    const unreadNotifications = notifications.value.filter(n => !n.read)
    
    // If showRegularToasts is disabled, only show error toasts
    if (!settingsStore.showRegularToasts) {
      return unreadNotifications.filter(n => n.type === 'error').slice(-3)
    }
    
    // Otherwise show all types
    return unreadNotifications.slice(-3) // Show last 3 unread
  })
  
  // Actions
  function addNotification(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
    const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      read: false,
      dismissible: notification.dismissible ?? true,
      duration: notification.duration ?? getDurationByType(notification.type)
    }
    
    notifications.value.unshift(newNotification)
    
    // Trim to max notifications
    if (notifications.value.length > maxNotifications) {
      notifications.value = notifications.value.slice(0, maxNotifications)
    }
    
    // Auto-dismiss if duration is set
    if (newNotification.duration > 0) {
      setTimeout(() => {
        markAsRead(id)
      }, newNotification.duration)
    }
    
    return id
  }
  
  function getDurationByType(type: Notification['type']): number {
    switch (type) {
      case 'error':
        return 8000 // 8 seconds for errors
      case 'warning':
        return 6000 // 6 seconds for warnings
      case 'info':
        return 4000 // 4 seconds for info
      case 'success':
        return 3000 // 3 seconds for success
      default:
        return 5000
    }
  }
  
  function success(title: string, message: string, options?: Partial<Notification>) {
    return addNotification({
      type: 'success',
      title,
      message,
      ...options
    })
  }
  
  function error(title: string, message: string, details?: string, options?: Partial<Notification>) {
    return addNotification({
      type: 'error',
      title,
      message,
      details,
      duration: 0, // Errors don't auto-dismiss by default
      ...options
    })
  }
  
  function warning(title: string, message: string, options?: Partial<Notification>) {
    return addNotification({
      type: 'warning',
      title,
      message,
      ...options
    })
  }
  
  function info(title: string, message: string, options?: Partial<Notification>) {
    return addNotification({
      type: 'info',
      title,
      message,
      ...options
    })
  }
  
  function markAsRead(id: string) {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }
  
  function markAllAsRead() {
    notifications.value.forEach(n => {
      n.read = true
    })
  }
  
  function dismiss(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  function dismissAll() {
    notifications.value = []
  }
  
  function getNotificationById(id: string): Notification | undefined {
    return notifications.value.find(n => n.id === id)
  }
  
  function getNotificationsByType(type: Notification['type']): Notification[] {
    return notifications.value.filter(n => n.type === type)
  }
  
  function exportLogs(): string {
    const logs = notifications.value.map(n => ({
      timestamp: n.timestamp.toISOString(),
      type: n.type,
      title: n.title,
      message: n.message,
      details: n.details
    }))
    
    return JSON.stringify(logs, null, 2)
  }
  
  function downloadLogs() {
    const logs = exportLogs()
    const blob = new Blob([logs], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `vdock-logs-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  return {
    notifications,
    unreadCount,
    errorCount,
    warningCount,
    toasts,
    addNotification,
    success,
    error,
    warning,
    info,
    markAsRead,
    markAllAsRead,
    dismiss,
    dismissAll,
    getNotificationById,
    getNotificationsByType,
    exportLogs,
    downloadLogs
  }
})

