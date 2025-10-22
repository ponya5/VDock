<template>
  <div
    class="deck-button"
    :class="buttonClasses"
    :style="buttonStyle"
    :draggable="isEditMode"
    @click="handleClick"
    @contextmenu.prevent="handleRightClick"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
  >
    <!-- Video background for video media -->
    <video
      v-if="button.media_url && button.media_type === 'video'"
      :src="button.media_url"
      class="button-video-background"
      autoplay
      loop
      muted
      playsinline
    />
    <div v-if="isEditMode" class="edit-overlay">
      <button class="edit-btn" @click.stop="emit('edit', button)" title="Edit">
        <FontAwesomeIcon :icon="['fas', 'edit']" />
      </button>
      <button class="copy-btn" @click.stop="emit('copy', button)" title="Copy">
        <FontAwesomeIcon :icon="['fas', 'copy']" />
      </button>
      <button class="delete-btn" @click.stop="emit('delete', button.id)" title="Delete">
        <FontAwesomeIcon :icon="['fas', 'trash']" />
      </button>
    </div>

    <div class="button-content">
      <!-- Individual Metric Displays -->
      <PerformanceMonitorButton 
        v-if="isMetricActionType"
        :metrics="[getMetricFromActionType]"
        :refresh-interval="button.action?.config?.refresh_interval || 2"
      />
      
      <!-- World Clock -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_world_clock'"
        time-option="world_time"
        :timezone="button.action?.config?.timezone || 'local'"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
      />
      
      <!-- Timer -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_timer'"
        time-option="timer"
        :timer-duration="button.action?.config?.timer_duration || 0"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
      />
      
      <!-- Countdown -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_countdown'"
        time-option="countdown"
        :countdown-target="button.action?.config?.countdown_target"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
      />
      
      <!-- Weather -->
      <WeatherQueryButton
        v-else-if="button.action?.type === 'weather'"
        :location="button.action?.config?.weather_location || 'auto'"
        :refresh-interval="button.action?.config?.refresh_interval || 15"
        :unit="button.action?.config?.temperature_unit || 'C'"
        :compact="compact"
      />
      
      <!-- Calendar -->
      <CalendarButton
        v-else-if="button.action?.type === 'calendar'"
      />
      
      <div v-else-if="button.icon || button.media_url" class="button-icon">
        <!-- Media (Video/GIF/Image) - Priority over icons -->
        <div v-if="button.media_url" class="media-container">
          <img 
            v-if="button.media_type === 'gif' || button.media_type === 'image'" 
            :src="button.media_url" 
            :style="mediaStyle"
            alt="Button media"
            class="media-element"
          />
          <video 
            v-else-if="button.media_type === 'video'" 
            :src="button.media_url" 
            :style="mediaStyle"
            autoplay
            loop
            muted
            playsinline
            alt="Button video"
            class="media-element"
          />
        </div>
        
        <!-- FontAwesome Icon - Only show if no media -->
        <FontAwesomeIcon 
          v-else-if="button.icon_type === 'fontawesome'" 
          :icon="Array.isArray(button.icon) ? button.icon : parseIcon(button.icon)" 
          :style="iconStyle"
          class="fontawesome-icon"
        />
        
        <!-- Custom Image Icon - Only show if no media -->
        <img 
          v-else-if="button.icon_type === 'custom'" 
          :src="button.icon" 
          :style="iconStyle"
          alt="Button icon"
          class="custom-icon"
        />
      </div>

      <div v-if="button.label && showLabels && !isSpecialActionType" class="button-label">
        {{ button.label }}
      </div>

      <div v-if="button.secondary_label && showLabels && !isSpecialActionType" class="button-secondary-label">
        {{ button.secondary_label }}
      </div>
    </div>

    <div v-if="button.tooltip && !isEditMode && showTooltips" class="button-tooltip">
      {{ button.tooltip }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Button } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import PerformanceMonitorButton from './PerformanceMonitorButton.vue'
import TimeOptionsButton from './TimeOptionsButton.vue'
import WeatherQueryButton from './WeatherQueryButton.vue'
import CalendarButton from './CalendarButton.vue'

interface Props {
  button: Button
  isEditMode?: boolean
  showLabels?: boolean
  showTooltips?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false,
  showLabels: true,
  showTooltips: true,
  compact: false
})

const emit = defineEmits<{
  click: [button: Button]
  edit: [button: Button]
  copy: [button: Button]
  delete: [buttonId: string]
  move: [buttonId: string, newPosition: { row: number; col: number }]
}>()

// Check if this is a special action type that renders its own content
const isSpecialActionType = computed(() => {
  const type = props.button.action?.type
  return type?.startsWith('metric_') || type?.startsWith('time_') || type === 'weather'
})

// Check if this is a metric action type
const isMetricActionType = computed(() => {
  return props.button.action?.type?.startsWith('metric_')
})

