import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/** Day (light) look, per device: On, Off, or Auto (follows the system's light/dark setting). */
export function useDayMode() {
  const settings = useSettingsStore()
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
  const isDay = computed(() => settings.dayMode === 'on' || (settings.dayMode === 'auto' && systemLight.value))
  return { isDay }
}
