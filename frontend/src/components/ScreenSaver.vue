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

    <div class="ss-bottom-bar">
      <div class="ss-card">
        <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-icon" />
        <div class="ss-card-info">
          <span class="ss-card-main">{{ tempStr }}</span>
          <span class="ss-card-sub">{{ location }}</span>
        </div>
      </div>
      <div class="ss-card">
        <div class="ss-card-info">
          <span class="ss-card-main">{{ nextEventName }}</span>
          <span class="ss-card-sub">{{ nextEventTime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useWeather } from '@/composables/useWeather'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ dismiss: [] }>()

const time = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null

const { weather, start: startWeather, stop: stopWeather } = useWeather()

const timeStr = computed(() =>
  time.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
)
const dateStr = computed(() =>
  time.value.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' }).toUpperCase()
)

const weatherIcon = computed(() => weather.value?.icon || ['fas', 'cloud-sun'])
const tempStr = computed(() => weather.value ? `${weather.value.temperature}°C` : '--°C')
const location = computed(() => weather.value?.location || '—')

const EVENTS = [
  { name: 'Daily Standup', time: '10:00 AM' },
  { name: 'Product Review', time: '2:00 PM' },
  { name: 'Gym Session',    time: '6:30 PM' },
]

function getNextEvent() {
  const now = time.value
  const h = now.getHours()
  const m = now.getMinutes()
  const currentMinutes = h * 60 + m
  const parsed = EVENTS.map(e => {
    const [hm, period] = e.time.split(' ')
    let [eh, em] = hm.split(':').map(Number)
    if (period === 'PM' && eh !== 12) eh += 12
    if (period === 'AM' && eh === 12) eh = 0
    return { ...e, totalMinutes: eh * 60 + em }
  })
  const upcoming = parsed.find(e => e.totalMinutes > currentMinutes)
  return upcoming || parsed[0]
}

const nextEventName = computed(() => getNextEvent().name)
const nextEventTime = computed(() => getNextEvent().time)

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
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (driftTimer) clearInterval(driftTimer)
  stopWeather()
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
  font-size: clamp(4rem, 12vw, 7rem);
  font-weight: 200;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1;
}

.ss-date {
  margin-top: 0.5rem;
  font-size: clamp(0.7rem, 1.5vw, 1rem);
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.38);
}

.ss-bottom-bar {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 1rem;
  width: min(90vw, 600px);
}

.ss-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.9rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.ss-weather-icon {
  font-size: 2rem;
  color: #ff9f0a;
  flex-shrink: 0;
}

.ss-card-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ss-card-main {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.ss-card-sub {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>
