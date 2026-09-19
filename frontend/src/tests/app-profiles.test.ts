import { describe, test, expect } from 'vitest'
import { shortcutsForExe, type AppProfileDto } from '../api/appProfiles'

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
