import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, test, expect } from 'vitest'
import { templateAppKey, launchApps } from '../api/appPaths'
import { templateCategories } from '../data/appTemplates'
import { settingsSource } from './helpers/settingsSource'

const settingsUiSource = settingsSource()
const editorSource = readFileSync(resolve(__dirname, '../components/AppPathEditor.vue'), 'utf-8')

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
    expect(keys).toContain('antigravity')
  })

  test('keys are unique', () => {
    const keys = launchApps.map((a) => a.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
})

describe('antigravity template', () => {
  const aiCoding = templateCategories.find((c) => c.id === 'ai-coding')!
  const card = aiCoding.templates.find((t) => t.id === 'antigravity')

  test('lives in the AI Coding category, exactly once gallery-wide', () => {
    expect(card).toBeDefined()
    const all = templateCategories.flatMap((c) => c.templates)
    expect(all.filter((t) => t.id === 'antigravity')).toHaveLength(1)
  })

  test('wires real antigravity_* pack actions, not URL stubs', () => {
    const types = card!.buttons.map((b) => b.action!.type)
    expect(types).toContain('antigravity_agent')
    expect(types).toContain('antigravity_new_thread')
    expect(types).toContain('antigravity_submit')
    expect(types).toContain('antigravity_followup')
    expect(types).toContain('antigravity_stop')
    expect(types).not.toContain('url')
  })

  test('the open_app launcher resolves the antigravity path key', () => {
    expect(templateAppKey(card!)).toBe('antigravity')
  })
})

describe('cursor template', () => {
  const aiCoding = templateCategories.find((c) => c.id === 'ai-coding')!
  const card = aiCoding.templates.find((t) => t.id === 'cursor')

  test('lives in the AI Coding category wired to the cursor_* pack', () => {
    expect(card).toBeDefined()
    const types = card!.buttons.map((b) => b.action!.type)
    expect(types).toContain('cursor_prompt')
    expect(types).toContain('cursor_submit')
    expect(types).toContain('cursor_accept')
    expect(templateAppKey(card!)).toBe('cursor')
  })
})

describe('templateCategories order', () => {
  test('AI Coding leads the gallery', () => {
    expect(templateCategories[0].id).toBe('ai-coding')
  })
})

describe('app path editor popup', () => {
  test('the standalone App launch paths panel is gone', () => {
    expect(settingsUiSource).not.toContain('id="app-paths"')
    expect(settingsUiSource).not.toContain('appPathRows')
  })

  test('the card gear opens a dialog, not an inline editor', () => {
    expect(settingsUiSource).toContain('aria-haspopup="dialog"')
    expect(settingsUiSource).toContain('role="dialog"')
    expect(settingsUiSource).toContain('modal-overlay')
  })

  test('the popup carries path input, Save, and Close', () => {
    expect(editorSource).toContain('class="input ape-input"')
    expect(editorSource).toMatch(/>\s*Close\s*<\/button>/)
    expect(editorSource).toContain("emit('close')")
    expect(editorSource).toContain("e.key === 'Escape'")
  })
})
