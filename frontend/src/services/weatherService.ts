/** Free, no-API-key weather via Open-Meteo, with BigDataCloud for reverse geocoding. */

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface WeatherResult {
  temperature: number
  humidity: number
  windSpeed: number
  description: string
  icon: [string, string]
  location: string
}

// WMO weather codes → description + FontAwesome icon
const WEATHER_CODE_MAP: Record<number, { description: string; icon: [string, string] }> = {
  0: { description: 'Clear Sky', icon: ['fas', 'sun'] },
  1: { description: 'Mostly Clear', icon: ['fas', 'sun'] },
  2: { description: 'Partly Cloudy', icon: ['fas', 'cloud-sun'] },
  3: { description: 'Overcast', icon: ['fas', 'cloud'] },
  45: { description: 'Fog', icon: ['fas', 'smog'] },
  48: { description: 'Rime Fog', icon: ['fas', 'smog'] },
  51: { description: 'Light Drizzle', icon: ['fas', 'cloud-rain'] },
  53: { description: 'Drizzle', icon: ['fas', 'cloud-rain'] },
  55: { description: 'Dense Drizzle', icon: ['fas', 'cloud-rain'] },
  61: { description: 'Light Rain', icon: ['fas', 'cloud-rain'] },
  63: { description: 'Rain', icon: ['fas', 'cloud-showers-heavy'] },
  65: { description: 'Heavy Rain', icon: ['fas', 'cloud-showers-heavy'] },
  71: { description: 'Light Snow', icon: ['fas', 'snowflake'] },
  73: { description: 'Snow', icon: ['fas', 'snowflake'] },
  75: { description: 'Heavy Snow', icon: ['fas', 'snowflake'] },
  80: { description: 'Rain Showers', icon: ['fas', 'cloud-showers-heavy'] },
  81: { description: 'Rain Showers', icon: ['fas', 'cloud-showers-heavy'] },
  82: { description: 'Violent Showers', icon: ['fas', 'cloud-showers-heavy'] },
  95: { description: 'Thunderstorm', icon: ['fas', 'bolt'] },
  96: { description: 'Thunderstorm', icon: ['fas', 'bolt'] },
  99: { description: 'Severe Thunderstorm', icon: ['fas', 'bolt'] }
}

function describeWeatherCode(code: number) {
  return WEATHER_CODE_MAP[code] ?? { description: 'Unknown', icon: ['fas', 'cloud-sun'] as [string, string] }
}

export async function geocodeCity(city: string): Promise<(Coordinates & { label: string }) | null> {
  const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Geocoding request failed')
  const data = await response.json()
  const match = data.results?.[0]
  if (!match) return null
  const label = match.admin1 ? `${match.name}, ${match.admin1}` : `${match.name}, ${match.country_code}`
  return { latitude: match.latitude, longitude: match.longitude, label }
}

export async function reverseGeocode(coords: Coordinates): Promise<string> {
  const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${coords.latitude}&longitude=${coords.longitude}&localityLanguage=en`
  const response = await fetch(url)
  if (!response.ok) return 'Current Location'
  const data = await response.json()
  const city = data.city || data.locality || data.principalSubdivision
  return city ? `${city}, ${data.countryCode || data.countryName || ''}`.replace(/, $/, '') : 'Current Location'
}

export function getBrowserLocation(): Promise<Coordinates> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
      (error) => reject(error),
      { timeout: 10000, maximumAge: 10 * 60 * 1000 }
    )
  })
}

export async function fetchCurrentWeather(coords: Coordinates, location: string): Promise<WeatherResult> {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${coords.latitude}&longitude=${coords.longitude}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&timezone=auto`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Weather request failed')
  const data = await response.json()
  const current = data.current
  const { description, icon } = describeWeatherCode(current.weather_code)

  return {
    temperature: Math.round(current.temperature_2m),
    humidity: Math.round(current.relative_humidity_2m),
    windSpeed: Math.round(current.wind_speed_10m),
    description,
    icon,
    location
  }
}
