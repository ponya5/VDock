<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal button-editor">
      <div class="modal-header">
        <h2>Edit Button</h2>
        <button class="close-btn" @click="emit('close')">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <div class="modal-body">
        <!-- Browse Actions Button -->
        <div class="form-group">
          <button class="btn btn-primary" @click="showActionsSidebar = true" style="width: 100%;">
            <FontAwesomeIcon :icon="['fas', 'list']" />
            Browse Button Actions
          </button>
        </div>
        <div class="form-group">
          <label>Label</label>
          <input v-model="editedButton.label" type="text" class="input" placeholder="Button label" />
        </div>

        <div class="form-group">
          <label>Secondary Label (optional)</label>
          <input 
            v-model="editedButton.secondary_label" 
            type="text" 
            class="input" 
            placeholder="Secondary text"
          />
        </div>

        <div class="form-group">
          <label>Icon</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.icon_type" class="select" style="flex: 1">
              <option value="fontawesome">FontAwesome Icon</option>
              <option value="custom">Custom Image</option>
            </select>
          </div>
        </div>

        <div v-if="editedButton.icon_type === 'fontawesome'" class="form-group">
          <label>FontAwesome Icon</label>
          <div class="flex gap-sm">
            <input 
              v-model="editedButton.icon" 
              type="text" 
              class="input" 
              placeholder="fas fa-home"
              style="flex: 1"
            />
            <button class="btn btn-secondary" @click="showAssetPicker = 'icon'">
              <FontAwesomeIcon :icon="['fas', 'icons']" /> Browse Icons
            </button>
          </div>
        </div>

        <div v-if="editedButton.icon_type === 'custom'" class="form-group">
          <label>Custom Image URL</label>
          <input 
            v-model="editedButton.icon" 
            type="text" 
            class="input" 
            placeholder="https://example.com/image.png"
          />
        </div>

        <div class="form-group">
          <label>Background Media (Optional)</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.media_type" class="select" style="flex: 1">
              <option value="">No Background Media</option>
              <option value="image">Static Image</option>
              <option value="gif">GIF Animation</option>
              <option value="video">Video</option>
            </select>
            <button 
              v-if="editedButton.media_type" 
              class="btn btn-secondary" 
              @click="showAssetPicker = 'animation'"
            >
              <FontAwesomeIcon :icon="['fas', 'film']" /> Browse Media
            </button>
          </div>
        </div>

        <div v-if="editedButton.media_type && !showAssetPicker" class="form-group">
          <label>Background Media URL</label>
          <input 
            v-model="editedButton.media_url" 
            type="text" 
            class="input" 
            placeholder="Enter media URL or use Browse Media button"
          />
          <p class="form-help">
            {{ getMediaHelpText(editedButton.media_type) }}
          </p>
        </div>

        <div class="form-group">
          <label>Background Color</label>
          <div class="color-picker-section">
            <div class="current-color" :style="{ backgroundColor: editedButton.style?.backgroundColor || '#2c3e50' }">
              <input 
                v-model="editedButton.style.backgroundColor" 
                type="color" 
                class="color-input"
                @input="updateBackgroundColor"
              />
            </div>
            <div class="color-palette">
              <div 
                v-for="color in colorPalette" 
                :key="color"
                class="color-swatch"
                :class="{ active: editedButton.style?.backgroundColor === color }"
                :style="{ backgroundColor: color }"
                @click="selectColor(color)"
                :title="color"
              ></div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Icon Size</label>
          <div class="icon-size-controls">
            <input 
              v-model.number="editedButton.style.iconSize" 
              type="range" 
              class="icon-size-slider"
              min="16" 
              max="128" 
              step="4"
              @input="updateIconSize"
            />
            <div class="icon-size-display">
              <span>{{ editedButton.style?.iconSize || 32 }}px</span>
              <div class="icon-preview">
                <FontAwesomeIcon 
                  :icon="editedButton.icon || ['fas', 'home']" 
                  :style="{ fontSize: `${editedButton.style?.iconSize || 32}px` }"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Shape</label>
          <select v-model="editedButton.shape" class="select">
            <option value="rectangle">Rectangle</option>
            <option value="rounded">Rounded</option>
            <option value="circle">Circle</option>
            <option value="hexagon">Hexagon</option>
            <option value="diamond">Diamond</option>
            <option value="octagon">Octagon</option>
          </select>
        </div>

        <div class="form-group">
          <label>Visual Effects</label>
          <div class="flex gap-sm">
            <select v-model="editedButton.style.effect" class="select" style="flex: 1">
              <option value="none">None</option>
              <option value="glass">Glass Morphism</option>
              <option value="neumorphism">Neumorphism</option>
              <option value="gradient">Gradient</option>
              <option value="glow">Glow Effect</option>
              <option value="3d">3D Effect</option>
            </select>
            <button 
              class="btn btn-secondary" 
              @click="showAssetPicker = 'background'"
              title="Browse Background Assets"
            >
              <FontAwesomeIcon :icon="['fas', 'palette']" /> Backgrounds
            </button>
          </div>
        </div>

        <div v-if="editedButton.style?.effect === 'gradient'" class="form-group">
          <label>Custom Gradient</label>
          <input 
            v-model="editedButton.style.gradient" 
            type="text" 
            class="input" 
            placeholder="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
          />
        </div>

        <div class="form-group">
          <label>Animation</label>
          <select v-model="editedButton.style.animation" class="select">
            <option value="none">None</option>
            <option value="pulse">Pulse</option>
            <option value="shimmer">Shimmer</option>
            <option value="bounce">Bounce</option>
            <option value="rotate">Rotate</option>
          </select>
        </div>

        <div class="form-group">
          <label>Position</label>
          <div class="flex gap-sm">
            <div style="flex: 1">
              <label class="small-label">Row</label>
              <input v-model.number="editedButton.position.row" type="number" class="input" min="0" />
            </div>
            <div style="flex: 1">
              <label class="small-label">Column</label>
              <input v-model.number="editedButton.position.col" type="number" class="input" min="0" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Size</label>
          <div class="flex gap-sm">
            <div style="flex: 1">
              <label class="small-label">Rows</label>
              <input v-model.number="editedButton.size.rows" type="number" class="input" min="1" max="3" />
            </div>
            <div style="flex: 1">
              <label class="small-label">Columns</label>
              <input v-model.number="editedButton.size.cols" type="number" class="input" min="1" max="3" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Action Type</label>
          <select v-model="actionType" class="select" @change="handleActionTypeChange">
            <option value="">No Action</option>
            <option value="url">Open URL</option>
            <option value="program">Launch Program</option>
            <option value="command">Run Command</option>
            <option value="hotkey">Send Hotkey</option>
            <option value="macro">Macro (Multiple Actions)</option>
            <option value="multi_action">Multi-Action</option>
            <option value="system_metric">System Metric Display</option>
            
            <optgroup label="📊 System Performance Monitor">
              <option value="metric_memory">Memory</option>
              <option value="metric_cpu_usage">CPU usage</option>
              <option value="metric_cpu_temperature">CPU temperature</option>
              <option value="metric_cpu_frequency">CPU frequency</option>
              <option value="metric_cpu_power">CPU package power</option>
              <option value="metric_internet_speed">Internet speed</option>
              <option value="metric_harddisk">Harddisk</option>
              <option value="metric_gpu_temperature">GPU temperature</option>
              <option value="metric_gpu_frequency">GPU core frequency</option>
              <option value="metric_gpu_usage">GPU Core Usage</option>
              <option value="metric_gpu_memory_freq">GPU memory frequency</option>
              <option value="metric_gpu_memory_usage">GPU Memory Usage</option>
            </optgroup>
            
            <optgroup label="🕐 Time Options">
              <option value="calendar">Calendar</option>
              <option value="time_world_clock">World Time</option>
              <option value="time_timer">Timer</option>
              <option value="time_countdown">Countdown</option>
            </optgroup>
            
            <optgroup label="🌤️ Weather query">
              <option value="weather">Weather query</option>
            </optgroup>
            
            <option value="system_control">System Control</option>
            <option value="cross_platform">Cross-Platform Action</option>
          </select>
        </div>

        <!-- Action-specific configuration -->
        <div v-if="actionType === 'url'" class="form-group">
          <label>URL</label>
          <input v-model="actionConfig.url" type="text" class="input" placeholder="https://example.com" />
        </div>

        <div v-if="actionType === 'program'" class="form-group">
          <label>Program Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\\Program Files\\..." />
        </div>

        <div v-if="actionType === 'command'" class="form-group">
          <label>Command</label>
          <textarea v-model="actionConfig.command" class="textarea" placeholder="echo Hello"></textarea>
        </div>

        <div v-if="actionType === 'hotkey'" class="form-group">
          <label>Keys (comma-separated)</label>
          <input 
            v-model="hotkeyString" 
            type="text" 
            class="input" 
            placeholder="ctrl, c" 
            @input="updateHotkeyConfig"
          />
        </div>

        <!-- Macro Configuration -->
        <div v-if="actionType === 'macro'" class="macro-editor">
          <div class="form-group">
            <div class="flex items-center justify-between">
              <label>Macro Steps</label>
              <button class="btn btn-sm btn-primary" @click="addMacroStep" type="button">
                <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Step
              </button>
            </div>
            <p class="form-help">Execute multiple actions in sequence with delays</p>
          </div>

          <div v-if="macroSteps.length === 0" class="empty-state">
            <p>No macro steps defined. Click "Add Step" to create your first macro step.</p>
          </div>

          <div v-for="(step, index) in macroSteps" :key="index" class="macro-step">
            <div class="macro-step-header">
              <span class="step-number">Step {{ index + 1 }}</span>
              <div class="step-actions">
                <button 
                  class="btn-icon" 
                  @click="moveMacroStep(index, -1)" 
                  :disabled="index === 0"
                  type="button"
                  title="Move Up"
                >
                  <FontAwesomeIcon :icon="['fas', 'arrow-up']" />
                </button>
                <button 
                  class="btn-icon" 
                  @click="moveMacroStep(index, 1)" 
                  :disabled="index === macroSteps.length - 1"
                  type="button"
                  title="Move Down"
                >
                  <FontAwesomeIcon :icon="['fas', 'arrow-down']" />
                </button>
                <button 
                  class="btn-icon btn-danger" 
                  @click="removeMacroStep(index)"
                  type="button"
                  title="Delete"
                >
                  <FontAwesomeIcon :icon="['fas', 'trash']" />
                </button>
              </div>
            </div>

            <div class="macro-step-content">
              <div class="form-group">
                <label class="small-label">Step Type</label>
                <select v-model="step.type" class="select">
                  <option value="hotkey">Hotkey</option>
                  <option value="delay">Delay</option>
                  <option value="text">Type Text</option>
                  <option value="click">Mouse Click</option>
                </select>
              </div>

              <div v-if="step.type === 'hotkey'" class="form-group">
                <label class="small-label">Keys (comma-separated)</label>
                <input 
                  v-model="step.keysString" 
                  type="text" 
                  class="input" 
                  placeholder="ctrl, c"
                  @input="updateMacroStepKeys(index)"
                />
                <p class="form-help-sm">Example: ctrl, c or alt, tab or win, d</p>
              </div>

              <div v-if="step.type === 'delay'" class="form-group">
                <label class="small-label">Delay (milliseconds)</label>
                <input 
                  v-model.number="step.delay" 
                  type="number" 
                  class="input" 
                  min="0" 
                  step="100"
                  placeholder="500"
                />
                <p class="form-help-sm">1000ms = 1 second</p>
              </div>

              <div v-if="step.type === 'text'" class="form-group">
                <label class="small-label">Text to Type</label>
                <textarea 
                  v-model="step.text" 
                  class="textarea" 
                  rows="2"
                  placeholder="Enter text to type automatically"
                ></textarea>
              </div>

              <div v-if="step.type === 'click'" class="form-group">
                <label class="small-label">Click Position (optional)</label>
                <div class="flex gap-sm">
                  <input 
                    v-model.number="step.clickX" 
                    type="number" 
                    class="input" 
                    placeholder="X coordinate"
                    style="flex: 1"
                  />
                  <input 
                    v-model.number="step.clickY" 
                    type="number" 
                    class="input" 
                    placeholder="Y coordinate"
                    style="flex: 1"
                  />
                </div>
                <p class="form-help-sm">Leave empty to click at current mouse position</p>
              </div>
            </div>
          </div>
        </div>

        <!-- System Metric Configuration -->
        <div v-if="actionType === 'system_metric'" class="form-group">
          <label>Metric Type</label>
          <select v-model="actionConfig.metric_type" class="select">
            <option value="cpu">CPU Usage</option>
            <option value="memory">Memory (RAM)</option>
            <option value="disk">Disk Space</option>
            <option value="network">Network Traffic</option>
            <option value="temperature">Temperature</option>
            <option value="battery">Battery</option>
            <option value="processes">Processes</option>
          </select>
          <p class="form-help">Button will display live metrics with auto-refresh</p>
        </div>

        <div v-if="actionType === 'system_metric'" class="form-group">
          <label>Refresh Interval (seconds)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="1" 
            max="60"
            placeholder="2"
          />
          <p class="form-help">How often to update the metric (default: 2 seconds)</p>
        </div>

        <!-- Individual Metric Configuration -->
        <div v-if="isMetricType" class="form-group">
          <label>Refresh Interval (seconds)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="1" 
            max="60"
            placeholder="2"
          />
          <p class="form-help">How often to update the metric (default: 2 seconds)</p>
        </div>

        <!-- World Clock Configuration -->
        <div v-if="actionType === 'time_world_clock'" class="form-group">
          <label>Timezone</label>
          <select v-model="actionConfig.timezone" class="select">
            <option value="local">Local Time</option>
            <option value="America/New_York">New York (EST/EDT)</option>
            <option value="America/Chicago">Chicago (CST/CDT)</option>
            <option value="America/Denver">Denver (MST/MDT)</option>
            <option value="America/Los_Angeles">Los Angeles (PST/PDT)</option>
            <option value="Europe/London">London (GMT/BST)</option>
            <option value="Europe/Paris">Paris (CET/CEST)</option>
            <option value="Asia/Tokyo">Tokyo (JST)</option>
            <option value="Asia/Shanghai">Shanghai (CST)</option>
            <option value="Asia/Dubai">Dubai (GST)</option>
            <option value="Australia/Sydney">Sydney (AEST/AEDT)</option>
          </select>
        </div>

        <!-- Timer Configuration -->
        <div v-if="actionType === 'time_timer'" class="form-group">
          <label>Timer Duration (seconds)</label>
          <input 
            v-model.number="actionConfig.timer_duration" 
            type="number" 
            class="input" 
            min="0"
            placeholder="0"
          />
          <p class="form-help">Initial duration (0 for stopwatch mode)</p>
        </div>

        <!-- Countdown Configuration -->
        <div v-if="actionType === 'time_countdown'" class="form-group">
          <label>Countdown Target Date/Time</label>
          <input 
            v-model="actionConfig.countdown_target" 
            type="datetime-local" 
            class="input"
          />
          <p class="form-help">Leave empty to countdown until tomorrow</p>
        </div>

        <!-- Weather Configuration -->
        <div v-if="actionType === 'weather'" class="form-group">
          <label>Location</label>
          <input 
            v-model="actionConfig.weather_location" 
            type="text" 
            class="input" 
            placeholder="auto (or enter city name)"
          />
          <p class="form-help">Enter city name or "auto" for automatic location</p>
        </div>

        <div v-if="actionType === 'weather'" class="form-group">
          <label>Refresh Interval (minutes)</label>
          <input 
            v-model.number="actionConfig.refresh_interval" 
            type="number" 
            class="input" 
            min="5" 
            max="120"
            placeholder="15"
          />
          <p class="form-help">How often to update weather data (default: 15 minutes)</p>
        </div>

        <div v-if="actionType === 'system_control'" class="form-group">
          <label>System Action</label>
          <select v-model="actionConfig.action" class="select">
            <option value="volume_up">Volume Up</option>
            <option value="volume_down">Volume Down</option>
            <option value="volume_mute">Mute/Unmute</option>
            <option value="media_play_pause">Play/Pause</option>
            <option value="media_next">Next Track</option>
            <option value="media_previous">Previous Track</option>
            <option value="fullscreen">Full Screen</option>
          </select>
        </div>

        <div v-if="actionType === 'cross_platform'" class="form-group">
          <label>Cross-Platform Action</label>
          <select v-model="actionConfig.action" class="select">
            <optgroup label="System Control">
              <option value="shutdown">Shutdown</option>
              <option value="restart">Restart</option>
              <option value="sleep">Sleep</option>
              <option value="lock_screen">Lock Screen</option>
            </optgroup>
            <optgroup label="Volume Control">
              <option value="volume_up">Volume Up</option>
              <option value="volume_down">Volume Down</option>
              <option value="volume_mute">Mute</option>
              <option value="volume_unmute">Unmute</option>
            </optgroup>
            <optgroup label="Brightness Control">
              <option value="brightness_up">Brightness Up</option>
              <option value="brightness_down">Brightness Down</option>
              <option value="brightness_set">Set Brightness</option>
            </optgroup>
            <optgroup label="Media Control">
              <option value="media_play_pause">Play/Pause</option>
              <option value="media_next">Next Track</option>
              <option value="media_previous">Previous Track</option>
              <option value="media_stop">Stop</option>
            </optgroup>
            <optgroup label="Web & Apps">
              <option value="open_url">Open URL</option>
              <option value="open_app">Open Application</option>
              <option value="open_folder">Open Folder</option>
              <option value="open_file">Open File</option>
              <option value="screenshot">Screenshot</option>
            </optgroup>
          </select>
        </div>

        <!-- Cross-platform action specific configuration -->
        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_url'" class="form-group">
          <label>URL</label>
          <input v-model="actionConfig.url" type="text" class="input" placeholder="https://example.com" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_app'" class="form-group">
          <label>Application Path/Name</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="notepad.exe" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_folder'" class="form-group">
          <label>Folder Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'open_file'" class="form-group">
          <label>File Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="C:\Windows\System32\notepad.exe" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'screenshot'" class="form-group">
          <label>Screenshot Path</label>
          <input v-model="actionConfig.path" type="text" class="input" placeholder="screenshot.png" />
        </div>

        <div v-if="actionType === 'cross_platform' && ['volume_up', 'volume_down', 'brightness_up', 'brightness_down'].includes(actionConfig.action)" class="form-group">
          <label>Step Size</label>
          <input v-model.number="actionConfig.step" type="number" class="input" min="1" max="100" placeholder="10" />
        </div>

        <div v-if="actionType === 'cross_platform' && actionConfig.action === 'brightness_set'" class="form-group">
          <label>Brightness Level (0-100)</label>
          <input v-model.number="actionConfig.brightness" type="number" class="input" min="0" max="100" placeholder="50" />
        </div>

        <div class="form-group">
          <label>Tooltip (optional)</label>
          <input v-model="editedButton.tooltip" type="text" class="input" placeholder="Button description" />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="editedButton.enabled" type="checkbox" />
            <span>Enabled</span>
          </label>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="handleSave">Save</button>
      </div>
    </div>

    <IconPicker 
      v-if="showIconPicker" 
      @select="handleIconSelect" 
      @close="showIconPicker = false" 
    />

    <!-- Asset Picker Modal -->
    <AssetPicker
      v-if="showAssetPicker"
      :type="showAssetPicker"
      :title="getAssetPickerTitle(showAssetPicker)"
      @close="showAssetPicker = null"
      @select="handleAssetSelect"
    />

    <!-- Actions Sidebar -->
    <ButtonActionsSidebar
      :is-open="showActionsSidebar"
      @close="showActionsSidebar = false"
      @select-action="handleActionSelection"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Button, ButtonAction, ActionType } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import IconPicker from './IconPicker.vue'
