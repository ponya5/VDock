import { describe, it, expect, beforeEach, vi } from 'vitest'

// Auto scene switching: a foreground change to an app with an enabled,
// scene-linked integration fires the scene-switch callbacks with that
// scene's id; unlinked/disabled/unknown apps do nothing.

type FakeApp = { exe: string; name?: string; path?: string }
let appChangeHandler: ((app: FakeApp) => void) | null = null

vi.mock('@/services/appMonitor', () => ({
  appMonitorService: {
    onAppChange: (cb: (app: FakeApp) => void) => { appChangeHandler = cb },
    offAppChange: () => { appChangeHandler = null },
    start: vi.fn().mockResolvedValue(true),
    stop: vi.fn().mockResolvedValue(true),
    getCurrentActiveApp: vi.fn().mockResolvedValue({ exe: 'spotify.exe' }),
  },
}))

import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'

const integrations = [
  { appExe: 'spotify.exe', appName: 'Spotify', sceneId: 'scene-spotify', enabled: true, autoCreateScene: false },
  { appExe: 'google chrome', appName: 'Google Chrome', sceneId: 'scene-chrome', enabled: true, autoCreateScene: false },
  { appExe: 'cursor.exe', appName: 'Cursor', sceneId: 'scene-cursor', enabled: false, autoCreateScene: false },
  { appExe: 'notepad.exe', appName: 'Notepad', sceneId: '', enabled: true, autoCreateScene: false },
]

describe('autoSceneSwitcher', () => {
  const onSwitch = vi.fn()

  beforeEach(async () => {
    onSwitch.mockClear()
    await autoSceneSwitcher.disable()
    autoSceneSwitcher.initialize(integrations)
    autoSceneSwitcher.onSceneSwitch(onSwitch)
    await autoSceneSwitcher.enable()
  })

  it('switches to the linked scene when the app takes focus', () => {
    appChangeHandler?.({ exe: 'spotify.exe' })
    expect(onSwitch).toHaveBeenCalledWith('scene-spotify', 'spotify.exe')
  })

  it('matches the executable name case-insensitively (Windows reports Spotify.exe)', () => {
    appChangeHandler?.({ exe: 'Spotify.exe' })
    expect(onSwitch).toHaveBeenCalledWith('scene-spotify', 'Spotify.exe')
  })

  it('matches a macOS bundle id to a scanned process name (DL-025)', () => {
    // Scanner stores 'google chrome'; the macOS monitor reports 'Google Chrome.app'
    appChangeHandler?.({
      exe: 'Google Chrome.app',
      name: 'Google Chrome',
      path: '/Applications/Google Chrome.app',
    })
    expect(onSwitch).toHaveBeenCalledWith('scene-chrome', 'Google Chrome.app')
  })

  it('matches a scanned Windows exe to a macOS bundle id and vice versa', () => {
    appChangeHandler?.({ exe: 'Spotify.app', name: 'Spotify', path: '/Applications/Spotify.app' })
    expect(onSwitch).toHaveBeenCalledWith('scene-spotify', 'Spotify.app')
  })

  it('ignores disabled integrations, unlinked integrations and unknown apps', () => {
    appChangeHandler?.({ exe: 'cursor.exe' })
    appChangeHandler?.({ exe: 'notepad.exe' })
    appChangeHandler?.({ exe: 'firefox.exe' })
    expect(onSwitch).not.toHaveBeenCalled()
  })

  it('does not match a different app sharing a prefix', () => {
    appChangeHandler?.({ exe: 'Spotify Helper.app', name: 'Spotify Helper' })
    expect(onSwitch).not.toHaveBeenCalled()
  })

  it('stops reacting once disabled', async () => {
    await autoSceneSwitcher.disable()
    expect(appChangeHandler).toBeNull()
    expect(onSwitch).not.toHaveBeenCalled()
  })

  it('checkAndSwitch applies the current foreground app immediately', async () => {
    await autoSceneSwitcher.checkAndSwitch()
    expect(onSwitch).toHaveBeenCalledWith('scene-spotify', 'spotify.exe')
  })
})
