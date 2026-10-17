// Apps offered in the first-run tour ("What do you use?"). `template` ids come from
// appTemplates.ts; the Spotify entry uses the media starter kit (appStarterActions.ts).
import { templateCategories, type AppTemplate } from '@/data/appTemplates'

export interface TutorialApp {
  id: string
  label: string
  /** appTemplates id, or 'starter:<exe>' for an app with a starter kit. */
  source: string
  icon: [string, string]
}

export const TUTORIAL_APPS: TutorialApp[] = [
  { id: 'claude-code', label: 'Claude Code', source: 'claude-code', icon: ['fas', 'terminal'] },
  { id: 'cursor', label: 'Cursor', source: 'cursor', icon: ['fas', 'code'] },
  { id: 'codex', label: 'Codex', source: 'codex', icon: ['fas', 'terminal'] },
  { id: 'github-copilot', label: 'GitHub Copilot', source: 'github-copilot', icon: ['fas', 'code'] },
  { id: 'claude', label: 'Claude', source: 'claude', icon: ['fas', 'robot'] },
  { id: 'chatgpt', label: 'ChatGPT', source: 'chatgpt', icon: ['fas', 'robot'] },
  { id: 'github', label: 'GitHub', source: 'github', icon: ['fab', 'github'] },
  { id: 'figma', label: 'Figma', source: 'figma', icon: ['fab', 'figma'] },
  { id: 'spotify', label: 'Spotify', source: 'starter:spotify', icon: ['fab', 'spotify'] },
]

export function findTemplate(id: string): AppTemplate | undefined {
  for (const c of templateCategories) {
    const t = c.templates.find(t => t.id === id)
    if (t) return t
  }
  return undefined
}
