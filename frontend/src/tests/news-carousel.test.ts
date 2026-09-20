// Feature: ai-dev-integration-packs, Property 4 (client half): the screensaver
// cycles through several headlines.
//
// The widget previously showed one GNews headline and needed an API key, so
// without one it showed nothing. It now pulls a merged RSS list from the
// backend and steps through it.
//
// The display is a stack of four tappable rows (DL-003): a tap opens the
// article's URL through the Electron shell / a new tab without dismissing
// the screensaver, and rotation advances a whole window of four so the row
// under the finger can't rotate out mid-tap. A touch pauses rotation for
// 20s.
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const get = vi.fn()
vi.mock('@/api/client', () => ({ default: { get: (...a: any[]) => get(...a) } }))

let useNews: any

const HEADLINES = [
  { title: 'First story', source: 'BBC News', url: 'https://e/1' },
  { title: 'Second story', source: 'Hacker News', url: 'https://e/2' },
  { title: 'Third story', source: 'Ars Technica', url: 'https://e/3' }
]

beforeEach(async () => {
  setActivePinia(createPinia())
  get.mockReset()
  get.mockResolvedValue({ data: { headlines: HEADLINES } })
  vi.resetModules()
  useNews = (await import('@/composables/useNews')).useNews
})

afterEach(() => {
  vi.useRealTimers()
})

describe('news rotation', () => {
  it('loads headlines from the backend, needing no API key', async () => {
    const news = useNews()
    await news.refresh()

    expect(get).toHaveBeenCalledWith('/news', {})
    expect(news.headlines.value).toHaveLength(3)
    expect(news.headline.value).toBe('First story')
    expect(news.source.value).toBe('BBC News')
  })

  it('advances the rotation index', async () => {
    const news = useNews()
    await news.refresh()

    // Window size is 4; on a 3-item list a step lands on index 1 either way.
    news.next()
    expect(news.headline.value).toBe('Second story')
    news.next()
    expect(news.headline.value).toBe('Third story')
  })

  it('shows a window of four headlines and steps by the window', async () => {
    const many = Array.from({ length: 9 }, (_, i) => ({
      title: `Story ${i}`,
      source: 'S',
      url: `https://e/${i}`
    }))
    get.mockResolvedValue({ data: { headlines: many } })
    const news = useNews()
    await news.refresh()

    expect(news.windowed.value.map((h: any) => h.title)).toEqual([
      'Story 0', 'Story 1', 'Story 2', 'Story 3'
    ])

    news.next()
    expect(news.windowed.value.map((h: any) => h.title)).toEqual([
      'Story 4', 'Story 5', 'Story 6', 'Story 7'
    ])

    // Wraps correctly when the count is not a multiple of the window size.
    news.next()
    expect(news.windowed.value[0].title).toBe('Story 8')
    expect(news.windowed.value).toHaveLength(4)
  })

  it('shows every headline when fewer than a full window', async () => {
    const news = useNews()
    await news.refresh()
    expect(news.windowed.value.map((h: any) => h.title)).toEqual([
      'First story', 'Second story', 'Third story'
    ])
  })

  it('pauses rotation after a touch and resumes on its own', async () => {
    vi.useFakeTimers()
    const many = Array.from({ length: 9 }, (_, i) => ({
      title: `Story ${i}`,
      source: 'S',
      url: `https://e/${i}`
    }))
    get.mockResolvedValue({ data: { headlines: many } })
    const news = useNews()
    await news.refresh()
    news.start()

    vi.advanceTimersByTime(8_000) // one tick at the default 8s interval
    expect(news.index.value).toBe(4)

    news.pause()
    vi.advanceTimersByTime(19_000)
    expect(news.index.value).toBe(4) // frozen while paused

    vi.advanceTimersByTime(9_000) // resume at +20s, first tick at +28s
    expect(news.index.value).toBe(8)
    news.stop()
  })

  it('wraps around at both ends', async () => {
    const news = useNews()
    await news.refresh()

    news.previous()
    expect(news.headline.value).toBe('Third story')
    news.next()
    expect(news.headline.value).toBe('First story')
  })

  it('does nothing when there are no headlines', async () => {
    get.mockResolvedValue({ data: { headlines: [] } })
    const news = useNews()
    await news.refresh()

    news.next()

    expect(news.index.value).toBe(0)
    expect(news.error.value).toBeTruthy()
  })

  it('keeps the index valid when the list shrinks on refresh', async () => {
    const news = useNews()
    await news.refresh()
    news.next()
    news.next()
    expect(news.index.value).toBe(2)

    get.mockResolvedValue({ data: { headlines: [HEADLINES[0]] } })
    await news.refresh()

    expect(news.index.value).toBe(0)
    expect(news.headline.value).toBe('First story')
  })

  it('reports a fetch failure instead of throwing', async () => {
    get.mockRejectedValue(new Error('offline'))
    const news = useNews()

    await news.refresh()

    expect(news.error.value).toBe('News unavailable')
    expect(news.headlines.value).toEqual([])
  })

  it('passes configured feeds through', async () => {
    const { useSettingsStore } = await import('@/stores/settings')
    const settings = useSettingsStore() as any
    settings.newsFeeds = 'https://a/feed\nhttps://b/feed'

    await useNews().refresh()

    expect(get).toHaveBeenCalledWith('/news', {
      feeds: 'https://a/feed,https://b/feed'
    })
  })

  it('only reports multiple when there is more than one headline', async () => {
    const news = useNews()
    await news.refresh()
    expect(news.hasMultiple.value).toBe(true)

    get.mockResolvedValue({ data: { headlines: [HEADLINES[0]] } })
    await news.refresh()
    expect(news.hasMultiple.value).toBe(false)
  })

  it('enforces a minimum rotation interval', async () => {
    const { useSettingsStore } = await import('@/stores/settings')
    const settings = useSettingsStore() as any

    settings.newsRotateSeconds = 1
    expect(useNews().rotateSeconds.value).toBeGreaterThanOrEqual(3)

    settings.newsRotateSeconds = 12
    expect(useNews().rotateSeconds.value).toBe(12)
  })
})

