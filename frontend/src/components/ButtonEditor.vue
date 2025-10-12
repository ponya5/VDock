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
            <input 
              v-model="editedButton.icon" 
              type="text" 
              class="input" 
              placeholder="fas fa-home"
              style="flex: 1"
            />
            <button class="btn btn-secondary" @click="showIconPicker = true">
              <FontAwesomeIcon :icon="['fas', 'icons']" /> Pick Icon
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>Shape</label>
          <select v-model="editedButton.shape" class="select">
            <option value="rectangle">Rectangle</option>
            <option value="rounded">Rounded</option>
            <option value="circle">Circle</option>
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
          </select>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Button, ButtonAction, ActionType } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import IconPicker from './IconPicker.vue'

interface Props {
  button: Button
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [button: Button]
  close: []
}>()

const editedButton = ref<Button>(JSON.parse(JSON.stringify(props.button)))
const showIconPicker = ref(false)

const actionType = ref<ActionType | ''>(props.button.action?.type || '')
const actionConfig = ref<Record<string, any>>(props.button.action?.config || {})
const hotkeyString = ref(props.button.action?.config?.keys?.join(', ') || '')

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

function handleSave() {
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
</style>

