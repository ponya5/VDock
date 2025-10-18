// App-specific shortcuts database for common applications

export interface AppShortcut {
  name: string
  keys: string[]
  description: string
  category: 'general' | 'editing' | 'navigation' | 'search' | 'debug' | 'view' | 'terminal' | 'git' | 'refactor'
  priority?: number // Higher priority shortcuts appear first when auto-populating
}

export interface AppShortcutDatabase {
  appExe: string
  appName: string
  shortcuts: AppShortcut[]
}

export const appShortcutsDatabase: AppShortcutDatabase[] = [
  {
    appExe: 'Cursor.exe',
    appName: 'Cursor',
    shortcuts: [
      // High Priority - Most Used
      { name: 'Command Palette', keys: ['Ctrl', 'Shift', 'P'], description: 'Open command palette', category: 'general', priority: 10 },
      { name: 'Quick Open', keys: ['Ctrl', 'P'], description: 'Quick file open', category: 'navigation', priority: 10 },
      { name: 'AI Chat', keys: ['Ctrl', 'L'], description: 'Open AI chat', category: 'general', priority: 10 },
      { name: 'Find in Files', keys: ['Ctrl', 'Shift', 'F'], description: 'Search across all files', category: 'search', priority: 9 },
      { name: 'Toggle Terminal', keys: ['Ctrl', '`'], description: 'Show/hide integrated terminal', category: 'terminal', priority: 9 },
      
      // Editing
      { name: 'Multi-Cursor', keys: ['Ctrl', 'Alt', 'Down'], description: 'Add cursor below', category: 'editing', priority: 8 },
      { name: 'Select Next Match', keys: ['Ctrl', 'D'], description: 'Add selection to next find match', category: 'editing', priority: 8 },
      { name: 'Comment Line', keys: ['Ctrl', '/'], description: 'Toggle line comment', category: 'editing', priority: 8 },
      { name: 'Duplicate Line', keys: ['Shift', 'Alt', 'Down'], description: 'Copy line down', category: 'editing', priority: 7 },
      { name: 'Move Line Up', keys: ['Alt', 'Up'], description: 'Move line up', category: 'editing', priority: 7 },
      { name: 'Move Line Down', keys: ['Alt', 'Down'], description: 'Move line down', category: 'editing', priority: 7 },
      { name: 'Delete Line', keys: ['Ctrl', 'Shift', 'K'], description: 'Delete entire line', category: 'editing', priority: 6 },
      { name: 'Format Document', keys: ['Shift', 'Alt', 'F'], description: 'Format entire document', category: 'editing', priority: 7 },
      { name: 'Fold Code', keys: ['Ctrl', 'Shift', '['], description: 'Fold current region', category: 'editing', priority: 5 },
      { name: 'Unfold Code', keys: ['Ctrl', 'Shift', ']'], description: 'Unfold current region', category: 'editing', priority: 5 },
      
      // Navigation
      { name: 'Go to Line', keys: ['Ctrl', 'G'], description: 'Jump to line number', category: 'navigation', priority: 7 },
      { name: 'Go to Symbol', keys: ['Ctrl', 'Shift', 'O'], description: 'Navigate to symbol', category: 'navigation', priority: 7 },
      { name: 'Go to Definition', keys: ['F12'], description: 'Jump to definition', category: 'navigation', priority: 8 },
      { name: 'Peek Definition', keys: ['Alt', 'F12'], description: 'Peek definition inline', category: 'navigation', priority: 6 },
      { name: 'Go Back', keys: ['Ctrl', 'Alt', '-'], description: 'Navigate back', category: 'navigation', priority: 6 },
      { name: 'Go Forward', keys: ['Ctrl', 'Shift', '-'], description: 'Navigate forward', category: 'navigation', priority: 6 },
      
      // Search & Replace
      { name: 'Find', keys: ['Ctrl', 'F'], description: 'Find in current file', category: 'search', priority: 8 },
      { name: 'Replace', keys: ['Ctrl', 'H'], description: 'Find and replace', category: 'search', priority: 7 },
      { name: 'Find References', keys: ['Shift', 'F12'], description: 'Find all references', category: 'search', priority: 6 },
      
      // View
      { name: 'Toggle Sidebar', keys: ['Ctrl', 'B'], description: 'Show/hide sidebar', category: 'view', priority: 7 },
      { name: 'Zen Mode', keys: ['Ctrl', 'K', 'Z'], description: 'Enter zen mode', category: 'view', priority: 5 },
      { name: 'Split Editor', keys: ['Ctrl', '\\'], description: 'Split editor', category: 'view', priority: 6 },
      { name: 'Close Editor', keys: ['Ctrl', 'W'], description: 'Close current editor', category: 'view', priority: 7 },
      
      // Refactor
      { name: 'Rename Symbol', keys: ['F2'], description: 'Rename symbol', category: 'refactor', priority: 7 },
      { name: 'Quick Fix', keys: ['Ctrl', '.'], description: 'Show quick fixes', category: 'refactor', priority: 7 },
      
      // Debug
      { name: 'Start Debugging', keys: ['F5'], description: 'Start debugging', category: 'debug', priority: 6 },
      { name: 'Toggle Breakpoint', keys: ['F9'], description: 'Toggle breakpoint', category: 'debug', priority: 7 },
      { name: 'Step Over', keys: ['F10'], description: 'Step over', category: 'debug', priority: 5 },
      { name: 'Step Into', keys: ['F11'], description: 'Step into', category: 'debug', priority: 5 },
    ]
  },
  {
    appExe: 'Code.exe',
    appName: 'VS Code',
    shortcuts: [
      { name: 'Command Palette', keys: ['Ctrl', 'Shift', 'P'], description: 'Open command palette', category: 'general', priority: 10 },
      { name: 'Quick Open', keys: ['Ctrl', 'P'], description: 'Quick file open', category: 'navigation', priority: 10 },
      { name: 'Find in Files', keys: ['Ctrl', 'Shift', 'F'], description: 'Search across all files', category: 'search', priority: 9 },
      { name: 'Toggle Terminal', keys: ['Ctrl', '`'], description: 'Show/hide integrated terminal', category: 'terminal', priority: 9 },
      { name: 'Multi-Cursor', keys: ['Ctrl', 'Alt', 'Down'], description: 'Add cursor below', category: 'editing', priority: 8 },
      { name: 'Comment Line', keys: ['Ctrl', '/'], description: 'Toggle line comment', category: 'editing', priority: 8 },
      { name: 'Format Document', keys: ['Shift', 'Alt', 'F'], description: 'Format entire document', category: 'editing', priority: 7 },
      { name: 'Go to Definition', keys: ['F12'], description: 'Jump to definition', category: 'navigation', priority: 8 },
      { name: 'Rename Symbol', keys: ['F2'], description: 'Rename symbol', category: 'refactor', priority: 7 },
      { name: 'Toggle Sidebar', keys: ['Ctrl', 'B'], description: 'Show/hide sidebar', category: 'view', priority: 7 },
    ]
  },
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
    ]
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
    ]
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
    ]
  }
]

