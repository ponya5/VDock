// DL-114 follow-up — "automatic" weather location resolves the machine's
// public IP via /api/geo first (works on the kiosk panel where
// navigator.geolocation is denied), then browser geolocation, then the
// saved manual city.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/socket', () => ({
  default: {
    on: vi.fn(),
    off: vi.fn(),
    isConnected: () => false,
    connect: vi.fn(),
    broadcastSettingsChange: vi.fn(),
  },
}))

vi.mock('@/api/client', () => ({
  default: { get: vi.fn().mockResolvedValue({ data: {} }), post: vi.fn(), put: vi.fn() },
}))

vi.mock('@/services/weatherService', () => ({
  geocodeCity: vi.fn(),
  reverseGeocode: vi.fn(async () => 'Browser City, US'),
  getBrowserLocation: vi.fn(),
  getMachineLocation: vi.fn(),
  fetchCurrentWeather: vi.fn(async (_coords: unknown, label: string) => ({
    temperature: 21, humidity: 50, windSpeed: 5,
    description: 'Clear Sky', icon: ['fas', 'sun'], location: label,
  })),
}))

import { useWeather } from '@/composables/useWeather'
import { useSettingsStore } from '@/stores/settings'
import {
  geocodeCity,
  getBrowserLocation,
  getMachineLocation,
  fetchCurrentWeather,
} from '@/services/weatherService'

const machineFix = { latitude: 32.08, longitude: 34.78, label: 'Tel Aviv, IL' }

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useWeather automatic location (DL-114 follow-up)', () => {
  it('uses the machine IP fix first — browser geolocation never runs', async () => {
    const settings = useSettingsStore()
    settings.weatherLocationMode = 'auto'
    vi.mocked(getMachineLocation).mockResolvedValue(machineFix)

    const { weather, error, refresh } = useWeather()
    await refresh()

    expect(error.value).toBeNull()
    expect(weather.value?.location).toBe('Tel Aviv, IL')
    expect(fetchCurrentWeather).toHaveBeenCalledWith(machineFix, 'Tel Aviv, IL')
    expect(getBrowserLocation).not.toHaveBeenCalled()
  })

  it('falls back to browser geolocation when the backend has no fix', async () => {
    const settings = useSettingsStore()
    settings.weatherLocationMode = 'auto'
    vi.mocked(getMachineLocation).mockResolvedValue(null)
    vi.mocked(getBrowserLocation).mockResolvedValue({ latitude: 1, longitude: 2 })

    const { weather, error, refresh } = useWeather()
    await refresh()

    expect(error.value).toBeNull()
    expect(weather.value?.location).toBe('Browser City, US')
    expect(getBrowserLocation).toHaveBeenCalledOnce()
  })

  it('falls back to the saved city when every auto source fails', async () => {
    const settings = useSettingsStore()
    settings.weatherLocationMode = 'auto'
    settings.weatherManualCity = 'Berlin'
    vi.mocked(getMachineLocation).mockResolvedValue(null)
    vi.mocked(getBrowserLocation).mockRejectedValue(new Error('denied'))
    vi.mocked(geocodeCity).mockResolvedValue({ latitude: 52.5, longitude: 13.4, label: 'Berlin, DE' })

    const { weather, error, refresh } = useWeather()
    await refresh()

    expect(error.value).toBeNull()
    expect(weather.value?.location).toBe('Berlin, DE')
  })

  it('manual mode still uses the saved city directly', async () => {
    const settings = useSettingsStore()
    settings.weatherLocationMode = 'manual'
    settings.weatherManualCity = 'Paris'
    vi.mocked(geocodeCity).mockResolvedValue({ latitude: 48.8, longitude: 2.3, label: 'Paris, FR' })

    const { weather, error, refresh } = useWeather()
    await refresh()

    expect(error.value).toBeNull()
    expect(weather.value?.location).toBe('Paris, FR')
    expect(getMachineLocation).not.toHaveBeenCalled()
    expect(getBrowserLocation).not.toHaveBeenCalled()
  })

  it('shows the honest error only when nothing resolves', async () => {
    const settings = useSettingsStore()
    settings.weatherLocationMode = 'auto'
    vi.mocked(getMachineLocation).mockResolvedValue(null)
    vi.mocked(getBrowserLocation).mockRejectedValue(new Error('denied'))

    const { error, refresh } = useWeather()
    await refresh()

    expect(error.value).toBe('Location unavailable — set a city in Settings')
  })
})
