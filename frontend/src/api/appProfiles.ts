import apiClient from '@/api/client'

export interface AppCommandDto {
  id: string
  label: string
  description: string
  keys: string[]
  icon: string
  keywords: string[]
  category: string
  priority: number
  risk: 'safe' | 'input' | 'destructive'
  requires_session: boolean
}

export interface AppProfileDto {
  id: string
  label: string
  exes: string[]
  kind: 'editor' | 'terminal_agent'
  status_source: string | null
  default_layout: string[][]
  commands: AppCommandDto[]
}

/** A command rendered as a plain hotkey shortcut, for shortcut-browsing UI. */
export interface AppShortcut {
  name: string
  keys: string[]
  description: string
  category: string
  priority?: number
}

/**
 * App profiles from the backend.
 *
 * This replaces data/appShortcuts.ts. That file duplicated the backend keymaps
 * and had already drifted from them; one source of truth is the whole point.
 */
export async function fetchAppProfiles(): Promise<AppProfileDto[]> {
  const { data } = await apiClient.get('/app-profiles')
  return data.profiles ?? []
}

/** Commands for a process name, highest priority first. */
export function shortcutsForExe(
  profiles: AppProfileDto[],
  exe: string,
): AppCommandDto[] {
  if (!exe) return []
  const needle = exe.toLowerCase()
  const profile = profiles.find(p => p.exes.some(e => e.toLowerCase() === needle))
  if (!profile) return []

  return [...profile.commands].sort(
    (a, b) => b.priority - a.priority || a.label.localeCompare(b.label),
  )
}

function toAppShortcut(command: AppCommandDto): AppShortcut {
  return {
    name: command.label,
    keys: command.keys,
    description: command.description,
    category: command.category,
    priority: command.priority,
  }
}

/** True when any profile knows commands for this process name. */
export function hasAppShortcuts(profiles: AppProfileDto[], exe: string): boolean {
  return shortcutsForExe(profiles, exe).length > 0
}

/** The top `count` commands for a process name, as display shortcuts. */
export function topAppShortcuts(
  profiles: AppProfileDto[],
  exe: string,
  count = 8,
): AppShortcut[] {
  return shortcutsForExe(profiles, exe).slice(0, count).map(toAppShortcut)
}

/** All commands for a process name, as display shortcuts. */
export function appShortcutsForExe(profiles: AppProfileDto[], exe: string): AppShortcut[] {
  return shortcutsForExe(profiles, exe).map(toAppShortcut)
}

/** The profile's display label for a process name, or the exe with its extension stripped. */
export function appLabelForExe(profiles: AppProfileDto[], exe: string): string {
  const needle = exe.toLowerCase()
  const profile = profiles.find(p => p.exes.some(e => e.toLowerCase() === needle))
  return profile?.label ?? exe.replace('.exe', '')
}
