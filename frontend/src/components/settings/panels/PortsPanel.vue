<template>
  <div class="content">
    <div class="col">
      <section class="panel" id="connection">
        <div class="panel-head"><h2>Ports &amp; host</h2><span class="hint">Ports are written to backend/.env and frontend/.env and take effect on the next launch.</span></div>
        <div class="panel-body">
          <div class="row">
            <div class="row-text">
              <span class="label">Host</span>
              <p>The interface the server binds to.</p>
            </div>
            <div class="row-control">
              <code class="kv-code">{{ serverConfig?.host ?? '127.0.0.1' }}</code>
            </div>
          </div>
          <div class="row">
            <div class="row-text">
              <span class="label">Ports</span>
              <p>Frontend is the port you open in the browser; backend is the API the frontend proxies to.</p>
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
          <div class="row">
            <div class="row-text">
              <span class="label">Applying port changes</span>
              <p>Needs a restart of VDock via <code class="kv-code">launch.bat</code>.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { useServerConfig } from '@/composables/useServerConfig'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import apiClient from '@/api/client'

const notificationsStore = useNotificationsStore()
const { serverConfig } = useServerConfig()

// Ports are written to the .env files and bind at process start — the UI
// validates and probes collisions, then tells the user to relaunch.
const serverPorts = ref({ frontend: 0, backend: 0 })
const portErrors = ref<{ frontend: string; backend: string }>({ frontend: '', backend: '' })
const portsStatus = ref<{ success: boolean; message: string } | null>(null)
const portsBusy = ref(false)

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
    if (!checkOnly) notificationsStore.success('Ports saved', data.message)
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
