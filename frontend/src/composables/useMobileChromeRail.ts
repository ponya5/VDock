import { ref } from 'vue'

/**
 * The phone's scene bar can fold away on a short landscape screen (device pref
 * `railAutoHide`). While it is folded, the fullscreen and menu buttons dock to
 * the right edge and the deck reserves a gutter for them.
 */
const docked = ref(false)

export function useMobileChromeRail() {
  return { docked }
}
