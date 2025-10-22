<template>
  <div class="time-options" :class="[`time-${timeOption}`, { compact: compact }]" :style="dynamicFontSizeStyle">
    <!-- Compact Mode -->
    <div v-if="compact" class="time-compact">
      <!-- World Time Compact -->
      <div v-if="timeOption === 'world_time'" class="world-time-compact">
        <div class="time-main-compact">{{ currentTime }}</div>
        <div class="time-date-compact">{{ currentDate }}</div>
      </div>
      
      <!-- Timer Compact -->
      <div v-else-if="timeOption === 'timer'" class="timer-compact">
        <div class="timer-display-compact">{{ formattedTimerTime }}</div>
        <button 
          class="timer-btn-compact" 
          @click="toggleTimer"
          :class="{ active: timerRunning }"
        >
          <FontAwesomeIcon :icon="timerRunning ? ['fas', 'pause'] : ['fas', 'play']" />
        </button>
      </div>
      
      <!-- Countdown Compact -->
      <div v-else-if="timeOption === 'countdown'" class="countdown-compact">
        <div class="countdown-display-compact">{{ formattedCountdown }}</div>
        <div class="countdown-progress-compact">
          <div class="countdown-bar-compact" :style="{ width: countdownPercent + '%' }"></div>
        </div>
      </div>
    </div>
    
    <!-- Full Mode -->
    <div v-else>
      <div class="time-header">
        <FontAwesomeIcon :icon="headerIcon" class="header-icon" />
        <span class="header-title">{{ headerTitle }}</span>
      </div>
      
      <div class="time-display">
        <!-- World Time -->
        <div v-if="timeOption === 'world_time'" class="world-time">
          <div class="time-main">{{ currentTime }}</div>
          <div class="time-date">{{ currentDate }}</div>
          <div class="time-timezone">{{ timezoneLabel }}</div>
        </div>
        
        <!-- Timer -->
        <div v-else-if="timeOption === 'timer'" class="timer">
          <div class="timer-display">{{ formattedTimerTime }}</div>
          <div class="timer-controls">
            <button 
              class="timer-btn" 
              @click="toggleTimer"
              :class="{ active: timerRunning }"
            >
              <FontAwesomeIcon :icon="timerRunning ? ['fas', 'pause'] : ['fas', 'play']" />
            </button>
            <button class="timer-btn" @click="resetTimer">
              <FontAwesomeIcon :icon="['fas', 'redo']" />
            </button>
          </div>
        </div>
        
        <!-- Countdown -->
        <div v-else-if="timeOption === 'countdown'" class="countdown">
          <div class="countdown-display">{{ formattedCountdown }}</div>
          <div class="countdown-label">{{ countdownLabel }}</div>
          <div class="countdown-progress">
            <div class="countdown-bar" :style="{ width: countdownPercent + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { TimeOptionType } from '@/types'

interface Props {
  timeOption: TimeOptionType
  timezone?: string
  timerDuration?: number
  countdownTarget?: string
  compact?: boolean
  fontSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  timezone: 'local',
  timerDuration: 0,
  countdownTarget: '',
  compact: false,
  fontSize: 1.0,
})

const currentDateTime = ref(new Date())
const timerElapsed = ref(0)
const timerRunning = ref(false)
let timerInterval: number | null = null
let clockInterval: number | null = null

const headerIcon = computed(() => {
  switch (props.timeOption) {
    case 'world_time': return ['fas', 'globe']
    case 'timer': return ['fas', 'stopwatch']
    case 'countdown': return ['fas', 'hourglass-half']
    default: return ['fas', 'clock']
  }
})

const headerTitle = computed(() => {
  switch (props.timeOption) {
    case 'world_time': return 'World Time'
    case 'timer': return 'Timer'
    case 'countdown': return 'Countdown'
    default: return 'Time'
  }
})

// World Time
const currentTime = computed(() => {
  if (props.timezone === 'local' || !props.timezone) {
    return currentDateTime.value.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }
  
  return currentDateTime.value.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: props.timezone
  })
})

const currentDate = computed(() => {
  if (props.timezone === 'local' || !props.timezone) {
    return currentDateTime.value.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }
  
  return currentDateTime.value.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: props.timezone
  })
})

const timezoneLabel = computed(() => {
  if (props.timezone === 'local' || !props.timezone) {
    return 'Local Time'
  }
  return props.timezone.replace('_', ' ')
})

