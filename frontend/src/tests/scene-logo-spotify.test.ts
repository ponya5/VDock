// A Spotify scene (auto-created, no appId) shows the Spotify logo.
import { describe, expect, it } from 'vitest'
import { sceneLogo } from '@/services/appDetection'

describe('sceneLogo — Spotify', () => {
  const base = { id: 's', name: 'Spotify', pages: [] }
  it.each(['spotify', 'Spotify.app', 'Spotify.exe'])('maps %s to the bundled logo', (exe) => {
    expect(sceneLogo({ ...base, triggeredByApp: exe })).toBe('/logos/spotify-color.png')
  })
  it('leaves other scenes alone', () => {
    expect(sceneLogo({ ...base, name: 'Other', triggeredByApp: 'notes' })).toBeNull()
  })
})
