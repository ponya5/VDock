<template>
  <div
    ref="buttonRef"
    class="deck-button"
    :class="buttonClasses"
    :style="buttonStyle"
    :draggable="isEditMode"
    @click="handleClick"
    @contextmenu.prevent="handleRightClick"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    @pointerdown="triggerRipple"
  >
    <!-- Video background for video media (from resolved fill) -->
    <video
      v-if="resolvedVisual.fill.type === 'video' && resolvedVisual.fill.value"
      :src="resolvedVisual.fill.value"
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

    <div class="button-content" :style="buttonContentStyle">
      <!-- Individual Metric Displays -->
      <PerformanceMonitorButton
        v-if="isMetricActionType && getMetricFromActionType"
        :metrics="[getMetricFromActionType]"
        :refresh-interval="button.action?.config?.refresh_interval || 10"
        :custom-icon="button.icon"
        :custom-icon-type="button.icon_type || 'fontawesome'"
        :custom-media-url="button.media_url"
        :custom-media-type="button.media_type"
      />

      <!-- World Clock -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_world_clock'"
        time-option="world_time"
        :timezone="button.action?.config?.timezone || 'local'"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
        :icon-size="button.style?.iconSize || 32"
      />

      <!-- Timer -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_timer'"
        time-option="timer"
        :timer-duration="button.action?.config?.timer_duration || 0"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
        :icon-size="button.style?.iconSize || 32"
      />

      <!-- Countdown -->
      <TimeOptionsButton
        v-else-if="button.action?.type === 'time_countdown'"
        time-option="countdown"
        :countdown-target="button.action?.config?.countdown_target"
        :compact="compact"
        :font-size="button.action?.config?.font_size || 1.0"
        :icon-size="button.style?.iconSize || 32"
      />

      <!-- Weather -->
      <WeatherQueryButton
        v-else-if="button.action?.type === 'weather'"
        :location="button.action?.config?.weather_location || 'auto'"
        :refresh-interval="button.action?.config?.refresh_interval || 15"
        :unit="button.action?.config?.temperature_unit || 'C'"
        :compact="compact"
        :icon-size="button.style?.iconSize || 32"
      />

      <!-- Calendar -->
      <CalendarButton
        v-else-if="button.action?.type === 'calendar'"
      />

      <div v-else-if="resolvedVisual.icon.type !== 'none' || (resolvedVisual.fill.type === 'image' && resolvedVisual.fill.value)" class="button-icon">
        <!-- Media (Video/GIF/Image) - Priority over icons -->
        <div v-if="resolvedVisual.fill.type === 'image' && resolvedVisual.fill.value" class="media-container">
          <img
            :src="resolvedVisual.fill.value"
            :style="mediaStyle"
            alt="Button media"
            class="media-element"
          />
        </div>

        <!-- FontAwesome Icon -->
        <FontAwesomeIcon
          v-else-if="resolvedVisual.icon.type === 'fontawesome'"
          :icon="Array.isArray(resolvedVisual.icon.value) ? resolvedVisual.icon.value : parseIcon(resolvedVisual.icon.value as string)"
          :style="iconStyle"
          :class="['fontawesome-icon', resolvedVisual.icon.loop !== 'none' ? `loop-${resolvedVisual.icon.loop}` : '']"
        />

        <!-- Custom Image Icon / Logo -->
        <img
          v-else-if="resolvedVisual.icon.type === 'custom' || resolvedVisual.icon.type === 'logo'"
          :src="Array.isArray(resolvedVisual.icon.value) ? resolvedVisual.icon.value[0] : resolvedVisual.icon.value"
          :style="iconStyle"
          alt="Button icon"
          :class="['custom-icon', resolvedVisual.icon.loop !== 'none' ? `loop-${resolvedVisual.icon.loop}` : '']"
        />
      </div>

      <div v-if="resolvedVisual.label.text && showLabels && !isSpecialActionType" class="button-label" :style="labelStyle">
        {{ resolvedVisual.label.text }}
      </div>

      <div v-if="resolvedVisual.label.secondary && showLabels && !isSpecialActionType" class="button-secondary-label" :style="secondaryLabelStyle">
        {{ resolvedVisual.label.secondary }}
      </div>
    </div>

    <div v-if="button.tooltip && !isEditMode && showTooltips" class="button-tooltip">
      {{ button.tooltip }}
    </div>

    <!-- Ripple container -->
    <span class="ripple-container" aria-hidden="true"></span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Button } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDoubleTap, useLongPress } from '@/composables/useGestures'
