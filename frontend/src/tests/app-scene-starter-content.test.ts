import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// DL-025: enabling an app auto-creates a scene only when it would have
// starter content — an empty scene prompts first.

vi.mock('@/api/appProfiles', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/appProfiles')>()
  return {
    ...actual,
    fetchAppProfiles: vi.fn().mockResolvedValue([
      {
        id: 'cursor', label: 'Cursor', exes: ['cursor.exe', 'cursor.app'],
        kind: 'editor', status_source: null, default_layout: [],
        commands: [
          { id: 'cursor_chat', label: 'Chat', description: '', keys: ['ctrl', 'l'], icon: 'comments', keywords: [], category: 'general', priority: 5, risk: 'safe', requires_session: false },
        ],
      },
    ]),
  }
})

import { appSceneHasStarterContent } from '@/composables/useAppShortcutScenes'

describe('appSceneHasStarterContent', () => {
  it('true for apps with starter presets, misc shortcuts, or a keymap profile', async () => {
    expect(await appSceneHasStarterContent('spotify', 'Spotify')).toBe(true)
    // macOS process name → static db via appName match
    expect(await appSceneHasStarterContent('google chrome', 'Google Chrome')).toBe(true)
    // macOS process name → backend profile via '.app' exe match
    expect(await appSceneHasStarterContent('cursor', 'Cursor')).toBe(true)
  })

  it('false for an app with no shortcuts or presets', async () => {
    expect(await appSceneHasStarterContent('accessoryd', 'accessoryd')).toBe(false)
  })
})

const panel = readFileSync(
  resolve(__dirname, '../components/settings/panels/SceneSwitchingPanel.vue'),
  'utf-8',
)

describe('SceneSwitchingPanel empty-scene confirm (DL-025)', () => {
  it('checks starter content and prompts before auto-creating', () => {
    expect(panel).toContain('appSceneHasStarterContent')
    expect(panel).toContain('confirmDialog')
    // The prompt is conditional — scenes with content still auto-create.
    expect(panel).toContain('if (!seeded)')
  })
})
