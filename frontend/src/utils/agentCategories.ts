import type { Button, Scene } from '@/types'

/**
 * DL-166: categories for the buttons of an AI coding scene (Claude Code,
 * Cursor, Codex, Antigravity, Devin). The set is fixed and ordered; ids are
 * what gets persisted in `Button.category`. A button with no override is
 * placed by `resolveButtonCategory`, so scenes created before this feature
 * group sensibly with no migration.
 */

export type AgentCategoryId =
  | 'session' | 'prompts' | 'review' | 'control' | 'context' | 'tools' | 'links' | 'other'

export interface AgentCategoryDef {
  id: AgentCategoryId
  label: string
  /** FontAwesome solid icon name. */
  icon: string
}

export const AGENT_CATEGORIES: readonly AgentCategoryDef[] = [
  { id: 'session', label: 'Session', icon: 'circle-play' },
  { id: 'prompts', label: 'Ask & Edit', icon: 'comment-dots' },
  { id: 'review', label: 'Review & Ship', icon: 'code-pull-request' },
  { id: 'control', label: 'Mode & Model', icon: 'sliders' },
  { id: 'context', label: 'Context', icon: 'layer-group' },
  { id: 'tools', label: 'Editor & Tools', icon: 'toolbox' },
  { id: 'links', label: 'Links', icon: 'arrow-up-right-from-square' },
  { id: 'other', label: 'Other', icon: 'ellipsis' },
]

export interface CategoryGroup extends AgentCategoryDef {
  buttons: Button[]
}

const CATEGORY_IDS = new Set<string>(AGENT_CATEGORIES.map(c => c.id))

export function isAgentCategoryId(value: unknown): value is AgentCategoryId {
  return typeof value === 'string' && CATEGORY_IDS.has(value)
}

export function agentCategoryDef(id: AgentCategoryId): AgentCategoryDef {
  return AGENT_CATEGORIES.find(c => c.id === id) ?? AGENT_CATEGORIES[AGENT_CATEGORIES.length - 1]
}

/** Page navigation means nothing on a surface without pages. */
export const PAGE_NAVIGATION_ACTIONS = new Set(['next_page', 'previous_page', 'home_page', 'goto_page'])

function list(ids: string, category: AgentCategoryId): Array<[string, AgentCategoryId]> {
  return ids.split(/\s+/).filter(Boolean).map(id => [id, category])
}

export const ACTION_TYPE_CATEGORY: Readonly<Record<string, AgentCategoryId>> = Object.fromEntries([
  ...list(`claude_continue cc_submit cc_interrupt cc_queue cc_resume cc_rewind cc_background
    cc_cancel cc_accept cc_approve cc_deny cc_nav_up cc_nav_down cc_newline cc_stash cc_undo
    cc_kill_agents cc_exit cursor_new_chat cursor_submit cursor_cancel codex_interrupt
    codex_submit codex_approve codex_deny codex_exit antigravity_new_thread antigravity_submit
    antigravity_stop devin_interrupt devin_submit devin_exit`, 'session'),
  ...list(`cursor_chat cursor_composer cursor_composer_full cursor_inline_edit antigravity_agent
    antigravity_inline cc_editor cc_paste_image cc_bash claude_api_prompt`, 'prompts'),
  ...list('cursor_accept cursor_reject cc_diff', 'review'),
  ...list('cc_mode cc_model cc_thinking cc_effort cc_fast cc_permissions codex_approvals', 'control'),
  ...list(`cc_clear cc_compact codex_compact cc_add_file cc_todos cc_transcript cc_memory
    cc_tasks cc_agents cc_history cc_help`, 'context'),
  ...list(`cursor_toggle_terminal cursor_command_palette cursor_quick_open cursor_toggle_sidebar
    cursor_find_in_files antigravity_toggle_terminal antigravity_command_palette
    antigravity_quick_open antigravity_toggle_sidebar antigravity_find_in_files
    antigravity_manager antigravity_settings cc_scroll_up cc_scroll_down cc_redraw devin_help
    devin_bug hotkey macro`, 'tools'),
  ...list('url claude_open', 'links'),
])