import { resolveBrandTint } from '@/utils/brandTint'
import { resolveButtonVisual, resolveButtonBrandTint } from '@/utils/buttonVisual'
import { vibrate } from '@/utils/haptics'
import PerformanceMonitorButton from './PerformanceMonitorButton.vue'
import TimeOptionsButton from './TimeOptionsButton.vue'
import WeatherQueryButton from './WeatherQueryButton.vue'
import CalendarButton from './CalendarButton.vue'

interface Props {
  button: Button
  isPlaceholder?: boolean
  isEditMode?: boolean
  showLabels?: boolean
  showTooltips?: boolean
  compact?: boolean
  buttonSize?: number
  gridIndex?: number
}

const props = withDefaults(defineProps<Props>(), {
  isPlaceholder: false,
  isEditMode: false,
  showLabels: true,
  showTooltips: true,
  compact: false,
  buttonSize: 1.0,
  gridIndex: 0
})

const emit = defineEmits<{
  click: [button: Button]
  edit: [button: Button]
  copy: [button: Button]
  delete: [buttonId: string]
  move: [buttonId: string, newPosition: { row: number; col: number }]
  doubleTap: [button: Button]
  longPress: [button: Button]
}>()

const buttonRef = ref<HTMLElement | null>(null)

useDoubleTap(buttonRef, {
  onDoubleTap: () => {
    if (props.isEditMode && props.button.action) {
      emit('click', props.button) // Double tap executes action in edit mode
    }
  }
})

useLongPress(buttonRef, {
  onLongPress: () => {
    if (!props.isEditMode) {
      emit('longPress', props.button)
    }
  }
})

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

const resolvedVisual = computed(() => resolveButtonVisual(props.button))

const buttonClasses = computed(() => {
  const vis = resolvedVisual.value
  const anim = props.button.layers?.behaviour ?? props.button.style?.animation ?? 'none'

  return {
    'shape-rectangle': props.button.shape === 'rectangle',
    'shape-rounded': props.button.shape === 'rounded',
    'shape-circle': props.button.shape === 'circle',
    'shape-hexagon': props.button.shape === 'hexagon',
    'shape-diamond': props.button.shape === 'diamond',
    'shape-octagon': props.button.shape === 'octagon',
    'is-placeholder': props.isPlaceholder,
    'edit-mode': props.isEditMode,
    'has-action': !!props.button.action,
    'disabled': !props.button.enabled,
    'deck-button-enhanced': props.button.style?.enhanced,

    // Effects from resolvedVisual
    'deck-button-glass': vis.effect.type === 'glass',
    'deck-button-neumorphism': vis.effect.type === 'neumorphism',
    'deck-button-gradient': vis.effect.type === 'gradient',
    'deck-button-glow': vis.effect.type === 'glow',
    'deck-button-neon': vis.effect.type === 'neon',
    'deck-button-metallic': vis.effect.type === 'metallic',
    'deck-button-liquid': vis.effect.type === 'liquid',
    'deck-button-holographic': vis.effect.type === 'holographic',
    'deck-button-shadow': vis.effect.type === 'shadow',
    'deck-button-emissive': vis.effect.type === 'emissive',

    // New CSS Effects
    'deck-button-fire': vis.effect.type === 'fire',
    'deck-button-plasma': vis.effect.type === 'plasma',
    'deck-button-particles': vis.effect.type === 'particles',
    'deck-button-aurora': vis.effect.type === 'aurora',
    'deck-button-scanline': vis.effect.type === 'scanline',
    'deck-button-rain': vis.effect.type === 'rain',

    // Animations (mapped from behaviour layer or legacy style.animation)
    'btn-pulse': anim === 'pulse',
    'btn-shimmer': anim === 'shimmer',
    'btn-bounce': anim === 'bounce',
    'btn-rotate': anim === 'rotate',
    'btn-wiggle': anim === 'wiggle',
    'btn-float': anim === 'float',
    'btn-scale': anim === 'scale',
    'btn-slide': anim === 'slide',
    'btn-fade': anim === 'fade',
    'btn-spin': anim === 'spin'
  }
})