import MediaPicker from './MediaPicker.vue'
import AssetPicker from './AssetPicker.vue'
import ButtonActionsSidebar from './ButtonActionsSidebar.vue'
import type { AssetMetadata } from '@/utils/assetManager'

interface Props {
  button: Button
  profileId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [button: Button]
  close: []
}>()

const editedButton = ref<Button>(JSON.parse(JSON.stringify(props.button)))
const showIconPicker = ref(false)
const showAssetPicker = ref<'icon' | 'animation' | 'background' | null>(null)
const showActionsSidebar = ref(false)

const actionType = ref<ActionType | ''>(props.button.action?.type || '')
const actionConfig = ref<Record<string, any>>(props.button.action?.config || {})
const hotkeyString = ref(props.button.action?.config?.keys?.join(', ') || '')

// Macro steps management
interface MacroStepUI {
  type: 'hotkey' | 'delay' | 'text' | 'click'
  keysString?: string
  keys?: string[]
  delay?: number
  text?: string
  clickX?: number
  clickY?: number
  position?: { x: number; y: number }
}

const macroSteps = ref<MacroStepUI[]>([])

// Performance Monitor metrics
const performanceMetricOptions = [
  { value: 'memory', label: 'Memory' },
  { value: 'cpu_usage', label: 'CPU usage' },
  { value: 'cpu_temperature', label: 'CPU temperature' },
  { value: 'cpu_frequency', label: 'CPU frequency' },
  { value: 'cpu_package_power', label: 'CPU package power' },
  { value: 'internet_speed', label: 'Internet speed' },
  { value: 'harddisk', label: 'Harddisk' },
  { value: 'gpu_temperature', label: 'GPU temperature' },
  { value: 'gpu_core_frequency', label: 'GPU core frequency' },
  { value: 'gpu_core_usage', label: 'Gpu Core Usage' },
  { value: 'gpu_memory_frequency', label: 'GPU memory frequency' },
  { value: 'gpu_memory_usage', label: 'Gpu Memory Usage' },
]

