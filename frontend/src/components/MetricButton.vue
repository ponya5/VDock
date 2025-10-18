<template>
  <div class="metric-button" :class="[`metric-${metricType}`, `status-${metricStatus}`]">
    <div class="metric-header">
      <FontAwesomeIcon v-if="metricIcon" :icon="metricIcon" class="metric-icon" />
      <span class="metric-label">{{ metricLabel }}</span>
      <FontAwesomeIcon v-if="isRefreshing && !isLoading" :icon="['fas', 'circle-notch']" spin class="refresh-indicator" />
    </div>
    
    <div class="metric-value">
      <span class="value-number">{{ formattedValue }}</span>
      <span v-if="unit" class="value-unit">{{ unit }}</span>
    </div>
    
    <div v-if="showProgressBar" class="metric-progress">
      <div class="progress-bar" :style="{ width: `${progressPercent}%` }"></div>
    </div>
    
    <div v-if="details" class="metric-details">
      <div v-for="(value, key) in details" :key="key" class="detail-row">
        <span class="detail-label">{{ key }}:</span>
        <span class="detail-value">{{ value }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import type { SystemMetricData } from '@/types'

interface Props {
  metricType: 'cpu' | 'memory' | 'disk' | 'network' | 'temperature' | 'battery' | 'processes'
  refreshInterval?: number // in milliseconds
  showProgressBar?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  refreshInterval: 5000,
  showProgressBar: true
})

const metricData = ref<any>(null)
const isLoading = ref(true) // Only true on initial load
const isRefreshing = ref(false) // For subtle refresh indicator
const error = ref<string | null>(null)
let intervalId: number | null = null
let isInitialLoad = true

const metricIcons: Record<string, any> = {
  cpu: ['fas', 'microchip'],
  memory: ['fas', 'memory'],
  disk: ['fas', 'hard-drive'],
  network: ['fas', 'network-wired'],
  temperature: ['fas', 'temperature-high'],
  battery: ['fas', 'battery-three-quarters'],
  processes: ['fas', 'list']
}

const metricLabels: Record<string, string> = {
  cpu: 'CPU Usage',
  memory: 'Memory',
  disk: 'Disk Space',
  network: 'Network',
  temperature: 'Temperature',
  battery: 'Battery',
  processes: 'Processes'
}

const metricIcon = computed(() => metricIcons[props.metricType])
const metricLabel = computed(() => metricLabels[props.metricType])

const formattedValue = computed(() => {
  if (!metricData.value) return '--'
  
  switch (props.metricType) {
    case 'cpu':
      return metricData.value.usage_percent?.toFixed(1) || '--'
    case 'memory':
      return metricData.value.usage_percent?.toFixed(1) || '--'
    case 'disk':
      if (metricData.value.partitions && metricData.value.partitions.length > 0) {
        return metricData.value.partitions[0].usage_percent?.toFixed(1) || '--'
      }
      return '--'
    case 'network':
      return `${metricData.value.bytes_sent_mb?.toFixed(1) || 0} / ${metricData.value.bytes_recv_mb?.toFixed(1) || 0}`
    case 'temperature':
      if (metricData.value.available && metricData.value.sensors && metricData.value.sensors.length > 0) {
        return metricData.value.sensors[0].current?.toFixed(1) || '--'
      }
      return 'N/A'
    case 'battery':
      if (metricData.value.available) {
        return metricData.value.percent?.toFixed(0) || '--'
      }
      return 'N/A'
    case 'processes':
      return metricData.value.total_processes || '--'
    default:
      return '--'
  }
})

const unit = computed(() => {
  switch (props.metricType) {
    case 'cpu':
    case 'memory':
    case 'disk':
    case 'battery':
      return '%'
    case 'temperature':
      return metricData.value?.available ? '°C' : ''
    case 'network':
      return 'MB'
    default:
      return ''
  }
})

const progressPercent = computed(() => {
  if (!metricData.value) return 0
  
  switch (props.metricType) {
    case 'cpu':
      return Math.min(metricData.value.usage_percent || 0, 100)
    case 'memory':
      return Math.min(metricData.value.usage_percent || 0, 100)
    case 'disk':
      if (metricData.value.partitions && metricData.value.partitions.length > 0) {
        return Math.min(metricData.value.partitions[0].usage_percent || 0, 100)
      }
      return 0
    case 'battery':
      return metricData.value.available ? Math.min(metricData.value.percent || 0, 100) : 0
    default:
      return 0
  }
})