const PROMPT_ACTIONS = new Set([
  'cc_prompt', 'cursor_prompt', 'cursor_followup', 'claude_prompt', 'claude_slash',
  'codex_prompt', 'antigravity_prompt', 'antigravity_followup', 'devin_prompt',
])

const AGENT_APP = /claude|cursor|antigravity|codex|devin/i

function configText(config: Record<string, unknown> | undefined, ...keys: string[]): string {
  for (const key of keys) {
    const value = config?.[key]
    if (typeof value === 'string') return value
  }
  return ''
}

function resolvePrompt(button: Button): AgentCategoryId {
  const config = button.action?.config as Record<string, unknown> | undefined
  const text = configText(config, 'text', 'prompt', 'command')
  if (!text.trim() || /^\s*continue\b/i.test(text)) return 'session'
  if (/^\s*\/(clear|compact)\b/i.test(text)) return 'context'
  if (/^\s*\/(resume|rewind)\b/i.test(text)) return 'session'
  if (/^\s*\/(model|mode|effort|permissions|config)\b/i.test(text)) return 'control'
  if (/^\s*\/(memory|todos|agents|context)\b/i.test(text)) return 'context'
  const haystack = `${text} ${button.secondary_label ?? ''} ${button.label ?? ''}`
  if (/review|diff|commit|pull request|\bPR\b|push|deploy|release|merge|changelog/i.test(haystack)) return 'review'
  return 'prompts'
}

function resolveShellCommand(command: string): AgentCategoryId {
  if (/review|diff|commit|\bpr\b|push|deploy|release/i.test(command)) return 'review'
  if (/approval-mode|--model|\s-q\b|--quiet/i.test(command)) return 'control'
  if (/^\s*(claude|codex|devin)(\s+resume|\s+--continue|\s+-c)?\s*$/i.test(command)) return 'session'
  return 'tools'
}

/** Which category a button belongs to: explicit override, else inferred from its action. */
export function resolveButtonCategory(button: Button): AgentCategoryId {
  if (isAgentCategoryId(button.category)) return button.category
  const type = button.action?.type ?? ''
  const config = button.action?.config as Record<string, unknown> | undefined

  const mapped = ACTION_TYPE_CATEGORY[type]
  if (mapped) return mapped
  if (type.startsWith('gh_')) return 'review'
  if (type.startsWith('metric_') || type.startsWith('time_')) return 'tools'

  if (PROMPT_ACTIONS.has(type)) return resolvePrompt(button)

  if (type === 'command') return resolveShellCommand(configText(config, 'command'))
  if (type === 'cross_platform') {
    const action = configText(config, 'action')
    if (action === 'run_command') return resolveShellCommand(configText(config, 'command'))
    if (action === 'open_app') return AGENT_APP.test(configText(config, 'path', 'app', 'name')) ? 'session' : 'tools'
  }
  if (type === 'program') return AGENT_APP.test(configText(config, 'path', 'app', 'name')) ? 'session' : 'tools'
  return 'other'
}

/** The buttons of a scene that a category view can show, in page / row / column reading order. */
export function sceneCategoryButtons(scene: Scene | null | undefined): Button[] {
  const out: Button[] = []
  for (const page of scene?.pages ?? []) {
    const sorted = [...page.buttons].sort((a, b) =>
      a.position.row - b.position.row || a.position.col - b.position.col)
    for (const button of sorted) {
      if (button.enabled === false || !button.action) continue
      if (PAGE_NAVIGATION_ACTIONS.has(button.action.type)) continue
      out.push(button)
    }
  }
  return out
}

/** Non-empty category groups of a scene, in the fixed category order. */
export function groupSceneButtons(scene: Scene | null | undefined): CategoryGroup[] {
  const buckets = new Map<AgentCategoryId, Button[]>()
  for (const button of sceneCategoryButtons(scene)) {
    const id = resolveButtonCategory(button)
    buckets.set(id, [...(buckets.get(id) ?? []), button])
  }
  return AGENT_CATEGORIES
    .filter(def => buckets.has(def.id))
    .map(def => ({ ...def, buttons: buckets.get(def.id)! }))
}
