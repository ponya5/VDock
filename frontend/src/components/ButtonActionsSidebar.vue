<template>
  <div class="actions-sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-header">
      <h2>Button Actions</h2>
      <button class="close-btn" @click="emit('close')">
        <FontAwesomeIcon :icon="['fas', 'times']" />
      </button>
    </div>

    <div class="search-box">
      <FontAwesomeIcon :icon="['fas', 'search']" class="search-icon" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search actions..."
        class="search-input"
      />
    </div>

    <div class="actions-list">
      <!-- System Category -->
      <div v-show="shouldShowCategory('system')" class="action-category">
        <button class="category-header" @click="toggleCategory('system')">
          <FontAwesomeIcon :icon="expandedCategories.includes('system') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>System</span>
          <span class="count">(10)</span>
        </button>
        <div v-show="expandedCategories.includes('system')" class="category-items">
          <button v-show="matchesSearch('Launch Program')" class="action-item" @click="selectAction('program')">
            <FontAwesomeIcon :icon="['fas', 'rocket']" />
            <span>Launch Program</span>
          </button>
          <button v-show="matchesSearch('Run Command')" class="action-item" @click="selectAction('command')">
            <FontAwesomeIcon :icon="['fas', 'terminal']" />
            <span>Run Command</span>
          </button>
          <button v-show="matchesSearch('Send Hotkey')" class="action-item" @click="selectAction('hotkey')">
            <FontAwesomeIcon :icon="['fas', 'keyboard']" />
            <span>Send Hotkey</span>
          </button>
          <button v-show="matchesSearch('Macro')" class="action-item" @click="selectAction('macro')">
            <FontAwesomeIcon :icon="['fas', 'list']" />
            <span>Macro</span>
          </button>
          <button v-show="matchesSearch('Open Folder')" class="action-item" @click="selectAction('folder')">
            <FontAwesomeIcon :icon="['fas', 'folder']" />
            <span>Open Folder</span>
          </button>
          <button v-show="matchesSearch('Screenshot')" class="action-item" @click="selectAction('screenshot')">
            <FontAwesomeIcon :icon="['fas', 'camera']" />
            <span>Screenshot</span>
          </button>
        </div>
      </div>

      <!-- Media Control Category -->
      <div v-show="shouldShowCategory('media')" class="action-category">
        <button class="category-header" @click="toggleCategory('media')">
          <FontAwesomeIcon :icon="expandedCategories.includes('media') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Media Control</span>
          <span class="count">(7)</span>
        </button>
        <div v-show="expandedCategories.includes('media')" class="category-items">
          <button v-show="matchesSearch('Play/Pause')" class="action-item" @click="selectAction('media_play_pause')">
            <FontAwesomeIcon :icon="['fas', 'play']" />
            <span>Play/Pause</span>
          </button>
          <button v-show="matchesSearch('Next Track')" class="action-item" @click="selectAction('media_next')">
            <FontAwesomeIcon :icon="['fas', 'forward']" />
            <span>Next Track</span>
          </button>
          <button v-show="matchesSearch('Previous Track')" class="action-item" @click="selectAction('media_previous')">
            <FontAwesomeIcon :icon="['fas', 'backward']" />
            <span>Previous Track</span>
          </button>
          <button v-show="matchesSearch('Stop')" class="action-item" @click="selectAction('media_stop')">
            <FontAwesomeIcon :icon="['fas', 'stop']" />
            <span>Stop</span>
          </button>
          <button v-show="matchesSearch('Volume Up')" class="action-item" @click="selectAction('volume_up')">
            <FontAwesomeIcon :icon="['fas', 'volume-up']" />
            <span>Volume Up</span>
          </button>
          <button v-show="matchesSearch('Volume Down')" class="action-item" @click="selectAction('volume_down')">
            <FontAwesomeIcon :icon="['fas', 'volume-down']" />
            <span>Volume Down</span>
          </button>
          <button v-show="matchesSearch('Mute')" class="action-item" @click="selectAction('volume_mute')">
            <FontAwesomeIcon :icon="['fas', 'volume-mute']" />
            <span>Mute</span>
          </button>
        </div>
      </div>

      <!-- Web & Apps Category -->
      <div v-show="shouldShowCategory('web')" class="action-category">
        <button class="category-header" @click="toggleCategory('web')">
          <FontAwesomeIcon :icon="expandedCategories.includes('web') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Web & Apps</span>
          <span class="count">(6)</span>
        </button>
        <div v-show="expandedCategories.includes('web')" class="category-items">
          <button v-show="matchesSearch('Open URL')" class="action-item" @click="selectAction('url')">
            <FontAwesomeIcon :icon="['fas', 'globe']" />
            <span>Open URL</span>
          </button>
          <button v-show="matchesSearch('Open Application')" class="action-item" @click="selectAction('program')">
            <FontAwesomeIcon :icon="['fas', 'rocket']" />
            <span>Open Application</span>
          </button>
          <button v-show="matchesSearch('Open Folder')" class="action-item" @click="selectAction('folder')">
            <FontAwesomeIcon :icon="['fas', 'folder']" />
            <span>Open Folder</span>
          </button>
          <button v-show="matchesSearch('Open File')" class="action-item" @click="selectAction('file')">
            <FontAwesomeIcon :icon="['fas', 'file']" />
            <span>Open File</span>
          </button>
          <button v-show="matchesSearch('Screenshot')" class="action-item" @click="selectAction('screenshot')">
            <FontAwesomeIcon :icon="['fas', 'camera']" />
            <span>Screenshot</span>
          </button>
          <button v-show="matchesSearch('Copy to Clipboard')" class="action-item" @click="selectAction('clipboard')">
            <FontAwesomeIcon :icon="['fas', 'clipboard']" />
            <span>Copy to Clipboard</span>
          </button>
        </div>
      </div>

      <!-- Monitor Metrics Category -->
      <div v-show="shouldShowCategory('metrics')" class="action-category">
        <button class="category-header" @click="toggleCategory('metrics')">
          <FontAwesomeIcon :icon="expandedCategories.includes('metrics') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Monitor Metrics</span>
          <span class="count">(12)</span>
        </button>
        <div v-show="expandedCategories.includes('metrics')" class="category-items">
          <button v-show="matchesSearch('Memory')" class="action-item" @click="selectAction('metric_memory')">
            <FontAwesomeIcon :icon="['fas', 'memory']" />
            <span>Memory</span>
          </button>
          <button v-show="matchesSearch('CPU usage')" class="action-item" @click="selectAction('metric_cpu_usage')">
            <FontAwesomeIcon :icon="['fas', 'microchip']" />
            <span>CPU usage</span>
          </button>
          <button v-show="matchesSearch('CPU temperature')" class="action-item" @click="selectAction('metric_cpu_temperature')">
            <FontAwesomeIcon :icon="['fas', 'thermometer-half']" />
            <span>CPU temperature</span>
          </button>
          <button v-show="matchesSearch('CPU frequency')" class="action-item" @click="selectAction('metric_cpu_frequency')">
            <FontAwesomeIcon :icon="['fas', 'wave-square']" />
            <span>CPU frequency</span>
          </button>
          <button v-show="matchesSearch('CPU package power')" class="action-item" @click="selectAction('metric_cpu_power')">
            <FontAwesomeIcon :icon="['fas', 'bolt']" />
            <span>CPU package power</span>
          </button>
          <button v-show="matchesSearch('Internet speed')" class="action-item" @click="selectAction('metric_internet_speed')">
            <FontAwesomeIcon :icon="['fas', 'network-wired']" />
            <span>Internet speed</span>
          </button>
          <button v-show="matchesSearch('Harddisk')" class="action-item" @click="selectAction('metric_harddisk')">
            <FontAwesomeIcon :icon="['fas', 'hdd']" />
            <span>Harddisk</span>
          </button>
          <button v-show="matchesSearch('GPU temperature')" class="action-item" @click="selectAction('metric_gpu_temperature')">
            <FontAwesomeIcon :icon="['fas', 'thermometer-half']" />
            <span>GPU temperature</span>
          </button>
          <button v-show="matchesSearch('GPU core frequency')" class="action-item" @click="selectAction('metric_gpu_frequency')">
            <FontAwesomeIcon :icon="['fas', 'wave-square']" />
            <span>GPU core frequency</span>
          </button>
          <button v-show="matchesSearch('GPU Core Usage')" class="action-item" @click="selectAction('metric_gpu_usage')">
            <FontAwesomeIcon :icon="['fas', 'grip-vertical']" />
            <span>GPU Core Usage</span>
          </button>
          <button v-show="matchesSearch('GPU memory frequency')" class="action-item" @click="selectAction('metric_gpu_memory_freq')">
            <FontAwesomeIcon :icon="['fas', 'memory']" />
            <span>GPU memory frequency</span>
          </button>
          <button v-show="matchesSearch('GPU Memory Usage')" class="action-item" @click="selectAction('metric_gpu_memory_usage')">
            <FontAwesomeIcon :icon="['fas', 'memory']" />
            <span>GPU Memory Usage</span>
          </button>
        </div>
      </div>

      <!-- Time Category -->
      <div v-show="shouldShowCategory('time')" class="action-category">
        <button class="category-header" @click="toggleCategory('time')">
          <FontAwesomeIcon :icon="expandedCategories.includes('time') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Time</span>
          <span class="count">(3)</span>
        </button>
        <div v-show="expandedCategories.includes('time')" class="category-items">
          <button v-show="matchesSearch('World Time')" class="action-item" @click="selectAction('time_world_clock')">
            <FontAwesomeIcon :icon="['fas', 'globe']" />
            <span>World Time</span>
          </button>
          <button v-show="matchesSearch('Timer')" class="action-item" @click="selectAction('time_timer')">
            <FontAwesomeIcon :icon="['fas', 'stopwatch']" />
            <span>Timer</span>
          </button>
          <button v-show="matchesSearch('Countdown')" class="action-item" @click="selectAction('time_countdown')">
            <FontAwesomeIcon :icon="['fas', 'hourglass-half']" />
            <span>Countdown</span>
          </button>
        </div>
      </div>

      <!-- Weather Category -->
      <div v-show="shouldShowCategory('weather')" class="action-category">
        <button class="category-header" @click="toggleCategory('weather')">
          <FontAwesomeIcon :icon="expandedCategories.includes('weather') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Weather</span>
          <span class="count">(1)</span>
        </button>
        <div v-show="expandedCategories.includes('weather')" class="category-items">
          <button v-show="matchesSearch('Weather query')" class="action-item" @click="selectAction('weather')">
            <FontAwesomeIcon :icon="['fas', 'cloud-sun']" />
            <span>Weather query</span>
          </button>
        </div>
      </div>

      <!-- Text & Input Category -->
      <div v-show="shouldShowCategory('text')" class="action-category">
        <button class="category-header" @click="toggleCategory('text')">
          <FontAwesomeIcon :icon="expandedCategories.includes('text') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Text & Input</span>
          <span class="count">(6)</span>
        </button>
        <div v-show="expandedCategories.includes('text')" class="category-items">
          <button v-show="matchesSearch('Send Hotkey')" class="action-item" @click="selectAction('hotkey')">
            <FontAwesomeIcon :icon="['fas', 'keyboard']" />
            <span>Send Hotkey</span>
          </button>
          <button v-show="matchesSearch('Type Text')" class="action-item" @click="selectAction('text')">
            <FontAwesomeIcon :icon="['fas', 'font']" />
            <span>Type Text</span>
          </button>
          <button v-show="matchesSearch('Copy to Clipboard')" class="action-item" @click="selectAction('clipboard')">
            <FontAwesomeIcon :icon="['fas', 'clipboard']" />
            <span>Copy to Clipboard</span>
          </button>
          <button v-show="matchesSearch('Paste from Clipboard')" class="action-item" @click="selectAction('paste')">
            <FontAwesomeIcon :icon="['fas', 'paste']" />
            <span>Paste from Clipboard</span>
          </button>
          <button v-show="matchesSearch('Macro')" class="action-item" @click="selectAction('macro')">
            <FontAwesomeIcon :icon="['fas', 'list']" />
            <span>Macro</span>
          </button>
        </div>
      </div>

      <!-- Streaming Category -->
      <div v-show="shouldShowCategory('streaming')" class="action-category">
        <button class="category-header" @click="toggleCategory('streaming')">
          <FontAwesomeIcon :icon="expandedCategories.includes('streaming') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Streaming</span>
          <span class="count">(7)</span>
        </button>
        <div v-show="expandedCategories.includes('streaming')" class="category-items">
          <button v-show="matchesSearch('OBS Start Recording')" class="action-item" @click="selectAction('obs_record')">
            <FontAwesomeIcon :icon="['fas', 'circle']" />
            <span>OBS Start Recording</span>
          </button>
          <button v-show="matchesSearch('OBS Start Streaming')" class="action-item" @click="selectAction('obs_stream')">
            <FontAwesomeIcon :icon="['fas', 'broadcast-tower']" />
            <span>OBS Start Streaming</span>
          </button>
          <button v-show="matchesSearch('OBS Switch Scene')" class="action-item" @click="selectAction('obs_scene')">
            <FontAwesomeIcon :icon="['fas', 'th-large']" />
            <span>OBS Switch Scene</span>
          </button>
          <button v-show="matchesSearch('Toggle Microphone')" class="action-item" @click="selectAction('mic_toggle')">
            <FontAwesomeIcon :icon="['fas', 'microphone']" />
            <span>Toggle Microphone</span>
          </button>
          <button v-show="matchesSearch('Toggle Camera')" class="action-item" @click="selectAction('camera_toggle')">
            <FontAwesomeIcon :icon="['fas', 'video']" />
            <span>Toggle Camera</span>
          </button>
        </div>
      </div>

      <!-- Custom Category -->
      <div v-show="shouldShowCategory('custom')" class="action-category">
        <button class="category-header" @click="toggleCategory('custom')">
          <FontAwesomeIcon :icon="expandedCategories.includes('custom') ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']" />
          <span>Custom</span>
          <span class="count">(4)</span>
        </button>
        <div v-show="expandedCategories.includes('custom')" class="category-items">
          <button v-show="matchesSearch('Multi-Action')" class="action-item" @click="selectAction('multi_action')">
            <FontAwesomeIcon :icon="['fas', 'layer-group']" />
            <span>Multi-Action</span>
          </button>
          <button v-show="matchesSearch('Plugin Action')" class="action-item" @click="selectAction('plugin')">
            <FontAwesomeIcon :icon="['fas', 'plug']" />
            <span>Plugin Action</span>
          </button>
          <button v-show="matchesSearch('Cross-Platform')" class="action-item" @click="selectAction('cross_platform')">
            <FontAwesomeIcon :icon="['fas', 'desktop']" />
            <span>Cross-Platform</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  isOpen?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
  selectAction: [actionType: string]
}>()