// Timer
const formattedTimerTime = computed(() => {
  const hours = Math.floor(timerElapsed.value / 3600)
  const minutes = Math.floor((timerElapsed.value % 3600) / 60)
  const seconds = timerElapsed.value % 60
  
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

function toggleTimer() {
  if (timerRunning.value) {
    stopTimer()
  } else {
    startTimer()
  }
}

function startTimer() {
  timerRunning.value = true
  timerInterval = setInterval(() => {
    timerElapsed.value++
  }, 1000) as unknown as number
}

function stopTimer() {
  timerRunning.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function resetTimer() {
  stopTimer()
  timerElapsed.value = 0
}

// Countdown
const countdownTarget = computed(() => {
  if (!props.countdownTarget) {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(0, 0, 0, 0)
    return tomorrow
  }
  return new Date(props.countdownTarget)
})

const formattedCountdown = computed(() => {
  const now = currentDateTime.value.getTime()
  const target = countdownTarget.value.getTime()
  const diff = Math.max(0, target - now)
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`
  } else if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`
  } else {
    return `${minutes}m ${seconds}s`
  }
})

const countdownLabel = computed(() => {
  if (!props.countdownTarget) {
    return 'Until Tomorrow'
  }
  return 'Remaining'
})

const countdownPercent = computed(() => {
  const now = currentDateTime.value.getTime()
  const target = countdownTarget.value.getTime()
  const start = target - (24 * 60 * 60 * 1000) // 24 hours ago
  
  const total = target - start
  const elapsed = now - start
  
  return Math.max(0, Math.min(100, (elapsed / total) * 100))
})

// Dynamic font sizing based on fontSize prop
const dynamicFontSizeStyle = computed(() => {
  return {
    '--font-size-multiplier': props.fontSize
  }
})

function updateClock() {
  currentDateTime.value = new Date()
}

onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000) as unknown as number
})

onUnmounted(() => {
  if (clockInterval) {
    clearInterval(clockInterval)
  }
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<style scoped>
.time-options {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: var(--spacing-md);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius-md);
  color: white;
}

.time-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

.header-icon {
  font-size: 1.2rem;
  opacity: 0.9;
}

.header-title {
  font-size: 0.9rem;
  font-weight: 600;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.time-display {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* World Time */
.world-time {
  text-align: center;
  width: 100%;
}

.time-main {
  font-size: calc(2.5rem * var(--font-size-multiplier, 1));
  font-weight: 700;
  line-height: 1;
  margin-bottom: var(--spacing-xs);
  font-variant-numeric: tabular-nums;
}

.time-date {
  font-size: calc(1rem * var(--font-size-multiplier, 1));
  opacity: 0.9;
  margin-bottom: var(--spacing-xs);
}

.time-timezone {
  font-size: 0.75rem;
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Timer */
.timer {
  text-align: center;
  width: 100%;
}

.timer-display {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: var(--spacing-md);
  font-variant-numeric: tabular-nums;
}

.timer-controls {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

.timer-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.timer-btn.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.7);
}

/* Countdown */
.countdown {
  text-align: center;
  width: 100%;
}

.countdown-display {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: var(--spacing-xs);
  font-variant-numeric: tabular-nums;
}

.countdown-label {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: var(--spacing-md);
}

.countdown-progress {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.countdown-bar {
  height: 100%;
  background: white;
  transition: width 0.3s ease-out;
  border-radius: 4px;
}

/* Compact Mode Styles */
.time-options.compact {
  padding: 0.25rem;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  container-type: inline-size;
}

.time-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

/* World Time Compact */
.world-time-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.time-main-compact {
  font-size: calc(0.75rem * var(--font-size-multiplier, 1));
  font-weight: 600;
  line-height: 0.9;
  margin-bottom: 0.125rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.time-date-compact {
  font-size: calc(0.5rem * var(--font-size-multiplier, 1));
  opacity: 0.8;
  line-height: 0.9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Container query responsive sizing */
@container (max-width: 100px) {
  .time-main-compact {
    font-size: 0.6rem;
  }
  .time-date-compact {
    font-size: 0.4rem;
  }
}

@container (max-width: 120px) {
  .time-main-compact {
    font-size: 0.65rem;
  }
  .time-date-compact {
    font-size: 0.45rem;
  }
}

@container (min-width: 150px) {
  .time-main-compact {
    font-size: 0.85rem;
  }
  .time-date-compact {
    font-size: 0.55rem;
  }
}

@container (min-width: 180px) {
  .time-main-compact {
    font-size: 1rem;
  }
  .time-date-compact {
    font-size: 0.6rem;
  }
}

@container (min-width: 220px) {
  .time-main-compact {
    font-size: 1.2rem;
  }
  .time-date-compact {
    font-size: 0.7rem;
  }
}

/* Timer Compact */
.timer-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.timer-display-compact {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.timer-btn-compact {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-btn-compact:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.timer-btn-compact.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.7);
}

/* Countdown Compact */
.countdown-compact {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.countdown-display-compact {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.countdown-progress-compact {
  width: 80%;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.countdown-bar-compact {
  height: 100%;
  background: white;
  transition: width 0.3s ease-out;
  border-radius: 2px;
}
</style>

