import { ref, computed, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { fetchHeadlines, parseFeedList, type NewsHeadline } from '@/services/newsService'

/**
 * Rotating headlines for the screensaver.
 *
 * Previously this fetched a single GNews headline and needed an API key, so
 * without one the widget showed nothing at all. It now pulls a merged list
 * from RSS feeds via the backend and steps through it, which is what makes a
 * carousel possible: there was only ever one item to show before.
 */
const REFRESH_INTERVAL_MS = 15 * 60 * 1000
const DEFAULT_ROTATE_SECONDS = 8
const MIN_ROTATE_SECONDS = 3
/**
 * The screensaver shows this many headlines at once and rotation steps a
 * whole window, not one item — with one-at-a-time stepping a tap could land a
 * beat after the headline you were reading swapped out.
 */
export const NEWS_WINDOW_SIZE = 4
/** Rotation pauses this long after any touch so a tap hits what you saw. */
const TOUCH_PAUSE_MS = 20 * 1000

export function useNews(feedsSource?: () => string[], label = 'News') {
  const settingsStore = useSettingsStore()

  const headlines = ref<NewsHeadline[]>([])
  const index = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let rotateTimer: ReturnType<typeof setInterval> | null = null
  let resumeTimer: ReturnType<typeof setTimeout> | null = null

  const current = computed<NewsHeadline | null>(
    () => headlines.value[index.value] ?? null
  )
  /** The visible block: up to NEWS_WINDOW_SIZE items starting at `index`. */
  const windowed = computed<NewsHeadline[]>(() => {
    const list = headlines.value
    if (!list.length) return []
    const start = index.value % list.length
    const size = Math.min(NEWS_WINDOW_SIZE, list.length)
    return Array.from(
      { length: size },
      (_, i) => list[(start + i) % list.length]
    )
  })
  // Kept so existing template bindings (newsHeadline / newsSource) still work.
  const headline = computed(() => current.value?.title ?? '')
  const source = computed(() => current.value?.source ?? '')
  const hasMultiple = computed(() => headlines.value.length > 1)

  const rotateSeconds = computed(() => {
    const configured = Number(
      (settingsStore as Record<string, unknown>).newsRotateSeconds
    )
    if (!Number.isFinite(configured) || configured <= 0) {
      return DEFAULT_ROTATE_SECONDS
    }
    return Math.max(MIN_ROTATE_SECONDS, configured)
  })

  function configuredFeeds(): string[] {
    // A caller-supplied source (e.g. the sports widget's sportsFeeds list)
    // wins; otherwise fall back to the regular headlines setting.
    if (feedsSource) return feedsSource()
    return parseFeedList((settingsStore as Record<string, unknown>).newsFeeds)
  }

  async function refresh(force = false) {
    loading.value = true
    error.value = null
    try {
      const result = await fetchHeadlines(configuredFeeds(), force)
      headlines.value = result
      // Keep the pointer valid when the list shrinks.
      if (index.value >= result.length) index.value = 0
      if (!result.length) error.value = `No ${label.toLowerCase()} headlines available`
    } catch (err) {
      error.value = `${label} unavailable`
      console.error('News fetch failed:', err)
    } finally {
      loading.value = false
    }
  }

  function next() {
    if (!headlines.value.length) return
    index.value = (index.value + NEWS_WINDOW_SIZE) % headlines.value.length
  }

  function previous() {
    if (!headlines.value.length) return
    index.value =
      (((index.value - NEWS_WINDOW_SIZE) % headlines.value.length) +
        headlines.value.length) %
      headlines.value.length
  }

  function startRotation() {
    stopRotation()
    // Respect the OS setting; an auto-advancing carousel is exactly the kind
    // of motion people turn this off for.
    const reduced =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduced) return

    rotateTimer = setInterval(next, rotateSeconds.value * 1000)
  }

  function stopRotation() {
    if (rotateTimer) {
      clearInterval(rotateTimer)
      rotateTimer = null
    }
  }

  /**
   * Freeze rotation after a touch so the row under the finger stays put;
   * resumes on its own once the pause elapses.
   */
  function pause(ms = TOUCH_PAUSE_MS) {
    stopRotation()
    if (resumeTimer) clearTimeout(resumeTimer)
    resumeTimer = setTimeout(() => {
      resumeTimer = null
      startRotation()
    }, ms)
  }

  function start() {
    refresh()
    refreshTimer = setInterval(() => refresh(), REFRESH_INTERVAL_MS)
    startRotation()
  }

  function stop() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    if (resumeTimer) {
      clearTimeout(resumeTimer)
      resumeTimer = null
    }
    stopRotation()
  }

  onUnmounted(stop)

  return {
    headlines,
    index,
    current,
    windowed,
    headline,
    source,
    hasMultiple,
    loading,
    error,
    rotateSeconds,
    refresh,
    next,
    previous,
    pause,
    start,
    stop
  }
}
