import type { Profile, Scene, Page, Button } from '@/types'

/**
 * Creates the factory-default scene: volume and playback controls, styled with the
 * button effects/overlay system so the redesign is visible from the start. Every
 * profile has exactly one scene built from this function, flagged `isDefault: true`.
 * Reused for first-run profile bootstrap, existing-profile migration, and
 * "Reset to Default" (see dashboard store's `resetScene`) — all three must produce
 * the same layout, so this is the single source of truth for it.
 */
export function createDefaultScene(): Scene {
  const sceneId = `scene-${Date.now()}`
  const pageId = `page-${Date.now()}`

  function makeButton(overrides: Partial<Button> & Pick<Button, 'id' | 'label' | 'position'>): Button {
    return {
      shape: 'rounded',
      size: { rows: 1, cols: 1 },
      icon_type: 'fontawesome',
      enabled: true,
      ...overrides
    }
  }

  const buttons: Button[] = [
    makeButton({
      id: `btn-${Date.now()}-1`,
      label: 'Volume Up',
      icon: ['fas', 'volume-up'],
      style: { backgroundColor: '#27ae60', textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'cross_platform', config: { action: 'volume_up', step: 10 } },
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${Date.now()}-2`,
      label: 'Volume Down',
      icon: ['fas', 'volume-down'],
      style: { backgroundColor: '#e74c3c', textColor: '#ffffff', iconSize: 32 },
      layers: { behaviour: 'float' },
      action: { type: 'cross_platform', config: { action: 'volume_down', step: 10 } },
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${Date.now()}-3`,
      label: 'Mute',
      icon: ['fas', 'volume-mute'],
      style: { backgroundColor: '#95a5a6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cross_platform', config: { action: 'volume_mute' } },
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${Date.now()}-4`,
      label: 'Play/Pause',
      icon: ['fas', 'play'],
      style: { backgroundColor: '#9b59b6', textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'neon', tint: 'brand' } },
      action: { type: 'cross_platform', config: { action: 'media_play_pause' } },
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${Date.now()}-5`,
      label: 'Previous',
      icon: ['fas', 'step-backward'],
      style: { backgroundColor: '#8e44ad', textColor: '#ffffff', iconSize: 32 },
      layers: { behaviour: 'pulse' },
      action: { type: 'cross_platform', config: { action: 'media_previous' } },
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${Date.now()}-6`,
      label: 'Next',
      icon: ['fas', 'step-forward'],
      style: { backgroundColor: '#8e44ad', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cross_platform', config: { action: 'media_next' } },
      position: { row: 1, col: 2 }
    }),
    makeButton({
      id: `btn-${Date.now()}-7`,
      label: 'Stop',
      icon: ['fas', 'stop'],
      style: { backgroundColor: '#c0392b', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cross_platform', config: { action: 'media_stop' } },
      position: { row: 1, col: 3 }
    })
  ]

  const page: Page = {
    id: pageId,
    name: 'Page 1',
    buttons,
    grid_config: { rows: 3, cols: 5 }
  }

  return {
    id: sceneId,
    name: 'Home',
    icon: 'house',
    color: '#3498db',
    pages: [page],
    isActive: true,
    isDefault: true,
    buttonSize: 1.0,
    overlay_style: 'light-sweep',
    transition_style: 'light-bar',
    stagger_order: 'by-column'
  }
}

/**
 * Creates a minimal default profile for first-time users, seeded with the factory
 * default scene (see `createDefaultScene`).
 */
export function createDefaultProfile(): Profile {
  const profileId = `profile-${Date.now()}`

  const profile: Profile = {
    id: profileId,
    name: 'My VDock',
    description: 'Volume and playback controls to get you started.',
    scenes: [createDefaultScene()],
    dockedButtons: [],
    theme: 'default',
    settings: {
      animationsEnabled: true,
      showLabels: true,
      showTooltips: true,
      defaultGridRows: 3,
      defaultGridCols: 3,
      buttonSize: 1.0
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  return profile
}
