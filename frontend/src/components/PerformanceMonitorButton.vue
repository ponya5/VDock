<template>
  <div class="performance-monitor" :class="statusClass">
    <div class="monitor-header">
      <FontAwesomeIcon v-if="customIconType === 'fontawesome' && customIcon" :icon="headerIcon" class="header-icon" />
      <img v-else-if="customIconType === 'custom' && customIcon" :src="customIcon" class="header-icon-img" alt="icon" />
      <img v-else-if="customMediaUrl && customMediaType === 'gif'" :src="customMediaUrl" class="header-icon-img" alt="icon" />
      <img v-else-if="customMediaUrl && customMediaType === 'image'" :src="customMediaUrl" class="header-icon-img" alt="icon" />
      <FontAwesomeIcon v-else :icon="headerIcon" class="header-icon" />
      <span v-if="!customIcon && !customMediaUrl" class="header-title">System Performance Monitor</span>
    </div>
    
    <div v-if="loading && isInitialLoad" class="loading-state">
      <FontAwesomeIcon :icon="['fas', 'spinner']" spin />
      <span>Loading metrics...</span>
    </div>
    
    <div v-else class="metrics-grid">
      <div 
        v-for="metric in selectedMetrics" 
        :key="metric"
        class="metric-item"
      >
        <div class="metric-icon">
          <FontAwesomeIcon :icon="getMetricIcon(metric)" />
        </div>
          <div class="metric-content">
          <div class="metric-label">
            {{ getMetricLabel(metric) }}
            <FontAwesomeIcon v-if="isRefreshing" :icon="['fas', 'circle-notch']" spin class="refresh-indicator" />
          </div>
          <div class="metric-value" :class="getMetricColorClass(metric)">
            {{ getMetricValue(metric) }}
            <span class="metric-unit">{{ getMetricUnit(metric) }}</span>
          </div>
          <div v-if="hasProgressBar(metric)" class="metric-bar">
            <div class="metric-bar-fill" :class="getMetricColorClass(metric)" :style="{ width: getMetricPercent(metric) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="error" class="error-state">
      <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'
import type { PerformanceMetric } from '@/types'

interface Props {
  metrics: PerformanceMetric[]
  refreshInterval?: number
  customIcon?: any
  customIconType?: 'fontawesome' | 'custom'
  customMediaUrl?: string
  customMediaType?: 'image' | 'gif' | 'video'
}

const props = withDefaults(defineProps<Props>(), {
  refreshInterval: 10,
  customIconType: 'fontawesome',
})

const metricsData = ref<Record<string, any>>({})
const loading = ref(true) // Only true on initial load
const isRefreshing = ref(false) // For subtle refresh indicator
const error = ref<string | null>(null)
let intervalId: number | null = null
let isInitialLoad = true

const selectedMetrics = computed(() => props.metrics || [])

const headerIcon = computed(() => {
  // Use custom icon if provided
  if (props.customIcon) {
    return props.customIcon
  }
  return ['fas', 'tachometer-alt']
})

const statusClass = computed(() => {
  // Add status classes based on metrics
  return 'status-normal'
})

function getMetricIcon(metric: PerformanceMetric): string[] {
  const iconMap: Record<PerformanceMetric, string[]> = {
    memory: ['fas', 'memory'],
    cpu_usage: ['fas', 'microchip'],
    cpu_temperature: ['fas', 'thermometer-half'],
    cpu_frequency: ['fas', 'wave-square'],
    cpu_package_power: ['fas', 'bolt'],
    internet_speed: ['fas', 'network-wired'],
    harddisk: ['fas', 'hdd'],
    gpu_temperature: ['fas', 'thermometer-half'],
    gpu_core_frequency: ['fas', 'wave-square'],
    gpu_core_usage: ['fas', 'grip-vertical'],
    gpu_memory_frequency: ['fas', 'memory'],
    gpu_memory_usage: ['fas', 'memory'],
  }
  return iconMap[metric] || ['fas', 'chart-line']
}

function getMetricLabel(metric: PerformanceMetric): string {
  const labelMap: Record<PerformanceMetric, string> = {
    memory: 'Memory',
    cpu_usage: 'CPU Usage',
    cpu_temperature: 'CPU Temp',
    cpu_frequency: 'CPU Frequency',
    cpu_package_power: 'CPU Power',
    internet_speed: 'Internet Speed',
    harddisk: 'Hard Disk',
    gpu_temperature: 'GPU Temp',
    gpu_core_frequency: 'GPU Frequency',
    gpu_core_usage: 'GPU Core Usage',
    gpu_memory_frequency: 'GPU Memory Freq',
    gpu_memory_usage: 'GPU Memory Usage',
  }
  return labelMap[metric] || metric
}

