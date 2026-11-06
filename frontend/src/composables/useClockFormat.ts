import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/** Extra Intl options for locale-driven clocks: forces 24-hour when the
 *  "24-hour clocks" setting is on, otherwise leaves the device locale in charge.
 *  `h23` (not `hour12: false`) so midnight reads 00, never 24. */
export function useClockFormat() {
  const settings = useSettingsStore()
  return computed<Intl.DateTimeFormatOptions>(() => (settings.clock24h ? { hourCycle: 'h23' } : {}))
}