const selectedPerformanceMetrics = ref<string[]>([])

// Check if action type is a metric type
const isMetricType = computed(() => {
  return actionType.value?.startsWith('metric_')
})

// Initialize macro steps from existing button action
if (props.button.action?.type === 'macro' && props.button.action.macro_steps) {
  macroSteps.value = props.button.action.macro_steps.map((step: any) => ({
    type: step.type,
    keysString: step.keys?.join(', ') || '',
    keys: step.keys || [],
    delay: step.delay,
    text: step.text,
    clickX: step.position?.x,
    clickY: step.position?.y,
    position: step.position
  }))
}

// Color palette for background color selection
const colorPalette = ref([
  '#2c3e50', '#34495e', '#7f8c8d', '#95a5a6', '#bdc3c7', '#ecf0f1',
  '#e74c3c', '#c0392b', '#e67e22', '#d35400', '#f39c12', '#f1c40f',
  '#27ae60', '#16a085', '#2ecc71', '#1abc9c', '#3498db', '#2980b9',
  '#9b59b6', '#8e44ad', '#e91e63', '#ad1457', '#673ab7', '#512da8',
  '#795548', '#5d4037', '#607d8b', '#455a64', '#000000', '#ffffff'
])

// Media picker value
const mediaValue = ref<{ url: string; type: string } | null>(
  props.button.media_url && props.button.media_type 
    ? { url: props.button.media_url, type: props.button.media_type }
    : null
)

