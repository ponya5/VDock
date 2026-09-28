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

  // Volume controls share row 0, transport controls share row 1 — grouping
  // by function (rather than the previous volume/play-pause/volume/transport
  // interleave) and ordering transport as Previous → Play/Pause → Next → Stop
  // reads the same way a physical remote's button row does.
  const buttons: Button[] = [
    makeButton({
      id: `btn-${Date.now()}-3`,
      label: 'Mute',
      icon: ['fas', 'volume-mute'],
      style: { backgroundColor: '#95a5a6', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cross_platform', config: { action: 'volume_mute' } },
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
      id: `btn-${Date.now()}-1`,
      label: 'Volume Up',
      icon: ['fas', 'volume-up'],
      style: { backgroundColor: '#27ae60', textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'cross_platform', config: { action: 'volume_up', step: 10 } },
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${Date.now()}-5`,
      label: 'Previous',
      icon: ['fas', 'step-backward'],
      style: { backgroundColor: '#8e44ad', textColor: '#ffffff', iconSize: 32 },
      layers: { behaviour: 'pulse' },
      action: { type: 'cross_platform', config: { action: 'media_previous' } },
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${Date.now()}-4`,
      label: 'Play/Pause',
      icon: ['fas', 'play'],
      style: { backgroundColor: '#9b59b6', textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'neon', tint: 'brand' } },
      action: { type: 'cross_platform', config: { action: 'media_play_pause' } },
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

const DEFAULT_SCENE_GRID = { rows: 3, cols: 5 }

function seedScene(
  ts: number,
  suffix: string,
  name: string,
  icon: string,
  color: string,
  buttons: Button[],
  gridConfig: { rows: number; cols: number } = DEFAULT_SCENE_GRID,
  appId?: string
): Scene {
  return {
    id: `scene-${ts}-${suffix}`,
    name,
    icon,
    color,
    appId,
    pages: [
      {
        id: `page-${ts}-${suffix}`,
        name: 'Page 1',
        buttons,
        grid_config: { ...gridConfig }
      }
    ],
    transition_style: 'light-bar',
    stagger_order: 'by-column'
  }
}

/**
 * "Claude Code" scene: open a session, then drive it. Every button after
 * "Open Claude" types into the live CLI window (cc_* keystroke actions), so
 * what you press is what you see happen in the session. No API key needed;
 * it's the user's own `claude` login.
 *
 * State-dependent actions (Submit, Continue, Interrupt, Approve/Deny) live in
 * the agent action bar above the grid, which swaps them as Claude's state
 * changes — the grid only holds what applies in any state.
 */
/**
 * A plain instruction rather than `/commit`: that slash command only exists
 * when a commit plugin is enabled, and otherwise Enter runs whichever command
 * autocomplete ranked first. Shared with the Cursor scene (DL-066) so
 * the two IDE decks stay textually identical wherever the same prompt applies.
 */
const COMMIT_PROMPT = 'Commit the current changes with a clear, descriptive commit message.'
const EXPLAIN_PROMPT = 'Explain what this code does:\n\n{clipboard}'
const WRITE_TESTS_PROMPT = 'Write tests for this code:\n\n{clipboard}'
const FIX_TESTS_PROMPT = 'The tests are failing. Find and fix the cause.'

export function createClaudeCodeScene(ts: number = Date.now()): Scene {
  const makeButton = seedButton(ts)
  const brand = '#D97757'
  const promptColor = '#7c5cd6'
  const livePrompt = (text: string): Button['action'] => ({ type: 'cc_prompt', config: { text } })
  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-c1`,
      label: 'Open Claude',
      icon: ['fas', 'window-maximize'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'claude_continue', config: { resume: true } },
      tooltip: 'Open a Claude Code session (resumes the last one when possible)',
      position: { row: 0, col: 0 }
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
      id: `btn-${ts}-c2`,
      label: 'Review',
      icon: ['fas', 'magnifying-glass'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt('/code-review'),
      secondary_label: '/code-review',
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-c3`,
      label: 'Commit',
      icon: ['fas', 'code-commit'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(COMMIT_PROMPT),
      secondary_label: 'git commit',
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-c5`,
      label: 'Explain',
      icon: ['fas', 'circle-question'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(EXPLAIN_PROMPT),
      tooltip: 'Asks the session to explain whatever is on the clipboard',
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-c6`,
      label: 'Write Tests',
      icon: ['fas', 'vial'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(WRITE_TESTS_PROMPT),
      tooltip: 'Asks the session to write tests for clipboard code',
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-c7`,
      label: 'Fix Tests',
      icon: ['fas', 'wrench'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(FIX_TESTS_PROMPT),
      position: { row: 1, col: 2 }
    })
  ]
  // appId stamped: scene→profile resolution relies on button command votes
  // alone otherwise, so deleting every button would orphan the agent bar
  // (and `appForScene` never consults votes, so the bundled wallpaper only
  // appears with a stamp). Same for the Cursor scene below.
  return seedScene(ts, 'claude', 'Claude Code', 'robot', brand, buttons, { rows: 2, cols: 4 }, 'claude-code')
}

/**
 * "Cursor" scene (DL-066): mirrors the Claude Code scene's shape —
 * one "open a session" button, then prompt buttons that type straight into
 * the live agent chat (`cursor_prompt`), plus the handful of direct editor
 * actions that aren't a chat message. Same 2×4 grid, same prompt texts as
 * Claude where the prompt is generic (Commit/Explain/Write Tests/Fix
 * Tests), so the two IDE decks read as one family instead of two different
 * button sets with two different grid densities.
 *
 * State-dependent actions (Submit, Continue/Stop, Accept, Reject) live in
 * the agent action bar above the grid — same split as Claude Code, driven
 * by the 'cursor' profile's `state_actions` (backend/integrations/keymaps/
 * cursor.py).
 */
function createCursorScene(ts: number = Date.now()): Scene {
  const makeButton = seedButton(ts)
  const brand = '#1f6fd1'
  const promptColor = '#7c5cd6'
  const livePrompt = (text: string): Button['action'] => ({ type: 'cursor_prompt', config: { text } })
  const buttons: Button[] = [
    makeButton({
      id: `btn-${ts}-u1`,
      label: 'New Agent',
      icon: ['fas', 'plus'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      layers: { effect: { type: 'glow', tint: 'brand' } },
      action: { type: 'cursor_new_chat', config: {} },
      tooltip: 'Open a new Cursor agent chat, input focused',
      position: { row: 0, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-u2`,
      label: 'Review',
      icon: ['fas', 'magnifying-glass'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt('Review this code for correctness, style, and potential bugs.'),
      position: { row: 0, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-u3`,
      label: 'Commit',
      icon: ['fas', 'code-commit'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(COMMIT_PROMPT),
      secondary_label: 'git commit',
      position: { row: 0, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-u4`,
      label: 'Inline Edit',
      icon: ['fas', 'pen-to-square'],
      style: { backgroundColor: brand, textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_inline_edit', config: {} },
      tooltip: 'Edit the current selection in place with AI (Ctrl+K)',
      position: { row: 0, col: 3 }
    }),
    makeButton({
      id: `btn-${ts}-u5`,
      label: 'Explain',
      icon: ['fas', 'circle-question'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(EXPLAIN_PROMPT),
      tooltip: 'Asks the session to explain whatever is on the clipboard',
      position: { row: 1, col: 0 }
    }),
    makeButton({
      id: `btn-${ts}-u6`,
      label: 'Write Tests',
      icon: ['fas', 'vial'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(WRITE_TESTS_PROMPT),
      tooltip: 'Asks the session to write tests for clipboard code',
      position: { row: 1, col: 1 }
    }),
    makeButton({
      id: `btn-${ts}-u7`,
      label: 'Fix Tests',
      icon: ['fas', 'wrench'],
      style: { backgroundColor: promptColor, textColor: '#ffffff', iconSize: 32 },
      action: livePrompt(FIX_TESTS_PROMPT),
      position: { row: 1, col: 2 }
    }),
    makeButton({
      id: `btn-${ts}-u8`,
      label: 'Terminal',
      icon: ['fas', 'terminal'],
      style: { backgroundColor: '#334155', textColor: '#ffffff', iconSize: 32 },
      action: { type: 'cursor_toggle_terminal', config: {} },
      position: { row: 1, col: 3 }
    })
  ]
  return seedScene(ts, 'cursor', 'Cursor', 'i-cursor', brand, buttons, { rows: 2, cols: 4 }, 'cursor')
}

/**
 * Factory-built IDE scenes that a user can restore in place via SceneEditor's
 * "Reset to Default" (DL-066 follow-up) — keyed by the scene name each
 * builder produces. A scene qualifies for the reset affordance purely by
 * name match; nothing else about a user's edited scene is inspected, so
 * renaming it opts back out (consistent with there being no other durable
 * link between a hand-editable scene and the factory template it came from).
 */
const FACTORY_IDE_SCENE_BUILDERS: Record<string, (ts?: number) => Scene> = {
  'Claude Code': createClaudeCodeScene,
  Cursor: createCursorScene
}

export function isFactoryIdeSceneName(name: string): boolean {
  return Object.prototype.hasOwnProperty.call(FACTORY_IDE_SCENE_BUILDERS, name)
}

export function createFactoryIdeScene(name: string): Scene | null {
  return FACTORY_IDE_SCENE_BUILDERS[name]?.() ?? null
}

/**
 * The exact action-type set the pre-DL-066-follow-up `createCursorScene`
 * shipped (Composer/Chat/Inline Edit/Palette/Accept/Reject/Terminal/Quick
 * Open, on the wrong 3x5 grid_config). Profiles created before that fix
 * still carry this scene verbatim — see `isUntouchedLegacyCursorScene`.
 */
const LEGACY_CURSOR_ACTION_TYPES = new Set([
  'cursor_composer', 'cursor_chat', 'cursor_inline_edit', 'cursor_command_palette',
  'cursor_accept', 'cursor_reject', 'cursor_toggle_terminal', 'cursor_quick_open'
])

/**
 * True only when a "Cursor" scene's buttons are *exactly* the untouched
 * pre-fix factory set — every legacy action type present, nothing else
 * added or removed. A user who kept even one of those buttons but added or
 * removed another has customised the scene, and this deliberately returns
 * false for it: silently overwriting a hand-edited scene on load would be
 * far worse than leaving one on the old layout. `setProfile` (dashboard
 * store) uses this to auto-upgrade only the untouched case; anyone who has
 * customised their Cursor scene keeps SceneEditor's explicit "Reset to
 * Default" as an opt-in path instead.
 */
export function isUntouchedLegacyCursorScene(scene: Scene): boolean {
  if (scene.name !== 'Cursor') return false
  const actionTypes = scene.pages.flatMap((page) => page.buttons.map((button) => button.action?.type))
  if (actionTypes.length !== LEGACY_CURSOR_ACTION_TYPES.size) return false
  return actionTypes.every((type) => type !== undefined && LEGACY_CURSOR_ACTION_TYPES.has(type))
}

/**
 * Untouched-legacy scene signatures (DL-100). `setProfile` prunes these once
 * per profile — only while `factorySeedsApplied` is absent, and only when the
 * scene is byte-identical to its legacy origin, so a customized scene (or a
 * freshly re-added "Claude" template on a marked profile) is never deleted.
 */

/** Pre-DL-047 default scene, when the factory deck was still named 'Home' —
 *  same media actions as today's Media scene on an older interleaved layout. */
const LEGACY_HOME_ACTIONS = [
  'volume_up', 'volume_down', 'volume_mute',
  'media_play_pause', 'media_previous', 'media_next', 'media_stop'
]

export function isLegacyHomeScene(scene: Scene): boolean {
  if (scene.name !== 'Home') return false
  const actions = scene.pages.flatMap((page) =>
    page.buttons.map((button) =>
      button.action?.type === 'cross_platform' ? button.action.config?.action : undefined
    )
  )
  return actions.length === LEGACY_HOME_ACTIONS.length
    && actions.every((action, index) => action === LEGACY_HOME_ACTIONS[index])
}

/** The AI Assistants "Claude" template applied as a scene — supplanted by the
 *  real Claude Code factory scene, which drives the live CLI instead of the
 *  web app's hotkeys. */
const LEGACY_CLAUDE_TEMPLATE_LABELS = [
  'New Chat', 'Open Claude', 'Projects', 'Upload File', 'Copy Last', 'Console', 'Docs'
]

export function isLegacyClaudeScene(scene: Scene): boolean {
  if (scene.name !== 'Claude' || scene.appId !== 'claude') return false
  const labels = scene.pages.flatMap((page) => page.buttons.map((button) => button.label))
  return labels.length === LEGACY_CLAUDE_TEMPLATE_LABELS.length
    && labels.every((label, index) => label === LEGACY_CLAUDE_TEMPLATE_LABELS[index])
}

/**
 * The non-Media factory scenes every profile should end up with (DL-079) —
 * ordered, one entry each. `createDefaultProfile` builds the first-run scene
 * list from this and `setProfile`'s backfill walks it to append whatever an
 * older profile never received, so the seed set has a single source of truth.
 * Media isn't listed: it's governed by the `isDefault` invariant instead.
 * DL-100: the out-of-box set is Media + Claude Code — Cursor stays reachable
 * via the template gallery and "Reset to Default" but is no longer seeded.
 */
export const FACTORY_SEED_SCENES: ReadonlyArray<{
  /** Stable key recorded in `profile.factorySeedsApplied`. */
  key: string
  /** A scene already carrying this name counts as present. */
  name: string
  build: (ts?: number) => Scene
}> = [
  { key: 'claude-code', name: 'Claude Code', build: createClaudeCodeScene },
]

/**
 * Creates a minimal default profile for first-time users, seeded with the
 * out-of-box scenes: Media and Claude Code (DL-100).
 */
export function createDefaultProfile(): Profile {
  const ts = Date.now()
  const profileId = `profile-${ts}`

  const profile: Profile = {
    id: profileId,
    name: 'My VDock',
    description: 'Media controls and Claude Code actions to get you started.',
    scenes: [createDefaultScene(), ...FACTORY_SEED_SCENES.map((seed) => seed.build(ts))],
    // Stamped so a brand-new profile never enters setProfile's one-time
    // legacy-scene prune — every seed it will ever need is already present.
    factorySeedsApplied: FACTORY_SEED_SCENES.map((seed) => seed.key),
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
