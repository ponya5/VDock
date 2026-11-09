/**
 * DL-165: which button presses touch shared code (push, commit, merge, deploy ...)
 * and deserve an "Are you sure?" first - the way Claude Code asks before it pushes.
 * Pure: the caller decides whether the user turned the prompt on.
 */
import type { Button } from '@/types'

export interface CodeActionRisk {
  title: string
  message: string
  /** Red confirm button: pushes and history rewrites cannot be taken back with one click. */
  danger: boolean
}

const PUSH = /\bgit\s+push\b|\bforce[-\s]?push\b|\bpush\s+--force\b/i
const REWRITE = /\bgit\s+(reset\s+--hard|clean\s+-\w*f|branch\s+-D|rebase)\b|\bcheckout\s+--\s/i
const SHIP = /\b(commit\s*(and|&|\+)\s*push|push\s+(it|this|the|my|all|these|changes|commits?|to|origin|upstream|branch)|merge\s+(the\s+|this\s+)?(pr|pull request)|deploy|publish|release)\b/i
/** Action families that work on code: agents, editors, GitHub, terminals, raw keys/text. */
const CODE_TYPE = /^(cc_|cursor|claude|copilot|vscode|jetbrains|vs_|gh_|github|antigravity|devin|git|dev_|command|terminal|text|hotkey|agent)/i
const LABEL = /\b(git\s+)?push\b|\bcommit\b|\bmerge\b|\bdeploy\b|\bpublish\b|\brelease\b|\bforce\b/i

function configText(config: unknown): string {
  try { return JSON.stringify(config ?? {}) } catch { return '' }
}

export function codeActionRisk(button: Pick<Button, 'label' | 'action'>): CodeActionRisk | null {
  const action = button.action
  if (!action?.type) return null
  const type = String(action.type)
  const text = configText(action.config)
  const label = button.label ?? ''
  const name = label ? `"${label}"` : 'This button'

  if (PUSH.test(text) || PUSH.test(label)) {
    return { title: `Push code?`, message: `${name} pushes your commits to the remote. Make sure the right branch is checked out and the work is ready.`, danger: true }
  }
  if (REWRITE.test(text)) {
    return { title: `Rewrite history?`, message: `${name} can discard local changes or rewrite history. This is hard to undo.`, danger: true }
  }
  if (CODE_TYPE.test(type) && SHIP.test(text)) {
    return { title: `Ship code?`, message: `${name} commits, merges or publishes code. Run it?`, danger: false }
  }
  if (CODE_TYPE.test(type) && LABEL.test(label)) {
    return { title: `Run ${name}?`, message: `${name} acts on your code (push, commit, merge or deploy). Run it?`, danger: false }
  }
  return null
}
