import socketClient from '@/api/socket'
import { markNetworkResume } from '@/api/client'
import { refreshVdock } from '@/composables/useVdockRefresh'
import { useDashboardStore } from '@/stores/dashboard'

/**
 * Self-healing for a deck that slept (DL-147): when the page comes back to the
 * foreground with a dead socket, dial at once instead of waiting out
 * socket.io's back-off; after every reconnect past the first, pull fresh
 * settings and profile so live faces and layouts are not stale. The viewer
 * stays on their scene and page, and an open editor is never refreshed under
 * the user's hands.
 */
export function initConnectionResume(): () => void {
  let connects = 0

  const onConnect = () => {
    connects += 1
    if (connects === 1) return
    if (useDashboardStore().isEditMode) return
    void refreshVdock({ keepPosition: true })
  }

  const onVisibilityChange = () => {
    if (document.visibilityState !== 'visible') return
    markNetworkResume()
    if (!socketClient.isConnected()) socketClient.ensureConnected()
  }

  const onOnline = () => {
    markNetworkResume()
    if (!socketClient.isConnected()) socketClient.ensureConnected()
  }

  socketClient.on('connect', onConnect)
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('online', onOnline)

  return () => {
    socketClient.off('connect', onConnect)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    window.removeEventListener('online', onOnline)
  }
}
