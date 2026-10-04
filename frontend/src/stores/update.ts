import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getHealthVersion, getUpdateStatus, installUpdate, type UpdateStatus } from '@/api/update'

const CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000
const POLL_MS = 2000
const ACTIVE = ['downloading', 'installing', 'restarting']

export const useUpdateStore = defineStore('update', () => {
  const status = ref<UpdateStatus | null>(null)
  // In memory only: "Later" hides the prompt until the next launch.
  const dismissedVersion = ref('')
  const checking = ref(false)
  const forbidden = ref(false)
  const installError = ref<string | null>(null)

  let started = false
  let checkTimer: ReturnType<typeof setInterval> | null = null
  let pollTimer: ReturnType<typeof setTimeout> | null = null
  let healthTimer: ReturnType<typeof setTimeout> | null = null

  const state = computed(() => status.value?.state ?? 'idle')
  const busy = computed(() => ACTIVE.includes(state.value))
  const visible = computed(() => {
    const s = status.value
    if (!s) return false
    if (busy.value || s.state === 'error') return true
    return !!s.available && !!s.latest && s.latest !== dismissedVersion.value
  })

  async function refresh(force = false) {
    checking.value = true
    try {
      status.value = await getUpdateStatus(force)
    } catch {
      // Offline / old backend: keep the previous status, stay quiet.
    } finally {
      checking.value = false
    }
    syncPolling()
  }

  function syncPolling() {
    if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
    if (state.value === 'restarting') { waitForRestart(); return }
    if (busy.value) {
      pollTimer = setTimeout(() => { void refresh() }, POLL_MS)
    }
  }

  /** Poll /health until the version changes or the backend returns after a gap. */
  function waitForRestart() {
    if (healthTimer) return
    const before = status.value?.current ?? ''
    let wasDown = false
    const tick = async () => {
      try {
        const v = await getHealthVersion()
        if (wasDown || (v && before && v !== before)) {
          healthTimer = null
          location.reload()
          return
        }
      } catch {
        wasDown = true
      }
      healthTimer = setTimeout(tick, POLL_MS)
    }
    healthTimer = setTimeout(tick, POLL_MS)
  }

  async function install() {
    forbidden.value = false
    installError.value = null
    try {
      await installUpdate()
      await refresh()
    } catch (e: any) {
      if (e?.response?.status === 403) forbidden.value = true
      else installError.value = e?.response?.data?.error || e?.message || 'Update failed'
    }
  }

  function dismiss() {
    const v = status.value?.latest
    if (!v) return
    dismissedVersion.value = v
  }

  function start() {
    if (started) return
    started = true
    void refresh()
    checkTimer = setInterval(() => { void refresh() }, CHECK_INTERVAL_MS)
  }

  function stop() {
    started = false
    if (checkTimer) clearInterval(checkTimer)
    if (pollTimer) clearTimeout(pollTimer)
    if (healthTimer) clearTimeout(healthTimer)
    checkTimer = pollTimer = healthTimer = null
  }

  return { status, dismissedVersion, checking, forbidden, installError, state, busy, visible, refresh, install, dismiss, start, stop }
})
