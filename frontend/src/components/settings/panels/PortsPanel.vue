<template>
  <section class="panel" id="connection">
    <div class="panel-head"><h2>Network &amp; ports</h2><span class="hint">Let a phone or tablet reach this deck, and where it finds it. Changes here also update the code under Security.</span></div>
    <div class="panel-body">
      <div class="row" data-tour="allow-lan">
        <div class="row-text">
          <span class="label">Allow phone &amp; tablet access</span>
          <p>Off by default — without it, no other device can connect. When on, devices on your Wi-Fi can open the deck, protected by pairing or a password (see Security).</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Allow phone and tablet access</span><input type="checkbox" :checked="lanEnabled" @change="toggleAllowLan" /><span class="track"></span></label>
        </div>
      </div>
      <div v-if="restartRequired || portsPendingRestart" class="row row-warn" data-testid="restart-required">
        <div class="row-text">
          <span class="label"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /> Restart needed</span>
          <p v-if="portsPendingRestart && !restartRequired">The new ports apply after VDock restarts. This window reloads by itself.</p>
          <p v-else-if="lanEnabled">VDock is still listening only on this {{ computerNoun }}, so your phone can't connect yet. Restart VDock to turn phone access on — this window reloads by itself.</p>
          <p v-else>VDock is still reachable from your network. Restart VDock to turn phone access off — this window reloads by itself.</p>
          <p v-if="restartError" class="restart-error">{{ restartError }}</p>
        </div>
        <div class="row-control">
          <button type="button" class="btn sm primary" :disabled="restarting" @click="restart">
            <FontAwesomeIcon :icon="['fas', restarting ? 'spinner' : 'rotate-right']" :spin="restarting" />
            {{ restarting ? 'Restarting…' : 'Restart VDock now' }}
          </button>
        </div>
      </div>
      <div v-if="networkPublic && lanEnabled" class="row" data-testid="public-network-warning">
        <div class="note warn qr-offline">
          <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
          <div>{{ PUBLIC_NETWORK_TEXT }}</div>
        </div>
      </div>
      <div v-if="lanUrl && lanReachable === false" class="row">
        <div class="note warn qr-offline">
          <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
          <div>
            <b>{{ lanUrl }}</b> isn't answering on the network yet — the code under Security won't
            connect a device until it does. {{ lanDeadHint }}
          </div>
        </div>
      </div>
      <div v-if="lanEnabled" class="row">
        <div class="row-text">
          <span class="label">Deck address</span>
          <p>What the QR code under Security opens. Change the host below to use another name or network card.</p>
        </div>
        <div class="row-control">
          <code class="kv-code kv-accent">{{ lanUrl ?? 'detecting…' }}</code>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Host</span>
          <p>The address phones use to reach this {{ computerNoun }} — a hostname or IPv4, e.g. <code>deck.local</code>. Empty = auto-detect. The QR code updates as soon as you apply it.</p>
        </div>
        <div class="row-control">
          <input
            v-model="deckHostInput"
            type="text"
            class="input"
            aria-label="Host address"
            :placeholder="serverConfig?.lan_ip ? `Auto: ${serverConfig.lan_ip}` : 'Auto-detect'"
            @keyup.enter="saveDeckHost"
          />
          <button type="button" class="btn sm" :disabled="!deckHostDirty" @click="saveDeckHost">Apply</button>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Listening on</span>
          <p>{{ lanEnabled ? 'Your network (all interfaces).' : 'This computer only.' }} Set by the switch above.</p>
        </div>
        <div class="row-control">
          <code class="kv-code">{{ serverConfig?.host ?? '127.0.0.1' }}</code>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Ports</span>
          <p>Frontend is the port you open in the browser; backend is the API the frontend proxies to. Applied after a restart.</p>
        </div>
        <div class="row-control">
          <label class="sr-only" for="fp">Frontend port</label>
          <input id="fp" v-model.number="serverPorts.frontend" type="number" class="input w-110" min="1024" max="65535" placeholder="3000" />
          <span class="muted">→</span>
          <label class="sr-only" for="bp">Backend port</label>
          <input id="bp" v-model.number="serverPorts.backend" type="number" class="input w-110" min="1024" max="65535" placeholder="5000" />
          <button type="button" class="btn sm" :disabled="portsBusy" @click="checkPorts">
            <FontAwesomeIcon :icon="['fas', 'plug']" /> Check
          </button>
          <button type="button" class="btn primary sm" :disabled="portsBusy" @click="savePorts">
            <FontAwesomeIcon :icon="['fas', 'save']" /> Save ports
          </button>
        </div>
      </div>
      <div v-if="portErrors.frontend || portErrors.backend || portsStatus" class="row row-status-row">
        <div class="row-text">
          <p v-if="portErrors.frontend" class="status-msg status-error">Frontend: {{ portErrors.frontend }}</p>
          <p v-if="portErrors.backend" class="status-msg status-error">Backend: {{ portErrors.backend }}</p>
          <p v-if="portsStatus" class="status-msg" :class="portsStatus.success ? 'status-success' : 'status-error'">{{ portsStatus.message }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { useBackendRestart } from '@/composables/useBackendRestart'
import { useHostOs } from '@/composables/useHostOs'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { serverConfig, lanUrl, setAllowLan } = useServerConfig()
const lanEnabled = computed(() => serverConfig.value?.allow_lan ?? false)
// The switch was saved but the running server still has its startup bind
// (DL-007). Nothing restarts on its own: this row asks, the user decides.
const restartRequired = computed(() => serverConfig.value?.restart_required === true)
const { restarting, error: restartError, restart } = useBackendRestart()
const { hostOs } = useHostOs()
const computerNoun = computed(() => (hostOs.value === 'macos' ? 'Mac' : 'PC'))

async function toggleAllowLan(event: Event) {
  const input = event.target as HTMLInputElement
  if (!(await setAllowLan(input.checked))) input.checked = !input.checked
}

// Shared Wi-Fi: pairing codes and the deck travel unencrypted on it (DL-154).
const PUBLIC_NETWORK_TEXT =
  'Windows treats this Wi-Fi as a Public network (cafés, hotels, shared offices), where other people can see what your devices send — including pairing codes. '
  + 'If this is your home Wi-Fi, set it to "Private" in Windows (Settings › Network & internet › Wi-Fi). Otherwise leave phone access off, or connect through a VPN such as Tailscale.'
const networkPublic = computed(() => serverConfig.value?.network_profile === 'public')

// Custom deck address (deck_host): bare hostname/IPv4 the QR encodes instead
// of the auto-detected NIC. Needs no restart. Empty restores auto-detect.
const deckHostInput = ref('')
watch(() => serverConfig.value?.deck_host, v => { deckHostInput.value = v ?? '' }, { immediate: true })
const deckHostDirty = computed(() => deckHostInput.value.trim() !== (serverConfig.value?.deck_host ?? ''))

async function saveDeckHost() {
  const value = deckHostInput.value.trim()
  const ok = await settingsStore.updateServerConfig({ deck_host: value || null })
  notificationsStore[ok ? 'success' : 'error'](
    ok
      ? (value ? `Host set to ${value}` : 'Host back to auto-detect')
      : 'Could not save — use a bare hostname or IPv4 (no http://, port, or path).'
  )
}

// Whether anything actually answers on the LAN address+port the QR
// encodes. In dev that's the Vite dev server, whose bind is decided at
// ITS startup — enabling phone access afterwards leaves Vite
// loopback-only while the QR cheerfully encodes a dead URL
// (DL-069 follow-up). The backend makes the TCP connect: a fetch() from
// this page is blocked by the CSP (connect-src 'self') whenever the page
// itself is on localhost, which made the built app always say
// "isn't answering" (DL-007). Probe failure = unknown, not dead.
const lanReachable = ref<boolean | null>(null)
async function probeLanReachability() {
  if (!lanUrl.value || !lanEnabled.value) { lanReachable.value = null; return }
  const port = import.meta.env.DEV ? Number(import.meta.env.VITE_PORT) || 3000 : serverConfig.value?.port
  try {
    const response = await apiClient.get('/system/lan-probe', { port })
    lanReachable.value = response.data?.reachable === true
  } catch {
    lanReachable.value = null
  }
}
watch(lanUrl, probeLanReachability)

// What to tell the user when the QR target is dead. In dev the broken
// link is almost always the Vite dev server still bound to localhost —
// it read allow_lan once at ITS startup, so it needs its own restart,
// not just a VDock/backend relaunch. A pending backend restart has its own
// row above; past that, the firewall is the usual culprit.
const FIREWALL_HINTS: Record<string, string> = {
  macos: 'If the phone still can\u2019t open it, check System Settings \u203a Network \u203a Firewall: allow incoming connections for Python (VDock\u2019s server).',
  windows: 'If the phone still can\u2019t open it, allow Python (VDock\u2019s server) through Windows Defender Firewall on Private networks.',
}
const FIREWALL_HINTS_PACKAGED: Record<string, string> = {
  macos: 'If the phone still can\u2019t open it, check System Settings \u203a Network \u203a Firewall: allow incoming connections for VDock.',
  windows: 'If the phone still can\u2019t open it, allow VDock through Windows Defender Firewall on Private networks.',
}
const lanDeadHint = computed(() => {
  if (import.meta.env.DEV) {
    return 'Restart the dev server so it re-binds with LAN access on — stop and re-run npm run dev in frontend/ (relaunching VDock alone doesn’t restart Vite).'
  }
  if (!lanEnabled.value) return 'Turn on Allow phone & tablet access above.'
  if (restartRequired.value) return 'Restart VDock (above) to apply phone access.'
  const hints = serverConfig.value?.packaged ? FIREWALL_HINTS_PACKAGED : FIREWALL_HINTS
  return (hints[hostOs.value] ?? 'If the phone still can’t open it, check the computer’s firewall allows the port.')
    + ' Guest Wi-Fi networks often block devices from reaching each other.'
})

// Re-probe whenever the page is opened — the deck address may have come up
// (or gone down) since the last visit — and keep re-checking while it stays
// open, so the "isn't answering" warning clears by itself once the server is
// back (and appears if it drops).
const LAN_PROBE_INTERVAL_MS = 5000
let lanProbeTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  void probeLanReachability()
  lanProbeTimer = setInterval(probeLanReachability, LAN_PROBE_INTERVAL_MS)
})
onBeforeUnmount(() => {
  if (lanProbeTimer !== null) clearInterval(lanProbeTimer)
})

