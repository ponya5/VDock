import { computed } from 'vue'
import { useDeviceClass } from '@/composables/useDeviceClass'

/**
 * Legacy phone-viewport flag (DL-147: now a shim over `useDeviceClass`).
 *
 * `isMobileViewport` is the original rule — a touch-capable device whose
 * smaller viewport dimension is ≤700px — and is what strips configuration
 * affordances on phones (the deck stays a pure control surface there;
 * editing, settings and profile management happen on the desktop).
 * New behaviour should read `deviceClass` / `layoutClass` instead.
 */
export function useMobileViewport() {
  const { isCompactTouch, orientation } = useDeviceClass()
  const isPortrait = computed(() => orientation.value === 'portrait')
  return { isMobileViewport: isCompactTouch, isPortrait }
}
