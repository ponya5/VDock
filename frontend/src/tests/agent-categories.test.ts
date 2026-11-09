// DL-166: every button of every AI coding template / factory scene lands in the category the design log assigns it.
import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import type { Button, Scene } from '@/types'
import { templateCategories, type AppTemplate } from '@/data/appTemplates'
import { templateShortcut } from '@/utils/templateShortcut'
import { createClaudeCodeScene, createFactoryIdeScene } from '@/utils/defaultProfile'
import {
  AGENT_CATEGORIES,
  groupSceneButtons,
  resolveButtonCategory,
  type AgentCategoryId,
} from '@/utils/agentCategories'

function sceneOf(buttons: Button[], cols = 5): Scene {
  return {
    id: 's', name: 'S',
    pages: [{ id: 'p', name: 'P', grid_config: { rows: 4, cols }, buttons }],
  } as Scene
}

function templateScene(id: string): Scene {
  const aiCoding = templateCategories.find(c => c.id === 'ai-coding')!
  const t: AppTemplate = aiCoding.templates.find(x => x.id === id)!
  const buttons = t.buttons.map((b, index) => ({
    id: `b${index}`, label: b.label, icon: b.icon, action: b.action, shape: 'rounded',
    position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
    tooltip: b.tooltip ?? b.label, enabled: true,
    secondary_label: templateShortcut(b) || undefined,
    category: b.category,
  })) as Button[]
  return sceneOf(buttons)
}

function backendScene(file: string): Scene {
  const data = JSON.parse(fs.readFileSync(
    path.resolve(__dirname, '../../../backend/data/templates', file), 'utf-8'))
  return { id: 's', name: data.name, pages: data.pages } as Scene
}

const byLabel = (scene: Scene) =>
  Object.fromEntries(scene.pages.flatMap(p => p.buttons).map(b => [b.label, resolveButtonCategory(b)]))
const rail = (scene: Scene) => groupSceneButtons(scene).map(g => `${g.id}:${g.buttons.length}`).join(' ')

describe('resolveButtonCategory: factory scenes', () => {
  it('Claude Code', () => {
    const scene = createClaudeCodeScene()
    expect(byLabel(scene)).toEqual({
      'Open Claude': 'session', Review: 'review', Interrupt: 'session', Continue: 'session',
      Queue: 'session', Mode: 'control', 'New Session': 'context', Compact: 'context',
    })
    expect(rail(scene)).toBe('session:4 review:1 control:1 context:2')
  })

  it('Cursor', () => {
    const scene = createFactoryIdeScene('Cursor')!
    expect(byLabel(scene)).toEqual({
      'New Agent': 'session', Review: 'review', Commit: 'review', 'Inline Edit': 'prompts',
      Explain: 'prompts', Terminal: 'tools',
    })
    expect(rail(scene)).toBe('session:1 prompts:2 review:2 tools:1')
  })
})

describe('resolveButtonCategory: AI Coding templates', () => {
  it('claude-code', () => {
    const scene = templateScene('claude-code')
    expect(byLabel(scene)).toEqual({
      Submit: 'session', Continue: 'session', Interrupt: 'session', 'New Session': 'context',
      Resume: 'session', Mode: 'control', Model: 'control', 'Add File': 'context',
      'Open Claude': 'session', 'Review Diff': 'review', Queue: 'session', Compact: 'context',
      Rewind: 'session', Thinking: 'control', Transcript: 'context',
    })
    expect(rail(scene)).toBe('session:7 review:1 control:3 context:4')
  })

  it('cursor (explicit overrides for the generic hotkeys and the empty prompt)', () => {
    const scene = templateScene('cursor')
    expect(byLabel(scene)).toEqual({
      'New Agent': 'session', Continue: 'session', Submit: 'session', Stop: 'session',
      Chat: 'prompts', Composer: 'prompts', 'Inline Edit': 'prompts', Accept: 'review', Reject: 'review',
      Terminal: 'tools', Mode: 'control', 'Agent Layout': 'tools', Models: 'control', Palette: 'tools',
    })
    expect(rail(scene)).toBe('session:4 prompts:3 review:2 control:2 tools:3')
  })

  it('antigravity', () => {
    const scene = templateScene('antigravity')
    expect(byLabel(scene)).toEqual({
      'Agent Panel': 'prompts', 'New Chat': 'session', Submit: 'session', Continue: 'session',
      Stop: 'session', Manager: 'tools', 'Inline Cmd': 'prompts', Terminal: 'tools',
      'Quick Open': 'tools', 'Open Antigravity': 'session',
    })
    expect(rail(scene)).toBe('session:5 prompts:2 tools:3')
  })

  it('codex', () => {
    const scene = templateScene('codex')
    expect(byLabel(scene)).toEqual({
      Interrupt: 'session', Continue: 'session', Submit: 'session', Approve: 'session', Deny: 'session',
      Approvals: 'control', Compact: 'context', 'Start Codex': 'session', 'Full Auto': 'control',
      'Quiet Mode': 'control', Resume: 'session', 'Auto Edit': 'control', Suggest: 'control',
      'Review Diff': 'review', Login: 'tools', Docs: 'links',
    })
    expect(rail(scene)).toBe('session:7 review:1 control:5 context:1 tools:1 links:1')
  })
})

