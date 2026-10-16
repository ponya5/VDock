<template>
  <div class="content">
    <div class="col">
      <section class="panel">
        <div class="panel-head"><h2>Connect a device</h2><span class="hint">Any phone or tablet on your Wi-Fi can be a second deck — no app to install.</span></div>
        <div class="panel-body">
          <!-- DL-008: one step from "I want my phone" to the QR - save LAN access
               (+ the recommended password), restart, land back here on the code. -->
          <div v-if="!lanEnabled" class="phone-setup" data-testid="phone-setup" data-tour="allow-lan">
            <div class="phone-setup-head">
              <FontAwesomeIcon :icon="['fas', 'mobile-screen-button']" class="phone-setup-icon" />
              <div>
                <b>Use VDock on your phone or tablet</b>
                <p>Phone access is off, so nothing else on your Wi-Fi can reach your deck. Turn it on and VDock restarts once — then scan the code that appears here.</p>
              </div>
            </div>
            <div v-if="!passwordSet && !skipPassword" class="phone-setup-pw">
              <label class="sr-only" for="phone-setup-pw">Deck password</label>
              <input id="phone-setup-pw" v-model="setupPassword" type="password" class="input" placeholder="Deck password" autocomplete="new-password" />
              <label class="sr-only" for="phone-setup-pw2">Confirm password</label>
              <input id="phone-setup-pw2" v-model="setupConfirm" type="password" class="input" placeholder="Confirm" autocomplete="new-password" @keyup.enter="enablePhoneAccess" />
              <p class="muted phone-setup-hint">Recommended: devices on your Wi-Fi enter it once (or sign in by scanning the code). This {{ computerNoun }} never needs it.</p>
            </div>
            <p v-if="setupError" class="status-msg status-error">{{ setupError }}</p>
            <div class="phone-setup-actions">
              <button type="button" class="btn primary" :disabled="restarting" data-action="enable-phone-access" @click="enablePhoneAccess">
                <FontAwesomeIcon :icon="['fas', restarting ? 'spinner' : 'power-off']" :spin="restarting" />
                {{ restarting ? 'Restarting VDock…' : 'Turn on phone access' }}
              </button>
              <button v-if="!passwordSet && !skipPassword" type="button" class="btn link sm" @click="skipPassword = true">Continue without a password</button>
              <span v-else-if="skipPassword" class="muted phone-setup-hint">No password: anyone on this Wi-Fi can press your keys. <button type="button" class="btn link sm" @click="skipPassword = false">Add one</button></span>
            </div>
          </div>
          <!-- DL-011: once phone access is live the code comes first - it is
               the one thing this card is for. -->
          <div v-if="lanUrl && phoneLive" class="row stack qr-first" data-testid="qr-first">
            <p class="qr-headline"><b>Point your phone's camera at this code</b> — VDock opens in its browser. {{ CONNECT_INSTALL_STEP }}</p>
            <div class="qr-row">
              <div class="qr-code-col">
                <canvas ref="qrCanvas" class="qr-canvas" />
                <p class="muted qr-note">Same Wi-Fi as this {{ computerNoun }}. The code opens the deck address below.</p>
                <p v-if="pairing" class="muted qr-note" data-testid="pair-warning">This code signs a device in — don't share screenshots of it.</p>
              </div>
              <div class="qr-preview-col">
                <img
                  :src="'/assets/help/mobile-preview.jpg'"
                  alt="VDock open on two phones side by side: the Media scene with volume controls and a slider on one, the Claude Code scene with Submit, Continue and Interrupt on the other"
                  class="qr-preview-img"
                  loading="lazy"
                />
                <p class="muted qr-note">This is what it looks like once it's open on the phone.</p>
              </div>
            </div>
          </div>
          <div v-else-if="lanEnabled && !restartRequired" class="row">
            <div class="note warn qr-offline">
              <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
              <div>
                LAN address unavailable. Enable <b>Allow LAN access</b> and restart VDock —
                until then VDock only listens on this {{ computerNoun }}.
              </div>
            </div>
          </div>
          <div class="row" data-tour="allow-lan">
            <div class="row-text">
              <span class="label">Allow LAN access</span>
              <p>Off by default. Turn it on to use VDock on a phone or tablet — without it, no other device can connect. Applies after a restart.</p>
            </div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Allow LAN access</span><input type="checkbox" :checked="serverConfig?.allow_lan ?? false" @change="toggleAllowLan" /><span class="track"></span></label>
            </div>
          </div>
          <div v-if="restartRequired" class="row row-warn" data-testid="restart-required">
            <div class="row-text">
              <span class="label"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /> Restart needed</span>
              <p v-if="lanEnabled">VDock is still listening only on this {{ computerNoun }}, so your phone can't connect yet. Restart it to apply <b>Allow LAN access</b> — this window reloads by itself.</p>
              <p v-else>VDock is still reachable from your network. Restart it to apply the change — this window reloads by itself.</p>
              <p v-if="restartError" class="restart-error">{{ restartError }}</p>
            </div>
            <div class="row-control">
              <button type="button" class="btn sm primary" :disabled="restarting" @click="restart">
                <FontAwesomeIcon :icon="['fas', restarting ? 'spinner' : 'rotate-right']" :spin="restarting" />
                {{ restarting ? 'Restarting…' : 'Restart VDock now' }}
              </button>
            </div>
          </div>
          <div v-if="serverConfig?.allow_lan && !serverConfig.require_auth" class="row row-warn">
            <div class="row-text">
              <span class="label"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /> Protect it with a password</span>
              <p>Without one, anyone on this Wi-Fi can press your keys and answer your agents. Each device enters it once.</p>
            </div>
            <div class="row-control">
              <DeckPasswordForm :cancellable="false" />
            </div>
          </div>
          <div class="row" v-if="lanUrl">
            <div class="row-text">
              <span class="label">Deck address</span>
              <p>Scan the code on the device, or type the address into its browser.</p>
            </div>
            <div class="row-control">
              <code class="kv-code kv-accent">{{ lanUrl }}</code>
              <button type="button" class="btn sm" @click="copyLanUrl">
                <FontAwesomeIcon :icon="['fas', 'copy']" /> Copy
              </button>
            </div>
          </div>
          <div class="row" v-if="lanUrl">
            <div class="row-text">
              <span class="label">Custom address</span>
              <p>Hostname or IPv4 for the code above — e.g. <code>deck.local</code>. Handy with multiple network cards, or when the auto-detected one is wrong. Leave empty for auto.</p>
            </div>
            <div class="row-control">
              <input
                v-model="deckHostInput"
                type="text"
                class="input"
                :placeholder="serverConfig?.lan_ip ? `Auto: ${serverConfig.lan_ip}` : 'Auto-detect'"
                @keyup.enter="saveDeckHost"
              />
              <button type="button" class="btn sm" :disabled="!deckHostDirty" @click="saveDeckHost">
                Apply
              </button>
            </div>
          </div>
          <div v-if="lanUrl && lanReachable === false" class="row">
            <div class="note warn qr-offline">
              <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
              <div>
                <b>{{ lanUrl }}</b> isn't answering on the network yet — the code below won't
                connect a device until it does. {{ lanDeadHint }}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { copyText } from '@/utils/copyText'
