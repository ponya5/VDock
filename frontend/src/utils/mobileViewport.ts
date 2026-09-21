import { computed, ref } from 'vue'

/**
 * Shared phone-viewport detection: a touch-capable device whose smaller
 * screen dimension is phone-sized (≤700px). Tablets (iPad ≈744–834px min
 * dim) and resized desktop windows (fine pointer, no touch points) are
 * excluded.
 *
 * Used to strip configuration affordances on phones — the deck stays a pure
 * control surface there (buttons + scene/page switching), while editing,
 * settings and profile management happen on the desktop.
 */
const vw = ref(0)
const vh = ref(0)
const isMobileViewport = ref(false)
const isPortrait = computed(() => vh.value > vw.value)

function update() {
  vw.value = window.innerWidth
  vh.value = window.innerHeight
  const coarse =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(pointer: coarse)').matches
  isMobileViewport.value =
    Math.min(vw.value, vh.value) <= 700 &&
    (coarse || navigator.maxTouchPoints > 0)
}

let installed = false

export function useMobileViewport() {
  if (!installed && typeof window !== 'undefined') {
    installed = true
    update()
    window.addEventListener('resize', update)
    window.addEventListener('orientationchange', update)
  }
  return { isMobileViewport, isPortrait }
}