const buttonStyle = computed(() => {
  const { position = { row: 0, col: 0 }, size = { rows: 1, cols: 1 }, style } = props.button
  const vis = resolvedVisual.value

  const baseStyle: Record<string, string | number | undefined> = {
    gridRow: `${position.row + 1} / span ${size.rows}`,
    gridColumn: `${position.col + 1} / span ${size.cols}`,
    opacity: style?.opacity || 1,
    fontSize: style?.fontSize ? `${style.fontSize}px` : '0.875rem',
    // Background image for visual image fill
    backgroundImage: (vis.fill.type === 'image' && vis.fill.value)
      ? `url(${vis.fill.value})` : undefined,
    backgroundSize: vis.fill.type === 'image' ? 'cover' : undefined,
    backgroundPosition: vis.fill.type === 'image' ? 'center' : undefined,
    backgroundRepeat: vis.fill.type === 'image' ? 'no-repeat' : undefined
  }

  // Resolve and set --btn-brand custom property
  const brandTint = resolveButtonBrandTint(props.button)
  if (brandTint !== undefined) {
    baseStyle['--btn-brand'] = brandTint
  }

  if (vis.fill.type === 'gradient' && vis.fill.value) {
    return {
      ...baseStyle,
      background: vis.fill.value,
      color: style?.textColor || '#ffffff'
    }
  } else if (vis.fill.type === 'solid' && vis.fill.value) {
    return {
      ...baseStyle,
      backgroundColor: vis.fill.value,
      color: style?.textColor || 'var(--color-text)',
      borderColor: style?.borderColor || 'var(--color-border)',
      borderWidth: style?.borderWidth ? `${style.borderWidth}px` : '2px'
    }
  } else if (vis.fill.type === 'tint') {
    return {
      ...baseStyle,
      backgroundColor: brandTint || 'var(--color-primary)',
      color: style?.textColor || '#ffffff',
      borderColor: style?.borderColor || 'var(--color-border)',
      borderWidth: style?.borderWidth ? `${style.borderWidth}px` : '2px'
    }
  }

  // Apply enhanced styling based on effect type
  if (vis.effect.type === 'glass') {
    // Glass effect styles are handled by CSS classes
    return {
      ...baseStyle,
      color: style?.textColor || 'rgba(255, 255, 255, 0.9)'
    }
  } else if (vis.effect.type === 'neumorphism') {
    // Neumorphism styles are handled by CSS classes
    return {
      ...baseStyle,
      color: style?.textColor || 'var(--color-text)'
    }
  } else if (vis.effect.type === 'gradient') {
    // Custom gradient or default
    const gradient = style?.gradient || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    return {
      ...baseStyle,
      background: gradient,
      color: style?.textColor || '#ffffff'
    }
  } else if (vis.effect.type === 'glow') {
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
  const vis = resolvedVisual.value
  // Scale icon size with buttonSize prop so label always has room
  const baseSize = vis.icon.size || 32
  const scale = props.buttonSize || 1.0
  // When label is shown, cap icon at 75% of scaled size to leave room for label
  const hasLabel = !!(vis.label.text && props.showLabels)
  const size = hasLabel ? Math.round(baseSize * scale * 0.75) : Math.round(baseSize * scale)

  const styleObj: Record<string, string | number | undefined> = {
    width: `${size}px`,
    height: `${size}px`,
    fontSize: `${size}px`
  }

  if (vis.icon.loop && vis.icon.loop !== 'none') {
    styleObj.animationDelay = `${(props.gridIndex * 137) % 1900}ms`
  }

  return styleObj
})

const mediaStyle = computed(() => {
  const vis = resolvedVisual.value
  const baseSize = props.button.style?.iconSize || 32
  const scale = props.buttonSize || 1.0
  const hasLabel = !!(vis.label.text && props.showLabels)
  const size = hasLabel ? Math.round(baseSize * scale * 0.75) : Math.round(baseSize * scale)

  const styleObj: Record<string, string | number | undefined> = {
    width: `${size}px`,
    height: `${size}px`
  }

  if (vis.icon.loop && vis.icon.loop !== 'none') {
    styleObj.animationDelay = `${(props.gridIndex * 137) % 1900}ms`
  }

  return styleObj
})

const labelStyle = computed(() => {
  const baseFontSize = props.button.style?.fontSize || 14
  const scale = props.buttonSize || 1.0
  const size = Math.max(10, Math.round(baseFontSize * scale))
  return {
    fontSize: `${size}px`
  }
})

const secondaryLabelStyle = computed(() => {
  const baseFontSize = props.button.style?.fontSize || 14
  const scale = props.buttonSize || 1.0
  const size = Math.max(9, Math.round(baseFontSize * scale * 0.75))
  return {
    fontSize: `${size}px`
  }
})

const buttonContentStyle = computed(() => {
  const style = props.button.style
  if (style?.innerBackgroundColor) {
    return {
      backgroundColor: style.innerBackgroundColor
    }
  }
  return {}
})

function parseIcon(iconString: string) {
  if (!iconString) return ['fas', 'question']
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
  if (!props.isEditMode) return

  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vdock-button', JSON.stringify(props.button))
    event.dataTransfer.effectAllowed = 'copyMove' // Allow both copy and move
      }
}