// Convert action type to metric name
const getMetricFromActionType = computed(() => {
  const type = props.button.action?.type
  if (!type || !type.startsWith('metric_')) return ''
  
  const metricMap: Record<string, string> = {
    'metric_memory': 'memory',
    'metric_cpu_usage': 'cpu_usage',
    'metric_cpu_temperature': 'cpu_temperature',
    'metric_cpu_frequency': 'cpu_frequency',
    'metric_cpu_power': 'cpu_package_power',
    'metric_internet_speed': 'internet_speed',
    'metric_harddisk': 'harddisk',
    'metric_gpu_temperature': 'gpu_temperature',
    'metric_gpu_frequency': 'gpu_core_frequency',
    'metric_gpu_usage': 'gpu_core_usage',
    'metric_gpu_memory_freq': 'gpu_memory_frequency',
    'metric_gpu_memory_usage': 'gpu_memory_usage',
  }
  
  return metricMap[type] || ''
})

const buttonClasses = computed(() => ({
  'shape-rectangle': props.button.shape === 'rectangle',
  'shape-rounded': props.button.shape === 'rounded',
  'shape-circle': props.button.shape === 'circle',
  'shape-hexagon': props.button.shape === 'hexagon',
  'shape-diamond': props.button.shape === 'diamond',
  'shape-octagon': props.button.shape === 'octagon',
  'edit-mode': props.isEditMode,
  'has-action': !!props.button.action,
  'disabled': !props.button.enabled,
  'deck-button-enhanced': props.button.style?.enhanced,
  'deck-button-glass': props.button.style?.effect === 'glass',
  'deck-button-neumorphism': props.button.style?.effect === 'neumorphism',
  'deck-button-gradient': props.button.style?.effect === 'gradient',
  'deck-button-glow': props.button.style?.effect === 'glow',
  'btn-pulse': props.button.style?.animation === 'pulse',
  'btn-shimmer': props.button.style?.animation === 'shimmer'
}))

const buttonStyle = computed(() => {
  const { position, size, style } = props.button
  
  const baseStyle = {
    gridRow: `${position.row + 1} / span ${size.rows}`,
    gridColumn: `${position.col + 1} / span ${size.cols}`,
    opacity: style?.opacity || 1,
    fontSize: style?.fontSize ? `${style.fontSize}px` : '0.875rem',
    // Only use background image for non-video media
    backgroundImage: (props.button.media_url && props.button.media_type !== 'video') 
      ? `url(${props.button.media_url})` : undefined,
    backgroundSize: (props.button.media_url && props.button.media_type !== 'video') 
      ? 'cover' : undefined,
    backgroundPosition: (props.button.media_url && props.button.media_type !== 'video') 
      ? 'center' : undefined,
    backgroundRepeat: (props.button.media_url && props.button.media_type !== 'video') 
      ? 'no-repeat' : undefined
  }

  // Apply enhanced styling based on effect type
  if (style?.effect === 'glass') {
    // Glass effect styles are handled by CSS classes
    return {
      ...baseStyle,
      color: style?.textColor || 'rgba(255, 255, 255, 0.9)'
    }
  } else if (style?.effect === 'neumorphism') {
    // Neumorphism styles are handled by CSS classes
    return {
      ...baseStyle,
      color: style?.textColor || 'var(--color-text)'
    }
  } else if (style?.effect === 'gradient') {
    // Custom gradient or default
    const gradient = style?.gradient || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    return {
      ...baseStyle,
      background: gradient,
      color: style?.textColor || '#ffffff'
    }
  } else if (style?.effect === 'glow') {
    return {
      ...baseStyle,
      backgroundColor: style?.backgroundColor || 'var(--color-primary)',
      color: style?.textColor || '#ffffff',
      borderColor: 'transparent'
    }
  } else {
    // Default styling
    return {
      ...baseStyle,
      backgroundColor: style?.backgroundColor || 'var(--color-surface)',
      color: style?.textColor || 'var(--color-text)',
      borderColor: style?.borderColor || 'var(--color-border)',
      borderWidth: style?.borderWidth ? `${style.borderWidth}px` : '2px'
    }
  }
})

const iconStyle = computed(() => {
  const size = props.button.style?.iconSize || 32
  return {
    width: `${size}px`,
    height: `${size}px`,
    fontSize: `${size}px`
  }
})

const mediaStyle = computed(() => {
  const size = props.button.style?.iconSize || 32
  return {
    width: `${size}px`,
    height: `${size}px`
  }
})

function parseIcon(iconString: string) {
  // Format: "fas fa-home" or "fab fa-twitter"
  const parts = iconString.split(' ')
  if (parts.length === 2) {
    return [parts[0], parts[1].replace('fa-', '')]
  }
  return ['fas', 'question']
}

function handleClick() {
  if (!props.isEditMode && props.button.enabled) {
    emit('click', props.button)
  }
}

function handleRightClick() {
  if (!props.isEditMode) {
    emit('edit', props.button)
  }
}

