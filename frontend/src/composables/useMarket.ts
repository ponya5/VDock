import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import {
  fetchCryptoPrices,
  fetchQuotes,
  parseTickers,
  type CoinPrice,
} from '@/services/marketService'

const REFRESH_INTERVAL_MS = 5 * 60 * 1000

/** What the screensaver market chip shows: user tickers when configured
 *  (stocks via Yahoo, crypto via CoinGecko -- both through the backend),
 *  else BTC/ETH from the keyless CoinGecko endpoint as before. */
export function useMarket() {
  const settingsStore = useSettingsStore()
  const prices = ref<CoinPrice[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      const tickers = parseTickers(settingsStore.marketTickers)
      if (tickers.length) {
        const quotes = await fetchQuotes(tickers)
        prices.value = quotes.map(q => ({
          id: q.symbol,
          symbol: q.symbol,
          price: q.price,
        }))
        // An empty result used to leave the chip blank with no hint why —
        // say which symbols produced nothing so a typo is visible.
        if (!quotes.length) error.value = `No quotes for ${tickers.join(', ')}`
      } else {
        prices.value = await fetchCryptoPrices()
      }
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
