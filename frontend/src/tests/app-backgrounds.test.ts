import { describe, test, expect } from 'vitest'
import {
  APP_SCENE_BACKGROUNDS,
  appBackgroundById,
  appBackgroundForExe,
  appBackgroundForScene,
  appForScene,
  appIdForExe,
} from '../data/appBackgrounds'
import type { AppIntegration } from '@/types'

const claude = APP_SCENE_BACKGROUNDS.find(e => e.id === 'claude-code')!
const cursor = APP_SCENE_BACKGROUNDS.find(e => e.id === 'cursor')!

describe('app background registry', () => {
  test('known ids resolve to bundled assets', () => {
    expect(appBackgroundById('claude-code')).toBe(claude)
    expect(appBackgroundById('cursor')).toBe(cursor)
    expect(appBackgroundById('n8n')).toBeUndefined()
    expect(appBackgroundById(undefined)).toBeUndefined()
  })

  test('exes resolve case-insensitively', () => {
    expect(appBackgroundForExe('Cursor.exe')).toBe(cursor)
    expect(appBackgroundForExe('cursor.exe')).toBe(cursor)
    expect(appIdForExe('cursor.exe')).toBe('cursor')
  })

  test('terminal exes resolve to claude-code, matching the backend claim', () => {
    for (const exe of ['cmd.exe', 'powershell.exe', 'wt.exe', 'WindowsTerminal.exe']) {
      expect(appBackgroundForExe(exe)).toBe(claude)
    }
  })

  test('unknown exes resolve to nothing', () => {
    expect(appBackgroundForExe('chrome.exe')).toBeUndefined()
    expect(appBackgroundForExe('')).toBeUndefined()
    expect(appBackgroundForExe(undefined)).toBeUndefined()
  })
})

describe('appBackgroundForScene resolution order', () => {
  const integration: AppIntegration = {
    appExe: 'cursor.exe', appName: 'Cursor', enabled: true,
    sceneId: 'scene-1', autoCreateScene: false,
  }

  test('appId wins over triggeredByApp and integration', () => {
    const scene = { id: 'scene-1', appId: 'claude-code', triggeredByApp: 'cursor.exe' }
    expect(appBackgroundForScene(scene, [integration])).toBe(claude)
  })

  test('triggeredByApp wins over integration', () => {
    const scene = { id: 'scene-1', triggeredByApp: 'cmd.exe' }
    expect(appBackgroundForScene(scene, [integration])).toBe(claude)
  })

  test('an enabled integration supplies the app when the scene has none', () => {
    const scene = { id: 'scene-1' }
    expect(appBackgroundForScene(scene, [integration])).toBe(cursor)
  })

  test('a disabled or unrelated integration contributes nothing', () => {
    const scene = { id: 'scene-1' }
    const disabled = { ...integration, enabled: false }
    const otherScene = { ...integration, sceneId: 'scene-2' }
    expect(appBackgroundForScene(scene, [disabled])).toBeUndefined()
    expect(appBackgroundForScene(scene, [otherScene])).toBeUndefined()
  })

  test('disableAppBackground opts out but keeps the association visible', () => {
    const scene = { id: 'scene-1', appId: 'cursor', disableAppBackground: true }
    expect(appBackgroundForScene(scene, [integration])).toBeUndefined()
    expect(appForScene(scene, [integration])).toBe(cursor)
  })

  test('plain scenes have no app default', () => {
    expect(appBackgroundForScene({ id: 'scene-9' }, [integration])).toBeUndefined()
  })
})
