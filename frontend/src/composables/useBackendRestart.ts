import { ref } from 'vue'
import { getHealth, restartBackend } from '@/api/system'
import { reloadPage } from '@/utils/reloadPage'

const POLL_MS = 1500
const GIVE_UP_MS = 90_000

/**
 * "Restart VDock now" for switches that only apply when the server binds its
 * socket (DL-007). The backend restarts itself (Electron or the launcher
 * brings it back); this page waits until a fresh process answers, then
 * reloads so it talks to the new one.
 */
export function useBackendRestart() {
  const restarting = ref(false)
  const error = ref<string | null>(null)

  async function waitForFreshBackend(uptimeBefore: number): Promise<boolean> {
    const deadline = Date.now() + GIVE_UP_MS
    let wasDown = false
    while (Date.now() < deadline) {
      await new Promise(resolve => setTimeout(resolve, POLL_MS))
      try {
        const health = await getHealth()
        // A lower uptime means a new process even if no poll caught it down.
        if (wasDown || health.uptimeS < uptimeBefore) return true
      } catch {
        wasDown = true
      }
    }
    return false
  }

  async function restart(): Promise<void> {
    if (restarting.value) return
    restarting.value = true
    error.value = null
    try {
      const before = await getHealth().catch(() => ({ uptimeS: Number.MAX_SAFE_INTEGER, restartRequired: true }))
      await restartBackend()
      if (await waitForFreshBackend(before.uptimeS)) {
        reloadPage()
        return
      }
      error.value = 'VDock did not come back. Start it again from your apps.'
    } catch (e: any) {
      error.value = e?.response?.data?.error || e?.message || 'Restart failed'
    }
    restarting.value = false
  }

  return { restarting, error, restart }
}
