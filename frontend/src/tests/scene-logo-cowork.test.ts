// A scene added from the Claude Cowork template shows the Cowork logo.
import { describe, expect, it } from 'vitest'
import { sceneLogo } from '@/services/appDetection'

describe('sceneLogo — Claude Cowork', () => {
  it('uses the Cowork logo, not the Claude one', () => {
    expect(sceneLogo({ id: 's', name: 'Claude Cowork', pages: [], appId: 'claude-cowork' }))
      .toBe('/logos/claudecowork-color.png')
  })
})
