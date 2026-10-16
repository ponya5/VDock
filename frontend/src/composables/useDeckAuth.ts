import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { authState, clearAuthToken, probeAuth } from '@/services/auth'
import type { ServerConfig } from '@/types'

/**
 * Turning the deck password on or off (DL-126). Shared by Security and the
 * password prompt in Connect so both write through one path.
 */
export function useDeckAuth() {
  const settingsStore = useSettingsStore()
  const notificationsStore = useNotificationsStore()

  /** Returns false (and reports it) when the server rejected the change. */
  async function setAuthEnabled(enabled: boolean, password?: string): Promise<boolean> {
    const payload: Partial<ServerConfig> = { require_auth: enabled }
    if (password !== undefined) payload.auth_password = password
    const ok = await settingsStore.updateServerConfig(payload)
    if (!ok) {
      notificationsStore.error('Could not save', 'Server rejected the change.')
      return false
    }
    if (enabled) {
      // Other devices now need the password; this one may not (the computer
      // VDock runs on is trusted, DL-008) - ask the server instead of
      // assuming the lock screen.
      authState.required = true
      await probeAuth()
    } else {
      authState.required = false
      clearAuthToken()
      notificationsStore.success('Authentication off', 'Devices no longer need the deck password.')
    }
    return true
  }

  return { setAuthEnabled }
}
