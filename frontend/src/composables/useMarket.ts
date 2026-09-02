import { ref } from 'vue'
import { fetchCryptoPrices, type CoinPrice } from '@/services/marketService'

const REFRESH_INTERVAL_MS = 5 * 60 * 1000

export function useMarket() {
  const prices = ref<CoinPrice[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      prices.value = await fetchCryptoPrices()
    } catch (err) {
      error.value = 'Market data unavailable'
      console.error('Market fetch failed:', err)
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

  return { prices, loading, error, refresh, start, stop }
}
