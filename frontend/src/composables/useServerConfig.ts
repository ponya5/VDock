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
    return `http://${host}:${port}`
  })

  // MCP clients always hit the backend port (never the Vite dev server).
  const mcpEndpoint = computed(() => {
    const host = serverConfig.value?.deck_host || serverConfig.value?.lan_ip || '127.0.0.1'
    const port = serverConfig.value?.port ?? 5000
    return `http://${host}:${port}/api/mcp`
  })

  // The bind address is chosen at startup, so the change only lands on relaunch.
  async function setAllowLan(enabled: boolean): Promise<boolean> {
    const ok = await settingsStore.updateServerConfig({ allow_lan: enabled })
    const notifications = useNotificationsStore()
    notifications[ok ? 'success' : 'error'](
      ok ? 'LAN access ' + (enabled ? 'enabled' : 'disabled') : 'Could not save',
      ok ? 'Relaunch VDock to apply — the bind address is chosen at startup.' : 'Server rejected the change.'
    )
    return ok
  }

  return { serverConfig, lanUrl, mcpEndpoint, setAllowLan }
}
