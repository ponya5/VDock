<template>
  <div
    v-if="visible"
    class="screensaver"
    @click="emit('dismiss')"
    @touchstart.passive="emit('dismiss')"
  >
    <div class="ss-glow"></div>

    <div class="ss-body" :style="driftStyle">
      <div class="ss-time">{{ timeStr }}</div>
      <div class="ss-date">{{ dateStr }}</div>
    </div>

    <div class="ss-bottom-bar" :class="`ss-bottom-bar-count-${activeWidgetCount}`">
      <div v-if="showWeatherWidget" class="ss-card ss-card-weather">
        <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-icon" />
        <div class="ss-card-info">
          <span class="ss-card-main">{{ tempStr }}</span>
          <span class="ss-card-sub">{{ location }}</span>
        </div>
      </div>

      <div v-if="showNewsWidget" class="ss-card ss-card-news">
        <FontAwesomeIcon :icon="['fas', 'newspaper']" class="ss-card-icon" />
        <div class="ss-card-info">
          <span class="ss-card-main ss-card-main-truncate">{{ newsHeadline || 'Loading headlines…' }}</span>
          <span class="ss-card-sub">{{ newsSource || 'News' }}</span>
        </div>
      </div>

      <div v-if="showMarketWidget" class="ss-card ss-card-market">
        <div v-for="coin in marketPrices" :key="coin.id" class="ss-market-row">
          <span class="ss-market-symbol">{{ coin.symbol }}</span>
          <span class="ss-market-price">${{ coin.price.toLocaleString() }}</span>
        </div>
      </div>

      <div v-if="showWorldClockWidget" class="ss-card ss-card-worldclock">
        <div v-for="tz in worldClocks" :key="tz.label" class="ss-worldclock-row">
          <span class="ss-worldclock-label">{{ tz.label }}</span>
          <span class="ss-worldclock-time">{{ tz.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useWeather } from '@/composables/useWeather'
import { useNews } from '@/composables/useNews'
import { useMarket } from '@/composables/useMarket'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ dismiss: [] }>()

const settingsStore = useSettingsStore()

const time = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null

const { weather, start: startWeather, stop: stopWeather } = useWeather()
const { headline: newsHeadline, source: newsSource, start: startNews, stop: stopNews } = useNews()
const { prices: marketPrices, start: startMarket, stop: stopMarket } = useMarket()

const timeStr = computed(() =>
  time.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
)
const dateStr = computed(() =>
  time.value.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' }).toUpperCase()
)

const weatherIcon = computed(() => weather.value?.icon || ['fas', 'cloud-sun'])
const tempStr = computed(() => weather.value ? `${weather.value.temperature}°C` : '--°C')
const location = computed(() => weather.value?.location || '—')

const showWeatherWidget = computed(() => settingsStore.screensaverWidgets.includes('weather'))
const showNewsWidget = computed(() => settingsStore.screensaverWidgets.includes('news'))
const showMarketWidget = computed(() => settingsStore.screensaverWidgets.includes('market'))
const showWorldClockWidget = computed(() => settingsStore.screensaverWidgets.includes('worldclock'))

const activeWidgetCount = computed(() =>
  [showWeatherWidget, showNewsWidget, showMarketWidget, showWorldClockWidget].filter(w => w.value).length
)

const WORLD_CLOCK_ZONES = [
  { label: 'New York', tz: 'America/New_York' },
  { label: 'London', tz: 'Europe/London' },
  { label: 'Tokyo', tz: 'Asia/Tokyo' },
]

const worldClocks = computed(() =>
  WORLD_CLOCK_ZONES.map(z => ({
    label: z.label,
    time: new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: z.tz }).format(time.value)
  }))
)

// Drift: ±20 px on X and Y on a 30-second sine cycle
const driftX = ref(0)
const driftY = ref(0)
let driftTimer: ReturnType<typeof setInterval> | null = null
let driftTick = 0

// Reset drift position each time the screensaver becomes visible so the
// clock never appears shifted on re-show.
watch(() => props.visible, (v) => {
  if (v) driftTick = 0
})

function updateDrift() {
  driftTick += 1
  driftX.value = Math.sin(driftTick / 60) * 20
  driftY.value = Math.cos(driftTick / 90) * 16
}

const driftStyle = computed(() => ({
  transform: `translate(${driftX.value}px, ${driftY.value}px)`,
}))

onMounted(() => {
  clockTimer = setInterval(() => { time.value = new Date() }, 1000)
  driftTimer = setInterval(updateDrift, 500)
  startWeather()
  if (showNewsWidget.value) startNews()
  if (showMarketWidget.value) startMarket()
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (driftTimer) clearInterval(driftTimer)
  stopWeather()
  stopNews()
  stopMarket()
})
</script>

<style scoped>
.screensaver {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: #050510;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.ss-glow {
  position: absolute;
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 400px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(0, 80, 200, 0.18), transparent 70%);
  pointer-events: none;
}

.ss-body {
  text-align: center;
  transition: transform 0.5s ease;
}

.ss-time {
  font-size: clamp(5rem, 16vw, 10rem);
  font-weight: 200;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1;
}

.ss-date {
  margin-top: 0.5rem;
  font-size: clamp(0.85rem, 1.8vw, 1.15rem);
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.38);
}

.ss-bottom-bar {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  width: min(92vw, 900px);
}

.ss-card {
  flex: 1 1 220px;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.9rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.ss-card-weather {
  padding: 1.1rem 1.4rem;
}

.ss-weather-icon {
  font-size: 2rem;
  color: #ff9f0a;
  flex-shrink: 0;
}

.ss-card-weather .ss-weather-icon {
  font-size: 3.2rem;
}

.ss-card-icon {
  font-size: 1.6rem;
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.ss-card-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.ss-card-main {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.ss-card-weather .ss-card-main {
  font-size: 1.6rem;
}

.ss-card-main-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.ss-card-sub {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.ss-card-market,
.ss-card-worldclock {
  flex-direction: column;
  align-items: stretch;
  gap: 0.4rem;
}

.ss-market-row,
.ss-worldclock-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.ss-market-symbol,
.ss-worldclock-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.ss-market-price,
.ss-worldclock-time {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}
</style>