watch(actionType, (newType) => {
  if (!newType) {
    editedButton.value.action = undefined
  } else {
    editedButton.value.action = {
      type: newType,
      config: actionConfig.value
    }
  }
})

watch(actionConfig, (newConfig) => {
  if (editedButton.value.action) {
    editedButton.value.action.config = newConfig
  }
}, { deep: true })

// Watch for media type changes to clear media when type is removed
watch(() => editedButton.value.media_type, (newType) => {
  if (!newType) {
    editedButton.value.media_url = undefined
    mediaValue.value = null
  }
})

function handleActionTypeChange() {
  actionConfig.value = {}
  hotkeyString.value = ''
}

function updateHotkeyConfig() {
  actionConfig.value.keys = hotkeyString.value
    .split(',')
    .map(k => k.trim())
    .filter(k => k.length > 0)
}

function handleIconSelect(icon: string) {
  editedButton.value.icon = icon
  editedButton.value.icon_type = 'fontawesome'
  showIconPicker.value = false
}

function getAssetPickerTitle(type: string): string {
  switch (type) {
    case 'icon': return 'Select Icon'
    case 'animation': return 'Select Animation'
    case 'background': return 'Select Background'
    default: return 'Select Asset'
  }
}

function handleAssetSelect(asset: AssetMetadata) {
  switch (showAssetPicker.value) {
    case 'icon':
      if (asset.format === 'fontawesome') {
        editedButton.value.icon_type = 'fontawesome'
        editedButton.value.icon = asset.icon
      } else {
        editedButton.value.icon_type = 'custom'
        editedButton.value.icon = asset.url
      }
      break
    
    case 'animation':
      editedButton.value.media_url = asset.url
      editedButton.value.media_type = asset.format === 'gif' ? 'gif' : 'video'
      break
    
    case 'background':
      if (asset.format === 'css') {
        editedButton.value.style = editedButton.value.style || {}
        editedButton.value.style.effect = 'gradient'
        editedButton.value.style.gradient = asset.css
      } else {
        // Handle image backgrounds
        editedButton.value.media_url = asset.url
        editedButton.value.media_type = 'image'
      }
      break
  }
  
  showAssetPicker.value = null
}

