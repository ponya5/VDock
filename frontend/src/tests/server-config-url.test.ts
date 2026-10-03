// DL-147 Task 4.5 - with USE_SSL on, the QR and MCP address must be https or a
// phone lands on a dead port.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSettingsStore } from '@/stores/settings'
import { useServerConfig } from '@/composables/useServerConfig'

function withConfig(over: Record<string, unknown>) {
  const store = useSettingsStore()
  store.serverConfig = { port: 5000, lan_ip: '192.168.1.5', deck_host: '', use_ssl: false, ...over } as never
  return useServerConfig()
}

beforeEach(() => {
  setActivePinia(createPinia())
  // The built app (the backend's port), not `npm run dev` (the Vite port).
  vi.stubEnv('DEV', false)
})
afterEach(() => vi.unstubAllEnvs())

describe('useServerConfig addresses', () => {
  it('stays http by default', () => {
    const { lanUrl, mcpEndpoint } = withConfig({})
    expect(lanUrl.value).toBe('http://192.168.1.5:5000')
    expect(mcpEndpoint.value).toBe('http://192.168.1.5:5000/api/mcp')
  })

  it('switches both to https when USE_SSL is on', () => {
    const { lanUrl, mcpEndpoint } = withConfig({ use_ssl: true })
    expect(lanUrl.value).toBe('https://192.168.1.5:5000')
    expect(mcpEndpoint.value).toBe('https://192.168.1.5:5000/api/mcp')
  })
})
