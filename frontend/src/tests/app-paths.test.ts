import { describe, test, expect } from 'vitest'
import { templateAppKey, launchApps } from '../api/appPaths'

describe('templateAppKey', () => {
  test('derives the key from an open_app program stem', () => {
    const t = {
      id: 'adobe-cc',
      buttons: [
        { action: { type: 'cross_platform', config: { action: 'open_app', path: 'adobe creative cloud' } } },
      ],
    }
    expect(templateAppKey(t)).toBe('adobe creative cloud')
  })

  test('strips an exe suffix and lowercases', () => {
    const t = {
      id: 'x',
      buttons: [
        { action: { type: 'cross_platform', config: { action: 'open_app', path: 'Cursor.EXE' } } },
      ],
    }
    expect(templateAppKey(t)).toBe('cursor')
  })

  test('maps the claude-code template id to the claude binary', () => {
    expect(templateAppKey({ id: 'claude-code', buttons: [] })).toBe('claude')
  })

  test('falls back to the template id for keymap/url packs', () => {
    const t = { id: 'chatgpt', buttons: [{ action: { type: 'url', config: { url: 'https://x' } } }] }
    expect(templateAppKey(t)).toBe('chatgpt')
  })

  test('handles windows-style paths', () => {
    const t = {
      id: 'y',
      buttons: [
        { action: { type: 'cross_platform', config: { action: 'open_app', path: 'C:\\Apps\\Tool.EXE' } } },
      ],
    }
    expect(templateAppKey(t)).toBe('tool')
  })
})

describe('launchApps', () => {
  test('covers cursor and vscode — the apps without gallery cards', () => {
    const keys = launchApps.map((a) => a.key)
    expect(keys).toContain('cursor')
    expect(keys).toContain('code')
    expect(keys).toContain('claude')
  })

  test('keys are unique', () => {
    const keys = launchApps.map((a) => a.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
})
