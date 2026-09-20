// DL-012: the iOS-style edit-mode wiggle is opt-in (default off). It annoyed
// on the 7" touch panel, and the ::after drag-handle dot already marks edit
// mode, so the wiggle now needs the explicit setting.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const grid = readFileSync(
  resolve(__dirname, '../components/DeckGrid.vue'),
  'utf-8'
)
const store = readFileSync(
  resolve(__dirname, '../stores/settings.ts'),
  'utf-8'
)
const view = readFileSync(
  resolve(__dirname, '../views/SettingsView.vue'),
  'utf-8'
)

describe('edit-mode wiggle setting', () => {
  it('is off by default', () => {
    expect(store).toContain('const editModeWiggle = ref(false)')
  })

  it('gates the wiggle behind the setting, not just edit mode', () => {
    expect(grid).toContain('wiggle-buttons')
    expect(grid).toMatch(/wiggle-buttons.*editModeWiggle/)
    expect(grid).toContain('.deck-grid.wiggle-buttons .deck-button')
    // Edit mode alone must no longer animate buttons.
    expect(grid).not.toMatch(
      /\.deck-grid\.is-edit-mode\s+\.deck-button[^}]*animation/
    )
  })

  it('is persisted and synced like every other setting', () => {
    expect(store).toContain('editModeWiggle: editModeWiggle.value')
    expect(store).toContain('editModeWiggle.value = settings.editModeWiggle')
    expect(store).toContain('editModeWiggle: settings.editModeWiggle === true')
  })

  it('is exposed as a toggle in Settings', () => {
    expect(view).toContain('settings.editModeWiggle')
  })

  it('is allowlisted for server persistence', () => {
    const backend = readFileSync(
      resolve(__dirname, '../../../backend/routes/user_settings.py'),
      'utf-8'
    )
    expect(backend).toContain("'editModeWiggle'")
  })
})