import DeckPasswordForm from '@/components/settings/DeckPasswordForm.vue'
import { PAIR_REFRESH_MS, buildPairUrl, requestPairToken } from '@/services/pairing'
import { CONNECT_INSTALL_STEP } from '@/utils/installCopy'
import { useBackendRestart } from '@/composables/useBackendRestart'
import { useHostOs } from '@/composables/useHostOs'
import apiClient from '@/api/client'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { serverConfig, lanUrl, setAllowLan } = useServerConfig()
const lanEnabled = computed(() => serverConfig.value?.allow_lan ?? false)
// The switch was saved but the running server still has its startup bind
// (DL-007) — "relaunching" used to reuse that server, so offer the restart here.
const restartRequired = computed(() => serverConfig.value?.restart_required === true)
const phoneLive = computed(() => lanEnabled.value && !restartRequired.value)
const { restarting, error: restartError, restart } = useBackendRestart()
const passwordSet = computed(() => !!serverConfig.value?.auth_password_set && !!serverConfig.value?.require_auth)

// --- One-step phone setup (DL-008) --------------------------------------------
const setupPassword = ref('')
const setupConfirm = ref('')
const skipPassword = ref(false)
const setupError = ref('')

async function enablePhoneAccess() {
  setupError.value = ''
  const changes: Record<string, unknown> = { allow_lan: true }
  if (!passwordSet.value && !skipPassword.value) {
    const pw = setupPassword.value.trim()
    if (pw.length < 4 || pw.length > 128) {
      setupError.value = 'Choose a password of 4–128 characters, or continue without one.'
      return
    }
    if (pw !== setupConfirm.value.trim()) {
      setupError.value = "Passwords don't match."
      return
    }
    changes.require_auth = true
    changes.auth_password = pw
  }
  if (!(await settingsStore.updateServerConfig(changes))) {
    setupError.value = 'VDock could not save this — try again.'
    return
  }
  setupPassword.value = ''
  setupConfirm.value = ''
  // Applies the new bind; the page reloads on this card with the QR showing.
  await restart()
  if (restartError.value) setupError.value = restartError.value
}
const { hostOs } = useHostOs()
const computerNoun = computed(() => (hostOs.value === 'macos' ? 'Mac' : 'PC'))

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

