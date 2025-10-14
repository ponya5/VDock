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
              max="64" 
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
            <option value="multi_action">Multi-Action</option>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Button, ButtonAction, ActionType } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import IconPicker from './IconPicker.vue'
import MediaPicker from './MediaPicker.vue'
import AssetPicker from './AssetPicker.vue'
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

const actionType = ref<ActionType | ''>(props.button.action?.type || '')
const actionConfig = ref<Record<string, any>>(props.button.action?.config || {})
const hotkeyString = ref(props.button.action?.config?.keys?.join(', ') || '')

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
  if (actionType.value && editedButton.value.action) {
    editedButton.value.action.config = actionConfig.value
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
  width: 40px;
  height: 40px;
  background-color: var(--color-surface-solid);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}
</style>

