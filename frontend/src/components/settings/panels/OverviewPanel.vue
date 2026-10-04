<template>
  <div class="content">
    <div class="col">
      <section class="panel" id="attention">
        <div class="panel-head"><h2>Needs attention</h2></div>
        <div class="panel-body">
          <div v-if="loaded && !attention.length" class="row all-set">
            <div class="row-text">
              <span class="label"><FontAwesomeIcon :icon="['fas', 'circle-check']" /> Everything is set up</span>
              <p>Nothing needs you right now.</p>
            </div>
          </div>
          <button
            v-for="item in attention"
            :key="item.id"
            type="button"
            class="attention-row"
            @click="emit('navigate', item.target)"
          >
            <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" class="attention-icon" />
            <span class="attention-text"><b>{{ item.title }}</b><span>{{ item.detail }}</span></span>
            <span class="attention-go">{{ item.action }} <FontAwesomeIcon :icon="['fas', 'arrow-right']" /></span>
          </button>
        </div>
      </section>

      <section class="panel" id="quick-switches">
        <div class="panel-head"><h2>Quick switches</h2></div>
        <div class="panel-body">
          <div class="row">
            <div class="row-text"><span class="label">Auto scene switching</span><p>Scenes follow the app in focus.</p></div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Auto scene switching</span><input type="checkbox" :checked="autoScenes" @change="setAutoSceneSwitching(($event.target as HTMLInputElement).checked)" /><span class="track"></span></label>
            </div>
          </div>
          <div class="row">
            <div class="row-text"><span class="label">Agent alerts</span><p>A banner when an agent waits for you.</p></div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Agent alerts</span><input type="checkbox" v-model="settingsStore.agentAlertsEnabled" /><span class="track"></span></label>
            </div>
          </div>
          <div class="row">
            <div class="row-text"><span class="label">Allow LAN access</span><p>Lets a phone or tablet open the deck. Applies on relaunch.</p></div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Allow LAN access</span><input type="checkbox" :checked="serverConfig?.allow_lan ?? false" @change="toggleLan" /><span class="track"></span></label>
            </div>
          </div>
          <div class="row">
            <div class="row-text"><span class="label">Screen saver</span><p>Shows widgets when the deck sits idle.</p></div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Screen saver</span><input type="checkbox" :checked="settingsStore.screensaverTimeout > 0" @change="toggleScreensaver" /><span class="track"></span></label>
            </div>
          </div>
        </div>
      </section>

      <section v-if="!isCompactTouch" class="panel" id="edit-keys">
        <div class="panel-body">
          <div class="row">
            <div class="row-text"><span class="label">Edit what a key does</span><p>Opens the dashboard in edit mode.</p></div>
            <div class="row-control">
              <RouterLink :to="{ path: '/', query: { edit: '1' } }" class="btn sm">
                <FontAwesomeIcon :icon="['fas', 'pen-to-square']" /> Edit keys
              </RouterLink>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useServerConfig } from '@/composables/useServerConfig'
import { useSetupStatus } from '@/composables/useSetupStatus'
import { useAutoSceneSwitching, setAutoSceneSwitching } from '@/composables/useAppIntegrations'
import { useDeviceClass } from '@/composables/useDeviceClass'
import type { SettingsRoute } from '@/settings/registry'

const emit = defineEmits<{ navigate: [target: SettingsRoute] }>()

const settingsStore = useSettingsStore()
const { serverConfig, setAllowLan } = useServerConfig()
const { githubTokenMissing, loaded, refresh } = useSetupStatus()
const { isCompactTouch } = useDeviceClass()
const autoScenes = useAutoSceneSwitching()

interface AttentionItem { id: string; title: string; detail: string; action: string; target: SettingsRoute }

const attention = computed<AttentionItem[]>(() => {
  const items: AttentionItem[] = []
  if (serverConfig.value?.allow_lan && !serverConfig.value.require_auth) {
    items.push({
      id: 'lan-open',
      title: 'Anyone on your Wi-Fi can press your keys',
      detail: 'LAN access is on without a deck password.',
      action: 'Set a password',
      target: { section: 'devices', page: 'connect' },
    })
  }
  if (githubTokenMissing.value) {
    items.push({
      id: 'github-token',
      title: 'GitHub token not set',
      detail: 'Live PR and CI buttons are off.',
      action: 'Add it',
      target: { section: 'integrations', page: 'accounts', anchor: 'accounts' },
    })
  }
  return items
})

async function toggleLan(event: Event) {
  const input = event.target as HTMLInputElement
  if (!(await setAllowLan(input.checked))) input.checked = !input.checked
}

function toggleScreensaver(event: Event) {
  const on = (event.target as HTMLInputElement).checked
  settingsStore.screensaverTimeout = on ? SETTINGS_DEFAULTS.screensaverTimeout : 0
}

onMounted(refresh)
</script>

<style scoped>
.all-set .label svg { color: #7fd8a0; }
.attention-row {
  display: flex; align-items: center; gap: 12px; width: 100%; min-height: 56px;
  padding: 10px 14px; text-align: left; cursor: pointer;
  background: #261e0d; border: 1px solid #4a3a18; border-radius: var(--r-md); color: #e7cd9a;
  font: inherit;
}
.attention-row + .attention-row { margin-top: 8px; }
.attention-icon { color: var(--warn); flex: none; }
.attention-text { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; font-size: var(--fs-sm); }
.attention-text b { color: var(--text); font-size: var(--fs-base, 1em); }
.attention-go { flex: none; font-weight: 600; color: #f2cd8d; white-space: nowrap; }
a.btn { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
@media (max-width: 480px) {
  .attention-row { flex-wrap: wrap; }
  .attention-go { margin-left: 28px; }
}
</style>
