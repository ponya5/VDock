<template>
  <div class="content">
    <div class="col">
      <section class="panel">
        <div class="panel-head"><h2>Connect a device</h2><span class="hint">Any phone or tablet on your Wi-Fi can be a second deck — no app to install.</span></div>
        <div class="panel-body">
          <ol class="connect-steps">
            <li><b>Same Wi-Fi.</b> Connect the phone or tablet to the same network as this PC.</li>
            <li><b>Allow LAN access.</b> Turn it on below and relaunch VDock once — this makes the deck reachable on your network.</li>
            <li><b>Scan the code.</b> Point the device camera at the QR, or type the deck address into its browser.</li>
          </ol>
          <div class="row">
            <div class="row-text">
              <span class="label">Allow LAN access</span>
              <p>Binds the server to your network so other devices can reach it. Applies on the next launch.</p>
            </div>
            <div class="row-control">
              <label class="switch"><span class="sr-only">Allow LAN access</span><input type="checkbox" :checked="serverConfig?.allow_lan ?? false" @change="toggleAllowLan" /><span class="track"></span></label>
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
                If it still won't load after that, check the PC's firewall allows the port.
              </div>
            </div>
          </div>
          <div v-if="lanUrl" class="row stack">
            <div class="qr-row">
              <div class="qr-code-col">
                <canvas ref="qrCanvas" class="qr-canvas" />
                <p class="muted qr-note">The code encodes the address above. It changes when the backend port or your LAN address changes.</p>
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
          <div v-else class="row">
            <div class="note warn qr-offline">
              <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
              <div>
                LAN address unavailable. Enable <b>Allow LAN access</b> and relaunch —
                until then VDock only listens on this PC.
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

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { serverConfig, lanUrl, setAllowLan } = useServerConfig()

// --- Connect a device (QR) ----------------------------------------------------
const qrCanvas = ref<HTMLCanvasElement | null>(null)

async function renderQr() {
  await nextTick()
  if (!qrCanvas.value || !lanUrl.value) return
  try {
    const QRCode = (await import('qrcode')).default
    await QRCode.toCanvas(qrCanvas.value, lanUrl.value, {
      width: 180,
      margin: 1,
      color: { dark: '#0d0b26', light: '#ffffff' },
    })
  } catch { /* QR is best-effort; the URL text remains */ }
}

watch([lanUrl, () => serverConfig.value?.lan_reachable], renderQr, { immediate: false })

// Whether anything actually answers on the LAN address+port the QR
// encodes. In dev that's the Vite dev server, whose bind is decided at
// ITS startup — enabling "Allow LAN access" afterwards leaves Vite
// loopback-only while the card cheerfully prints a QR for a dead URL
// (DL-069 follow-up). Probing from this page is exactly the request the
// phone would make: an opaque no-cors response means the interface is
// bound and the phone will connect; a rejection means nothing is
// listening there yet.
const lanReachable = ref<boolean | null>(null)
async function probeLanReachability() {
  const url = lanUrl.value
  if (!url) { lanReachable.value = null; return }
  try {
    await fetch(url, { mode: 'no-cors', cache: 'no-store', signal: AbortSignal.timeout(4000) })
    lanReachable.value = true
  } catch {
    lanReachable.value = false
  }
}
watch(lanUrl, probeLanReachability)

// What to tell the user when the QR target is dead. In dev the broken
// link is almost always the Vite dev server still bound to localhost —
// it read allow_lan once at ITS startup, so it needs its own restart,
// not just a VDock/backend relaunch.
const lanDeadHint = import.meta.env.DEV
  ? 'Restart the dev server so it re-binds with LAN access on — stop and re-run npm run dev in frontend/ (relaunching VDock alone doesn\u2019t restart Vite).'
  : 'Relaunch VDock — the bind address is chosen at startup.'

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
})

// DL-057: present the QR immediately — refresh the LAN URL, then draw.
onMounted(() => { void settingsStore.loadServerConfig().then(renderQr) })
</script>

<style scoped>
.kv-accent { color: #9cc0ff; }
.row-warn .label svg { color: var(--warn); }
.note.warn {
  border-color: #4a3a18;
  background: #261e0d;
  color: #e7cd9a;
}
.note.warn svg { color: var(--warn); }
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
  width: 128px;
  height: 128px;
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