function handleMediaChange(value: { url: string; type: string } | null) {
  if (value) {
    editedButton.value.media_url = value.url
    editedButton.value.media_type = value.type
  } else {
    editedButton.value.media_url = undefined
    editedButton.value.media_type = undefined
  }
}

function getMediaPlaceholder(mediaType: string) {
  switch (mediaType) {
    case 'image':
      return 'https://example.com/image.png'
    case 'gif':
      return 'https://example.com/animation.gif'
    case 'video':
      return 'https://example.com/video.mp4'
    default:
      return ''
  }
}

function getMediaHelpText(mediaType: string) {
  switch (mediaType) {
    case 'image':
      return 'Static image will be displayed as background behind the icon'
    case 'gif':
      return 'GIF animation will loop continuously behind the icon'
    case 'video':
      return 'Video will autoplay, loop, and be muted behind the icon'
    default:
      return ''
  }
}

function selectColor(color: string) {
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.backgroundColor = color
}

function updateBackgroundColor(event: Event) {
  const target = event.target as HTMLInputElement
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.backgroundColor = target.value
}

function updateIconSize(event: Event) {
  const target = event.target as HTMLInputElement
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  editedButton.value.style.iconSize = parseInt(target.value)
}

// Macro step functions
function addMacroStep() {
  macroSteps.value.push({
    type: 'hotkey',
    keysString: '',
    keys: [],
    delay: 500
  })
}

