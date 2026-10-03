<template>
  <div class="content">
    <div class="col">
      <section class="panel" id="accounts">
        <div class="panel-head"><h2>Accounts &amp; keys</h2><span class="hint">What VDock can reach. Keys are never shown here.</span></div>
        <div class="panel-body">
          <div v-for="item in secrets" :key="item.id" class="row" :data-key="item.id">
            <div class="row-text">
              <span class="label">{{ item.label }} <span class="status" :class="item.configured ? 'is-ok' : 'is-off'">{{ item.configured ? 'Configured' : 'Not set' }}</span></span>
              <p>{{ item.unlocks }}</p>
            </div>
            <div v-if="!item.configured" class="row-control">
              <button type="button" class="btn sm" @click="copyLine(item)">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy line
              </button>
              <a v-if="item.help_url" class="btn sm" :href="item.help_url" target="_blank" rel="noopener">
                <FontAwesomeIcon :icon="['fas', 'up-right-from-square']" /> Get a key
              </a>
            </div>
          </div>
          <div class="row stack env-row">
            <div class="row-text">
              <span class="label">Where keys go</span>
              <p>Paste the copied line into <code>{{ envFile || 'the .env file' }}</code>, save, and relaunch VDock. Keys stay in that file — they are never displayed or sent to other devices.</p>
            </div>
            <div v-if="isLocalDevice" class="row-control">
              <button type="button" class="btn sm" @click="openEnv">
                <FontAwesomeIcon :icon="['fas', 'file-pen']" /> Open .env
              </button>
            </div>
          </div>
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
import { onMounted } from 'vue'
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
a.btn { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
.env-row code { word-break: break-all; }
</style>
