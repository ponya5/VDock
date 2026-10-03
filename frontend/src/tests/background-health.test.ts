import { describe, expect, it } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { settingsSource } from './helpers/settingsSource'

// DL-109: the dashboard/preview background chain, pinned end-to-end.
// A live sweep of all 58 catalog ids found two component backgrounds that
// hard-failed (shader compile + vgpu validation) and a failure state that
// rendered as an unlabelled checkerboard — these tests keep the whole
// catalog renderable and the failure state honest.

const root = join(__dirname, '..')
const read = (p: string) => readFileSync(join(root, p), 'utf-8')

const catalogSrc = read('data/backgrounds.ts')
const catalogIds = [...catalogSrc.matchAll(/id: '([^']+)'[^\n]*kind: '(css|component)'/g)].map(
  m => ({ id: m[1], kind: m[2] }),
)

describe('background catalog coverage', () => {
  it('every css-kind catalog id has a dashboard-bg-* rule in main.css', () => {
    const css = read('assets/styles/main.css')
    const cssIds = catalogIds.filter(e => e.kind === 'css' && e.id !== 'default').map(e => e.id)
    expect(cssIds.length).toBeGreaterThan(0)
    const missing = cssIds.filter(id => !css.includes(`dashboard-bg-${id}`))
    expect(missing).toEqual([])
  })

  it('every component-kind catalog id maps to a backgrounds/ component', () => {
    const components = new Set(
      readdirSync(join(root, 'components/backgrounds')).filter(f => f.endsWith('.vue')),
    )
    const imported = [...catalogSrc.matchAll(/import \w+ from '@\/components\/backgrounds\/([^']+)'/g)].map(m => m[1])
    for (const file of imported) expect(components.has(file)).toBe(true)
    // every component-kind entry's `component:` reference must be an imported symbol
    const compEntries = catalogIds.filter(e => e.kind === 'component')
    expect(compEntries.length).toBeGreaterThan(0)
    for (const { id } of compEntries) {
      const block = catalogSrc.match(new RegExp(`id: '${id}'[^}]+component: (\\w+)`))
      expect(block, `${id} should declare a component`).toBeTruthy()
    }
  })
})

describe('component shader/gpu health', () => {
  it('MoltenMetal: int loop counter is cast to float before float arithmetic', () => {
    // GLSL ES 1.0 has no implicit int→float: `i * 1.7` fails to compile.
    const src = read('components/backgrounds/MoltenMetal.vue')
    expect(src).toContain('for (int i = 0')
    expect(src).toContain('float(i) * 1.7')
    expect(src).not.toMatch(/[^t(]i \* 1\.7/)
  })

  it('ShapeWaves: vgpu mask texture declares an explicit kind', () => {
    // gpu.device is the vgpu Device wrapper; createTexture requires kind.
    const src = read('components/backgrounds/ShapeWaves.vue')
    expect(src).toContain('gpu.device.createTexture')
    expect(src).toMatch(/createTexture\(\{[^}]*kind: '2d'/)
  })

  it('no other component passes a raw device.createTexture without kind', () => {
    const offenders: string[] = []
    for (const file of readdirSync(join(root, 'components/backgrounds'))) {
      if (!file.endsWith('.vue')) continue
      const src = read(`components/backgrounds/${file}`)
      for (const m of src.matchAll(/\.device\.createTexture\(\{([^}]*)\}/g)) {
        if (!/kind:/.test(m[1])) offenders.push(file)
      }
    }
    expect(offenders).toEqual([])
  })
})

describe('settings preview failure state', () => {
  it('a failed component preview shows a labelled unavailable state, not a bare checkerboard', () => {
    const src = settingsSource() // the preview lives in a panel/composable after the DL-146 split
    expect(src).toContain('bgPreviewFailed.value = settingsStore.background')
    expect(src).toContain('previewBgUnavailable')
    expect(src).toContain('preview-bg-note')
    expect(src).toContain('Preview unavailable')
    expect(src).toContain('v-else-if="previewBgUnavailable"')
  })
})