// Helper function to get shortcuts for a specific app
export function getShortcutsForApp(appExe: string): AppShortcut[] {
  const app = appShortcutsDatabase.find(db => db.appExe.toLowerCase() === appExe.toLowerCase())
  return app?.shortcuts || []
}

// Get shortcuts sorted by priority
export function getTopShortcutsForApp(appExe: string, count: number = 8): AppShortcut[] {
  const shortcuts = getShortcutsForApp(appExe)
  return shortcuts
    .sort((a, b) => (b.priority || 0) - (a.priority || 0))
    .slice(0, count)
}

// Get shortcuts by category
export function getShortcutsByCategory(appExe: string, category: AppShortcut['category']): AppShortcut[] {
  const shortcuts = getShortcutsForApp(appExe)
  return shortcuts.filter(s => s.category === category)
}

// Get all available categories for an app
export function getCategoriesForApp(appExe: string): AppShortcut['category'][] {
  const shortcuts = getShortcutsForApp(appExe)
  const categories = new Set(shortcuts.map(s => s.category))
  return Array.from(categories)
}

// Check if app has shortcuts
export function hasShortcuts(appExe: string): boolean {
  return appShortcutsDatabase.some(db => db.appExe.toLowerCase() === appExe.toLowerCase())
}

// Get app name
export function getAppName(appExe: string): string {
  const app = appShortcutsDatabase.find(db => db.appExe.toLowerCase() === appExe.toLowerCase())
  return app?.appName || appExe.replace('.exe', '')
}

