<template>
  <div class="content">
    <div class="col">
      <section class="panel" id="security">
        <div class="panel-head"><h2>Security</h2><span class="hint">The deck password every device unlocks with.</span></div>
        <div class="panel-body">
          <div class="row">
            <div class="row-text">
              <span class="label">Authentication</span>
              <p>{{ serverConfig?.require_auth ? 'On. Every device unlocks with the deck password.' : 'Off. Anyone on your network who can reach the deck address can control this deck.' }}</p>
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
              <span class="label">Deck password</span>
              <p>{{ authChangeOpen ? 'Already-unlocked devices stay unlocked — the new password applies to the next unlock.' : 'Change the password devices use to unlock.' }}</p>
            </div>
            <div class="row-control">
              <DeckPasswordForm v-if="authChangeOpen" mode="change" @done="authChangeOpen = false" @cancel="authChangeOpen = false" />
              <button v-else type="button" class="btn sm" @click="authChangeOpen = true">
                <FontAwesomeIcon :icon="['fas', 'key']" /> Change password
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useServerConfig } from '@/composables/useServerConfig'
import { useDeckAuth } from '@/composables/useDeckAuth'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import DeckPasswordForm from '@/components/settings/DeckPasswordForm.vue'
import { confirmDialog } from '@/composables/useConfirm'

const { serverConfig } = useServerConfig()
const { setAuthEnabled } = useDeckAuth()

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
