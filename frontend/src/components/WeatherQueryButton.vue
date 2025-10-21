<template>
  <div class="weather-query" :class="[weatherClass, { compact: compact }]">
    <!-- Compact Mode -->
    <div v-if="compact" class="weather-compact">
      <div v-if="loading" class="loading-compact">
        <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
      </div>
      
      <div v-else-if="error" class="error-compact">
        <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
      </div>
      
      <div v-else-if="weatherData" class="weather-content-compact">
        <div class="weather-icon-compact">
          <FontAwesomeIcon :icon="weatherIcon" />
        </div>
        <div class="weather-temp-compact">
          {{ weatherData.temperature }}{{ weatherData.unit_symbol || '°' + weatherData.unit }}
        </div>
        <div class="weather-desc-compact">{{ weatherData.description }}</div>
      </div>
    </div>
    
    <!-- Full Mode -->
    <div v-else>
      <div class="weather-header">
        <FontAwesomeIcon :icon="['fas', 'cloud-sun']" class="header-icon" />
        <span class="header-title">Weather query</span>
      </div>
      
      <div v-if="loading" class="loading-state">
        <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
        <span>Loading weather...</span>
      </div>
      
      <div v-else-if="error" class="error-state">
        <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
        <span>{{ error }}</span>
      </div>
      
      <div v-else-if="weatherData" class="weather-content">
        <div class="weather-main">
          <div class="weather-icon">
            <FontAwesomeIcon :icon="weatherIcon" />
          </div>
          <div class="weather-temp">
            {{ weatherData.temperature }}{{ weatherData.unit_symbol || '°' + weatherData.unit }}
          </div>
        </div>
        
        <div class="weather-description">{{ weatherData.description }}</div>
        
        <div class="weather-location">
          <FontAwesomeIcon :icon="['fas', 'map-marker-alt']" />
          {{ weatherData.location }}
        </div>
        
        <!-- Demo mode indicator -->
        <div v-if="isDemoMode" class="demo-mode-indicator">
          <FontAwesomeIcon :icon="['fas', 'info-circle']" />
          <span>Demo Mode - Get your own API key at weatherapi.com</span>
        </div>
        
        <div class="weather-details">
          <div class="detail-item">
            <FontAwesomeIcon :icon="['fas', 'tint']" />
            <span>{{ weatherData.humidity }}%</span>
          </div>
          <div class="detail-item">
            <FontAwesomeIcon :icon="['fas', 'wind']" />
            <span>{{ weatherData.windSpeed }}</span>
          </div>
          <div class="detail-item">
            <FontAwesomeIcon :icon="['fas', 'eye']" />
            <span>{{ weatherData.visibility }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'

interface Props {
  location?: string
  refreshInterval?: number
  compact?: boolean
  unit?: string
}

const props = withDefaults(defineProps<Props>(), {
  location: 'auto',
  refreshInterval: 15, // minutes
  compact: false,
  unit: 'C'
})

interface WeatherData {
  temperature: number
  unit: string
  unit_symbol?: string
  description: string
  condition: string
  location: string
  humidity: number
  windSpeed: string
  visibility: string
  icon: string
}

const weatherData = ref<WeatherData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const isDemoMode = ref(false)
let intervalId: number | null = null

const weatherClass = computed(() => {
  if (!weatherData.value || !weatherData.value.condition) return ''
  
  const condition = weatherData.value.condition.toLowerCase()
  
  if (condition.includes('clear') || condition.includes('sunny')) {
    return 'weather-clear'
  } else if (condition.includes('cloud')) {
    return 'weather-cloudy'
  } else if (condition.includes('rain') || condition.includes('drizzle')) {
    return 'weather-rainy'
  } else if (condition.includes('snow')) {
    return 'weather-snowy'
  } else if (condition.includes('storm') || condition.includes('thunder')) {
    return 'weather-stormy'
  }
  
  return 'weather-default'
})

const weatherIcon = computed(() => {
  if (!weatherData.value || !weatherData.value.condition) return ['fas', 'cloud']
  
  const condition = weatherData.value.condition.toLowerCase()
  
  if (condition.includes('clear') || condition.includes('sunny')) {
    return ['fas', 'sun']
  } else if (condition.includes('partly')) {
    return ['fas', 'cloud-sun']
  } else if (condition.includes('cloud')) {
    return ['fas', 'cloud']
  } else if (condition.includes('rain') || condition.includes('drizzle')) {
    return ['fas', 'cloud-rain']
  } else if (condition.includes('snow')) {
    return ['fas', 'snowflake']
  } else if (condition.includes('storm') || condition.includes('thunder')) {
    return ['fas', 'bolt']
  } else if (condition.includes('fog') || condition.includes('mist')) {
    return ['fas', 'smog']
  }
  
  return ['fas', 'cloud']
})

async function fetchWeather() {
  loading.value = true
  error.value = null
  
  try {
    const response = await apiClient.get('/weather', {
      params: {
        location: props.location,
        unit: props.unit || 'C'
      }
    })
    
    weatherData.value = response.data.data
    
    // Check if we're in demo mode based on the message
    isDemoMode.value = response.data.message && response.data.message.includes('demo mode')
  } catch (err: any) {
    console.error('Failed to fetch weather:', err)
    
    // Mock data for demo purposes
    weatherData.value = {
      temperature: props.unit === 'C' ? 22 : 72,
      unit: props.unit || 'C',
      unit_symbol: props.unit === 'C' ? '°C' : '°F',
      description: 'Partly Cloudy',
      condition: 'Partly Cloudy',
      location: props.location === 'auto' ? 'Your Location' : props.location,
      humidity: 65,
      windSpeed: props.unit === 'C' ? '13 km/h' : '8 mph',
      visibility: props.unit === 'C' ? '16 km' : '10 mi',
      icon: 'partly-cloudy'
    }
    
    error.value = null // Clear error for mock data
    isDemoMode.value = true // Mock data means demo mode
  } finally {
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  intervalId = setInterval(fetchWeather, props.refreshInterval * 60 * 1000) as unknown as number
}

function stopPolling() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  fetchWeather()
  startPolling()
})

