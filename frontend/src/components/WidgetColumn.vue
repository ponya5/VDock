<template>
  <aside class="widget-column card">
    <!-- Clock Widget -->
    <section class="widget-card widget-clock">
      <div class="clock-time">{{ formatTime(time) }}<span class="clock-seconds">{{ formatSeconds(time) }}</span></div>
      <div class="clock-date">{{ formatDate(time) }}</div>
    </section>

    <!-- Weather Widget -->
    <section class="widget-card widget-weather">
      <div class="weather-header">
        <span class="weather-title">Weather</span>
        <span class="weather-location">London, UK</span>
      </div>
      <div class="weather-body">
        <FontAwesomeIcon :icon="['fas', 'cloud-sun']" class="weather-large-icon" />
        <div class="weather-info">
          <span class="weather-temp">21°C</span>
          <span class="weather-desc">Partly Cloudy</span>
        </div>
      </div>
      <div class="weather-details">
        <div class="detail-item">
          <FontAwesomeIcon :icon="['fas', 'tint']" />
          <span>64%</span>
        </div>
        <div class="detail-item">
          <FontAwesomeIcon :icon="['fas', 'wind']" />
          <span>12 km/h</span>
        </div>
      </div>
    </section>

    <!-- Calendar & Schedule Widget -->
    <section class="widget-card widget-schedule">
      <div class="schedule-header">
        <span class="schedule-title">Today's Schedule</span>
        <span class="schedule-day">{{ formatDayOfWeek(time) }}</span>
      </div>
      <div class="schedule-events">
        <div v-for="event in events" :key="event.id" class="event-item">
          <div class="event-time-bar" :style="{ backgroundColor: event.color }"></div>
          <div class="event-details">
            <span class="event-name">{{ event.name }}</span>
            <span class="event-time">{{ event.time }}</span>
          </div>
        </div>
      </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const time = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null

interface EventItem {
  id: number
  name: string
  time: string
  color: string
}

const events = ref<EventItem[]>([
  { id: 1, name: 'Daily Standup', time: '10:00 AM - 10:15 AM', color: '#007aff' },
  { id: 2, name: 'Product Review', time: '2:00 PM - 3:00 PM', color: '#34c759' },
  { id: 3, name: 'Gym Session', time: '6:30 PM - 7:30 PM', color: '#af52de' }
])

function formatTime(d: Date): string {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

function formatSeconds(d: Date): string {
  return ':' + d.getSeconds().toString().padStart(2, '0')
}

function formatDate(d: Date): string {
  return d.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })
}

function formatDayOfWeek(d: Date): string {
  return d.toLocaleDateString([], { weekday: 'long' })
}

onMounted(() => {
  timer = setInterval(() => {
    time.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.widget-column {
  width: 200px;
  background-color: rgba(255, 255, 255, 0.02);
  border-left: 1px solid var(--color-border);
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  box-sizing: border-box;
  height: 100%;
  overflow-y: auto;
}

.widget-card {
  background-color: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  transition: all 0.2s var(--ease-out);
}

.widget-card:hover {
  background-color: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.1);
}

/* Clock Widget styles */
.widget-clock {
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md) var(--spacing-xs);
}

.clock-time {
  font-size: 2.1rem;
  font-weight: 700;
  color: var(--color-text);
  display: flex;
  align-items: baseline;
  line-height: 1;
}

.clock-seconds {
  font-size: 1rem;
  font-weight: 400;
  color: var(--color-text-secondary);
  margin-left: 2px;
}

.clock-date {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  text-align: center;
  font-weight: 500;
}

/* Weather Widget styles */
.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.weather-title {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.weather-location {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
}

.weather-body {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xs);
}

.weather-large-icon {
  font-size: 1.8rem;
  color: #ff9f0a;
}

.weather-info {
  display: flex;
  flex-direction: column;
}

.weather-temp {
  font-size: 1.3rem;
  font-weight: 600;
  line-height: 1.1;
}

.weather-desc {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
}

.weather-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: var(--spacing-xs);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Schedule Widget styles */
.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.schedule-title {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.schedule-day {
  font-size: 0.7rem;
  color: var(--color-primary);
  font-weight: 500;
}

.schedule-events {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.event-item {
  display: flex;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  overflow: hidden;
  height: 38px;
}

.event-time-bar {
  width: 3px;
  height: 100%;
}

.event-details {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 var(--spacing-xs);
  overflow: hidden;
}

.event-name {
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-time {
  font-size: 0.6rem;
  color: var(--color-text-secondary);
}
</style>
