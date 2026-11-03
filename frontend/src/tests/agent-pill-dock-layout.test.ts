// The "waiting for input" pill and the bottom-right session chips used to
// overlap on landscape phones: the pill now flags itself on <html> and the
// dock lifts above it.
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (f: string) => readFileSync(resolve(__dirname, '../components', f), 'utf8')

describe('waiting pill vs chip dock', () => {
  it('pill toggles agent-pill-visible and the dock reacts to it', () => {
    expect(read('AgentWaitingGlow.vue')).toContain("'agent-pill-visible'")
    expect(read('AgentWaitingDock.vue')).toContain('html.agent-pill-visible .agent-waiting-dock')
  })
})
