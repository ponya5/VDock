<template>
  <div class="row stack" data-testid="connection-check">
    <div class="row-text">
      <span class="label">Why can't my phone connect?</span>
      <p>Checks the address in the QR, phone access and the firewall, and offers a one-click fix.</p>
    </div>
    <div class="row-control">
      <button type="button" class="btn sm" data-action="run-check" :disabled="running" @click="run">
        <FontAwesomeIcon :icon="['fas', running ? 'spinner' : 'stethoscope']" :spin="running" /> {{ checks ? 'Check again' : 'Check connection' }}
      </button>
    </div>
    <p v-if="failed" class="muted" data-testid="check-error">Could not run the check — is VDock still running?</p>
    <ul v-if="checks" class="check-list">
      <li v-for="c in checks" :key="c.id" class="check-item" :class="`is-${c.status}`" :data-check="c.id">
        <FontAwesomeIcon :icon="['fas', ICONS[c.status]]" class="check-icon" />
        <div class="check-text">
          <b>{{ c.title }}</b>
          <span class="muted">{{ c.detail }}</span>
        </div>
        <button v-if="c.fix" type="button" class="btn sm primary" :data-fix="c.fix.action" :disabled="running" @click="applyFix(c.fix)">{{ c.fix.label }}</button>
      </li>
    </ul>
    <p v-if="checks" class="muted check-foot">
      All green and the phone still shows nothing? Guest Wi-Fi and some office networks block phone-to-computer traffic ("client isolation"); VDock can't detect that.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { fetchConnectionCheck, fixPayload, type ConnectionCheckItem } from '@/services/connectionCheck'

const ICONS = { ok: 'circle-check', warn: 'triangle-exclamation', fail: 'circle-xmark', info: 'circle-info' } as const

const settings = useSettingsStore()
const notifications = useNotificationsStore()
const checks = ref<ConnectionCheckItem[] | null>(null)
const running = ref(false)
const failed = ref(false)

async function run() {
  running.value = true
  const result = await fetchConnectionCheck()
  failed.value = result === null
  if (result) checks.value = result
  running.value = false
}

async function applyFix(fix: NonNullable<ConnectionCheckItem['fix']>) {
  running.value = true
  const ok = await settings.updateServerConfig(fixPayload(fix))
  if (ok) await settings.loadServerConfig()
  notifications[ok ? 'success' : 'error'](
    ok ? 'Address updated' : 'Could not save',
    ok ? 'The QR code now uses the new address — scan it again.' : 'Try again.',
  )
  running.value = false
  if (ok) await run()
}
</script>

<style scoped>
.check-list { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.check-item { display: flex; align-items: flex-start; gap: 10px; padding: 8px 10px; border-radius: 10px; background: rgba(255, 255, 255, 0.04); }
.check-text { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.check-icon { margin-top: 3px; }
.is-ok .check-icon { color: #2ecc71; }
.is-warn .check-icon { color: #f5a524; }
.is-fail .check-icon { color: #ff5a5f; }
.is-info .check-icon { opacity: 0.7; }
.check-foot { margin-top: 6px; font-size: 0.85em; }
</style>
