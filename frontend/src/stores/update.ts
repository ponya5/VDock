import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getHealthVersion, getUpdateStatus, installUpdate, type UpdateStatus } from '@/api/update'
import { useNotificationsStore } from '@/stores/notifications'
import { confirmDialog } from '@/composables/useConfirm'
import { reloadPage } from '@/utils/reloadPage'

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
  let loadedVersion = ''

  const state = computed(() => status.value?.state ?? 'idle')
  const busy = computed(() => ACTIVE.includes(state.value))
  const visible = computed(() => {
    const s = status.value
    if (!s) return false
    if (busy.value || s.state === 'error') return true
    return !!s.available && !!s.latest && s.latest !== dismissedVersion.value
  })

  /**
   * One-time "Updated to vX" confirmation. The installer relaunches the app
   * silently, so without this an update looks like nothing happened (DL-152).
   * The last seen version is per device/browser.
   */
  function announceIfUpdated(current: string) {
    try {
      const KEY = 'vdock.update.lastSeenVersion'
      const previous = localStorage.getItem(KEY)
      localStorage.setItem(KEY, current)
      if (previous && previous !== current) {
        useNotificationsStore().success(`Updated to v${current}`, `VDock was v${previous}. See Settings > About for details.`)
      }
    } catch {
      // storage unavailable: skip the confirmation
    }
  }

  async function refresh(force = false) {
    // An explicit "Check now" re-prompts even if "Later" hid this version.
    if (force) dismissedVersion.value = ''
    checking.value = true
    try {
      status.value = await getUpdateStatus(force)
    } catch {
      // Offline / old backend: keep the previous status, stay quiet.
    } finally {
      checking.value = false
    }
    // The backend can restart between two polls, so 'restarting' may never be
    // seen. A different version than the one this page loaded with means the
    // bundle we are running is stale.
    const current = status.value?.current
    if (current) {
      if (!loadedVersion) { loadedVersion = current; announceIfUpdated(current) }
      else if (current !== loadedVersion) { stop(); reloadPage(); return }
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
          reloadPage()
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
    const ok = await confirmDialog({
      title: `Update to v${status.value?.latest ?? ''}?`,
      message: 'VDock will download the new version, replace the current one and restart.',
      confirmLabel: 'Update',
      cancelLabel: 'Not now',
      danger: false,
      icon: 'download',
    })
    if (!ok) return
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
