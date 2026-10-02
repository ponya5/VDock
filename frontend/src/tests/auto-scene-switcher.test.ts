import { describe, it, expect, beforeEach, vi } from 'vitest'

// Auto scene switching: a foreground change to an app with an enabled,
// scene-linked integration fires the scene-switch callbacks with that
// scene's id; unlinked/disabled/unknown apps do nothing.

let appChangeHandler: ((app: { exe: string }) => void) | null = null

vi.mock('@/services/appMonitor', () => ({
  appMonitorService: {
    onAppChange: (cb: (app: { exe: string }) => void) => { appChangeHandler = cb },
    offAppChange: () => { appChangeHandler = null },
    start: vi.fn().mockResolvedValue(true),
    stop: vi.fn().mockResolvedValue(true),
    getCurrentActiveApp: vi.fn().mockResolvedValue({ exe: 'spotify.exe' }),
  },
}))

import { autoSceneSwitcher } from '@/services/autoSceneSwitcher'

const integrations = [
  { appExe: 'spotify.exe', appName: 'Spotify', sceneId: 'scene-spotify', enabled: true, autoCreateScene: false },
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

  it('ignores disabled integrations, unlinked integrations and unknown apps', () => {
    appChangeHandler?.({ exe: 'cursor.exe' })
    appChangeHandler?.({ exe: 'notepad.exe' })
    appChangeHandler?.({ exe: 'chrome.exe' })
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