function removeMacroStep(index: number) {
  macroSteps.value.splice(index, 1)
}

function moveMacroStep(index: number, direction: number) {
  const newIndex = index + direction
  if (newIndex >= 0 && newIndex < macroSteps.value.length) {
    const temp = macroSteps.value[index]
    macroSteps.value[index] = macroSteps.value[newIndex]
    macroSteps.value[newIndex] = temp
  }
}

function updateMacroStepKeys(index: number) {
  const step = macroSteps.value[index]
  if (step.keysString) {
    step.keys = step.keysString
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0)
  }
}

function handleActionSelection(selectedActionType: string) {
  actionType.value = selectedActionType as ActionType
  actionConfig.value = {}
  hotkeyString.value = ''
  showActionsSidebar.value = false
  
  // Set default labels based on action type
  const actionLabels: Record<string, string> = {
    'metric_memory': 'Memory',
    'metric_cpu_usage': 'CPU',
    'metric_cpu_temperature': 'CPU Temp',
    'metric_cpu_frequency': 'CPU Freq',
    'metric_cpu_power': 'CPU Power',
    'metric_internet_speed': 'Internet',
    'metric_harddisk': 'Disk',
    'metric_gpu_temperature': 'GPU Temp',
    'metric_gpu_frequency': 'GPU Freq',
    'metric_gpu_usage': 'GPU Usage',
    'metric_gpu_memory_freq': 'GPU Mem Freq',
    'metric_gpu_memory_usage': 'GPU Mem',
    'calendar': 'Calendar',
    'time_world_clock': 'World Clock',
    'time_timer': 'Timer',
    'time_countdown': 'Countdown',
    'weather': 'Weather'
  }
  
  if (actionLabels[selectedActionType]) {
    editedButton.value.label = actionLabels[selectedActionType]
  }
}

