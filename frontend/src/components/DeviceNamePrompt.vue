<template>
  <Teleport to="body">
    <div v-if="current" class="modal-overlay confirm-overlay theme-dark">
      <form class="modal confirm-dialog" role="dialog" aria-modal="true" aria-label="Name this device" data-testid="device-name-prompt" @submit.prevent="save">
        <div class="confirm-icon"><FontAwesomeIcon :icon="['fas', 'mobile-screen-button']" /></div>
        <h2 class="confirm-title">Name this device</h2>
        <p class="confirm-message">{{ current.label }}. So you can recognise it in Connected devices on your computer — and spot one you don't.</p>
        <input v-model="name" class="input" maxlength="40" :placeholder="current.label" autocomplete="off" aria-label="Device name" />
        <div class="confirm-actions">
          <button type="button" class="btn btn-secondary" @click="skip">Not now</button>
          <button type="submit" class="btn btn-primary" :disabled="!name.trim()">Save</button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { authState } from '@/services/auth'
import { fetchDevices, renameDevice, type PairedDevice } from '@/services/pairing'

// Asked once, on the device itself, right after it signs in. The backend
// marks loopback (this computer) as already named, so only phones see it.
const current = ref<PairedDevice | null>(null)
const name = ref('')
// Remembered on this browser too: a re-sign-in (new device record) or "Not now"
// must not bring the question back on every refresh.
const LOCAL_KEY = 'vdock.deviceName'
const SKIP_KEY = 'vdock.deviceNameSkipped'
const read = (key: string) => { try { return localStorage.getItem(key) } catch { return null } }
const write = (key: string, value: string) => { try { localStorage.setItem(key, value) } catch { /* ignore */ } }

async function check() {
  if (authState.required && !authState.unlocked) return
  const me = (await fetchDevices())?.find(d => d.current && !d.named)
  if (!me) return
  const remembered = read(LOCAL_KEY)
  if (remembered) { await renameDevice(me.id, remembered); return }
  if (read(SKIP_KEY) === '1') return
  current.value = me
  name.value = me.label
}
watch(() => authState.unlocked, check, { immediate: true })

async function save() {
  if (current.value && await renameDevice(current.value.id, name.value)) {
    write(LOCAL_KEY, name.value.trim())
    current.value = null
  }
}
function skip() {
  write(SKIP_KEY, '1')
  current.value = null
}
</script>
