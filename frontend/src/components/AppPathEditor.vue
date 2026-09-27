<script setup lang="ts">
/**
 * Compact editor for one app's executable override (DL-084). Rendered as an
 * inline panel — from a template card's gear, or standalone in the "App
 * launch paths" settings row. The path persists via /api/config app_paths.
 */
import { computed, ref } from 'vue'
import { appPaths, saveAppPaths, probeAppPath } from '@/api/appPaths'
import { useElectron } from '@/composables/useElectron'
import { useNotificationsStore } from '@/stores/notifications'

const props = defineProps<{
  /** Key into app_paths (e.g. 'cursor', 'vscode', 'claude'). */
  appKey: string
  /** Human label for the field, e.g. 'Cursor'. */
  label: string
}>()

const emit = defineEmits<{ (e: 'close'): void }>()

const { isElectron, pickExecutable } = useElectron()
const notifications = useNotificationsStore()

const input = ref(appPaths[props.appKey] ?? '')
const saving = ref(false)
const probing = ref(false)
const browsing = ref(false)
const error = ref('')

const current = computed(() => appPaths[props.appKey] ?? '')
const dirty = computed(() => input.value.trim() !== current.value)

async function save() {
  if (saving.value) return
  saving.value = true
  error.value = ''
  try {
    await saveAppPaths({ ...appPaths, [props.appKey]: input.value.trim() })
    emit('close')
  } catch (e: any) {
    error.value = e?.response?.data?.error || 'Could not save the path'
  } finally {
    saving.value = false
  }
}

async function clear() {
  input.value = ''
  await save()
}

async function browse() {
  browsing.value = true
  try {
    const picked = await pickExecutable()
    if (picked) input.value = picked
  } finally {
    browsing.value = false
  }
}

async function detect() {
  probing.value = true
  error.value = ''
  try {
    const found = await probeAppPath(props.appKey)
    if (found) {
      input.value = found
    } else {
      error.value = `Couldn't locate ${props.label} — browse or paste the path`
    }
  } catch {
    error.value = 'Detect failed — enter the path manually'
  } finally {
    probing.value = false
  }
}
</script>

<template>
  <div class="app-path-editor" @click.stop>
    <label class="ape-label" :for="`ape-${appKey}`">{{ label }} executable</label>
    <div class="ape-row">
      <input
        :id="`ape-${appKey}`"
        v-model="input"
        class="input ape-input"
        type="text"
        spellcheck="false"
        placeholder="e.g. C:\Users\you\AppData\Local\Programs\cursor\Cursor.exe"
        @keydown.enter="save"
      />
      <button
        v-if="isElectron()"
        type="button"
        class="btn btn-secondary ape-btn"
        :disabled="browsing"
        @click="browse"
      >
        {{ browsing ? '…' : 'Browse' }}
      </button>
      <button
        type="button"
        class="btn btn-secondary ape-btn"
        :disabled="probing"
        title="Search PATH and the usual install folders"
        @click="detect"
      >
        {{ probing ? '…' : 'Detect' }}
      </button>
    </div>
    <p v-if="error" class="ape-error">{{ error }}</p>
    <div class="ape-actions">
      <button
        v-if="current"
        type="button"
        class="btn btn-secondary ape-btn ape-clear"
        @click="clear"
      >
        Reset to auto
      </button>
      <span class="ape-spacer" />
      <button
        type="button"
        class="btn btn-primary ape-btn"
        :disabled="saving || !dirty"
        @click="save"
      >
        {{ saving ? 'Saving…' : 'Save' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.app-path-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ape-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--vdock-text-secondary, rgba(255, 255, 255, 0.6));
}

.ape-row {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.ape-input {
  flex: 1;
  min-width: 0;
  font-size: 0.8rem;
  font-family: ui-monospace, monospace;
}

.ape-btn {
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  white-space: nowrap;
}

.ape-error {
  margin: 0;
  font-size: 0.72rem;
  color: #f87171;
}

.ape-actions {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.ape-clear {
  color: var(--vdock-text-secondary, rgba(255, 255, 255, 0.6));
}

.ape-spacer {
  flex: 1;
}
</style>
