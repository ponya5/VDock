/**
 * DL-133 — screensaver type registry.
 *
 * `screensaverStyle` can be any of the four ids below; `'shuffle'` is a
 * meta-type — ScreenSaver.vue rotates the *effective* style through
 * SHUFFLE_POOL every `screensaverShuffleMinutes` while the saver is up.
 * The saved value stays 'shuffle' — rotation never rewrites settings.
 */
export const SAVER_TYPES = [
  { id: 'widgets', label: 'Widget dashboard' },
  { id: 'spectrum', label: 'Spectrum visualizer' },
  { id: 'stats', label: 'System stats' },
  { id: 'shuffle', label: 'Shuffle' },
] as const

export type ScreensaverType = typeof SAVER_TYPES[number]['id']

/** The real views shuffle rotates through — never 'shuffle' itself. */
export const SHUFFLE_POOL: ScreensaverType[] = ['widgets', 'spectrum', 'stats']

export function saverTypeLabel(id: string): string {
  return SAVER_TYPES.find(t => t.id === id)?.label ?? 'Widget dashboard'
}

/** Next shuffle pick — always a real style, never the current one. */
export function pickNextSaverType(current: string): ScreensaverType {
  const pool = SHUFFLE_POOL.filter(t => t !== current)
  return pool[Math.floor(Math.random() * pool.length)]
}
