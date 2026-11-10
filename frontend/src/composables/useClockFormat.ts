import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/** Extra Intl options for locale-driven clocks: forces 24-hour when the
 *  "24-hour clocks" setting is on, otherwise leaves the device locale in charge.
 *  `h23` (not `hour12: false`) so midnight reads 00, never 24. */
export function useClockFormat() {
  const settings = useSettingsStore()
  return computed<Intl.DateTimeFormatOptions>(() => (settings.clock24h ? { hourCycle: 'h23' } : {}))
}

/** The AM/PM text for a formatToParts result. Empty whenever "24-hour clocks"
 *  is on, even if the engine's Intl ignored `hourCycle` and still emitted a
 *  dayPeriod part (seen on some Electron/OS locale combinations). */
export function pickDayPeriod(parts: Intl.DateTimeFormatPart[], clock24h: boolean): string {
  if (clock24h) return ''
  return parts.find(part => part.type === 'dayPeriod')?.value ?? ''
}
