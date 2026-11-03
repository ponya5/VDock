// DL-159: Cursor in front + a live Claude CLI session hosted by Cursor →
// Claude scene; back to the Cursor scene when it ends. Opt-out + failure safe.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

type FakeApp = { exe: string }
let appChangeHandler: ((app: FakeApp) => void) | null = null

vi.mock('@/services/appMonitor', () => ({
  appMonitorService: {
    onAppChange: (cb: (app: FakeApp) => void) => { appChangeHandler = cb },
    offAppChange: () => { appChangeHandler = null },
    start: vi.fn().mockResolvedValue(true),
    stop: vi.fn().mockResolvedValue(true),
    getCurrentActiveApp: vi.fn(),
  },
}))
const fetchSessions = vi.fn()
vi.mock('@/api/agentSessions', () => ({ fetchAgentSessions: (...a: unknown[]) => fetchSessions(...a) }))

import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'

const integrations = [
  { appExe: 'cursor', appName: 'Cursor', sceneId: 'scene-cursor', enabled: true, autoCreateScene: false },
  { appExe: 'spotify', appName: 'Spotify', sceneId: 'scene-spotify', enabled: true, autoCreateScene: false },
]
const session = (over: Record<string, unknown> = {}) => ({
  pid: 1, hwnd: 1, title: '', cwd: null, project: 'p', state: 'working', prompted: true,
  detail: '', host: 'Cursor', started: null, ...over,
})
const flush = async () => { await vi.advanceTimersByTimeAsync(0) }

describe('Claude in Cursor → Claude scene', () => {
  const onSwitch = vi.fn()
  let aware = true

  beforeEach(async () => {
    vi.useFakeTimers()
    onSwitch.mockClear()
    fetchSessions.mockReset().mockResolvedValue({ sessions: [], pinned_pid: null, resolved_pid: null })
    aware = true
    await autoSceneSwitcher.disable()
    autoSceneSwitcher.initialize(integrations)
    autoSceneSwitcher.setClaudeSceneSource(() => 'scene-claude', () => aware)
    autoSceneSwitcher.onSceneSwitch(onSwitch)
    await autoSceneSwitcher.enable()
  })
  afterEach(async () => {
    autoSceneSwitcher.offSceneSwitch(onSwitch)
    await autoSceneSwitcher.disable()
    vi.useRealTimers()
  })

  it('picks the Claude scene when a Cursor-hosted Claude session is working', async () => {
    fetchSessions.mockResolvedValue({ sessions: [session()] })
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenCalledTimes(1)
    expect(onSwitch).toHaveBeenCalledWith('scene-claude', 'Cursor')
    expect(fetchSessions).toHaveBeenCalledWith('claude')
  })

  it('keeps the Cursor scene with no session, or a session hosted elsewhere', async () => {
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor')
    onSwitch.mockClear()
    fetchSessions.mockResolvedValue({ sessions: [session({ host: 'Terminal' })] })
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor')
  })

  it('ignores an unprompted idle session (freshly launched, nothing asked)', async () => {
    fetchSessions.mockResolvedValue({ sessions: [session({ state: 'ready', prompted: false })] })
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor')
  })

  it('follows the session while Cursor stays in front, emitting only on change', async () => {
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenCalledTimes(1) // cursor scene
    await vi.advanceTimersByTimeAsync(3000)
    expect(onSwitch).toHaveBeenCalledTimes(1) // nothing changed → quiet
    fetchSessions.mockResolvedValue({ sessions: [session()] })
    await vi.advanceTimersByTimeAsync(3000)
    expect(onSwitch).toHaveBeenLastCalledWith('scene-claude', 'Cursor')
    expect(onSwitch).toHaveBeenCalledTimes(2)
    fetchSessions.mockResolvedValue({ sessions: [] })
    await vi.advanceTimersByTimeAsync(3000)
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor')
  })

  it('stops watching once another app takes focus', async () => {
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    appChangeHandler?.({ exe: 'spotify' })
    expect(onSwitch).toHaveBeenLastCalledWith('scene-spotify', 'spotify') // immediate, no fetch
    fetchSessions.mockClear()
    await vi.advanceTimersByTimeAsync(9000)
    expect(fetchSessions).not.toHaveBeenCalled()
  })

  it('does nothing special when the setting is off, and survives a failing API', async () => {
    aware = false
    fetchSessions.mockResolvedValue({ sessions: [session()] })
    appChangeHandler?.({ exe: 'Cursor' })
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor') // sync, as before
    expect(fetchSessions).not.toHaveBeenCalled()
    aware = true
    fetchSessions.mockRejectedValue(new Error('down'))
    appChangeHandler?.({ exe: 'Cursor' })
    await flush()
    expect(onSwitch).toHaveBeenLastCalledWith('scene-cursor', 'Cursor')
  })
})
