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
              <label class="sr-only" for="auth-pw-new">New password</label>
              <input id="auth-pw-new" v-model="authPwNew" type="password" class="input w-110" placeholder="Password" autocomplete="new-password" />
              <label class="sr-only" for="auth-pw-confirm">Confirm password</label>
              <input id="auth-pw-confirm" v-model="authPwConfirm" type="password" class="input w-110" placeholder="Confirm" autocomplete="new-password" @keyup.enter="saveAuthPassword(true)" />
              <button type="button" class="btn primary sm" :disabled="authPwBusy" @click="saveAuthPassword(true)">
                Enable
              </button>
              <button type="button" class="btn sm" :disabled="authPwBusy" @click="cancelAuthSetup">
                Cancel
              </button>
            </div>
          </div>
          <div v-if="authSetupOpen && authPwError" class="row row-status-row">
            <div class="row-text">
              <p class="status-msg status-error">{{ authPwError }}</p>
            </div>
          </div>
          <div v-if="serverConfig?.require_auth" class="row">
            <div class="row-text">
              <span class="label">Deck password</span>
              <p>{{ authChangeOpen ? 'Already-unlocked devices stay unlocked — the new password applies to the next unlock.' : 'Change the password devices use to unlock.' }}</p>
            </div>
            <div class="row-control">
              <template v-if="authChangeOpen">
                <label class="sr-only" for="auth-pw-change">New password</label>
                <input id="auth-pw-change" v-model="authPwNew" type="password" class="input w-110" placeholder="New password" autocomplete="new-password" />
                <label class="sr-only" for="auth-pw-change2">Confirm new password</label>
                <input id="auth-pw-change2" v-model="authPwConfirm" type="password" class="input w-110" placeholder="Confirm" autocomplete="new-password" @keyup.enter="saveAuthPassword(false)" />
                <button type="button" class="btn primary sm" :disabled="authPwBusy" @click="saveAuthPassword(false)">
                  Save
                </button>
                <button type="button" class="btn sm" :disabled="authPwBusy" @click="authChangeOpen = false">
                  Cancel
                </button>
              </template>
              <button v-else type="button" class="btn sm" @click="authChangeOpen = true">
                <FontAwesomeIcon :icon="['fas', 'key']" /> Change password
              </button>
            </div>
          </div>
          <div v-if="authChangeOpen && authPwError" class="row row-status-row">
            <div class="row-text">
              <p class="status-msg status-error">{{ authPwError }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { ServerConfig } from '@/types'
import { authState, clearAuthToken } from '@/services/auth'
import { confirmDialog } from '@/composables/useConfirm'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { serverConfig } = useServerConfig()

// ── Authentication (DL-126) ──────────────────────────────────────────────
// require_auth writes through the same /api/config channel as the other
// toggles, but the switch is bound to serverConfig so its visual state must
// be reverted by hand whenever the change is cancelled or rejected.
// Enabling locks THIS device too: after a successful enable the lock screen
// takes over and the user unlocks once with the password they just set.
const authSetupOpen = ref(false)
const authChangeOpen = ref(false)
const authPwNew = ref('')
const authPwConfirm = ref('')
const authPwError = ref('')
const authPwBusy = ref(false)
let authSwitchEl: HTMLInputElement | null = null

function revertAuthSwitch(enabled: boolean) {
  if (authSwitchEl) authSwitchEl.checked = !enabled
}

async function applyAuthToggle(enabled: boolean, password?: string) {
  const payload: Partial<ServerConfig> = { require_auth: enabled }
  if (password !== undefined) payload.auth_password = password
  const ok = await settingsStore.updateServerConfig(payload)
  if (!ok) {
    notificationsStore.error('Could not save', 'Server rejected the change.')
    revertAuthSwitch(enabled)
    return
  }
  if (enabled) {
    // The server now demands a token this device doesn't hold — the gate
    // takes over; unlocking with the just-set password reloads clean.
    authState.required = true
    authState.unlocked = false
  } else {
    authState.required = false
    clearAuthToken()
    notificationsStore.success('Authentication off', 'Devices no longer need the deck password.')
  }
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
      authPwError.value = ''
      authPwNew.value = ''
      authPwConfirm.value = ''
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
  authPwError.value = ''
  revertAuthSwitch(true)
}

async function saveAuthPassword(enableAfter: boolean) {
  authPwError.value = ''
  const pw = authPwNew.value.trim()
  if (pw.length < 4 || pw.length > 128) {
    authPwError.value = 'Password must be 4–128 characters.'
    return
  }
  if (pw !== authPwConfirm.value.trim()) {
    authPwError.value = "Passwords don't match."
    return
  }
  authPwBusy.value = true
  try {
    if (enableAfter) {
      await applyAuthToggle(true, pw)
      authSetupOpen.value = false
    } else {
      const ok = await settingsStore.updateServerConfig({ auth_password: pw })
      if (ok) {
        authChangeOpen.value = false
        notificationsStore.success('Password updated', 'New devices will need it at the lock screen.')
      } else {
        authPwError.value = 'Server rejected the change.'
      }
    }
  } finally {
    authPwBusy.value = false
    authPwNew.value = ''
    authPwConfirm.value = ''
  }
}
</script>