// Ports are written to the .env files and bind at process start — the UI
// validates and probes collisions, then offers the restart.
const serverPorts = ref({ frontend: 0, backend: 0 })
const portErrors = ref<{ frontend: string; backend: string }>({ frontend: '', backend: '' })
const portsStatus = ref<{ success: boolean; message: string } | null>(null)
const portsBusy = ref(false)
const portsPendingRestart = ref(false)

async function loadPorts() {
  try {
    const { data } = await apiClient.get('/system/ports')
    if (data.success) {
      serverPorts.value = { frontend: data.frontend_port, backend: data.backend_port }
    }
  } catch { /* informational — fields stay editable */ }
}

async function submitPorts(checkOnly: boolean) {
  portsBusy.value = true
  portErrors.value = { frontend: '', backend: '' }
  portsStatus.value = null
  try {
    const { data } = await apiClient.put('/system/ports', {
      frontend_port: serverPorts.value.frontend,
      backend_port: serverPorts.value.backend,
      check_only: checkOnly,
    })
    portsStatus.value = { success: true, message: data.message }
    if (!checkOnly) {
      portsPendingRestart.value = true
      notificationsStore.success('Ports saved', 'Restart VDock to apply them.')
    }
  } catch (err: any) {
    const errors = err?.response?.data?.errors
    if (errors) {
      portErrors.value = {
        frontend: errors.frontend_port ?? '',
        backend: errors.backend_port ?? '',
      }
      portsStatus.value = { success: false, message: 'Fix the highlighted ports and try again.' }
    } else {
      portsStatus.value = { success: false, message: err?.message || 'Could not save ports.' }
    }
  } finally {
    portsBusy.value = false
  }
}

const checkPorts = () => submitPorts(true)
const savePorts = () => submitPorts(false)

onMounted(loadPorts)
</script>

<style scoped>
.kv-accent { color: #9cc0ff; }
.row-warn .label svg { color: var(--warn); }
.restart-error { color: var(--danger, #ff6b6b); }
.note.warn {
  border-color: #4a3a18;
  background: #261e0d;
  color: #e7cd9a;
}
.note.warn svg { color: var(--warn); }
.qr-offline { margin-top: 8px; }
</style>
