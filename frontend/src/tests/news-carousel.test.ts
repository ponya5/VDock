// Feature: ai-dev-integration-packs, Property 4 (client half): the screensaver
// cycles through several headlines.
//
// The widget previously showed one GNews headline and needed an API key, so
// without one it showed nothing. It now pulls a merged RSS list from the
// backend and steps through it.
//
// One of these pins down a bug that only a running browser revealed: the track
// was translated by `index * 100%`, but a percentage translate resolves against
// the *track's own height* -- every slide stacked -- not one slide. At index 5
// of 15 that scrolled 45 slides down instead of 5, so the widget showed blanks.
// The transform now multiplies a single-slide custom property instead.
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

describe('news carousel', () => {
  it('loads headlines from the backend, needing no API key', async () => {
    const news = useNews()
    await news.refresh()

    expect(get).toHaveBeenCalledWith('/news', {})
    expect(news.headlines.value).toHaveLength(3)
    expect(news.headline.value).toBe('First story')
    expect(news.source.value).toBe('BBC News')
  })

  it('advances one headline at a time', async () => {
    const news = useNews()
    await news.refresh()

    news.next()
    expect(news.headline.value).toBe('Second story')
    news.next()
    expect(news.headline.value).toBe('Third story')
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

describe('carousel transform', () => {
  const source = readFileSync(
    resolve(__dirname, '../components/ScreenSaver.vue'),
    'utf-8'
  )

  it('translates by one slide height, not a percentage', () => {
    // `translateY(-${index * 100}%)` resolves against the track's own height
    // (all slides stacked), so each step moved by the whole list.
    expect(source).not.toMatch(/translateY\(-\$\{newsIndex \* 100\}%\)/)
    expect(source).toContain('var(--ss-news-slide-h)')
  })

  it('defines the slide height once and reuses it', () => {
    const declarations = source.match(/--ss-news-slide-h:\s*[\d.]+em/g) ?? []
    expect(declarations).toHaveLength(1)
    // Viewport height, slide height and slide flex-basis all reference it.
    const uses = source.match(/var\(--ss-news-slide-h\)/g) ?? []
    expect(uses.length).toBeGreaterThanOrEqual(4)
  })

  it('pauses rotation when the system prefers reduced motion', () => {
    expect(source).toContain('prefers-reduced-motion')
  })
})
