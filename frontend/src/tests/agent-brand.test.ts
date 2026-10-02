import { describe, it, expect } from 'vitest'
import { agentBrandFor, agentBrandVars } from '@/services/agentBrand'

describe('agentBrand', () => {
  it('gives Claude Code its logo and the clay-orange accent', () => {
    const b = agentBrandFor('claude')
    expect(b.logo).toBe('/logos/claudecode-color.png')
    expect(b.solid).toBe('#d97757')
  })

  it.each(['cursor', 'antigravity', 'codex'])('brands %s with its own logo', (source) => {
    expect(agentBrandFor(source).logo).toMatch(/^\/logos\/.+\.png$/)
  })

  it('keeps the green robot fallback for unbranded sources', () => {
    for (const source of ['generic', 'devin', undefined, null]) {
      const b = agentBrandFor(source)
      expect(b.logo).toBeUndefined()
      expect(b.rgb).toBe('34, 197, 94')
    }
  })

  it('exposes the palette as CSS custom properties', () => {
    const vars = agentBrandVars('claude') as Record<string, string>
    expect(vars['--agent-rgb']).toBe('217, 119, 87')
    expect(vars['--agent-solid']).toBe('#d97757')
    expect(Object.keys(vars).every((k) => k.startsWith('--agent-'))).toBe(true)
  })

  it('every shipped logo file exists', async () => {
    const { existsSync } = await import('node:fs')
    const { resolve } = await import('node:path')
    for (const source of ['claude', 'cursor', 'antigravity', 'codex']) {
      const logo = agentBrandFor(source).logo!
      expect(existsSync(resolve(__dirname, '../../public', logo.slice(1)))).toBe(true)
    }
  })
})