function handleDragStart(event: DragEvent) {
  console.log('DeckButton: drag start', props.button.label, 'edit mode:', props.isEditMode)
  if (!props.isEditMode) return
  
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vdock-button', JSON.stringify(props.button))
    event.dataTransfer.effectAllowed = 'copyMove' // Allow both copy and move
    console.log('DeckButton: drag data set', props.button)
  }
}

function handleDragEnd() {
  // Clean up any drag state if needed
}
</script>

<style scoped>
.deck-button {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
  user-select: none;
  /* Enhanced shadow for more alive UI */
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.deck-button[draggable="true"] {
  cursor: grab;
}

.deck-button[draggable="true"]:active {
  cursor: grabbing;
  transform: scale(0.95);
  opacity: 0.8;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.2),
    0 1px 2px rgba(0, 0, 0, 0.15),
    inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.deck-button.shape-rectangle {
  border-radius: var(--radius-sm);
}

.deck-button.shape-rounded {
  border-radius: var(--radius-lg);
}

.deck-button.shape-circle {
  border-radius: var(--radius-full);
}

.deck-button.has-action:hover:not(.edit-mode) {
  transform: scale(1.05);
  box-shadow: 
    0 8px 25px rgba(0, 0, 0, 0.25),
    0 4px 8px rgba(0, 0, 0, 0.15),
    0 0 20px rgba(var(--color-primary-rgb, 255, 107, 107), 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border-color: var(--color-primary);
}

.deck-button:active:not(.edit-mode) {
  transform: scale(0.95);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.2),
    0 1px 2px rgba(0, 0, 0, 0.15),
    inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  opacity: 0;
  transition: opacity var(--transition-fast);
  z-index: 10;
}

.deck-button.edit-mode:hover .edit-overlay {
  opacity: 1;
}

.edit-btn,
.copy-btn,
.delete-btn {
  padding: var(--spacing-sm);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1.25rem;
  transition: all var(--transition-fast);
}

.edit-btn {
  background-color: var(--color-primary);
  color: white;
}

.copy-btn {
  background-color: var(--color-accent);
  color: white;
}

.delete-btn {
  background-color: var(--color-error);
  color: white;
}

.edit-btn:hover,
.copy-btn:hover,
.delete-btn:hover {
  transform: scale(1.1);
}

.button-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  border-radius: inherit;
}

.button-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  text-align: center;
  width: 100%;
  height: 100%;
}

/* Special action types that render full content */
.button-content > .performance-monitor,
.button-content > .time-options,
.button-content > .weather-query {
  width: 100%;
  height: 100%;
  pointer-events: auto;
}

.button-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.button-icon img,
.button-icon video {
  object-fit: contain;
  border-radius: var(--radius-sm);
}

.fontawesome-icon {
  z-index: 2;
  position: relative;
}

.custom-icon {
  z-index: 2;
  position: relative;
}

.media-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.media-element {
  object-fit: cover;
  border-radius: var(--radius-sm);
  z-index: 1;
}

/* When both icon and media are present, overlay them */
.button-icon:has(.fontawesome-icon):has(.media-container) {
  position: relative;
}

.button-icon:has(.fontawesome-icon):has(.media-container) .fontawesome-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 3;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 2px;
  border-radius: var(--radius-sm);
}

.button-icon:has(.fontawesome-icon):has(.media-container) .media-element {
  opacity: 0.8;
}

.button-label {
  font-weight: 600;
  word-wrap: break-word;
  max-width: 100%;
  position: relative;
  z-index: 2;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.button-secondary-label {
  font-size: 0.75em;
  opacity: 0.8;
  word-wrap: break-word;
  max-width: 100%;
  position: relative;
  z-index: 2;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.button-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background-color: rgba(0, 0, 0, 0.9);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 100;
}

.deck-button:hover .button-tooltip {
  opacity: 1;
}

/* Enhanced shadows for different button states */
.deck-button.edit-mode {
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.deck-button.edit-mode:hover {
  box-shadow: 
    0 4px 15px rgba(0, 0, 0, 0.15),
    0 2px 5px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Special shadow effects for different shapes */
.deck-button.shape-circle {
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.05);
}

.deck-button.shape-hexagon,
.deck-button.shape-diamond,
.deck-button.shape-octagon {
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Ripple animation */
.deck-button::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  transform: translate(-50%, -50%);
  transition: width var(--transition-normal), height var(--transition-normal), opacity var(--transition-normal);
  opacity: 0;
}

.deck-button:active::after:not(.edit-mode) {
  width: 100%;
  height: 100%;
  opacity: 0.3;
}

/* Disabled button styles */
.deck-button.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.deck-button.disabled:hover {
  transform: none;
  box-shadow: inherit;
}

.deck-button.disabled:active {
  transform: none;
}

.deck-button.disabled .button-content {
  pointer-events: none;
}
</style>

