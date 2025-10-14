<template>
  <div class="calendar-display">
    <div class="calendar-month">{{ currentMonth }}</div>
    <div class="calendar-date">{{ currentDate }}</div>
    <div class="calendar-day">{{ currentDay }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const currentMonth = ref('')
const currentDate = ref('')
const currentDay = ref('')

let updateInterval: number | null = null

function updateCalendar() {
  const now = new Date()
  
  // Format month (e.g., "January", "February")
  currentMonth.value = now.toLocaleDateString('en-US', { month: 'long' })
  
  // Format date (e.g., "15")
  currentDate.value = now.getDate().toString()
  
  // Format day of week (e.g., "Monday")
  currentDay.value = now.toLocaleDateString('en-US', { weekday: 'long' })
}

onMounted(() => {
  updateCalendar()
  // Update every minute to ensure date changes are reflected
  updateInterval = window.setInterval(updateCalendar, 60000)
})

onUnmounted(() => {
  if (updateInterval !== null) {
    clearInterval(updateInterval)
  }
})
</script>

<style scoped>
.calendar-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: var(--spacing-sm);
  color: var(--color-text);
}

.calendar-month {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.calendar-date {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 2px;
}

.calendar-day {
  font-size: 0.7rem;
  font-weight: 500;
  opacity: 0.7;
  text-transform: capitalize;
}
</style>