function getMetricValue(metric: PerformanceMetric): string {
  const data = metricsData.value[metric]
  if (!data) return '--'
  
  switch (metric) {
    case 'memory':
      return data.usage_percent?.toFixed(1) || '--'
    case 'cpu_usage':
      return data.usage_percent?.toFixed(1) || '--'
    case 'cpu_temperature':
      return data.current?.toFixed(1) || '--'
    case 'cpu_frequency':
      return data.frequency_current?.toFixed(0) || '--'
    case 'cpu_package_power':
      return data.power_watts?.toFixed(1) || '--'
    case 'internet_speed':
      return data.bytes_recv_mb?.toFixed(1) || '--'
    case 'harddisk':
      return data[0]?.usage_percent?.toFixed(1) || '--'
    case 'gpu_temperature':
      return data[0]?.temperature_celsius?.toFixed(1) || '--'
    case 'gpu_core_frequency':
      return data[0]?.core_clock?.toFixed(0) || '--'
    case 'gpu_core_usage':
      return (data[0]?.load_percent || 0).toFixed(1)
    case 'gpu_memory_frequency':
      return data[0]?.memory_clock?.toFixed(0) || '--'
    case 'gpu_memory_usage':
      return ((data[0]?.memory_used_mb / data[0]?.memory_total_mb) * 100)?.toFixed(1) || '--'
    default:
      return '--'
  }
}

function getMetricUnit(metric: PerformanceMetric): string {
  const unitMap: Record<PerformanceMetric, string> = {
    memory: '%',
    cpu_usage: '%',
    cpu_temperature: '°C',
    cpu_frequency: 'MHz',
    cpu_package_power: 'W',
    internet_speed: 'Mbps',
    harddisk: '%',
    gpu_temperature: '°C',
    gpu_core_frequency: 'MHz',
    gpu_core_usage: '%',
    gpu_memory_frequency: 'MHz',
    gpu_memory_usage: '%',
  }
  return unitMap[metric] || ''
}

function hasProgressBar(metric: PerformanceMetric): boolean {
  return ['memory', 'cpu_usage', 'harddisk', 'gpu_core_usage', 'gpu_memory_usage'].includes(metric)
}

function getMetricPercent(metric: PerformanceMetric): number {
  const value = parseFloat(getMetricValue(metric))
  return isNaN(value) ? 0 : value
}

function getMetricColorClass(metric: PerformanceMetric): string {
  const percent = getMetricPercent(metric)
  
  // If metric shows -- or is not available, use default color
  if (isNaN(percent) || percent === 0) {
    return 'metric-normal'
  }
  
  // Color coding based on thresholds
  // High values are bad for these metrics
  if (['memory', 'cpu_usage', 'harddisk', 'cpu_temperature', 'gpu_temperature', 'gpu_core_usage', 'gpu_memory_usage'].includes(metric)) {
    if (percent >= 90) {
      return 'metric-critical'  // Red
    } else if (percent >= 75) {
      return 'metric-warning'   // Orange/Yellow
    } else if (percent >= 50) {
      return 'metric-moderate'  // Light yellow
    } else {
      return 'metric-normal'    // Green/Default
    }
  }
  
  // For other metrics (frequency, speed, power), just show default color
  return 'metric-normal'
}

