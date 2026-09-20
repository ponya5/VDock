export type ScreensaverWidgetId = 'clock' | 'weather' | 'news' | 'market' | 'worldclock' | 'sports'

export interface ScreensaverWidgetLayout {
  /** Widget center as a percentage of viewport width. */
  x: number
  /** Widget center as a percentage of viewport height. */
  y: number
  /** Extra size multiplier applied on top of the size sliders. */
  scale: number
}

export type ScreensaverLayout = Record<ScreensaverWidgetId, ScreensaverWidgetLayout>

export const SCREENSAVER_WIDGET_IDS: ScreensaverWidgetId[] = [
  'clock',
  'weather',
  'news',
  'market',
  'worldclock',
  'sports',
]

export const SCREENSAVER_WIDGET_LABELS: Record<ScreensaverWidgetId, string> = {
  clock: 'Clock',
  weather: 'Weather',
  news: 'News',
  market: 'Market',
  worldclock: 'World Clock',
  sports: 'Sports',
}

/**
 * Editorial default: weather top-left, ticker top-right, big clock centered,
 * and the reading sections (headlines, sports, world time) in a row across
 * the lower half. Positions are widget centers in viewport percent; clamped
 * to 6..94 so a center-anchored widget can never be pushed fully off-screen.
 */
export const DEFAULT_SCREENSAVER_LAYOUT: ScreensaverLayout = {
  clock: { x: 50, y: 36, scale: 1 },
  weather: { x: 13, y: 9, scale: 1 },
  market: { x: 87, y: 9, scale: 1 },
  news: { x: 26, y: 78, scale: 1 },
  sports: { x: 60, y: 78, scale: 1 },
  worldclock: { x: 86, y: 76, scale: 1 },
}

function clampNum(v: unknown, min: number, max: number, fallback: number): number {
  return typeof v === 'number' && Number.isFinite(v)
    ? Math.min(max, Math.max(min, v))
    : fallback
}

export function defaultScreensaverLayout(): ScreensaverLayout {
  return JSON.parse(JSON.stringify(DEFAULT_SCREENSAVER_LAYOUT))
}

/** Accepts persisted JSON of any shape and always returns a full layout. */
export function normalizeScreensaverLayout(raw: unknown): ScreensaverLayout {
  const out = defaultScreensaverLayout()
  if (!raw || typeof raw !== 'object') return out
  const rec = raw as Record<string, Partial<ScreensaverWidgetLayout> | undefined>
  for (const id of SCREENSAVER_WIDGET_IDS) {
    const v = rec[id]
    if (!v || typeof v !== 'object') continue
    out[id] = {
      x: clampNum(v.x, 0, 100, out[id].x),
      y: clampNum(v.y, 0, 100, out[id].y),
      scale: clampNum(v.scale, 0.4, 3, out[id].scale),
    }
  }
  return out
}
