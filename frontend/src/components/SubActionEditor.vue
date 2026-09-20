<template>
  <div class="sub-action-editor">
    <div class="sub-action-row">
      <select
        class="input sub-action-type"
        :value="modelValue?.type || ''"
        @change="onTypeChange(($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Pick an action…</option>
        <option v-for="opt in TYPE_OPTIONS" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <button
        v-if="modelValue?.type"
        class="btn-icon"
        title="Clear action"
        @click="emit('update:modelValue', undefined)"
      >
        <FontAwesomeIcon :icon="['fas', 'times']" />
      </button>
    </div>

    <template v-if="modelValue?.type === 'hotkey'">
      <input
        class="input"
        type="text"
        :value="keysText"
        placeholder="ctrl, shift, t"
        @input="setConfig('keys', splitKeys(($event.target as HTMLInputElement).value))"
      />
      <p class="field-hint">Comma-separated keys, e.g. <code>ctrl, c</code></p>
    </template>

    <template v-else-if="modelValue?.type === 'cross_platform'">
      <select
        class="input"
        :value="modelValue.config?.action || ''"
        @change="setConfig('action', ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>System action…</option>
        <option v-for="a in CROSS_PLATFORM_ACTIONS" :key="a.value" :value="a.value">
          {{ a.label }}
        </option>
      </select>
    </template>

    <template v-else-if="modelValue?.type === 'url'">
      <input
        class="input"
        type="url"
        :value="modelValue.config?.url || ''"
        placeholder="https://…"
        @input="setConfig('url', ($event.target as HTMLInputElement).value)"
      />
    </template>

    <template v-else-if="modelValue?.type === 'command'">
      <input
        class="input"
        type="text"
        :value="modelValue.config?.command || ''"
        placeholder="shell command"
        @input="setConfig('command', ($event.target as HTMLInputElement).value)"
      />
    </template>

    <template v-else-if="modelValue?.type === 'program'">
      <input
        class="input"
        type="text"
        :value="modelValue.config?.path || ''"
        placeholder="C:\path\to\app.exe"
        @input="setConfig('path', ($event.target as HTMLInputElement).value)"
      />
    </template>

    <template v-else-if="modelValue?.type === 'http_request'">
      <div class="sub-action-row">
        <select
          class="input method-select"
          :value="modelValue.config?.method || 'GET'"
          @change="setConfig('method', ($event.target as HTMLSelectElement).value)"
        >
          <option>GET</option><option>POST</option>
          <option>PUT</option><option>DELETE</option>
        </select>
        <input
          class="input"
          type="url"
          :value="modelValue.config?.url || ''"
          placeholder="https://hook.local/…"
          @input="setConfig('url', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </template>

    <template v-else-if="modelValue?.type === 'ui_control'">
      <select
        class="input"
        :value="modelValue.config?.action || ''"
        @change="setConfig('action', ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>VDock UI action…</option>
        <option value="toggle_header">Toggle header</option>
        <option value="ui_brightness_up">UI brighter</option>
        <option value="ui_brightness_down">UI dimmer</option>
      </select>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * A nested action inside a multi_action step, a toggle side, or a release
 * action — one type select + the one or two fields that type needs. Deliberately
 * a curated subset: the full catalog belongs on the button itself; nested
 * actions are the "glue" actions (keys, URLs, system toggles, HTTP).
 */
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { ActionType } from '@/types'

interface SubAction {
  type: ActionType | string
  config: Record<string, any>
}

const props = defineProps<{
  modelValue?: SubAction
}>()

const emit = defineEmits<{
  'update:modelValue': [value: SubAction | undefined]
}>()

const TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'hotkey', label: 'Hotkey' },
  { value: 'cross_platform', label: 'System Action' },
  { value: 'url', label: 'Open URL' },
  { value: 'command', label: 'Run Command' },
  { value: 'program', label: 'Launch Program' },
  { value: 'http_request', label: 'HTTP Request' },
  { value: 'ui_control', label: 'VDock UI' },
]

const CROSS_PLATFORM_ACTIONS = [
  { value: 'volume_up', label: 'Volume up' },
  { value: 'volume_down', label: 'Volume down' },
  { value: 'volume_mute', label: 'Mute' },
  { value: 'volume_unmute', label: 'Unmute' },
  { value: 'microphone_mute', label: 'Mic mute' },
  { value: 'microphone_unmute', label: 'Mic unmute' },
  { value: 'brightness_up', label: 'Brightness up' },
  { value: 'brightness_down', label: 'Brightness down' },
  { value: 'media_play_pause', label: 'Play / pause' },
  { value: 'media_next', label: 'Next track' },
  { value: 'media_previous', label: 'Previous track' },
  { value: 'media_stop', label: 'Stop' },
  { value: 'lock_screen', label: 'Lock screen' },
  { value: 'screenshot', label: 'Screenshot' },
  { value: 'sleep', label: 'Sleep' },
]

const keysText = computed(() =>
  (props.modelValue?.config?.keys ?? []).join(', ')
)

function splitKeys(text: string): string[] {
  return text.split(',').map((k) => k.trim().toLowerCase()).filter(Boolean)
}

function onTypeChange(type: string) {
  emit('update:modelValue', type ? { type: type as ActionType, config: {} } : undefined)
}

function setConfig(key: string, value: any) {
  if (!props.modelValue) return
  emit('update:modelValue', {
    ...props.modelValue,
    config: { ...props.modelValue.config, [key]: value },
  })
}
</script>

<style scoped>
.sub-action-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  flex: 1;
}
.sub-action-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.sub-action-type {
  flex: 1;
  min-width: 0;
}
.method-select {
  max-width: 110px;
}
.field-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #9aa0b4);
}
.field-hint code {
  color: var(--color-primary, #5b8cff);
}
.btn-icon {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.14));
  border-radius: 10px;
  color: var(--color-text-muted, #9aa0b4);
  cursor: pointer;
}
.btn-icon:hover {
  color: var(--color-text, #fff);
  border-color: var(--color-primary, #5b8cff);
}
</style>
