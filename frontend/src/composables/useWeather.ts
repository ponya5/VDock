import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import {
  geocodeCity,
  reverseGeocode,
  getBrowserLocation,
  fetchCurrentWeather,
  type WeatherResult
} from '@/services/weatherService'

const REFRESH_INTERVAL_MS = 15 * 60 * 1000

export function useWeather() {
  const settingsStore = useSettingsStore()
  const weather = ref<WeatherResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  async function refresh() {
    loading.value = true
    error.value = null

    try {
      if (settingsStore.weatherLocationMode === 'manual' && settingsStore.weatherManualCity.trim()) {
        const geocoded = await geocodeCity(settingsStore.weatherManualCity.trim())
        if (!geocoded) {
          error.value = `Couldn't find "${settingsStore.weatherManualCity}"`
          return
        }
        weather.value = await fetchCurrentWeather(geocoded, geocoded.label)
        return
      }

      const coords = await getBrowserLocation()
      const location = await reverseGeocode(coords)
      weather.value = await fetchCurrentWeather(coords, location)
    } catch (err) {
      if (settingsStore.weatherLocationMode === 'auto' && settingsStore.weatherManualCity.trim()) {
        // Geolocation failed/denied but a manual city is on file — fall back to it
        try {
          const geocoded = await geocodeCity(settingsStore.weatherManualCity.trim())
          if (geocoded) {
            weather.value = await fetchCurrentWeather(geocoded, geocoded.label)
            return
          }
        } catch {
          // fall through to error below
        }
      }
      error.value = 'Location unavailable — set a city in Settings'
      console.error('Weather fetch failed:', err)
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

  return { weather, loading, error, refresh, start, stop }
}