// Whether anything actually answers on the LAN address+port the QR
// encodes. In dev that's the Vite dev server, whose bind is decided at
// ITS startup — enabling "Allow LAN access" afterwards leaves Vite
// loopback-only while the card cheerfully prints a QR for a dead URL
// (DL-069 follow-up). The backend makes the TCP connect: a fetch() from
// this page is blocked by the CSP (connect-src 'self') whenever the page
// itself is on localhost, which made the built app always say
// "isn't answering" (DL-007). Probe failure = unknown, not dead.
const lanReachable = ref<boolean | null>(null)
async function probeLanReachability() {
  if (!lanUrl.value) { lanReachable.value = null; return }
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
    return 'Restart the dev server so it re-binds with LAN access on — stop and re-run npm run dev in frontend/ (relaunching VDock alone doesn\u2019t restart Vite).'
  }
  if (!lanEnabled.value) return 'Turn on Allow LAN access above.'
  if (restartRequired.value) return 'Restart VDock (above) to apply Allow LAN access.'
  const hints = serverConfig.value?.packaged ? FIREWALL_HINTS_PACKAGED : FIREWALL_HINTS
  return (hints[hostOs.value] ?? 'If the phone still can\u2019t open it, check the computer\u2019s firewall allows the port.')
    + ' Guest Wi-Fi networks often block devices from reaching each other.'
})

async function toggleAllowLan(event: Event) {
  await setAllowLan((event.target as HTMLInputElement).checked)
  await nextTick()
  renderQr()
}

// Custom deck address (deck_host): bare hostname/IPv4 shown in the QR
// card instead of the auto-detected NIC. Empty restores auto-detect.
const deckHostInput = ref('')
watch(() => serverConfig.value?.deck_host, v => { deckHostInput.value = v ?? '' }, { immediate: true })
const deckHostDirty = computed(() => deckHostInput.value.trim() !== (serverConfig.value?.deck_host ?? ''))

async function saveDeckHost() {
  const value = deckHostInput.value.trim()
  const ok = await settingsStore.updateServerConfig({ deck_host: value || null })
  notificationsStore[ok ? 'success' : 'error'](
    ok
      ? (value ? `Deck address set to ${value}` : 'Deck address back to auto-detect')
      : 'Could not save — use a bare hostname or IPv4 (no http://, port, or path).'
  )
  if (ok) { await nextTick(); renderQr() }
}

async function copyLanUrl() {
  if (!lanUrl.value) return
  const ok = await copyText(lanUrl.value)
  notificationsStore[ok ? 'success' : 'info'](ok ? 'Copied' : 'Copy failed', lanUrl.value)
}

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
  if (pairTimer !== null) clearInterval(pairTimer)
})

// DL-057: present the QR immediately — refresh the LAN URL, then draw.
onMounted(() => { void settingsStore.loadServerConfig().then(renderQr) })
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
.qr-first { margin-bottom: 8px; }
.qr-headline { margin: 0 0 12px; }
.phone-setup {
  display: flex; flex-direction: column; gap: 12px;
  padding: 16px; margin-bottom: 12px; border-radius: 12px;
  background: color-mix(in srgb, var(--accent, #4c8dff) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent, #4c8dff) 40%, transparent);
}
.phone-setup-head { display: flex; gap: 12px; align-items: flex-start; }
.phone-setup-head p { margin: 4px 0 0; }
.phone-setup-icon { font-size: 1.6em; color: var(--accent, #4c8dff); margin-top: 2px; }
.phone-setup-pw { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.phone-setup-pw .input { width: 180px; max-width: 100%; }
.phone-setup-hint { flex-basis: 100%; margin: 0; font-size: var(--fs-sm); }
.phone-setup-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.connect-steps {
  margin: 0 0 6px;
  padding: 12px 14px 12px 30px;
  display: grid;
  gap: 8px;
  background: var(--panel-2);
  border: 1px solid var(--line-soft);
  border-radius: var(--r-md);
  color: var(--text-2);
  font-size: var(--fs-sm);
}
.connect-steps b { color: var(--text); }
.qr-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}
.qr-code-col,
.qr-preview-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: none;
}
.qr-canvas {
  width: 156px;
  height: 156px;
  border-radius: var(--r-md);
  background: #fff;
  padding: 6px;
  flex: none;
}
.qr-preview-col { margin-left: auto; max-width: 100%; }
.qr-preview-img {
  width: 380px;
  max-width: 100%;
  border-radius: var(--r-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  border: 1px solid var(--line-soft);
}
.qr-note { max-width: 22ch; }
.qr-offline { margin-top: 8px; }
</style>
