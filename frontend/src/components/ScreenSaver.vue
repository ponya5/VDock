<template>
  <div
    v-if="visible"
    class="screensaver"
    @click="emit('dismiss')"
    @touchstart.passive="emit('dismiss')"
  >
    <div class="ss-glow"></div>

    <!-- Weather pinned to its own corner so it never competes for reading
         space with the clock or the widgets below it. -->
    <div
      v-if="showWeatherWidget"
      class="ss-weather-corner"
      :style="{ '--ss-weather-scale': String(weatherScale) }"
    >
      <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-corner-icon" />
      <div class="ss-weather-corner-info">
        <span class="ss-weather-corner-temp">{{ tempStr }}</span>
        <span class="ss-weather-corner-loc">{{ location }}</span>
      </div>
    </div>

    <div class="ss-body" :style="driftStyle">
      <div class="ss-time">{{ timeStr }}</div>
      <div class="ss-date">{{ dateStr }}</div>
    </div>

    <!-- Everything below the clock is one narrow, centered column rather than
         a row of side-by-side cards -- on a small touch panel a row like that
         squeezed each widget's text down to the point of being unreadable.
         News gets the most weight since it is the thing you actually read;
         market and world clock are compact chips underneath it. -->
    <div
      v-if="showNewsWidget || showMarketWidget || showWorldClockWidget"
      class="ss-widgets"
    >
      <div v-if="showNewsWidget" class="ss-news">
        <FontAwesomeIcon :icon="['fas', 'newspaper']" class="ss-news-icon" />

        <!-- A vertical carousel: the whole track slides up by one row per
             tick, so several headlines share one widget instead of a single
             truncated line. -->
        <div class="ss-news-viewport" aria-live="polite">
          <div
            class="ss-news-track"
            :style="{ transform: `translateY(calc(${-newsIndex} * var(--ss-news-slide-h)))` }"
          >
            <div
              v-for="(item, i) in newsHeadlines"
              :key="`${i}-${item.url || item.title}`"
              class="ss-news-slide"
              :aria-hidden="i !== newsIndex"
            >
              <span class="ss-news-title">{{ item.title }}</span>
              <span class="ss-news-source">{{ item.source }}</span>
            </div>

            <div v-if="!newsHeadlines.length" class="ss-news-slide">
              <span class="ss-news-title">
                {{ newsError || 'Loading headlines…' }}
              </span>
              <span class="ss-news-source">News</span>
            </div>
          </div>
        </div>

        <div v-if="newsHasMultiple" class="ss-news-progress">
          <span
            v-for="i in Math.min(newsHeadlines.length, 8)"
            :key="i"
            class="ss-news-dot"
            :class="{ 'is-active': (i - 1) === newsIndex % 8 }"
          ></span>
        </div>
      </div>

      <div v-if="showMarketWidget || showWorldClockWidget" class="ss-chip-row">
        <div v-if="showMarketWidget" class="ss-chip">
          <div v-for="coin in marketPrices" :key="coin.id" class="ss-chip-line">
            <span class="ss-chip-label">{{ coin.symbol }}</span>
            <span class="ss-chip-value">${{ coin.price.toLocaleString() }}</span>
          </div>
        </div>

        <div v-if="showWorldClockWidget" class="ss-chip">
          <div v-for="tz in worldClocks" :key="tz.label" class="ss-chip-line">
            <span class="ss-chip-label">{{ tz.label }}</span>
            <span class="ss-chip-value">{{ tz.time }}</span>
          </div>
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
const {
  headlines: newsHeadlines,
  index: newsIndex,
  hasMultiple: newsHasMultiple,
  error: newsError,
  start: startNews,
  stop: stopNews
} = useNews()
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
// User-set percentage (default 100) that enlarges the corner pill for small
// touch panels, where the vw-clamped sizes end up too small to glance at.
const weatherScale = computed(() => settingsStore.screensaverWeatherSize / 100)
const showNewsWidget = computed(() => settingsStore.screensaverWidgets.includes('news'))
const showMarketWidget = computed(() => settingsStore.screensaverWidgets.includes('market'))
const showWorldClockWidget = computed(() => settingsStore.screensaverWidgets.includes('worldclock'))

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
  font-size: clamp(4.5rem, 15vw, 10rem);
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

