/**
 * DL-165: the shortcut a template key really sends, shown under its name - derived from the action itself
 * (hotkeys) or from the "(Ctrl+L)" / "/clear - ..." the template author wrote in the tooltip. Windows key names.
 */
const IS_MAC = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || '')
const KEY_NAMES: Record<string, string> = {
  mod: IS_MAC ? 'Cmd' : 'Ctrl', // the OS-neutral primary modifier
  escape: 'Esc', esc: 'Esc', enter: 'Enter', ctrl: 'Ctrl', shift: 'Shift', alt: 'Alt', tab: 'Tab',
  backspace: 'Backspace', delete: 'Del', space: 'Space', win: 'Win', cmd: 'Cmd',
}

export function formatKeys(keys: readonly string[]): string {
  return keys.map((k) => KEY_NAMES[k.toLowerCase()] ?? (k.length <= 2 ? k.toUpperCase() : k[0].toUpperCase() + k.slice(1))).join('+')
}

const CHORD = /\b(Ctrl|Alt|Shift|Cmd|Win|Esc|Enter|Tab|Backspace|F\d{1,2})\b/

export function templateShortcut(b: {
  action?: { type?: string; config?: Record<string, unknown> }
  tooltip?: string
  secondary?: string
}): string {
  if (b.secondary) return b.secondary
  const a = b.action
  if (a?.type === 'hotkey') {
    const keys = a.config?.keys
    if (Array.isArray(keys) && keys.length) return formatKeys(keys.map(String))
  }
  const tip = b.tooltip ?? ''
  const slash = tip.match(/^(\/[a-z][a-z-]*)/)
  if (slash) return slash[1]
  const paren = tip.match(/\(([^()]+)\)\s*$/)
  if (paren && CHORD.test(paren[1])) return paren[1].trim()
  return ''
}
