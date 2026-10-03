import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { authState, clearAuthToken } from '@/services/auth'
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
      // The server now demands a token this device doesn't hold — the gate
      // takes over; unlocking with the just-set password reloads clean.
      authState.required = true
      authState.unlocked = false
    } else {
      authState.required = false
      clearAuthToken()
      notificationsStore.success('Authentication off', 'Devices no longer need the deck password.')
    }
    return true
  }

  return { setAuthEnabled }
}