const searchQuery = ref('')
const expandedCategories = ref<string[]>(['metrics', 'time', 'weather']) // Auto-expand new categories

function toggleCategory(category: string) {
  const index = expandedCategories.value.indexOf(category)
  if (index >= 0) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(category)
  }
}

function matchesSearch(actionName: string): boolean {
  if (!searchQuery.value) return true
  return actionName.toLowerCase().includes(searchQuery.value.toLowerCase())
}

function shouldShowCategory(category: string): boolean {
  if (!searchQuery.value) return true
  
  // If searching, show category if any of its items match
  const categoryItems: Record<string, string[]> = {
    system: ['Launch Program', 'Run Command', 'Send Hotkey', 'Macro', 'Open Folder', 'Screenshot'],
    media: ['Play/Pause', 'Next Track', 'Previous Track', 'Stop', 'Volume Up', 'Volume Down', 'Mute'],
    web: ['Open URL', 'Open Application', 'Open Folder', 'Open File', 'Screenshot', 'Copy to Clipboard'],
    metrics: ['Memory', 'CPU usage', 'CPU temperature', 'CPU frequency', 'CPU package power', 'Internet speed', 'Harddisk', 'GPU temperature', 'GPU core frequency', 'GPU Core Usage', 'GPU memory frequency', 'GPU Memory Usage'],
    time: ['World Time', 'Timer', 'Countdown'],
    weather: ['Weather query'],
    text: ['Send Hotkey', 'Type Text', 'Copy to Clipboard', 'Paste from Clipboard', 'Macro'],
    streaming: ['OBS Start Recording', 'OBS Start Streaming', 'OBS Switch Scene', 'Toggle Microphone', 'Toggle Camera'],
    custom: ['Multi-Action', 'Plugin Action', 'Cross-Platform']
  }
  
  const items = categoryItems[category] || []
  return items.some(item => matchesSearch(item))
}

function selectAction(actionType: string) {
  emit('selectAction', actionType)
}
</script>

<style scoped>
.actions-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background: linear-gradient(180deg, #2d1b4e 0%, #1a0d2e 100%);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
}

.actions-sidebar.is-open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.5rem;
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color 0.2s;
}

.close-btn:hover {
  color: white;
}

.search-box {
  position: relative;
  padding: var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-icon {
  position: absolute;
  left: calc(var(--spacing-md) + 12px);
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.5);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  color: white;
  font-size: 0.9rem;
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: var(--color-primary);
}

.actions-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.action-category {
  margin-bottom: var(--spacing-xs);
}

.category-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.category-header:hover {
  background: rgba(255, 255, 255, 0.1);
}

.category-header .count {
  margin-left: auto;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.category-items {
  padding: var(--spacing-xs) 0;
  padding-left: var(--spacing-md);
}

.action-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.action-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(4px);
}

.action-item svg {
  width: 18px;
  color: var(--color-primary);
}

/* Scrollbar styling */
.actions-list::-webkit-scrollbar {
  width: 8px;
}

.actions-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.actions-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.actions-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>

