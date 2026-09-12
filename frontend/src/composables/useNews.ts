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

export function useNews() {
  const settingsStore = useSettingsStore()

  const headlines = ref<NewsHeadline[]>([])
  const index = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let rotateTimer: ReturnType<typeof setInterval> | null = null

  const current = computed<NewsHeadline | null>(
    () => headlines.value[index.value] ?? null
  )
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
      if (!result.length) error.value = 'No headlines available'
    } catch (err) {
      error.value = 'News unavailable'
      console.error('News fetch failed:', err)
    } finally {
      loading.value = false
    }
  }

  function next() {
    if (!headlines.value.length) return
    index.value = (index.value + 1) % headlines.value.length
  }

  function previous() {
    if (!headlines.value.length) return
    index.value =
      (index.value - 1 + headlines.value.length) % headlines.value.length
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
    stopRotation()
  }

  onUnmounted(stop)

  return {
    headlines,
    index,
    current,
    headline,
    source,
    hasMultiple,
    loading,
    error,
    rotateSeconds,
    refresh,
    next,
    previous,
    start,
    stop
  }
}