function handleSave() {
  // Ensure style object exists
  if (!editedButton.value.style) {
    editedButton.value.style = {}
  }
  
  // Set default values if not provided
  if (!editedButton.value.style.backgroundColor) {
    editedButton.value.style.backgroundColor = '#2c3e50'
  }
  if (!editedButton.value.style.iconSize) {
    editedButton.value.style.iconSize = 32
  }
  
  // Update action if configured
  if (actionType.value) {
    if (!editedButton.value.action) {
      editedButton.value.action = {
        type: actionType.value,
        config: {}
      }
    }
    
    editedButton.value.action.type = actionType.value
    editedButton.value.action.config = actionConfig.value
    
    // Handle macro steps
    if (actionType.value === 'macro') {
      editedButton.value.action.macro_steps = macroSteps.value.map(step => {
        const macroStep: any = {
          type: step.type
        }
        
        if (step.type === 'hotkey' && step.keys) {
          macroStep.keys = step.keys
        } else if (step.type === 'delay') {
          macroStep.delay = step.delay || 500
        } else if (step.type === 'text') {
          macroStep.text = step.text || ''
        } else if (step.type === 'click') {
          if (step.clickX !== undefined && step.clickY !== undefined) {
            macroStep.position = { x: step.clickX, y: step.clickY }
          }
        }
        
        return macroStep
      })
    }
    
    // Handle performance monitor metrics
    if (actionType.value === 'performance_monitor') {
      editedButton.value.action.performance_metrics = selectedPerformanceMetrics.value
    }
    
    // Handle time options
    if (actionType.value === 'time_options') {
      editedButton.value.action.time_option = actionConfig.value.time_option
      editedButton.value.action.timezone = actionConfig.value.timezone
      editedButton.value.action.timer_duration = actionConfig.value.timer_duration
      editedButton.value.action.countdown_target = actionConfig.value.countdown_target
    }
    
    // Handle weather query
    if (actionType.value === 'weather_query') {
      editedButton.value.action.weather_location = actionConfig.value.weather_location || 'auto'
    }
  }
  
  emit('save', editedButton.value)
}
</script>

