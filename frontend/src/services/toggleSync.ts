import socketClient from '@/api/socket'
import apiClient from '@/api/client'
import { useButtonStateStore } from '@/stores/buttonState'

/**
 * Toggle state sync. The backend owns toggle sides (process memory); presses
 * broadcast `toggle_state` so every window/device paints the same switch.
 * A freshly loaded client fetches /actions/toggles to catch up.
 */

let initialized = false

export function useToggleSync() {
  function init() {
    if (initialized) return
    initialized = true
    const buttonState = useButtonStateStore()

    socketClient.on('toggle_state', (payload: { button_id?: string; side?: number; sublabel?: string }) => {
      if (!payload?.button_id || (payload.side !== 0 && payload.side !== 1)) return
      buttonState.set(payload.button_id, {
        toggleSide: payload.side as 0 | 1,
        sublabel: payload.sublabel,
      })
    })

    // Sides recorded while this client was offline.
    apiClient.get('/actions/toggles')
      .then((res) => {
        const sides: Record<string, number> = res.data?.sides ?? {}
        for (const [buttonId, side] of Object.entries(sides)) {
          if (side === 0 || side === 1) {
            buttonState.set(buttonId, { toggleSide: side as 0 | 1 })
          }
        }
      })
      .catch(() => { /* backend offline — ignore */ })
  }

  return { init }
}