describe('tappable news rows', () => {
  const source = readFileSync(
    resolve(__dirname, '../components/ScreenSaver.vue'),
    'utf-8'
  )

  it('renders each visible headline as a button that opens its article', () => {
    expect(source).toContain('class="ss-news-row"')
    expect(source).toContain('@click.stop="openArticle(item)"')
  })

  it('keeps taps on the news card from reaching the dismiss handler', () => {
    // The root dismisses on click/touchstart; the news card must stop both.
    expect(source).toMatch(/class="ss-news"[\s\S]*?@touchstart\.stop/)
    expect(source).toMatch(/@click\.stop="pauseRotation\(\)"/)
  })

  it('keeps every row at least a finger tall', () => {
    const block = source.match(/\.ss-news-row\s*\{[\s\S]*?\}/)?.[0] ?? ''
    expect(block).toContain('min-height: 44px')
  })

  it('opens through the Electron shell when available, else a new tab', () => {
    expect(source).toContain('openExternal')
    expect(source).toMatch(/window\.open\(item\.url, '_blank'/)
  })

  it('pauses rotation when the system prefers reduced motion', () => {
    expect(source).toContain('prefers-reduced-motion')
  })
})

describe('screensaver layout', () => {
  const source = readFileSync(
    resolve(__dirname, '../components/ScreenSaver.vue'),
    'utf-8'
  )
  const layoutUtil = readFileSync(
    resolve(__dirname, '../utils/screensaverLayout.ts'),
    'utf-8'
  )

  it('positions every widget in its own absolutely-placed wrapper', () => {
    // Widgets live in .ss-pos wrappers whose left/top come from the saved
    // layout as viewport-percent widget centers (DL-013).
    expect(source).toContain('ss-pos')
    expect(source).toMatch(/\.ss-pos\s*\{[^}]*position:\s*absolute/)
    expect(source).toContain("left: `${l.x}%`")
    expect(source).toContain("top: `${l.y}%`")
  })

  it('pins weather to its own corner, separate from the other widgets', () => {
    // Weather is a glance value, not something to read -- it must not sit
    // inside the same visual group as news/market/world clock, where it
    // would compete with the headline for space on a small touch screen.
    expect(source).toContain('ss-pos ss-weather-corner')
  })

  it('gives the news headline more visual weight than the secondary chips', () => {
    const titleSize = source.match(/\.ss-news-title\s*\{[^}]*font-size:\s*clamp\(([^,]+)/)
    const chipSize = source.match(/\.ss-chip-value\s*\{[^}]*font-size:\s*clamp\(([^,]+)/)
    expect(titleSize).toBeTruthy()
    expect(chipSize).toBeTruthy()
    // Compare the clamp() minimums: the headline should never be the small one.
    expect(parseFloat(titleSize![1])).toBeGreaterThanOrEqual(parseFloat(chipSize![1]))
  })

  it('places news, market and world clock side by side in the default layout', () => {
    // DL-013: the three info widgets get distinct x centers so they render
    // as a row across the lower half instead of stacking.
    const newsX = layoutUtil.match(/news:\s*\{[^}]*x:\s*([\d.]+)/)
    const marketX = layoutUtil.match(/market:\s*\{[^}]*x:\s*([\d.]+)/)
    const worldclockX = layoutUtil.match(/worldclock:\s*\{[^}]*x:\s*([\d.]+)/)
    expect(newsX).toBeTruthy()
    expect(marketX).toBeTruthy()
    expect(worldclockX).toBeTruthy()
    const xs = [newsX, marketX, worldclockX].map(m => parseFloat(m![1]))
    expect(new Set(xs).size).toBe(3)
    expect(Math.min(...xs)).toBeLessThan(35)
    expect(Math.max(...xs)).toBeGreaterThan(65)
    // The clock stays centered and a bit above the middle.
    const clock = layoutUtil.match(/clock:\s*\{[^}]*x:\s*([\d.]+)[^}]*y:\s*([\d.]+)/)
    expect(parseFloat(clock![1])).toBe(50)
    expect(parseFloat(clock![2])).toBeLessThan(40)
  })

  it('falls back to a stacked column on narrow portrait panels', () => {
    expect(source).toMatch(/max-width:\s*620px[\s\S]*?\.ss-pos[\s\S]*?position:\s*relative/)
    expect(source).toMatch(/max-width:\s*620px[\s\S]*?transform:\s*none/)
  })

  it('supports a drag/resize edit mode that emits the saved layout', () => {
    expect(source).toContain('layoutEdit')
    expect(source).toContain('ss-editing')
    expect(source).toContain('ss-resize')
    expect(source).toContain("'save-layout'")
    // Children must not receive pointer events while editing or a drag
    // would trigger a news row's click.
    expect(source).toMatch(/\.ss-editing\s*>\s*\*:not\(\.ss-resize\)\s*\{[^}]*pointer-events:\s*none/)
  })
})
