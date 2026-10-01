/**
 * Screensaver visibility shared with app-level chrome.
 *
 * DashboardView owns `screensaverVisible`; App.vue's BackgroundRenderer needs
 * it to suspend the animated dashboard background while the saver covers the
 * screen — occlusion doesn't stop rAF, so a shader background would otherwise
 * keep burning GPU under an opaque canvas and eat the saver's frame budget.
 */
import { ref } from 'vue'

/**
 * True once the saver is fully opaque — lags the visible flag by roughly the
 * saver-dissolve enter duration so the background stays alive through the
 * fade, and clears instantly on dismiss so it's back for the fade-out.
 */
export const screensaverCovered = ref(false)

const ENTER_MS = 500
let coverTimer: ReturnType<typeof setTimeout> | undefined

export function setScreensaverVisible(visible: boolean): void {
  clearTimeout(coverTimer)
  if (!visible) {
    screensaverCovered.value = false
    return
  }
  coverTimer = setTimeout(() => {
    screensaverCovered.value = true
  }, ENTER_MS)
}