const metricStatus = computed(() => {
  if (!metricData.value) return 'normal'
  
  switch (props.metricType) {
    case 'cpu':
    case 'memory':
    case 'disk':
      return metricData.value.status || 'normal'
    case 'battery':
      return metricData.value.health || 'normal'
    case 'temperature':
      if (metricData.value.available && metricData.value.sensors && metricData.value.sensors.length > 0) {
        const temp = metricData.value.sensors[0].current
        return temp > 80 ? 'critical' : temp > 60 ? 'warning' : 'normal'
      }
      return 'normal'
    default:
      return 'normal'
  }
})

const details = computed(() => {
  if (!metricData.value) return null
  
  switch (props.metricType) {
    case 'cpu':
      return {
        'Cores': metricData.value.cores_physical,
        'Threads': metricData.value.cores_logical,
        'Freq': `${metricData.value.frequency_current} MHz`
      }
    case 'memory':
      return {
        'Used': `${metricData.value.used_gb?.toFixed(1)} GB`,
        'Total': `${metricData.value.total_gb?.toFixed(1)} GB`,
        'Available': `${metricData.value.available_gb?.toFixed(1)} GB`
      }
    case 'disk':
      if (metricData.value.partitions && metricData.value.partitions.length > 0) {
        const disk = metricData.value.partitions[0]
        return {
          'Used': `${disk.used_gb?.toFixed(1)} GB`,
          'Free': `${disk.free_gb?.toFixed(1)} GB`,
          'Total': `${disk.total_gb?.toFixed(1)} GB`
        }
      }
      return null
    case 'network':
      return {
        'Sent': `${metricData.value.bytes_sent_mb?.toFixed(1)} MB`,
        'Received': `${metricData.value.bytes_recv_mb?.toFixed(1)} MB`,
        'Errors': metricData.value.errors_in + metricData.value.errors_out
      }
    case 'battery':
      if (metricData.value.available) {
        return {
          'Status': metricData.value.status,
          'Time Left': metricData.value.time_left_minutes ? `${metricData.value.time_left_minutes} min` : 'N/A'
        }
      }
      return null
    default:
      return null
  }
})

async function fetchMetric() {
  // Only show full loading on initial load
  if (isInitialLoad) {
    isLoading.value = true
  } else {
    // Prevent concurrent fetches
    if (isRefreshing.value) return
    isRefreshing.value = true
  }
  error.value = null
  
  try {
    const response = await apiClient.get(`/metrics/${props.metricType}`)
    if (response.data.success) {
      metricData.value = response.data.data
    } else {
      if (isInitialLoad) {
        error.value = response.data.error || 'Failed to fetch metric'
      }
    }
    
    if (isInitialLoad) {
      isInitialLoad = false
    }
  } catch (err: any) {
    if (isInitialLoad) {
      error.value = err.message || 'Network error'
    }
    console.error(`Error fetching ${props.metricType} metric:`, err)
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

onMounted(() => {
  fetchMetric()
  intervalId = window.setInterval(fetchMetric, props.refreshInterval)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.metric-button {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  transition: all var(--transition-fast);
  min-height: 120px;
}

.metric-button.status-warning {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.05);
}

.metric-button.status-critical {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.refresh-indicator {
  font-size: 0.75rem;
  opacity: 0.5;
  margin-left: auto;
}

.metric-icon {
  font-size: 1.25rem;
  color: var(--color-primary);
}

.metric-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
}

.value-number {
  font-size: 2rem;
  font-weight: bold;
  color: var(--color-text);
  line-height: 1;
}

.status-warning .value-number {
  color: #f59e0b;
}

.status-critical .value-number {
  color: #ef4444;
}

.value-unit {
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.metric-progress {
  height: 6px;
  background: var(--color-background);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--spacing-xs);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  transition: width var(--transition-normal);
  border-radius: var(--radius-full);
}

.status-warning .progress-bar {
  background: linear-gradient(90deg, #f59e0b, #fb923c);
}

.status-critical .progress-bar {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.metric-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.75rem;
  margin-top: var(--spacing-xs);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
}

.detail-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.detail-value {
  color: var(--color-text);
  font-weight: 600;
}
</style>

