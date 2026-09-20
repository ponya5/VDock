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
    name: 'Media',
    icon: 'music',
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

function seedScene(ts: number, suffix: string, name: string, icon: string, color: string, buttons: Button[]): Scene {
  return {
    id: `scene-${ts}-${suffix}`,
    name,
    icon,
    color,
    pages: [
      {
        id: `page-${ts}-${suffix}`,
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
 * "Claude Code" scene: the most useful actions from the dev-claude-code
 * template — session resume, slash commands, clipboard prompts. No API key
 * needed; actions drive the user's own `claude` login.
 */
function createClaudeCodeScene(ts: number): Scene {
  const makeButton = seedButton(ts)
  const brand = '#D97757'
  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-c1`,
      label: 'Open Claude',
      icon: ['fas', 'window-maximize'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'claude_continue', config: { resume: true } },
      tooltip: 'Resume the last Claude Code session',
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-c2`,
      label: 'Review',
      icon: ['fas', 'magnifying-glass'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_slash', config: { command: '/code-review', output: 'notify' } },
      secondary_label: '/code-review',
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-c3`,
      label: 'Commit',
      icon: ['fas', 'code-commit'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_slash', config: { command: '/commit', output: 'notify' } },
      secondary_label: '/commit',
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-c4`,
      label: 'claude.ai',
      icon: ['fas', 'globe'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_open', config: { target: 'new_chat' } },
      tooltip: 'Open a new chat on claude.ai',
      position: { row: 0, col: 3 }
    }),
    makeButton({
      id: `btn-${ts}-c5`,
      label: 'Explain',
      icon: ['fas', 'circle-question'],
      style: { backgroundColor: '#7c5cd6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_prompt', config: { prompt: 'Explain what this code does:\n\n{clipboard}', output: 'both' } },
      tooltip: 'Explains whatever is on the clipboard',
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-c6`,
      label: 'Write Tests',
      icon: ['fas', 'vial'],
      style: { backgroundColor: '#7c5cd6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_prompt', config: { prompt: 'Write tests for this code:\n\n{clipboard}', output: 'both' } },
      tooltip: 'Generates tests for clipboard code',
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-c7`,
      label: 'Fix Tests',
      icon: ['fas', 'wrench'],
      style: { backgroundColor: '#7c5cd6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_prompt', config: { prompt: 'The tests are failing. Find and fix the cause.', output: 'notify' } },
      position: { row: 1, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-c8`,
      label: 'Continue',
      icon: ['fas', 'forward'],
      style: { backgroundColor: '#7c5cd6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'claude_prompt', config: { prompt: 'continue', continue_session: true } },
      tooltip: 'Send "continue" to the running session',
      position: { row: 1, col: 3 }
    })
  ]
  return seedScene(ts, 'claude', 'Claude Code', 'robot', brand, buttons)
}

/**
 * "Cursor" scene: the composer/chat/inline-edit action set from the
 * dev-cursor-ai template — one-tap AI editing controls.
 */
function createCursorScene(ts: number): Scene {
  const makeButton = seedButton(ts)
  const brand = '#1f6fd1'
  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-u1`,
      label: 'Composer',
      icon: ['fas', 'wand-magic-sparkles'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'cursor_composer', config: {} },
      tooltip: 'Open Cursor Composer',
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-u2`,
      label: 'Chat',
      icon: ['fas', 'comments'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_chat', config: {} },
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-u3`,
      label: 'Inline Edit',
      icon: ['fas', 'pen-to-square'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_inline_edit', config: {} },
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-u4`,
      label: 'Palette',
      icon: ['fas', 'terminal'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_command_palette', config: {} },
      tooltip: 'Command palette',
      position: { row: 0, col: 3 }
    }),
    makeButton({
      id: `btn-${ts}-u5`,
      label: 'Accept',
      icon: ['fas', 'check'],
      style: { backgroundColor: '#16a34a', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_accept', config: {} },
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-u6`,
      label: 'Reject',
      icon: ['fas', 'xmark'],
      style: { backgroundColor: '#dc2626', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_reject', config: {} },
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-u7`,
      label: 'Terminal',
      icon: ['fas', 'square-terminal'],
      style: { backgroundColor: '#334155', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_toggle_terminal', config: {} },
      position: { row: 1, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-u8`,
      label: 'Quick Open',
      icon: ['fas', 'file-circle-plus'],
      style: { backgroundColor: '#334155', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_quick_open', config: {} },
      position: { row: 1, col: 3 }
    })
  ]
  return seedScene(ts, 'cursor', 'Cursor', 'i-cursor', brand, buttons)
}

/**
 * "Websites" scene: generic, globally-known sites only — nothing
 * region- or user-specific ships in the default profile.
 */
function createWebsitesScene(ts: number): Scene {
  const makeButton = seedButton(ts)
  const site = (id: string, label: string, icon: string[], color: string, url: string, row: number, col: number) =>
    makeButton({
      id: `btn-${ts}-${id}`,
      label,
      icon: icon as [string, string],
      style: { backgroundColor: color, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'url', config: { url } },
      position: { row, col }
    })

  const buttons: Button[] = [
    site('w1', 'YouTube', ['fab', 'youtube'], '#ff0000', 'https://www.youtube.com', 0, 0),
    site('w2', 'Google', ['fab', 'google'], '#4285f4', 'https://www.google.com', 0, 1),
    site('w3', 'GitHub', ['fab', 'github'], '#24292f', 'https://github.com', 0, 2),
    site('w4', 'Gmail', ['fas', 'envelope'], '#ea4335', 'https://mail.google.com', 0, 3),
    site('w5', 'Reddit', ['fab', 'reddit-alien'], '#ff4500', 'https://www.reddit.com', 1, 0),
    site('w6', 'Stack Overflow', ['fab', 'stack-overflow'], '#f48024', 'https://stackoverflow.com', 1, 1),
    site('w7', 'Wikipedia', ['fab', 'wikipedia-w'], '#636466', 'https://www.wikipedia.org', 1, 2),
    site('w8', 'Discord', ['fab', 'discord'], '#5865f2', 'https://discord.com/app', 1, 3)
  ]
  return seedScene(ts, 'websites', 'Websites', 'globe', '#0ea5e9', buttons)
}

/**
 * Creates a minimal default profile for first-time users, seeded with the
 * out-of-box scenes: Media, Claude Code, Cursor, Websites.
 */
export function createDefaultProfile(): Profile {
  const ts = Date.now()
  const profileId = `profile-${ts}`

  const profile: Profile = {
    id: profileId,
    name: 'My VDock',
    description: 'Media controls, Claude Code and Cursor actions, and quick website links to get you started.',
    scenes: [createDefaultScene(), createClaudeCodeScene(ts), createCursorScene(ts), createWebsitesScene(ts)],
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
