import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useDevicePrefs } from '@/services/devicePrefs'

/** Day (light) look, per device: On, Off, or Auto (follows the system's light/dark setting). */
export function useDayMode() {
  const prefs = useDevicePrefs()
  const systemLight = ref(false)
  let query: MediaQueryList | null = null
  const sync = () => { systemLight.value = Boolean(query?.matches) }
  onMounted(() => {
    if (typeof window.matchMedia !== 'function') return
    query = window.matchMedia('(prefers-color-scheme: light)')
    sync()
    query.addEventListener?.('change', sync)
  })
  onUnmounted(() => query?.removeEventListener?.('change', sync))
  const isDay = computed(() => prefs.dayMode === 'on' || (prefs.dayMode === 'auto' && systemLight.value))
  return { isDay }
}
