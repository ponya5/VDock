<template>
  <div class="performance-monitor" :class="statusClass">
    <div class="monitor-header">
      <FontAwesomeIcon :icon="headerIcon" class="header-icon" />
      <span class="header-title">System Performance Monitor</span>
    </div>
    
    <div v-if="loading" class="loading-state">
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
          <div class="metric-label">{{ getMetricLabel(metric) }}</div>
          <div class="metric-value">
            {{ getMetricValue(metric) }}
            <span class="metric-unit">{{ getMetricUnit(metric) }}</span>
          </div>
          <div v-if="hasProgressBar(metric)" class="metric-bar">
            <div class="metric-bar-fill" :style="{ width: getMetricPercent(metric) + '%' }"></div>
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
}

const props = withDefaults(defineProps<Props>(), {
  refreshInterval: 2,
})

const metricsData = ref<Record<string, any>>({})
const loading = ref(false)
const error = ref<string | null>(null)
let intervalId: number | null = null

const selectedMetrics = computed(() => props.metrics || [])

const headerIcon = computed(() => ['fas', 'tachometer-alt'])

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
      return data.used_percent?.toFixed(1) || '--'
    case 'cpu_usage':
      return data.percent?.toFixed(1) || '--'
    case 'cpu_temperature':
      return data.current?.toFixed(1) || '--'
    case 'cpu_frequency':
      return data.current_mhz?.toFixed(0) || '--'
    case 'cpu_package_power':
      return data.watts?.toFixed(1) || '--'
    case 'internet_speed':
      return data.download_mbps?.toFixed(1) || '--'
    case 'harddisk':
      return data[0]?.percent?.toFixed(1) || '--'
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

async function fetchMetrics() {
  loading.value = true
  error.value = null
  
  try {
    // Fetch all metrics data
    const responses = await Promise.all([
      apiClient.get('/metrics/cpu').catch(() => null),
      apiClient.get('/metrics/memory').catch(() => null),
      apiClient.get('/metrics/disk').catch(() => null),
      apiClient.get('/metrics/network').catch(() => null),
      apiClient.get('/metrics/temperature').catch(() => null),
      apiClient.get('/metrics/gpu').catch(() => null),
    ])
    
    metricsData.value = {
      cpu_usage: responses[0]?.data || {},
      cpu_frequency: responses[0]?.data || {},
      cpu_package_power: responses[0]?.data || {},
      memory: responses[1]?.data || {},
      harddisk: responses[2]?.data || [],
      internet_speed: responses[3]?.data || {},
      cpu_temperature: responses[4]?.data?.cpu_temp?.[0] || {},
      gpu_temperature: responses[5]?.data || [],
      gpu_core_frequency: responses[5]?.data || [],
      gpu_core_usage: responses[5]?.data || [],
      gpu_memory_frequency: responses[5]?.data || [],
      gpu_memory_usage: responses[5]?.data || [],
    }
  } catch (err: any) {
    console.error('Failed to fetch performance metrics:', err)
    error.value = 'Failed to load metrics'
  } finally {
    loading.value = false
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
  padding: var(--spacing-sm);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
}

.header-icon {
  font-size: 1.2rem;
  color: var(--color-primary);
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
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
  padding: var(--spacing-xs);
  background: var(--color-background);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  font-size: 1rem;
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-bottom: 2px;
}

.metric-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
}

.metric-unit {
  font-size: 0.7em;
  font-weight: normal;
  opacity: 0.8;
  margin-left: 2px;
}

.metric-bar {
  width: 100%;
  height: 4px;
  background-color: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.metric-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-success), var(--color-warning), var(--color-danger));
  transition: width 0.3s ease-out;
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
}

.error-state {
  color: var(--color-danger);
}
</style>