function handleDragEnd() {
  // Clean up any drag state if needed
}

function triggerRipple(event: PointerEvent) {
  if (!buttonRef.value) return
  // Call haptics on press (non-placeholder, non-edit-mode)
  if (!props.isEditMode && props.button.enabled) {
    vibrate(50)
  }

  const btn = buttonRef.value
  const rect = btn.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const ripple = document.createElement('span')
  ripple.className = 'ripple-wave'
  ripple.style.left = `${x}px`
  ripple.style.top = `${y}px`

  const container = btn.querySelector('.ripple-container')
  if (container) {
    container.appendChild(ripple)
    ripple.addEventListener('animationend', () => ripple.remove(), { once: true })
  }
}
</script>

<style scoped>
.deck-button {
  --btn-bg: #080808;
  --btn-radius: var(--radius-md);
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: var(--btn-radius);
  background-color: var(--btn-bg);
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  user-select: none;
  min-width: 60px;
  min-height: 60px;
  outline: none;
  box-shadow:
    inset 0 0.3rem 0.9rem rgba(255, 255, 255, 0.3),
    inset 0 -0.1rem 0.3rem rgba(0, 0, 0, 0.7),
    inset 0 -0.4rem 0.9rem rgba(255, 255, 255, 0.5),
    0 3rem 3rem rgba(0, 0, 0, 0.3),
    0 1rem 1rem -0.6rem rgba(0, 0, 0, 0.8);
}

/* Uiverse hover state */
.deck-button:not(.edit-mode):not(.is-placeholder):not(.disabled):hover {
  box-shadow:
    inset 0 0.3rem 0.5rem rgba(255, 255, 255, 0.4),
    inset 0 -0.1rem 0.3rem rgba(0, 0, 0, 0.7),
    inset 0 -0.4rem 0.9rem rgba(255, 255, 255, 0.7),
    0 3rem 3rem rgba(0, 0, 0, 0.3),
    0 1rem 1rem -0.6rem rgba(0, 0, 0, 0.8);
}

/* Uiverse active/press state */
.deck-button:not(.edit-mode):not(.is-placeholder):not(.disabled):active {
  transform: scale(0.94);
  box-shadow:
    inset 0 0.3rem 0.5rem rgba(255, 255, 255, 0.5),
    inset 0 -0.1rem 0.3rem rgba(0, 0, 0, 0.8),
    inset 0 -0.4rem 0.9rem rgba(255, 255, 255, 0.4),
    0 3rem 3rem rgba(0, 0, 0, 0.3),
    0 1rem 1rem -0.6rem rgba(0, 0, 0, 0.8);
}

