// DL-035 → DL-054: the Button Behaviour pane's nested sub-tab row was replaced
// by a single Buttons page (sidebar IA) whose panels — Sizing & touch, Key
// design, Motion, Labels & feedback — are reached by anchor scrolling.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const view = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

describe('button behaviour page (DL-054 merged panels)', () => {
  it('declares appearanceSubTab with buttons default', () => {
    expect(view).toContain("appearanceSubTab = ref<'buttons' | 'layout' | 'background' | 'screensaver'>('buttons')")
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

  it('routes settings search through deepTab anchors', () => {
    expect(view).toContain('deepTab')
    expect(view).toContain('deepTabAnchor')
    expect(view).toContain('scrollToPanel(anchor)')
  })
})