/* --- Weather: pinned to its own corner ------------------------------------ */
/* Kept out of the reading column entirely -- it's a glance-and-go value, not
   something you read, so it never has to fight the news carousel for space
   on a small touch panel. */
.ss-weather-corner {
  --ss-weather-scale: 1;
  position: absolute;
  top: clamp(1rem, 3vw, 2rem);
  right: clamp(1rem, 3vw, 2rem);
  display: flex;
  align-items: center;
  gap: calc(0.6rem * var(--ss-weather-scale));
  padding: calc(0.5rem * var(--ss-weather-scale)) calc(0.9rem * var(--ss-weather-scale));
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  pointer-events: none;
}

.ss-weather-corner-icon {
  font-size: calc(clamp(1.3rem, 2.4vw, 1.8rem) * var(--ss-weather-scale));
  color: #ff9f0a;
  flex-shrink: 0;
}

.ss-weather-corner-info {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.ss-weather-corner-temp {
  font-size: calc(clamp(1rem, 1.8vw, 1.3rem) * var(--ss-weather-scale));
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.ss-weather-corner-loc {
  font-size: calc(clamp(0.65rem, 1vw, 0.78rem) * var(--ss-weather-scale));
  color: rgba(255, 255, 255, 0.45);
}

/* --- Widgets column: news + chips, stacked below the clock ---------------- */
/* One narrow column instead of a row of cards. A row squeezed each widget's
   text down until it wasn't readable on a small touch screen; stacking lets
   every widget use the full width for its own content instead. */
.ss-widgets {
  margin-top: clamp(1.75rem, 5vh, 3.25rem);
  width: min(92vw, 640px);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.9rem;
}

.ss-news {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.3rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 14px;
}

.ss-news-icon {
  font-size: clamp(1.3rem, 2.2vw, 1.7rem);
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

/* One row is visible; the track slides up a row at a time. Height is bound to
   the two lines inside a slide so the transform lands exactly on a boundary. */
.ss-news-viewport {
  /* One row tall. The track is translated by exactly this much per step --
     a percentage would resolve against the track's own height (every slide
     stacked), which moved the carousel far past the end and showed blanks. */
  --ss-news-slide-h: 3.6em;
  flex: 1;
  min-width: 0;
  height: var(--ss-news-slide-h);
  overflow: hidden;
  position: relative;
  -webkit-mask-image: linear-gradient(
    to bottom, transparent, #000 14%, #000 86%, transparent
  );
  mask-image: linear-gradient(
    to bottom, transparent, #000 14%, #000 86%, transparent
  );
}

.ss-news-track {
  display: flex;
  flex-direction: column;
  transition: transform 620ms cubic-bezier(0.22, 0.61, 0.36, 1);
  will-change: transform;
}

.ss-news-slide {
  height: var(--ss-news-slide-h);
  flex: 0 0 var(--ss-news-slide-h);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  min-width: 0;
  text-align: left;
}

.ss-news-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: clamp(1rem, 2.2vw, 1.3rem);
  font-weight: 600;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.92);
  white-space: normal;
}

.ss-news-source {
  font-size: clamp(0.7rem, 1.2vw, 0.85rem);
  color: rgba(255, 255, 255, 0.42);
}

.ss-news-progress {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex-shrink: 0;
}

.ss-news-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  transition: background 300ms ease, transform 300ms ease;
}

.ss-news-dot.is-active {
  background: rgba(255, 255, 255, 0.85);
  transform: scale(1.6);
}

/* Market + world clock: compact chips underneath the news card, side by side
   on wide screens and stacked on a narrow touch panel. */
.ss-chip-row {
  display: flex;
  gap: 0.9rem;
  flex-wrap: wrap;
}

.ss-chip {
  flex: 1 1 200px;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.85rem 1.1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.ss-chip-line {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.75rem;
}

.ss-chip-label {
  font-size: clamp(0.75rem, 1.4vw, 0.9rem);
  color: rgba(255, 255, 255, 0.45);
  white-space: nowrap;
}

.ss-chip-value {
  font-size: clamp(0.95rem, 1.8vw, 1.15rem);
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .ss-news-track {
    transition: none;
  }
  .ss-news-dot {
    transition: none;
  }
}

/* Small touch panels: stack the chips instead of trying to fit them
   side by side, since that's where a row of cards became unreadable. */
@media (max-width: 480px) {
  .ss-chip-row {
    flex-direction: column;
  }
}
</style>
