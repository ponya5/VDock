import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { fetchTopHeadline } from '@/services/newsService'

const REFRESH_INTERVAL_MS = 30 * 60 * 1000

export function useNews() {
  const settingsStore = useSettingsStore()
  const headline = ref('')
  const source = ref('')
  const loading = ref(false)
  const error = ref<string | null>(null)
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  async function refresh() {
    if (!settingsStore.newsApiKey.trim()) {
      error.value = 'No API key configured'
      return
    }
    loading.value = true
    error.value = null
    try {
      const result = await fetchTopHeadline(settingsStore.newsApiKey.trim())
      headline.value = result.title
      source.value = result.source
    } catch (err) {
      error.value = 'News unavailable'
      console.error('News fetch failed:', err)
    } finally {
      loading.value = false
    }
  }

  function start() {
    refresh()
    refreshTimer = setInterval(refresh, REFRESH_INTERVAL_MS)
  }

  function stop() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  return { headline, source, loading, error, refresh, start, stop }
}
