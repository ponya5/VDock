// DL-035: Button Behaviour pane split into Button Display / Live Preview /
// Touch Mode sub-tabs, each with a Save & Apply action.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const view = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')

describe('button behaviour sub-tabs', () => {
  it('declares buttonsSubTab with display default', () => {
    expect(view).toContain("buttonsSubTab = ref<'display' | 'preview' | 'touch'>('display')")
  })

  it('renders the three nested sub-tab buttons', () => {
    for (const t of ["buttonsSubTab === 'display'", "buttonsSubTab === 'preview'", "buttonsSubTab === 'touch'"]) {
      // each appears twice: active-class check + section v-if
      expect(view.split(t).length).toBeGreaterThanOrEqual(3)
    }
    expect(view).toContain('Button Display')
    expect(view).toContain('Live Preview')
    expect(view).toContain('Touch Mode')
  })

  it('gives every sub-tab a save/apply action', () => {
    expect(view).toContain('saveAndApplyButtonSettings')
    // two generic applies (display + touch) + the apply-all in preview
    expect(view.split('saveAndApplyButtonSettings').length).toBeGreaterThanOrEqual(3)
    expect(view).toContain('applyButtonBehaviourToAll')
    expect(view).toContain('requestVdockRefresh()')
  })

  it('routes settings search to the nested tabs', () => {
    expect(view).toContain("deepTab")
    expect(view).toContain("buttonsSubTab.value = match.deepTab")
  })
})
