<template>
  <div class="content">
    <div class="col">
      <section class="panel" id="accounts">
        <div class="panel-head"><h2>Accounts &amp; keys</h2><span class="hint">Keys are saved on this PC and never shown again.</span></div>
        <div class="panel-body">
          <div v-for="item in secrets" :key="item.id" class="row stack key-row" :data-key="item.id">
            <div class="key-top">
              <div class="row-text">
                <span class="label">{{ item.label }} <span class="status" :class="item.configured || item.builtin ? 'is-ok' : 'is-off'">{{ item.configured ? 'Set' : item.builtin ? (item.builtin_label || 'Built-in') : 'Not set' }}</span></span>
                <p>{{ item.unlocks }}</p>
              </div>
              <div v-if="editingId !== item.id" class="row-control">
                <button v-if="isLocalDevice" type="button" class="btn sm touch" data-action="set" @click="startEdit(item.id)">
                  <FontAwesomeIcon :icon="['fas', 'key']" /> {{ item.configured ? 'Replace' : item.builtin ? 'Use my own key' : 'Set key' }}
                </button>
                <a v-if="item.help_url && !item.builtin" class="btn sm touch" :href="item.help_url" target="_blank" rel="noopener">
                  <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" /> Get a key
                </a>
              </div>
            </div>
            <form v-if="editingId === item.id" class="key-edit" autocomplete="off" @submit.prevent="save(item)">
              <input
                :ref="setInputRef" v-model="draft" class="input key-input" type="password" autocomplete="off"
                autocapitalize="off" autocorrect="off" spellcheck="false" maxlength="512"
                :aria-label="`${item.label} value`" placeholder="Paste key"
              />
              <p v-if="errorText" class="key-error" role="alert">{{ errorText }}</p>
              <div class="key-actions">
                <button type="submit" class="btn sm touch btn-primary" :disabled="busy || !draft.trim()">Save</button>
                <button type="button" class="btn sm touch" :disabled="busy" @click="cancelEdit">Cancel</button>
                <button v-if="item.configured" type="button" class="btn sm touch" :disabled="busy" data-action="remove" @click="remove(item)">Remove</button>
              </div>
            </form>
          </div>
          <p v-if="!isLocalDevice" class="row env-note">Keys can only be changed from the PC VDock runs on.</p>
          <details class="row stack env-row advanced">
            <summary>Advanced</summary>
            <p>Prefer editing the file yourself? Copy a line, paste it into <code>{{ envFile || 'the .env file' }}</code>, add the key after the <code>=</code>, save, and relaunch VDock.</p>
            <div class="row-control">
              <button v-for="item in secrets" :key="item.id" type="button" class="btn sm touch" @click="copyLine(item)">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy {{ item.id }}
              </button>
              <button v-if="isLocalDevice" type="button" class="btn sm touch" @click="openEnv">
                <FontAwesomeIcon :icon="['fas', 'file-pen']" /> Open .env
              </button>
            </div>
          </details>
        </div>
      </section>

      <section class="panel" id="tools">
        <div class="panel-head"><h2>Tools on this PC</h2><span class="hint">Command-line tools some actions call.</span></div>
        <div class="panel-body">
          <div v-for="item in tools" :key="item.id" class="row" :data-key="item.id">
            <div class="row-text">
              <span class="label">{{ item.label }} <span class="status" :class="item.configured ? 'is-ok' : 'is-off'">{{ item.configured ? 'Found' : 'Not found' }}</span></span>
            </div>
            <div v-if="!item.configured && item.help_url" class="row-control">
              <a class="btn sm" :href="item.help_url" target="_blank" rel="noopener">
                <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" /> Install
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import apiClient from '@/api/client'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useNotificationsStore } from '@/stores/notifications'
import { useSetupStatus, type IntegrationItem } from '@/composables/useSetupStatus'
import { copyText } from '@/utils/copyText'

const notificationsStore = useNotificationsStore()
const { secrets, tools, envFile, refresh } = useSetupStatus()

// The backend only opens the file for requests from the PC itself.
const isLocalDevice = ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)

async function copyLine(item: IntegrationItem) {
  const ok = await copyText(`${item.id}=`)
  notificationsStore[ok ? 'success' : 'info'](ok ? 'Copied' : 'Copy failed', ok ? `Paste it into ${envFile.value || '.env'}, then add the key after the =` : '')
}

// The typed value lives only in this local ref and is wiped on save/cancel/remove.
const editingId = ref('')
const draft = ref('')
const errorText = ref('')
const busy = ref(false)
let inputEl: HTMLInputElement | null = null

function setInputRef(el: unknown) { inputEl = el as HTMLInputElement | null }

async function startEdit(id: string) {
  editingId.value = id
  draft.value = ''
  errorText.value = ''
  await nextTick()
  inputEl?.focus()
}

function cancelEdit() {
  editingId.value = ''
  draft.value = ''
  errorText.value = ''
}

async function save(item: IntegrationItem) {
  if (busy.value || !draft.value.trim()) return
  busy.value = true
  errorText.value = ''
  try {
    await apiClient.put(`/config/integrations/${item.id}`, { value: draft.value.trim() })
    cancelEdit()
    await refresh()
    notificationsStore.success('Saved', 'Active now')
  } catch (e: any) {
    errorText.value = e?.response?.data?.error || 'Could not save the key.'
  } finally {
    busy.value = false
  }
}

async function remove(item: IntegrationItem) {
  if (busy.value) return
  busy.value = true
  try {
    await apiClient.delete(`/config/integrations/${item.id}`)
    cancelEdit()
    await refresh()
    notificationsStore.success('Removed', `${item.label} cleared`)
  } catch (e: any) {
    errorText.value = e?.response?.data?.error || 'Could not remove the key.'
  } finally {
    busy.value = false
  }
}

async function openEnv() {
  try {
    await apiClient.post('/config/open-env')
  } catch {
    notificationsStore.error('Could not open', `Open ${envFile.value || 'the .env file'} yourself.`)
  }
}

onMounted(refresh)
</script>

<style scoped>
.status { margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: var(--fs-sm); font-weight: 600; border: 1px solid var(--line); color: var(--text-3); }
.status.is-ok { color: #7fd8a0; border-color: #1f5a3a; background: rgba(60, 200, 120, 0.08); }
.status.is-off { color: #f2cd8d; border-color: #5c4a1f; background: rgba(245, 181, 71, 0.09); }
.key-top { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; justify-content: space-between; width: 100%; }
.key-edit { display: flex; flex-direction: column; gap: 8px; width: 100%; min-width: 0; }
.key-row .key-input.input { height: 44px; width: 100%; max-width: 100%; min-height: 44px; box-sizing: border-box; }
.key-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.touch, .accounts-scope .btn.touch, .key-row .btn.touch, .advanced .btn.touch { min-height: 44px; min-width: 44px; }
.key-error { margin: 0; color: #f2a0a0; font-size: var(--fs-sm); }
.advanced summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; font-weight: 600; }
.advanced .row-control { display: flex; flex-wrap: wrap; gap: 8px; }
.env-note { color: var(--text-3); }
a.btn { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
.env-row code { word-break: break-all; }
</style>