describe('resolveButtonCategory: backend dev templates', () => {
  it('dev-claude-code', () => {
    const scene = backendScene('dev-claude-code.json')
    const cats = byLabel(scene)
    expect(cats['Open Claude']).toBe('session')
    expect(cats.Review).toBe('review')
    expect(cats.Interrupt).toBe('session')
    expect(cats.Queue).toBe('session')
    expect(cats.Ask).toBe('prompts')
    expect(cats.Continue).toBe('session')
    expect(cats['Summarise Diff']).toBe('review')
    expect(cats.Terminal).toBe('tools')
    expect(cats.Mode).toBe('control')
    expect(cats['New Session']).toBe('context')
    expect(cats.Compact).toBe('context')
    expect(cats.Clock).toBe('tools')
    expect(rail(scene)).toBe('session:4 prompts:1 review:2 control:1 context:2 tools:4')
  })

  it('dev-cursor-ai', () => {
    const scene = backendScene('dev-cursor-ai.json')
    expect(rail(scene)).toBe('session:3 prompts:4 review:4 tools:5')
    const cats = byLabel(scene)
    expect(cats['New Agent']).toBe('session')
    expect(cats.Stop).toBe('session')
    expect(cats.Continue).toBe('session')
    expect(cats.Commit).toBe('review')
    expect(cats.Accept).toBe('review')
    expect(cats.Explain).toBe('prompts')
    expect(cats.CPU).toBe('tools')
  })
})

describe('resolveButtonCategory: rules', () => {
  const button = (action: Button['action'], extra: Partial<Button> = {}): Button => ({
    id: 'x', label: 'X', shape: 'rounded', position: { row: 0, col: 0 }, size: { rows: 1, cols: 1 },
    enabled: true, action, ...extra,
  }) as Button

  it('an explicit category wins over the action', () => {
    expect(resolveButtonCategory(button({ type: 'cc_interrupt', config: {} }, { category: 'tools' }))).toBe('tools')
  })

  it('an unknown or empty category falls back to auto', () => {
    expect(resolveButtonCategory(button({ type: 'cc_interrupt', config: {} }, { category: 'nope' as never }))).toBe('session')
    expect(resolveButtonCategory(button({ type: 'cc_interrupt', config: {} }, { category: '' }))).toBe('session')
  })

  it('classifies prompt text, slash commands and gh_ / metric_ prefixes', () => {
    expect(resolveButtonCategory(button({ type: 'cc_prompt', config: { text: '/model' } }))).toBe('control')
    expect(resolveButtonCategory(button({ type: 'cc_prompt', config: { text: '/memory' } }))).toBe('context')
    expect(resolveButtonCategory(button({ type: 'cc_prompt', config: { text: 'explain this' } }))).toBe('prompts')
    expect(resolveButtonCategory(button({ type: 'gh_ci_status', config: {} }))).toBe('review')
    expect(resolveButtonCategory(button({ type: 'metric_cpu_usage', config: {} }))).toBe('tools')
    expect(resolveButtonCategory(button({ type: 'something_else', config: {} }))).toBe('other')
  })

  it('classifies shell commands and app launches', () => {
    expect(resolveButtonCategory(button({ type: 'command', config: { command: 'git push' } }))).toBe('review')
    expect(resolveButtonCategory(button({ type: 'command', config: { command: 'codex --model o3' } }))).toBe('control')
    expect(resolveButtonCategory(button({ type: 'command', config: { command: 'claude' } }))).toBe('session')
    expect(resolveButtonCategory(button({ type: 'cross_platform', config: { action: 'open_app', app: 'wt' } }))).toBe('tools')
    expect(resolveButtonCategory(button({ type: 'program', config: { path: 'C:/x/Cursor.exe' } }))).toBe('session')
  })
})

describe('groupSceneButtons', () => {
  const mk = (id: string, type: string, row: number, col: number, extra: Partial<Button> = {}): Button => ({
    id, label: id, shape: 'rounded', position: { row, col }, size: { rows: 1, cols: 1 },
    enabled: true, action: { type, config: {} }, ...extra,
  }) as Button

  it('drops page navigation, disabled and action-less buttons, and hides empty groups', () => {
    const scene = sceneOf([
      mk('a', 'cc_interrupt', 0, 0),
      mk('nav', 'next_page', 0, 1),
      mk('off', 'cc_compact', 0, 2, { enabled: false }),
      mk('none', 'cc_mode', 0, 3, { action: undefined }),
    ])
    expect(groupSceneButtons(scene).map(g => g.id)).toEqual(['session'])
  })

  it('orders groups by the category table and buttons by page, row, column', () => {
    const scene = {
      id: 's', name: 'S',
      pages: [
        { id: 'p1', name: 'P1', grid_config: { rows: 2, cols: 3 }, buttons: [
          mk('mode', 'cc_mode', 0, 0), mk('late', 'cc_interrupt', 1, 0), mk('early', 'cc_submit', 0, 2),
        ] },
        { id: 'p2', name: 'P2', grid_config: { rows: 2, cols: 3 }, buttons: [mk('p2', 'cc_queue', 0, 0)] },
      ],
    } as Scene
    const groups = groupSceneButtons(scene)
    expect(groups.map(g => g.id)).toEqual(['session', 'control'])
    expect(groups[0].buttons.map(b => b.id)).toEqual(['early', 'late', 'p2'])
    const order = AGENT_CATEGORIES.map(c => c.id)
    expect(order.indexOf(groups[0].id)).toBeLessThan(order.indexOf(groups[1].id as AgentCategoryId))
  })
})
