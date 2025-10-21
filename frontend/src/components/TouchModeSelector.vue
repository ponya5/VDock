<template>
  <div class="touch-mode-selector">
    <div class="selector-header">
      <h3>Touch Mode</h3>
      <p class="description">Optimize interface size for different input methods</p>
    </div>
    
    <div class="mode-options">
      <div
        v-for="mode in modes"
        :key="mode.id"
        class="mode-option"
        :class="{ active: settingsStore.touchMode === mode.id }"
        @click="selectMode(mode.id)"
      >
        <div class="mode-icon">
          <FontAwesomeIcon :icon="mode.icon" />
        </div>
        <div class="mode-content">
          <h4>{{ mode.name }}</h4>
          <p class="mode-scale">{{ mode.scale }}</p>
          <p class="mode-desc">{{ mode.description }}</p>
        </div>
        <div class="mode-check">
          <FontAwesomeIcon 
            :icon="['fas', 'check-circle']"
            v-if="settingsStore.touchMode === mode.id"
          />
        </div>
      </div>
    </div>
    
    <div class="preview-section">
      <h4>Preview</h4>
      <div class="preview-container">
        <button 
          class="preview-button"
          :style="{
            padding: `${0.75 * settingsStore.touchModeMultiplier}rem ${1 * settingsStore.touchModeMultiplier}rem`,
            minHeight: `${Math.max(36 * settingsStore.touchModeMultiplier, settingsStore.minimumTouchTargetSize)}px`,
            fontSize: `${0.875 * settingsStore.touchModeMultiplier}rem`
          }"
        >
          <FontAwesomeIcon 
            :icon="['fas', 'play']" 
            :style="{ fontSize: `${1 * settingsStore.touchModeMultiplier}rem` }"
          />
          Sample Button
        </button>
        
        <div class="preview-info">
          <div class="info-item">
            <span class="label">Multiplier:</span>
            <span class="value">{{ settingsStore.touchModeMultiplier }}x</span>
          </div>
          <div class="info-item">
            <span class="label">Min Target Size:</span>
            <span class="value">{{ settingsStore.minimumTouchTargetSize }}px</span>
          </div>
          <div class="info-item">
            <span class="label">Button Height:</span>
            <span class="value">{{ Math.max(36 * settingsStore.touchModeMultiplier, settingsStore.minimumTouchTargetSize) }}px</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="advanced-settings">
      <button 
        class="toggle-advanced"
        @click="showAdvanced = !showAdvanced"
      >
        <FontAwesomeIcon :icon="['fas', showAdvanced ? 'chevron-up' : 'chevron-down']" />
        Advanced Settings
      </button>
      
      <div v-if="showAdvanced" class="advanced-content">
        <div class="form-group">
          <label>
            Minimum Touch Target Size (px)
            <span class="help-text">WCAG 2.1 AA requires 44px minimum</span>
          </label>
          <input
            type="range"
            v-model.number="settingsStore.minimumTouchTargetSize"
            min="24"
            max="64"
            step="4"
            class="slider"
          />
          <div class="slider-value">{{ settingsStore.minimumTouchTargetSize }}px</div>
        </div>
      </div>
    </div>
    
    <div class="touch-mode-tips">
      <div class="tip-header">
        <FontAwesomeIcon :icon="['fas', 'lightbulb']" />
        <span>Tips</span>
      </div>
      <ul>
        <li><strong>Normal:</strong> Best for mouse and trackpad users on desktop screens</li>
        <li><strong>Touch-Friendly:</strong> Ideal for touchscreen laptops and 2-in-1 devices</li>
        <li><strong>Tablet:</strong> Optimized for tablets and large-format touchscreens</li>
        <li>Changes apply immediately across the entire interface</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const showAdvanced = ref(false)

const modes = [
  {
    id: 'normal',
    name: 'Normal',
    scale: '1.0x',
    description: 'Standard size for mouse and keyboard',
    icon: ['fas', 'desktop']
  },
  {
    id: 'touch-friendly',
    name: 'Touch-Friendly',
    scale: '1.5x',
    description: 'Larger targets for touchscreen devices',
    icon: ['fas', 'laptop']
  },
  {
    id: 'tablet',
    name: 'Tablet',
    scale: '2.0x',
    description: 'Extra large for tablets and kiosks',
    icon: ['fas', 'tablet-screen-button']
  }
]

function selectMode(mode: 'normal' | 'touch-friendly' | 'tablet') {
  settingsStore.touchMode = mode
  notificationsStore.success(
    'Touch Mode Updated',
    `Interface scaled to ${modes.find(m => m.id === mode)?.scale} for ${mode} mode`
  )
}
</script>

<style scoped>
.touch-mode-selector {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.selector-header h3 {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text);
  font-size: 1.2rem;
}

.description {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.mode-options {
  margin-top: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.mode-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  background: var(--color-background);
}

.mode-option:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-hover);
  transform: translateX(4px);
}

.mode-option.active {
  border-color: var(--color-primary);
  background: rgba(var(--color-primary-rgb), 0.1);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
}

.mode-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  font-size: 1.5rem;
  color: var(--color-primary);
}

.mode-option.active .mode-icon {
  background: var(--color-primary);
  color: white;
}

.mode-content {
  flex: 1;
}

.mode-content h4 {
  margin: 0 0 2px;
  font-size: 1rem;
  color: var(--color-text);
}

.mode-scale {
  margin: 0 0 4px;
  font-size: 0.75rem;
  color: var(--color-primary);
  font-weight: 600;
}

.mode-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.mode-check {
  flex-shrink: 0;
  font-size: 1.5rem;
  color: var(--color-primary);
}

.preview-section {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-md);
}

.preview-section h4 {
  margin: 0 0 var(--spacing-md);
  font-size: 0.95rem;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  align-items: center;
}

.preview-button {
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.preview-button:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.preview-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.info-item .label {
  color: var(--color-text-secondary);
}

.info-item .value {
  color: var(--color-text);
  font-weight: 600;
}

.advanced-settings {
  margin-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-md);
}

.toggle-advanced {
  background: transparent;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.toggle-advanced:hover {
  background: var(--color-surface-hover);
}

.advanced-content {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-size: 0.9rem;
  color: var(--color-text);
  font-weight: 500;
}

.help-text {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 400;
  margin-top: 2px;
}

.slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: var(--color-border);
  outline: none;
  opacity: 0.8;
  transition: opacity var(--transition-fast);
  cursor: pointer;
}

.slider:hover {
  opacity: 1;
}

.slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: none;
}

.slider-value {
  text-align: center;
  font-size: 1rem;
  color: var(--color-primary);
  font-weight: 600;
  padding: var(--spacing-xs);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
}

.touch-mode-tips {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-md);
  background: rgba(var(--color-primary-rgb), 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-primary);
}

.tip-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  color: var(--color-primary);
  font-weight: 600;
  font-size: 0.9rem;
}

.touch-mode-tips ul {
  margin: 0;
  padding-left: var(--spacing-lg);
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  line-height: 1.6;
}

.touch-mode-tips li {
  margin-bottom: var(--spacing-xs);
}

.touch-mode-tips strong {
  color: var(--color-text);
}

@media (max-width: 768px) {
  .touch-mode-selector {
    padding: var(--spacing-md);
  }
  
  .mode-option {
    flex-direction: column;
    text-align: center;
  }
  
  .preview-container {
    padding: var(--spacing-sm);
  }
}
</style>