<style scoped>
.button-editor {
  width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text);
}

.small-label {
  font-size: 0.75rem;
  font-weight: normal;
  color: var(--color-text-secondary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.form-help {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  margin-bottom: 0;
}

/* Color Picker Styles */
.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.current-color {
  width: 60px;
  height: 40px;
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.color-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0;
}

.color-palette {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--spacing-xs);
  max-width: 300px;
}

.color-swatch {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.color-swatch:hover {
  transform: scale(1.1);
  border-color: var(--color-primary);
}

.color-swatch.active {
  border-color: var(--color-primary);
  border-width: 3px;
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

/* Icon Size Controls */
.icon-size-controls {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.icon-size-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.icon-size-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface-solid);
  box-shadow: var(--shadow-sm);
}

.icon-size-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface-solid);
  box-shadow: var(--shadow-sm);
}

.icon-size-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.icon-size-display span {
  font-weight: 500;
  color: var(--color-text);
  font-size: 0.875rem;
}

.icon-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background-color: var(--color-surface-solid);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

/* Macro Editor Styles */
.macro-editor {
  margin: var(--spacing-md) 0;
}

.macro-step {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.macro-step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.step-number {
  font-weight: 600;
  color: var(--color-primary);
  font-size: 0.875rem;
}

.step-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.btn-icon {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  cursor: pointer;
  color: var(--color-text);
  transition: all var(--transition-fast);
  font-size: 0.75rem;
}

.btn-icon:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon.btn-danger:hover:not(:disabled) {
  background: #ef4444;
  border-color: #ef4444;
}

.macro-step-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.small-label {
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: var(--spacing-xs);
  display: block;
}

.form-help-sm {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  max-height: 300px;
  overflow-y: auto;
}

.checkbox-group .checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: background-color 0.2s;
}

.checkbox-group .checkbox-label:hover {
  background-color: var(--color-background);
}

.checkbox-group input[type="checkbox"] {
  cursor: pointer;
}

.btn-sm {
  font-size: 0.875rem;
  padding: var(--spacing-xs) var(--spacing-sm);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
}
</style>

