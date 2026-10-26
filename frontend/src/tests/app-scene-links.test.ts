import { describe, it, expect } from 'vitest'
import { relinkAppIntegrations } from '@/utils/appSceneLinks'
import type { AppIntegration, Scene } from '@/types'

const scene = (id: string, triggeredByApp?: string) => ({ id, name: id, pages: [], triggeredByApp }) as unknown as Scene
const int = (appExe: string, sceneId: string): AppIntegration =>
  ({ appExe, appName: appExe, sceneId, enabled: true, autoCreateScene: false })

describe('relinkAppIntegrations', () => {
  it('returns null when every link is valid', () => {
    expect(relinkAppIntegrations([int('Spotify.exe', 's1')], [scene('s1')])).toBeNull()
  })

  it('clears a link to a scene that no longer exists', () => {
    const out = relinkAppIntegrations([int('Spotify.exe', 'gone')], [scene('s1')])
    expect(out?.[0].sceneId).toBe('')
  })

  it('re-points a dangling or empty link at the scene made for that app', () => {
    const scenes = [scene('s1'), scene('s2', 'spotify.exe')]
    const out = relinkAppIntegrations([int('Spotify.exe', 'gone'), int('SPOTIFY.EXE', '')], scenes)
    expect(out?.map(i => i.sceneId)).toEqual(['s2', 's2'])
  })

  it('leaves an unlinked integration with no matching scene alone', () => {
    expect(relinkAppIntegrations([int('cursor.exe', '')], [scene('s1')])).toBeNull()
  })
})