// Watch for unit changes and refetch weather
watch(() => props.unit, () => {
  fetchWeather()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.weather-query {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: var(--spacing-md);
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: var(--radius-md);
  color: white;
  position: relative;
  overflow: hidden;
}

.weather-query::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.weather-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  position: relative;
  z-index: 1;
}

.header-icon {
  font-size: 1rem;
  opacity: 0.9;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  opacity: 0.9;
}

.weather-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.weather-main {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.weather-icon {
  font-size: 3rem;
  opacity: 0.9;
}

.weather-temp {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
}

.temp-unit {
  font-size: 1.5rem;
  opacity: 0.8;
}

.weather-description {
  font-size: 1.1rem;
  margin-bottom: var(--spacing-xs);
  opacity: 0.9;
}

.weather-location {
  font-size: 0.85rem;
  opacity: 0.7;
  margin-bottom: var(--spacing-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.weather-details {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.85rem;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  flex: 1;
  color: white;
  position: relative;
  z-index: 1;
}

/* Weather condition specific styles */
.weather-clear {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.weather-cloudy {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}

.weather-rainy {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.weather-snowy {
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}

.weather-stormy {
  background: linear-gradient(135deg, #434343 0%, #000000 100%);
}

/* Compact Mode Styles */
.weather-query.compact {
  padding: 0.5rem;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.weather-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.loading-compact,
.error-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
}

.weather-content-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.weather-icon-compact {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.weather-temp-compact {
  font-size: 1.2rem;
  font-weight: 600;
  line-height: 1;
}

.weather-desc-compact {
  font-size: 0.7rem;
  opacity: 0.8;
  line-height: 1;
  text-align: center;
}

.demo-mode-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 0.25rem;
  font-size: 0.7rem;
  color: #ffc107;
  opacity: 0.9;
}

.demo-mode-indicator svg {
  font-size: 0.8rem;
}
</style>

