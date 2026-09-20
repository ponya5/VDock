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

function seedButton(ts: number) {
  return function makeButton(
    overrides: Partial<Button> & Pick<Button, 'id' | 'label' | 'position'>
  ): Button {
    return {
      shape: 'rounded',
      size: { rows: 1, cols: 1 },
      icon_type: 'fontawesome',
      enabled: true,
      ...overrides
    }
  }
}

/**
 * "AI Assistant" scene for new profiles: one-tap access to the free web
 * chatbots plus clipboard helpers so prompts can be moved in/out quickly.
 * Uses only `url`/`hotkey`/`cross_platform` actions — no API keys needed.
 */
function createAiAssistantScene(ts: number): Scene {
  const makeButton = seedButton(ts)

  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-a1`,
      label: 'Claude',
      icon: ['fas', 'robot'],
      style: { backgroundColor: '#d97757', textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'url', config: { url: 'https://claude.ai' } },
      tooltip: 'Open Claude in your browser',
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-a2`,
      label: 'ChatGPT',
      icon: ['fas', 'comment-dots'],
      style: { backgroundColor: '#10a37f', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'url', config: { url: 'https://chatgpt.com' } },
      tooltip: 'Open ChatGPT in your browser',
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-a3`,
      label: 'Gemini',
      icon: ['fas', 'star'],
      style: { backgroundColor: '#1a73e8', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'url', config: { url: 'https://gemini.google.com' } },
      tooltip: 'Open Gemini in your browser',
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-a4`,
      label: 'Perplexity',
      icon: ['fas', 'magnifying-glass'],
      style: { backgroundColor: '#20b8cd', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'url', config: { url: 'https://www.perplexity.ai' } },
      tooltip: 'Open Perplexity in your browser',
      position: { row: 0, col: 3 }
    }),
    makeButton({
      id: `btn-${ts}-a5`,
      label: 'Copy',
      icon: ['fas', 'copy'],
      style: { backgroundColor: '#6366f1', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['ctrl', 'c'] } },
      tooltip: 'Copy selection — grab text to paste into a chat',
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-a6`,
      label: 'Paste',
      icon: ['fas', 'paste'],
      style: { backgroundColor: '#6366f1', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['ctrl', 'v'] } },
      tooltip: 'Paste into the focused field',
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-a7`,
      label: 'Screenshot',
      icon: ['fas', 'camera'],
      style: { backgroundColor: '#f59e0b', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['win', 'shift', 's'] } },
      tooltip: 'Capture a region — paste it into a chat for vision models',
      position: { row: 1, col: 2 }
    })
  ]

  return {
    id: `scene-${ts}-ai`,
    name: 'AI Assistant',
    icon: 'robot',
    color: '#8b5cf6',
    pages: [
      {
        id: `page-${ts}-ai`,
        name: 'Page 1',
        buttons,
        grid_config: { rows: 3, cols: 5 }
      }
    ],
    transition_style: 'light-bar',
    stagger_order: 'by-column'
  }
}

/**
 * "Tools" scene for new profiles: everyday system/productivity hotkeys —
 * lock, fullscreen, terminal, undo/redo — all key- or shell-level actions
 * that work on a stock Windows install without extra configuration.
 */
function createToolsScene(ts: number): Scene {
  const makeButton = seedButton(ts)

  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-t1`,
      label: 'Lock',
      icon: ['fas', 'lock'],
      style: { backgroundColor: '#ef4444', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['win', 'l'] } },
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-t2`,
      label: 'Screenshot',
      icon: ['fas', 'camera'],
      style: { backgroundColor: '#f59e0b', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['win', 'shift', 's'] } },
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-t3`,
      label: 'Fullscreen',
      icon: ['fas', 'expand'],
      style: { backgroundColor: '#0ea5e9', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['f11'] } },
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-t4`,
      label: 'Terminal',
      icon: ['fas', 'terminal'],
      style: { backgroundColor: '#1e293b', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cross_platform', config: { action: 'open_app', app: 'wt' } },
      tooltip: 'Open Windows Terminal',
      position: { row: 0, col: 3 }
    }),
    makeButton({
      id: `btn-${ts}-t5`,
      label: 'Undo',
      icon: ['fas', 'rotate-left'],
      style: { backgroundColor: '#8b5cf6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['ctrl', 'z'] } },
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-t6`,
      label: 'Redo',
      icon: ['fas', 'rotate-right'],
      style: { backgroundColor: '#8b5cf6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['ctrl', 'y'] } },
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-t7`,
      label: 'Task View',
      icon: ['fas', 'table-cells-large'],
      style: { backgroundColor: '#64748b', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'hotkey', config: { keys: ['win', 'tab'] } },
      position: { row: 1, col: 2 }
    })
  ]

  return {
    id: `scene-${ts}-tools`,
    name: 'Tools',
    icon: 'toolbox',
    color: '#f59e0b',
    pages: [
      {
        id: `page-${ts}-tools`,
        name: 'Page 1',
        buttons,
        grid_config: { rows: 3, cols: 5 }
      }
    ],
    transition_style: 'light-bar',
    stagger_order: 'by-column'
  }
}

/**
 * Creates a minimal default profile for first-time users, seeded with the factory
 * default scene (see `createDefaultScene`).
 */
export function createDefaultProfile(): Profile {
  const ts = Date.now()
  const profileId = `profile-${ts}`

  const profile: Profile = {
    id: profileId,
    name: 'My VDock',
    description: 'Media controls, AI assistant shortcuts, and everyday tools to get you started.',
    scenes: [createDefaultScene(), createAiAssistantScene(ts), createToolsScene(ts)],
    dockedButtons: [],
    theme: 'default',
    settings: {
      animationsEnabled: true,
      editModeWiggle: false,
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