async function fetchMetrics() {
  // Don't fetch if no metrics are selected or metrics array is empty/invalid
  if (!selectedMetrics.value || selectedMetrics.value.length === 0 || !selectedMetrics.value[0]) {
    console.warn('[PerformanceMonitorButton] No valid metrics to fetch:', selectedMetrics.value)
    loading.value = false
    isRefreshing.value = false
    return
  }
  
  // Only show full loading on initial load
  if (isInitialLoad) {
    loading.value = true
  } else {
    // Prevent concurrent fetches
    if (isRefreshing.value) return
    isRefreshing.value = true
  }
  error.value = null
  
  try {
    // Determine which API endpoints we need based on the selected metrics
    const endpointsToFetch = new Set<string>()
    
    selectedMetrics.value.forEach(metric => {
      switch (metric) {
        case 'memory':
          endpointsToFetch.add('memory')
          break
        case 'harddisk':
          endpointsToFetch.add('disk')
          break
        case 'cpu_usage':
        case 'cpu_frequency':
        case 'cpu_package_power':
          endpointsToFetch.add('cpu')
          break
        case 'cpu_temperature':
          endpointsToFetch.add('temperature')
          break
        case 'internet_speed':
          endpointsToFetch.add('network')
          break
        case 'gpu_memory_usage':
          endpointsToFetch.add('memory')
          break
        case 'gpu_temperature':
          endpointsToFetch.add('temperature')
          break
        case 'gpu_core_frequency':
        case 'gpu_core_usage':
        case 'gpu_memory_frequency':
          // GPU metrics would need their own endpoint
          break
      }
    })
    
    // Fetch only the metrics we need
    const fetchPromises: Promise<any>[] = []
    const endpointOrder: string[] = []
    
    if (endpointsToFetch.has('cpu')) {
      fetchPromises.push(apiClient.get('/metrics/cpu').catch(() => ({ status: 'rejected' })))
      endpointOrder.push('cpu')
    }
    if (endpointsToFetch.has('memory')) {
      fetchPromises.push(apiClient.get('/metrics/memory').catch(() => ({ status: 'rejected' })))
      endpointOrder.push('memory')
    }
    if (endpointsToFetch.has('disk')) {
      fetchPromises.push(apiClient.get('/metrics/disk').catch(() => ({ status: 'rejected' })))
      endpointOrder.push('disk')
    }
    if (endpointsToFetch.has('network')) {
      fetchPromises.push(apiClient.get('/metrics/network').catch(() => ({ status: 'rejected' })))
      endpointOrder.push('network')
    }
    if (endpointsToFetch.has('temperature')) {
      fetchPromises.push(apiClient.get('/metrics/temperature').catch(() => ({ status: 'rejected' })))
      endpointOrder.push('temperature')
    }
    
    const responses = await Promise.allSettled(fetchPromises)
    
    // Process responses based on what was actually fetched
    let cpuData = {}
    let memoryData = {}
    let diskData = {}
    let networkData = {}
    let tempData = {}
    
    responses.forEach((response, index) => {
      const endpoint = endpointOrder[index]
      if (response.status === 'fulfilled' && response.value?.data?.data) {
        switch (endpoint) {
          case 'cpu':
            cpuData = response.value.data.data
            break
          case 'memory':
            memoryData = response.value.data.data
            break
          case 'disk':
            diskData = response.value.data.data
            break
          case 'network':
            networkData = response.value.data.data
            break
          case 'temperature':
            tempData = response.value.data.data
            break
        }
      }
    })
    
    metricsData.value = {
      cpu_usage: cpuData,
      cpu_frequency: cpuData,
      cpu_package_power: cpuData,  // Not available - will show --
      memory: memoryData,
      harddisk: diskData.partitions || [],
      internet_speed: networkData,
      cpu_temperature: (tempData.sensors && tempData.sensors.length > 0) ? tempData.sensors[0] : null,
      // GPU metrics not supported yet - will show --
      gpu_temperature: [],
      gpu_core_frequency: [],
      gpu_core_usage: [],
      gpu_memory_frequency: [],
      gpu_memory_usage: [],
    }
    
    if (isInitialLoad) {
      isInitialLoad = false
    }
  } catch (err: any) {
    // Only show error on initial load
    if (isInitialLoad) {
      console.error('Failed to fetch performance metrics:', err)
      error.value = 'Failed to load metrics'
    }
  } finally {
    loading.value = false
    isRefreshing.value = false
  }
}

function startPolling() {
  stopPolling()
  intervalId = setInterval(fetchMetrics, props.refreshInterval * 1000) as unknown as number
}

function stopPolling() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  fetchMetrics()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.performance-monitor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.header-icon-img {
  width: 1rem;
  height: 1rem;
  object-fit: contain;
}

.header-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  overflow-y: auto;
  flex: 1;
}

.metric-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-background);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  flex: 1;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  font-size: 1.2rem;
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.metric-label {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.refresh-indicator {
  font-size: 0.6rem;
  opacity: 0.6;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 0.6; }
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
  transition: color 0.3s ease;
}

/* Metric color states based on value */
.metric-value.metric-normal {
  color: #4ade80;  /* Green - Good */
}

.metric-value.metric-moderate {
  color: #fbbf24;  /* Yellow - Moderate */
}

.metric-value.metric-warning {
  color: #fb923c;  /* Orange - Warning */
}

.metric-value.metric-critical {
  color: #ef4444;  /* Red - Critical */
}

.metric-unit {
  font-size: 0.6em;
  font-weight: normal;
  opacity: 0.8;
  margin-left: 4px;
}

.metric-bar {
  width: 100%;
  height: 6px;
  background-color: var(--color-border);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 6px;
}

.metric-bar-fill {
  height: 100%;
  transition: width 0.3s ease-out, background-color 0.3s ease;
}

.metric-bar-fill.metric-normal {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.metric-bar-fill.metric-moderate {
  background: linear-gradient(90deg, #eab308, #fbbf24);
}

.metric-bar-fill.metric-warning {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.metric-bar-fill.metric-critical {
  background: linear-gradient(90deg, #dc2626, #ef4444);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-lg);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  flex: 1;
}

.error-state {
  color: var(--color-danger);
}
</style>

