// Shortcut suggestions for apps outside VDock's IDE/agent keymap system.
//
// Cursor and VS Code (Copilot) shortcuts moved to the backend keymaps package
// and are served over /api/app-profiles (see api/appProfiles.ts) — that is
// what phase 1 of the IDE agent control workstream consolidated. Chrome,
// Discord and OBS were never part of that duplication: they have no backend
// Command definitions and nothing to drift against. Deleting them along with
// the old appShortcuts.ts would have silently dropped shortcut-browsing and
// scene auto-populate for these apps, so they stay here as a plain, static
// database until (if ever) a future phase gives them real profiles.

export interface MiscAppShortcut {
  name: string
  keys: string[]
  description: string
  category: string
  priority?: number
}

export interface MiscAppShortcutDatabase {
  appExe: string
  appName: string
  shortcuts: MiscAppShortcut[]
}

export const MISC_APP_SHORTCUTS: readonly MiscAppShortcutDatabase[] = [
  {
    appExe: 'chrome.exe',
    appName: 'Google Chrome',
    shortcuts: [
      { name: 'New Tab', keys: ['Ctrl', 'T'], description: 'Open new tab', category: 'general', priority: 10 },
      { name: 'New Window', keys: ['Ctrl', 'N'], description: 'Open new window', category: 'general', priority: 8 },
      { name: 'New Incognito', keys: ['Ctrl', 'Shift', 'N'], description: 'Open incognito window', category: 'general', priority: 9 },
      { name: 'Close Tab', keys: ['Ctrl', 'W'], description: 'Close current tab', category: 'general', priority: 8 },
      { name: 'Reopen Tab', keys: ['Ctrl', 'Shift', 'T'], description: 'Reopen last closed tab', category: 'general', priority: 9 },
      { name: 'DevTools', keys: ['F12'], description: 'Open developer tools', category: 'debug', priority: 9 },
      { name: 'Refresh', keys: ['Ctrl', 'R'], description: 'Refresh page', category: 'general', priority: 8 },
      { name: 'Hard Refresh', keys: ['Ctrl', 'Shift', 'R'], description: 'Hard refresh (clear cache)', category: 'general', priority: 7 },
      { name: 'Find in Page', keys: ['Ctrl', 'F'], description: 'Find in current page', category: 'search', priority: 8 },
      { name: 'Address Bar', keys: ['Ctrl', 'L'], description: 'Focus address bar', category: 'navigation', priority: 8 },
      { name: 'Downloads', keys: ['Ctrl', 'J'], description: 'Open downloads', category: 'general', priority: 6 },
      { name: 'History', keys: ['Ctrl', 'H'], description: 'Open history', category: 'general', priority: 6 },
      { name: 'Bookmarks', keys: ['Ctrl', 'Shift', 'B'], description: 'Toggle bookmarks bar', category: 'general', priority: 6 },
    ],
  },
  {
    appExe: 'Discord.exe',
    appName: 'Discord',
    shortcuts: [
      { name: 'Mark as Read', keys: ['Esc'], description: 'Mark server/channel as read', category: 'general', priority: 8 },
      { name: 'Search', keys: ['Ctrl', 'K'], description: 'Quick search', category: 'search', priority: 10 },
      { name: 'Toggle Mute', keys: ['Ctrl', 'Shift', 'M'], description: 'Toggle mute', category: 'general', priority: 9 },
      { name: 'Toggle Deafen', keys: ['Ctrl', 'Shift', 'D'], description: 'Toggle deafen', category: 'general', priority: 8 },
      { name: 'Answer Call', keys: ['Ctrl', 'Enter'], description: 'Answer incoming call', category: 'general', priority: 7 },
      { name: 'Start Call', keys: ['Ctrl', "'"], description: 'Start voice call', category: 'general', priority: 7 },
      { name: 'Create/Join Server', keys: ['Ctrl', 'Shift', 'N'], description: 'Create or join server', category: 'general', priority: 6 },
      { name: 'Upload File', keys: ['Ctrl', 'Shift', 'U'], description: 'Upload file', category: 'general', priority: 7 },
      { name: 'Pin Message', keys: ['Ctrl', 'Shift', 'P'], description: 'Pin message', category: 'general', priority: 5 },
    ],
  },
  {
    appExe: 'obs64.exe',
    appName: 'OBS Studio',
    shortcuts: [
      { name: 'Start Recording', keys: ['Ctrl', 'Shift', 'R'], description: 'Start/stop recording', category: 'general', priority: 10 },
      { name: 'Start Streaming', keys: ['Ctrl', 'Shift', 'S'], description: 'Start/stop streaming', category: 'general', priority: 10 },
      { name: 'Pause Recording', keys: ['Ctrl', 'Shift', 'P'], description: 'Pause recording', category: 'general', priority: 8 },
      { name: 'Studio Mode', keys: ['Ctrl', 'Shift', 'M'], description: 'Toggle studio mode', category: 'view', priority: 7 },
      { name: 'Settings', keys: ['Ctrl', 'Shift', 'T'], description: 'Open settings', category: 'general', priority: 6 },
      { name: 'Toggle Preview', keys: ['Ctrl', 'Shift', 'V'], description: 'Toggle preview', category: 'view', priority: 7 },
    ],
  },
]

function findDatabase(exe: string): MiscAppShortcutDatabase | undefined {
  const needle = exe.toLowerCase()
  return MISC_APP_SHORTCUTS.find(db => db.appExe.toLowerCase() === needle)
}

/** True when a static entry (not a backend profile) covers this process name. */
export function hasMiscAppShortcuts(exe: string): boolean {
  return !!exe && !!findDatabase(exe)
}

/** All static shortcuts for a process name, or an empty list. */
export function miscAppShortcutsForExe(exe: string): MiscAppShortcut[] {
  return findDatabase(exe)?.shortcuts ?? []
}

/** The static database's display label for a process name, if any. */
export function miscAppLabelForExe(exe: string): string | undefined {
  return findDatabase(exe)?.appName
}
