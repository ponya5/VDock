import { computed } from 'vue'
import { agentStates } from '@/services/agentState'
import { isAgentWaitingDismissed } from '@/services/agentWaiting'

/**
 * DL-147 - how many agent sources need the user right now: blocked on a
 * permission dialog, or idle after a prompt (the same "ready and prompted,
 * not snoozed" rule the waiting glow and scene rails use). Read from the
 * socket-fed agent state, so the phone menu badge costs no polling.
 */
export function useNeedsYouCount() {
  return computed(() =>
    Object.values(agentStates).filter(
      (entry) =>
        entry.state === 'permission' ||
        (entry.state === 'ready' && entry.prompted === true && !isAgentWaitingDismissed(entry.source)),
    ).length,
  )
}
