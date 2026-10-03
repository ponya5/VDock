import { computed, watch } from 'vue'
import { agentStates } from '@/services/agentState'
import { useDeviceClass } from '@/composables/useDeviceClass'

/**
 * DL-147 - on a phone or tablet a session asking for permission is what the
 * user is waiting for (the deck is their approval remote), so it wakes the
 * screensaver like a touch would. Desktop and the 7" panel keep today's
 * behaviour: the alert overlay shows over the saver without dismissing it.
 */
export function useWakeOnPermission(wake: () => void): void {
  const { deviceClass } = useDeviceClass()
  const permissionKey = computed(() =>
    Object.values(agentStates)
      .filter((entry) => entry.state === 'permission')
      .map((entry) => `${entry.source}:${entry.ts}`)
      .join(','),
  )

  watch(permissionKey, (key) => {
    if (key && (deviceClass.value === 'phone' || deviceClass.value === 'tablet')) wake()
  })
}
