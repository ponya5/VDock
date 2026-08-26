/**
 * Shared "refresh VDock" logic: re-fetches settings and profile data from the
 * backend and re-applies the current profile, without a full page reload.
 * Used by the header's manual Refresh button and automatically when the
 * Settings screen is closed, so changes made there (templates, integrations,
 * etc. — anything not covered by live settings sync) take effect immediately.
 */
import { useSettingsStore } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { useDashboardStore } from '@/stores/dashboard'
import socketClient from '@/api/socket'

const REFRESH_REQUEST_CHANNEL = 'vdock-refresh-request'
const REFRESH_REQUEST_STORAGE_KEY = 'vdock_refresh_request'

export async function refreshVdock(): Promise<void> {
  const settingsStore = useSettingsStore()
  const profilesStore = useProfilesStore()
  const dashboardStore = useDashboardStore()

  try {
    await settingsStore.loadSettingsFromServer()
    await profilesStore.loadProfiles()

    const profileId = dashboardStore.currentProfile?.id || localStorage.getItem('vdock_last_profile')
    if (profileId) {
      const profile = await profilesStore.getProfile(profileId)
      if (profile) {
        dashboardStore.setProfile(profile)
      }
    }

    if (!socketClient.isConnected()) {
      socketClient.disconnect()
      socketClient.connect()
    }
  } catch (error) {
    console.error('Failed to refresh VDock, reloading page:', error)
    window.location.reload()
  }
}

/**
 * Asks any other open VDock window/tab (e.g. the main dashboard, when
 * settings were opened in a separate browser tab) to refresh itself. Uses
 * BroadcastChannel where available, falling back to a localStorage "storage"
 * event for older browsers/contexts.
 */
export function requestVdockRefresh(): void {
  if ('BroadcastChannel' in window) {
    const channel = new BroadcastChannel(REFRESH_REQUEST_CHANNEL)
    channel.postMessage({ requestedAt: Date.now() })
    channel.close()
  }

  localStorage.setItem(REFRESH_REQUEST_STORAGE_KEY, String(Date.now()))
}

/**
 * Listens for refresh requests broadcast by `requestVdockRefresh` and runs
 * `refreshVdock`. Call once from the main dashboard view; returns a cleanup
 * function to remove the listeners on unmount.
 */
export function listenForVdockRefreshRequests(): () => void {
  let broadcastChannel: BroadcastChannel | null = null

  if ('BroadcastChannel' in window) {
    broadcastChannel = new BroadcastChannel(REFRESH_REQUEST_CHANNEL)
    broadcastChannel.onmessage = () => {
      void refreshVdock()
    }
  }

  const handleStorageEvent = (event: StorageEvent) => {
    if (event.key === REFRESH_REQUEST_STORAGE_KEY && event.newValue) {
      void refreshVdock()
    }
  }
  window.addEventListener('storage', handleStorageEvent)

  return () => {
    broadcastChannel?.close()
    broadcastChannel = null
    window.removeEventListener('storage', handleStorageEvent)
  }
}