.deck-button[draggable="true"] {
  cursor: grab;
}

.deck-button[draggable="true"]:active {
  cursor: grabbing;
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

.deck-button.is-placeholder {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.1) !important;
  cursor: default;
  box-shadow: none;
}

.deck-button.is-placeholder .button-content {
  mask-image: none;
  -webkit-mask-image: none;
}

.deck-button.is-placeholder .button-content::before,
.deck-button.is-placeholder .button-content::after {
  display: none;
}

.deck-button-glass {
  background: var(--glass-bg, rgba(255, 255, 255, 0.05));
  backdrop-filter: var(--glass-blur, blur(10px));
  -webkit-backdrop-filter: var(--glass-blur, blur(10px));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  box-shadow: var(--glass-shadow, 0 8px 32px rgba(0, 0, 0, 0.1));
}

.deck-button-glass:hover:not(.edit-mode):not(.is-placeholder) {
  background: rgba(255, 255, 255, 0.15);
  box-shadow: var(--glass-shadow, 0 8px 32px rgba(0, 0, 0, 0.1)), var(--glass-glow, 0 0 15px rgba(255, 255, 255, 0.3));
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
  font-size: clamp(1.00rem, 2vw + 0.62rem, 1.50rem);
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
  gap: 4px;
  text-align: center;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  overflow: hidden;
  padding: 8px 6px;
  box-sizing: border-box;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  transition: transform 0.2s ease;
  /* Uiverse label mask — fades bottom edge for depth */
  mask-image: linear-gradient(to bottom, white 60%, transparent);
  -webkit-mask-image: linear-gradient(to bottom, white 60%, transparent);
}

/* Uiverse top-dome highlight */
.button-content::before {
  content: '';
  position: absolute;
  left: -15%;
  right: -15%;
  bottom: 25%;
  top: -100%;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.12);
  transition: transform 0.3s ease;
  pointer-events: none;
}

/* Uiverse inner gloss strip */
.button-content::after {
  content: '';
  position: absolute;
  left: 6%;
  right: 6%;
  top: 12%;
  bottom: 40%;
  border-radius: 22px 22px 0 0;
  box-shadow: inset 0 10px 8px -10px rgba(255, 255, 255, 0.8);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.3) 0%,
    rgba(0, 0, 0, 0) 50%,
    rgba(0, 0, 0, 0) 100%
  );
  transition: opacity 0.3s ease, transform 0.3s ease;
  pointer-events: none;
}

.deck-button:not(.edit-mode):not(.is-placeholder):not(.disabled):hover .button-content {
  transform: translateY(-4%);
}

.deck-button:not(.edit-mode):not(.is-placeholder):not(.disabled):hover .button-content::before {
  transform: translateY(-5%);
}

.deck-button:not(.edit-mode):not(.is-placeholder):not(.disabled):hover .button-content::after {
  opacity: 0.4;
  transform: translateY(5%);
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
  overflow-wrap: break-word;
  max-width: 100%;
  width: 100%;
  text-align: center;
  position: relative;
  z-index: 2;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  line-height: 1.2;
  flex-shrink: 0;
  /* Ensure label is always visible — never hidden */
  opacity: 1 !important;
  visibility: visible !important;
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
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
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

/* Ripple effect */
.ripple-container {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  overflow: hidden;
  pointer-events: none;
  z-index: 5;
}

.ripple-wave {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.55);
  transform: translate(-50%, -50%) scale(0);
  animation: ripple-expand 0.55s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)) forwards;
  pointer-events: none;
}

@keyframes ripple-expand {
  to {
    transform: translate(-50%, -50%) scale(80);
    opacity: 0;
  }
}

/* Glow pulse on trigger */
.deck-button.triggered {
  animation: glow-pulse 0.4s ease-out forwards;
}

@keyframes glow-pulse {
  0% { box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb, 52, 152, 219), 0.6); }
  70% { box-shadow: 0 0 0 10px rgba(var(--color-primary-rgb, 52, 152, 219), 0); }
  100% { box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb, 52, 152, 219), 0); }
}
</style>

