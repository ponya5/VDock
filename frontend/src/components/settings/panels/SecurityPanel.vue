<template>
  <section class="panel" id="security">
    <div class="panel-head"><h2>Security &amp; pairing</h2><span class="hint">The QR code, who may connect, and the devices already signed in.</span></div>
    <div class="panel-body">
      <div v-if="serverConfig?.allow_lan && !serverConfig.require_auth" class="row row-warn" data-testid="unprotected-row">
        <div class="row-text">
          <span class="label"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /> Phone access is unprotected</span>
          <p>Right now anyone on this Wi-Fi can press your keys and answer your agents. Require pairing so only devices that scan the code can connect.</p>
        </div>
        <div class="row-control">
          <button type="button" class="btn sm primary" data-action="require-pairing" @click="requirePairing">Require pairing</button>
          <button type="button" class="btn link sm" data-action="use-password" @click="authSetupOpen = true">Use a password instead</button>
        </div>
      </div>
      <div v-if="!lanEnabled" class="row" data-testid="phone-off">
        <div class="row-text">
          <span class="label">Phone &amp; tablet access is off</span>
          <p>Turn on <b>Allow phone &amp; tablet access</b> under Network &amp; ports above to get a QR code for your phone.</p>
        </div>
      </div>
      <div v-else-if="restartRequired" class="row" data-testid="qr-waiting">
        <div class="row-text">
          <span class="label">QR code ready after restart</span>
          <p>Restart VDock (button above) and the code to scan appears here.</p>
        </div>
      </div>
      <div v-if="lanUrl && phoneLive" class="row stack qr-first" data-testid="qr-first">
        <p class="qr-headline"><b>Point your phone's camera at this code</b> — it opens the deck address in its browser. {{ CONNECT_INSTALL_STEP }}</p>
        <div class="qr-row">
          <div class="qr-code-col">
            <canvas ref="qrCanvas" class="qr-canvas" />
            <code class="kv-code kv-accent qr-url">{{ lanUrl }}</code>
            <button type="button" class="btn sm" data-action="copy-link" @click="copyLanUrl">
              <FontAwesomeIcon :icon="['fas', 'copy']" /> {{ pairing ? 'Copy pairing link' : 'Copy address' }}
            </button>
            <p v-if="pairing" class="muted qr-note" data-testid="pair-warning">This code signs a device in — don't share screenshots of it.</p>
          </div>
          <div class="qr-preview-col">
            <img
              :src="'/assets/help/mobile-preview.jpg'"
              alt="VDock open on two phones side by side: the Media scene with volume controls and a slider on one, the Claude Code scene with Submit, Continue and Interrupt on the other"
              class="qr-preview-img"
              loading="lazy"
            />
          </div>
        </div>
      </div>
      <div v-if="phoneLive" class="row stack" data-testid="devices">
        <div class="row-text">
          <span class="label">Connected devices</span>
          <p v-if="!devices.length" class="muted">No device has connected yet — scan the code above with a phone.</p>
          <p v-else>A phone is asked for a name the first time it connects. Revoke any device you don't recognise (needs authentication on to keep it out).</p>
        </div>
        <ul v-if="devices.length" class="device-list">
          <li v-for="d in devices" :key="d.id" class="device-item">
            <template v-if="editingId === d.id">
              <input v-model="editName" class="input" maxlength="40" :aria-label="`Name for ${d.label}`" @keyup.enter="saveName(d.id)" @keyup.esc="editingId = null" />
              <button type="button" class="btn sm primary" @click="saveName(d.id)">Save</button>
            </template>
            <template v-else>
              <span class="device-name">{{ d.label }}<span v-if="d.current" class="muted"> (this device)</span><span v-if="d.ip" class="muted"> · {{ d.ip }}</span></span>
              <span class="muted device-meta">first seen {{ timeAgo(d.paired_at) }} · seen {{ timeAgo(d.last_seen) }}</span>
              <button type="button" class="btn sm" :data-rename="d.id" @click="startRename(d)">Rename</button>
            </template>
            <button type="button" class="btn sm" :data-revoke="d.id" @click="revoke(d.id)">Revoke</button>
          </li>
        </ul>
        <button v-if="devices.length > 1" type="button" class="btn sm" data-action="revoke-all" @click="revokeAll">Sign out all devices</button>
      </div>
      <!-- While phone access is unprotected the warning row above is the one control. -->
      <div v-if="!(serverConfig?.allow_lan && !serverConfig.require_auth)" class="row">
        <div class="row-text">
          <span class="label">Authentication</span>
          <p>{{ serverConfig?.require_auth ? (serverConfig.pair_only ? 'On, pairing only. A device gets in by scanning the QR code above — there is no password.' : 'On. Every device unlocks with the deck password.') : 'Off. Anyone on your network who can reach the deck address can control this deck.' }}</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Require authentication</span><input type="checkbox" :checked="serverConfig?.require_auth ?? false" @change="toggleAuth" /><span class="track"></span></label>
        </div>
      </div>
      <div v-if="authSetupOpen" class="row">
        <div class="row-text">
          <span class="label">Choose a deck password</span>
          <p>Needed once per device — the panel, your phone, your browser. 4–128 characters.</p>
        </div>
        <div class="row-control">
          <DeckPasswordForm @done="authSetupOpen = false" @cancel="cancelAuthSetup" />
        </div>
      </div>
      <div v-if="serverConfig?.require_auth" class="row">
        <div class="row-text">
          <span class="label">{{ serverConfig.pair_only ? 'Use a password instead' : 'Deck password' }}</span>
          <p v-if="serverConfig.pair_only">Switches off pairing-only: devices can then also unlock by typing this password. Scanning the QR code still works.</p>
          <p v-else>{{ authChangeOpen ? 'Already-unlocked devices stay unlocked — the new password applies to the next unlock.' : 'Change the password devices use to unlock.' }}</p>
        </div>
        <div class="row-control">
          <DeckPasswordForm v-if="authChangeOpen" mode="change" @done="authChangeOpen = false" @cancel="authChangeOpen = false" />
          <button v-else type="button" class="btn sm" @click="authChangeOpen = true">
            <FontAwesomeIcon :icon="['fas', 'key']" /> {{ serverConfig.pair_only ? 'Set a password' : 'Change password' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { useDeckAuth } from '@/composables/useDeckAuth'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import DeckPasswordForm from '@/components/settings/DeckPasswordForm.vue'
import { confirmDialog } from '@/composables/useConfirm'
import { copyText } from '@/utils/copyText'
import {
  PAIR_REFRESH_MS, buildPairUrl, requestPairToken, fetchDevices, renameDevice, revokeDevice, revokeAllDevices, timeAgo,
  type PairedDevice,
} from '@/services/pairing'
import { CONNECT_INSTALL_STEP } from '@/utils/installCopy'

const { serverConfig, lanUrl } = useServerConfig()
const { setAuthEnabled } = useDeckAuth()
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()

async function requirePairing() {
  const ok = await settingsStore.updateServerConfig({ pair_only: true })
  notificationsStore[ok ? 'success' : 'error'](
    ok ? 'Pairing required' : 'Could not save',
    ok ? 'Devices now have to scan the code to connect.' : 'Try again.',
  )
  if (ok) await settingsStore.loadServerConfig()
}

// ── Authentication (DL-126) ──────────────────────────────────────────────
// require_auth writes through the same /api/config channel as the other
// toggles, but the switch is bound to serverConfig so its visual state must
// be reverted by hand whenever the change is cancelled or rejected.
// Enabling locks THIS device too: after a successful enable the lock screen
// takes over and the user unlocks once with the password they just set.
const authSetupOpen = ref(false)
const authChangeOpen = ref(false)
let authSwitchEl: HTMLInputElement | null = null

function revertAuthSwitch(enabled: boolean) {
  if (authSwitchEl) authSwitchEl.checked = !enabled
}

async function applyAuthToggle(enabled: boolean) {
  if (!(await setAuthEnabled(enabled))) revertAuthSwitch(enabled)
}

async function toggleAuth(event: Event) {
  authSwitchEl = event.target as HTMLInputElement
  const enabling = authSwitchEl.checked
  if (enabling) {
    if (!serverConfig.value?.auth_password_set) {
      // No password on file — the server rejects a bare enable anyway, so
      // collect one inline and send password + toggle in a single PUT.
      authSetupOpen.value = true
      authChangeOpen.value = false
      return
    }
    const ok = await confirmDialog({
      title: 'Require authentication?',
      message: 'This device — and every device that connects — will need the deck password.',
      confirmLabel: 'Enable',
      danger: false,
      icon: 'lock',
    })
    if (!ok) { revertAuthSwitch(true); return }
    await applyAuthToggle(true)
  } else {
    const ok = await confirmDialog({
      title: 'Turn off authentication?',
      message: 'Any device on your network will be able to control this deck without a password.',
      confirmLabel: 'Turn off',
      icon: 'lock-open',
    })
    if (!ok) { revertAuthSwitch(false); return }
    await applyAuthToggle(false)
  }
}

function cancelAuthSetup() {
  authSetupOpen.value = false
  revertAuthSwitch(true)
}

const lanEnabled = computed(() => serverConfig.value?.allow_lan ?? false)
const restartRequired = computed(() => serverConfig.value?.restart_required === true)
const phoneLive = computed(() => lanEnabled.value && !restartRequired.value)

// --- Connect a device (QR) ----------------------------------------------------
const qrCanvas = ref<HTMLCanvasElement | null>(null)

async function renderQr() {
  await nextTick()
  if (!qrCanvas.value || !qrValue.value) return
  try {
    const QRCode = (await import('qrcode')).default
    await QRCode.toCanvas(qrCanvas.value, qrValue.value, {
      width: 216,
      margin: 1,
      color: { dark: '#0d0b26', light: '#ffffff' },
    })
  } catch { /* QR is best-effort; the URL text remains */ }
}

// With a deck password the QR carries a single-use pairing token so the phone
// signs in by scanning (DL-147). The shown/copied address stays the plain URL.
const pairToken = ref<string | null>(null)
const pairing = computed(() => !!serverConfig.value?.require_auth)
const qrValue = computed(() =>
  lanUrl.value && pairing.value && pairToken.value ? buildPairUrl(lanUrl.value, pairToken.value) : lanUrl.value,
)

async function refreshPairToken() {
  pairToken.value = pairing.value ? await requestPairToken() : null
}

let pairTimer: ReturnType<typeof setInterval> | null = null
watch(pairing, (on) => {
  if (pairTimer !== null) clearInterval(pairTimer)
  pairTimer = null
  void refreshPairToken()
  if (on) pairTimer = setInterval(refreshPairToken, PAIR_REFRESH_MS)
}, { immediate: true })

watch([qrValue, () => serverConfig.value?.lan_reachable], renderQr, { immediate: false })

// Pairing deck: the copied link carries its own fresh one-time token, so it
// never competes with the QR's token (DL-154).
async function copyLanUrl() {
  if (!lanUrl.value) return
  let link = lanUrl.value
  if (pairing.value) {
    const token = await requestPairToken()
    if (token) link = buildPairUrl(lanUrl.value, token)
  }
  const ok = await copyText(link)
  const pairLink = link !== lanUrl.value
  notificationsStore[ok ? 'success' : 'info'](
    ok ? (pairLink ? 'Pairing link copied' : 'Copied') : 'Copy failed',
    pairLink ? 'Works once, for the next 3 minutes.' : lanUrl.value,
  )
}

// --- Connected devices (DL-154) -------------------------------------------------
const devices = ref<PairedDevice[]>([])
let knownDeviceIds: Set<string> | null = null

async function loadDevices() {
  const rows = await fetchDevices()
  if (!rows) return
  const fresh = knownDeviceIds ? rows.filter(d => !knownDeviceIds!.has(d.id)) : []
  knownDeviceIds = new Set(rows.map(d => d.id))
  devices.value = rows
  if (fresh.length) {
    notificationsStore.success(`${fresh[0].label} paired`, 'It can now use this deck.')
    void refreshPairToken() // the code that was just used is spent
  }
}

async function revoke(id: string) {
  const ok = await revokeDevice(id)
  notificationsStore[ok ? 'success' : 'error'](ok ? 'Device signed out' : 'Could not sign it out')
  await loadDevices()
}

async function revokeAll() {
  const ok = await revokeAllDevices()
  notificationsStore[ok ? 'success' : 'error'](ok ? 'All devices signed out' : 'Could not sign them out')
  await loadDevices()
}


const editingId = ref<string | null>(null)
const editName = ref('')
function startRename(d: PairedDevice) { editingId.value = d.id; editName.value = d.label }
async function saveName(id: string) {
  const ok = await renameDevice(id, editName.value)
  notificationsStore[ok ? 'success' : 'error'](ok ? 'Device renamed' : 'Could not rename — enter a name')
  if (ok) editingId.value = null
  await loadDevices()
}

const DEVICES_INTERVAL_MS = 5000
let devicesTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  void loadDevices()
  devicesTimer = setInterval(loadDevices, DEVICES_INTERVAL_MS)
  void settingsStore.loadServerConfig().then(renderQr)
})
onBeforeUnmount(() => {
  if (devicesTimer !== null) clearInterval(devicesTimer)
  if (pairTimer !== null) clearInterval(pairTimer)
})
</script>

<style scoped>
.kv-accent { color: #9cc0ff; }
.row-warn .label svg { color: var(--warn); }
.qr-first { margin-bottom: 8px; }
.qr-headline { margin: 0 0 12px; }
.qr-row { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.qr-code-col, .qr-preview-col { display: flex; flex-direction: column; gap: 8px; flex: none; }
.qr-canvas { width: 156px; height: 156px; border-radius: var(--r-md); background: #fff; padding: 6px; flex: none; }
.qr-url { word-break: break-all; max-width: 24ch; }
.qr-preview-col { margin-left: auto; max-width: 100%; }
.qr-preview-img { width: 380px; max-width: 100%; border-radius: var(--r-md); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35); border: 1px solid var(--line-soft); }
.qr-note { max-width: 22ch; }
.device-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; width: 100%; }
.device-item {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px;
  padding: 8px 12px; border-radius: var(--r-md);
  background: var(--panel-2); border: 1px solid var(--line-soft);
}
.device-name { font-weight: 600; }
.device-meta { flex: 1; font-size: var(--fs-sm); }
</style>
