import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'

/**
 * Read-only view of the backend server config plus the addresses derived from
 * it. Shared by the Settings panels that show where this deck can be reached
 * (Connect a device, MCP server). Writes still go through the settings store.
 */
export function useServerConfig() {
  const settingsStore = useSettingsStore()
  const serverConfig = computed(() => settingsStore.serverConfig)

  // The URL a phone needs is the one actually serving live code. In a built
  // (production/packaged) app, that's the backend port, which serves dist/.
  // In dev (`npm run dev`), it's the Vite dev server's own port instead —
  // Vite binds every interface (see vite.config.ts), so a LAN device gets
  // the same always-fresh HMR source the desktop Electron window does,
  // instead of silently freezing on whatever dist/ happened to contain the
  // last time someone ran `npm run build` (see DL-069).
  const lanUrl = computed(() => {
    const host = serverConfig.value?.deck_host || serverConfig.value?.lan_ip
    const port = import.meta.env.DEV
      ? Number(import.meta.env.VITE_PORT) || 3000
      : serverConfig.value?.port
    if (!host || !port) return null
    // With USE_SSL the backend serves HTTPS on that port; the dev server stays HTTP.
    const scheme = serverConfig.value?.use_ssl && !import.meta.env.DEV ? 'https' : 'http'
    return `${scheme}://${host}:${port}`
  })

  // MCP clients always hit the backend port (never the Vite dev server).
  const mcpEndpoint = computed(() => {
    const host = serverConfig.value?.deck_host || serverConfig.value?.lan_ip || '127.0.0.1'
    const port = serverConfig.value?.port ?? 5000
    const scheme = serverConfig.value?.use_ssl ? 'https' : 'http'
    return `${scheme}://${host}:${port}/api/mcp`
  })

  // The bind address is chosen at startup, so the change only lands after a
  // restart; the reloaded config's `restart_required` drives the Restart row.
  // Turning phone access on never leaves it open: with no auth yet it also
  // requires pairing (or re-enables auth when a password already exists).
  async function setAllowLan(enabled: boolean): Promise<boolean> {
    const cfg = serverConfig.value
    const changes: Record<string, unknown> = { allow_lan: enabled }
    if (enabled && !cfg?.require_auth) {
      if (cfg?.auth_password_set) changes.require_auth = true
      else changes.pair_only = true
    }
    const ok = await settingsStore.updateServerConfig(changes)
    if (ok) await settingsStore.loadServerConfig()
    const notifications = useNotificationsStore()
    const needsRestart = ok && settingsStore.serverConfig?.restart_required === true
    notifications[ok ? 'success' : 'error'](
      ok ? 'Phone & tablet access ' + (enabled ? 'on' : 'off') : 'Could not save',
      !ok ? 'Server rejected the change.'
        : needsRestart ? 'Restart VDock for this to take effect — Settings › Connect & security has the button.'
        : 'Applied.',
    )
    return ok
  }

  return { serverConfig, lanUrl, mcpEndpoint, setAllowLan }
}
