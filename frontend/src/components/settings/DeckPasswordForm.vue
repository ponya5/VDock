<template>
  <div class="pw-form">
    <div class="pw-fields">
      <label class="sr-only" :for="`${uid}-new`">{{ mode === 'change' ? 'New password' : 'Password' }}</label>
      <input :id="`${uid}-new`" v-model="password" type="password" class="input" :placeholder="mode === 'change' ? 'New password' : 'Password'" autocomplete="new-password" />
      <label class="sr-only" :for="`${uid}-confirm`">Confirm password</label>
      <input :id="`${uid}-confirm`" v-model="confirm" type="password" class="input" placeholder="Confirm" autocomplete="new-password" @keyup.enter="save" />
    </div>
    <div class="pw-actions">
      <button type="button" class="btn primary sm" :disabled="busy" @click="save">{{ mode === 'change' ? 'Save' : 'Enable' }}</button>
      <button v-if="cancellable" type="button" class="btn sm" :disabled="busy" @click="emit('cancel')">Cancel</button>
    </div>
    <p v-if="error" class="status-msg status-error pw-error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, useId } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { useDeckAuth } from '@/composables/useDeckAuth'

/**
 * Choose a deck password. `enable` sets it and turns authentication on in one
 * request; `change` only replaces the password while authentication stays on.
 */
const props = withDefaults(defineProps<{ mode?: 'enable' | 'change'; cancellable?: boolean }>(), {
  mode: 'enable',
  cancellable: true,
})
const emit = defineEmits<{ done: []; cancel: [] }>()

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const { setAuthEnabled } = useDeckAuth()

const uid = useId()
const password = ref('')
const confirm = ref('')
const error = ref('')
const busy = ref(false)

async function save() {
  error.value = ''
  const pw = password.value.trim()
  if (pw.length < 4 || pw.length > 128) {
    error.value = 'Password must be 4–128 characters.'
    return
  }
  if (pw !== confirm.value.trim()) {
    error.value = "Passwords don't match."
    return
  }
  busy.value = true
  try {
    if (props.mode === 'enable') {
      // Enabling locks THIS device too; the lock screen takes over.
      if (await setAuthEnabled(true, pw)) emit('done')
    } else if (await settingsStore.updateServerConfig({ auth_password: pw })) {
      notificationsStore.success('Password updated', 'New devices will need it at the lock screen.')
      emit('done')
    } else {
      error.value = 'Server rejected the change.'
    }
  } finally {
    busy.value = false
    password.value = ''
    confirm.value = ''
  }
}
</script>

<style scoped>
.pw-form { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; max-width: 100%; }
.pw-fields, .pw-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.pw-fields .input { width: 140px; max-width: 100%; }
.pw-error { flex-basis: 100%; margin: 0; }
</style>
