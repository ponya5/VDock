import socketClient from '@/api/socket'
import { setProfileKeepingPosition } from '@/composables/useVdockRefresh'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { useProfilesStore } from '@/stores/profiles'

export const PROFILE_REFETCH_DEBOUNCE_MS = 500

/**
 * A layout saved on another device reaches this one (DL-147). The server only
 * relays the profile id; if it is the profile on screen the new copy is
 * fetched (bursts of saves collapse into one fetch) and swapped in without
 * moving the viewer. An open editor is never overwritten: it gets a toast.
 */
export function initProfileSync(): () => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  let changedId: string | null = null

  async function apply() {
    const id = changedId
    changedId = null
    timer = null
    const dashboardStore = useDashboardStore()
    if (!id || dashboardStore.currentProfile?.id !== id) return

    if (dashboardStore.isEditMode) {
      useNotificationsStore().info('Profile changed on another device', 'Refresh to load the latest layout.')
      return
    }

    const profile = await useProfilesStore().getProfile(id)
    if (profile && !dashboardStore.isEditMode) setProfileKeepingPosition(profile)
  }

  const onProfileChanged = (payload: { id?: unknown }) => {
    if (typeof payload?.id !== 'string') return
    if (useDashboardStore().currentProfile?.id !== payload.id) return
    changedId = payload.id
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => void apply(), PROFILE_REFETCH_DEBOUNCE_MS)
  }

  socketClient.on('profile_changed', onProfileChanged)

  return () => {
    socketClient.off('profile_changed', onProfileChanged)
    if (timer) clearTimeout(timer)
    timer = null
  }
}
