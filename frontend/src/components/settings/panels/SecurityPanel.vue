<template>
  <section class="panel" id="security">
    <div class="panel-head"><h2>Who can connect</h2><span class="hint">Pairing or a deck password keeps other devices on your Wi-Fi out.</span></div>
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
      <!-- While phone access is unprotected the warning row above is the one control. -->
      <div v-if="!(serverConfig?.allow_lan && !serverConfig.require_auth)" class="row">
        <div class="row-text">
          <span class="label">Authentication</span>
          <p>{{ serverConfig?.require_auth ? (serverConfig.pair_only ? 'On, pairing only. A device gets in by scanning the code on Connect a device — there is no password.' : 'On. Every device unlocks with the deck password.') : 'Off. Anyone on your network who can reach the deck address can control this deck.' }}</p>
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
          <p v-if="serverConfig.pair_only">Switches off pairing-only: devices can then also unlock by typing this password. Scanning the Connect code still works.</p>
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
import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { useDeckAuth } from '@/composables/useDeckAuth'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import DeckPasswordForm from '@/components/settings/DeckPasswordForm.vue'
import { confirmDialog } from '@/composables/useConfirm'

const { serverConfig } = useServerConfig()
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
</script>
