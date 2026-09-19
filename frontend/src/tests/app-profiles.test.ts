import { describe, test, expect } from 'vitest'
import {
  shortcutsForExe,
  appShortcutsForExe,
  hasAppShortcuts,
  topAppShortcuts,
  appLabelForExe,
  type AppProfileDto,
} from '../api/appProfiles'

const PROFILES: AppProfileDto[] = [
  {
    id: 'cursor',
    label: 'Cursor',
    exes: ['cursor.exe'],
    kind: 'editor',
    status_source: null,
    default_layout: [['cursor_composer', 'cursor_chat']],
    commands: [
      { id: 'cursor_chat', label: 'Cursor Chat', description: '', keys: ['ctrl', 'l'], icon: 'comments', keywords: [], category: 'general', priority: 5, risk: 'safe', requires_session: false },
      { id: 'cursor_composer', label: 'Composer', description: '', keys: ['ctrl', 'i'], icon: 'wand', keywords: [], category: 'general', priority: 10, risk: 'safe', requires_session: false },
    ],
  },
]

describe('shortcutsForExe', () => {
  test('matches an exe case-insensitively', () => {
    expect(shortcutsForExe(PROFILES, 'Cursor.exe')).toHaveLength(2)
    expect(shortcutsForExe(PROFILES, 'cursor.exe')).toHaveLength(2)
  })

  test('sorts by priority descending', () => {
    expect(shortcutsForExe(PROFILES, 'cursor.exe')[0].id).toBe('cursor_composer')
  })

  test('an unknown exe yields an empty list, not an error', () => {
    expect(shortcutsForExe(PROFILES, 'notepad.exe')).toEqual([])
  })

  test('an empty exe yields an empty list', () => {
    expect(shortcutsForExe(PROFILES, '')).toEqual([])
  })
})

describe('apps outside the backend keymap system fall back to the static database', () => {
  test('a backend-covered app uses its API commands', () => {
    expect(appShortcutsForExe(PROFILES, 'cursor.exe')).toHaveLength(2)
    expect(appLabelForExe(PROFILES, 'cursor.exe')).toBe('Cursor')
  })

  test('chrome, Discord and OBS still have shortcuts despite no backend profile', () => {
    for (const exe of ['chrome.exe', 'Discord.exe', 'obs64.exe']) {
      expect(hasAppShortcuts(PROFILES, exe)).toBe(true)
      expect(appShortcutsForExe(PROFILES, exe).length).toBeGreaterThan(0)
      expect(topAppShortcuts(PROFILES, exe, 3)).toHaveLength(3)
    }
    expect(appLabelForExe(PROFILES, 'chrome.exe')).toBe('Google Chrome')
  })

  test('an app in neither source has no shortcuts', () => {
    expect(hasAppShortcuts(PROFILES, 'notepad.exe')).toBe(false)
    expect(appShortcutsForExe(PROFILES, 'notepad.exe')).toEqual([])
  })
})
