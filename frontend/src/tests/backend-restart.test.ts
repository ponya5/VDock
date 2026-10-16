// DL-007 - "Allow LAN access" only applies once the server re-binds. The
// Connect card offers the restart itself (relaunching used to reuse the old
// loopback-only server), and the page reloads once a fresh backend answers.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { settingsSource } from './helpers/settingsSource'

const api = vi.hoisted(() => ({
  getHealth: vi.fn(),
  restartBackend: vi.fn(),
}))
vi.mock('@/api/system', () => api)
const reload = vi.hoisted(() => ({ reloadPage: vi.fn() }))
vi.mock('@/utils/reloadPage', () => reload)

import { useBackendRestart } from '@/composables/useBackendRestart'

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers()
})

describe('useBackendRestart', () => {
  it('reloads once the backend went away and came back', async () => {
    api.getHealth
      .mockResolvedValueOnce({ uptimeS: 500, restartRequired: true })
      .mockRejectedValueOnce(new Error('down'))
      .mockResolvedValueOnce({ uptimeS: 2, restartRequired: false })
    api.restartBackend.mockResolvedValue(undefined)
    const { restart, restarting } = useBackendRestart()
    const done = restart()
    expect(restarting.value).toBe(true)
    await vi.runAllTimersAsync()
    await done
    expect(api.restartBackend).toHaveBeenCalledOnce()
    expect(reload.reloadPage).toHaveBeenCalledOnce()
  })

  it('treats a lower uptime as a fresh process even if no poll saw it down', async () => {
    api.getHealth
      .mockResolvedValueOnce({ uptimeS: 500, restartRequired: true })
      .mockResolvedValueOnce({ uptimeS: 1, restartRequired: false })
    api.restartBackend.mockResolvedValue(undefined)
    const done = useBackendRestart().restart()
    await vi.runAllTimersAsync()
    await done
    expect(reload.reloadPage).toHaveBeenCalledOnce()
  })

  it('reports a refused restart instead of reloading', async () => {
    api.getHealth.mockResolvedValue({ uptimeS: 500, restartRequired: true })
    api.restartBackend.mockRejectedValue({ response: { data: { error: 'Restart VDock from the computer it runs on.' } } })
    const { restart, restarting, error } = useBackendRestart()
    await restart()
    expect(reload.reloadPage).not.toHaveBeenCalled()
    expect(error.value).toBe('Restart VDock from the computer it runs on.')
    expect(restarting.value).toBe(false)
  })
})

describe('Connect a device restart row', () => {
  const view = settingsSource()

  it('shows the restart action while the saved switch is not applied', () => {
    expect(view).toContain("serverConfig.value?.restart_required === true")
    expect(view).toContain('data-testid="restart-required"')
    expect(view).toContain('Restart VDock now')
  })

  it('no longer tells the user to just relaunch (that reused the old server)', () => {
    expect(view).not.toContain('Relaunch VDock — the bind address is chosen at startup.')
  })

  it('names the firewall setting for the host OS', () => {
    expect(view).toContain('System Settings \\u203a Network \\u203a Firewall')
    expect(view).toContain('Windows Defender Firewall')
  })
})
