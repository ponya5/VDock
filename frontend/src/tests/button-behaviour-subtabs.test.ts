// DL-035 → DL-054: the Button Behaviour pane's nested sub-tab row was replaced
// by a single Buttons page (sidebar IA) whose panels — Sizing & touch, Key
// design, Motion, Labels & feedback — are reached by anchor scrolling.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { settingsSource, settingsViewSource } from './helpers/settingsSource'
import { SECTIONS, SEARCH } from '@/settings/registry'

const view = settingsSource()

describe('button behaviour page (DL-054 merged panels)', () => {
  it('registers Buttons as the first Appearance page', () => {
    const appearance = SECTIONS.find((s) => s.id === 'appearance')!
    expect(appearance.pages.map((p) => p.id)).toEqual(['buttons', 'layout', 'background', 'screensaver'])
    expect(appearance.pages[0].panels).toEqual(['AppearanceButtons'])
  })

  it('renders the merged panels with anchor ids', () => {
    for (const id of ['id="sizing"', 'id="design"', 'id="motion"', 'id="feedback"', 'id="touch"']) {
      expect(view).toContain(id)
    }
    expect(view).toContain('Sizing &amp; touch')
    expect(view).toContain('Key design')
    expect(view).toContain('Live preview')
    expect(view).toContain('Touch mode')
  })

  it('keeps the save/apply action — one button that applies to all keys', () => {
    // DL-031 follow-up: Save & Apply IS the mass-apply — the old
    // draft-only savebar path looked identical, so picks never landed.
    expect(view).not.toContain('saveAndApplyButtonSettings')
    expect(view).toContain('applyButtonBehaviourToAll')
    expect(view).toContain('requestVdockRefresh()')
    expect(view).toContain('await ensureProfileLoaded()')
    // BroadcastChannel never reaches the sender's own window — the apply
    // must refresh the current window itself, not only other tabs.
    expect(view).toContain('await refreshVdock()')
  })

  it('routes settings search to the Buttons panels through registry anchors', () => {
    const anchors = SEARCH.filter((e) => e.page === 'buttons').map((e) => e.anchor)
    expect(anchors).toEqual(expect.arrayContaining(['touch', 'sizing', 'design', 'motion', 'feedback']))
    expect(settingsViewSource()).toContain('anchor: match.anchor')
  })
})
