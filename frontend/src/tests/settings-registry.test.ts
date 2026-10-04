// DL-146 Phase 3b: the settings registry is the single source for nav, search and deep links.
import { describe, it, expect } from 'vitest'
import {
  SECTIONS, NAV_SECTIONS, SEARCH, NOT_SEARCHABLE, LEGACY_TABS, LEGACY_SUBS, LANDING,
  findSection, findPage, resolveRoute, searchSettings,
} from '@/settings/registry'
import { settingsSource } from './helpers/settingsSource'

const source = settingsSource()
const allAnchors = SECTIONS.flatMap((s) => s.pages.flatMap((p) => p.anchors))

describe('registry shape', () => {
  it('has at most seven sections and lists only those with pages', () => {
    expect(SECTIONS.length).toBeLessThanOrEqual(7)
    expect(NAV_SECTIONS.every((s) => s.pages.length > 0)).toBe(true)
    expect(findSection(LANDING)).toBeDefined()
  })

  it('has unique page ids within a section and unique search labels', () => {
    for (const s of SECTIONS) expect(new Set(s.pages.map((p) => p.id)).size).toBe(s.pages.length)
    expect(new Set(SEARCH.map((e) => e.label)).size).toBe(SEARCH.length)
  })

  it('points every search entry at a real page and anchor', () => {
    for (const e of SEARCH.filter((x) => x.section !== 'guide')) {
      const page = findPage(findSection(e.section)!, e.page)
      expect(page, e.label).toBeDefined()
      if (e.anchor) expect(page!.anchors, e.label).toContain(e.anchor)
    }
  })
})

describe('anchors', () => {
  it('exist as ids in the panel sources', () => {
    for (const id of allAnchors) expect(source, id).toContain(`id="${id}"`)
  })

  it('cover every panel section in the sources', () => {
    const panelIds = [...source.matchAll(/<section class="panel[^"]*" id="([a-z-]+)"/g)].map((m) => m[1])
    for (const id of panelIds) expect(allAnchors, id).toContain(id)
  })

  it('are searchable unless explicitly exempt', () => {
    const searched = new Set(SEARCH.map((e) => e.anchor))
    for (const id of allAnchors) {
      if (!NOT_SEARCHABLE.includes(id)) expect(searched.has(id), id).toBe(true)
    }
  })
})

describe('resolveRoute', () => {
  it('resolves the current ?section=&page=&anchor= form', () => {
    expect(resolveRoute({ section: 'devices', page: 'security' })).toEqual({ section: 'devices', page: 'security' })
    expect(resolveRoute({ section: 'appearance', page: 'buttons', anchor: 'touch' })).toEqual({ section: 'appearance', page: 'buttons', anchor: 'touch' })
  })

  it('resolves a bare ?anchor= to the page that owns it', () => {
    expect(resolveRoute({ anchor: 'ss-widgets' })).toEqual({ section: 'appearance', page: 'screensaver', anchor: 'ss-widgets' })
  })

  it('maps every legacy tab/sub pair to a real page', () => {
    for (const [tab, target] of Object.entries(LEGACY_TABS)) {
      const section = findSection(target.section)!
      expect(resolveRoute({ tab }).section).toBe(section.id)
      for (const sub of [...section.pages.map((p) => p.id), ...Object.keys(LEGACY_SUBS)]) {
        const route = resolveRoute({ tab, sub })
        expect(findPage(findSection(route.section)!, route.page)).toBeDefined()
      }
    }
    expect(resolveRoute({ tab: 'server' })).toEqual({ section: 'devices', page: 'ports' })
    expect(resolveRoute({ tab: 'connect' })).toEqual({ section: 'devices', page: 'connect' })
    expect(resolveRoute({ tab: 'integration', sub: 'alerts' })).toEqual({ section: 'agents', page: 'alerts' })
    expect(resolveRoute({ tab: 'integration', sub: 'apps' })).toEqual({ section: 'agents', page: 'scenes' })
    expect(resolveRoute({ tab: 'appearance', sub: 'layout' })).toEqual({ section: 'appearance', page: 'layout' })
  })

  it('falls back to the landing section for unknown input', () => {
    expect(resolveRoute({ tab: 'nope', sub: 'x' }).section).toBe(LANDING)
    expect(resolveRoute({}).section).toBe(LANDING)
  })
})

describe('searchSettings', () => {
  const first = (q: string) => searchSettings(q)[0]

  it('is case-insensitive and ranks label hits before keyword hits', () => {
    expect(searchSettings('PASSWORD')[0].label).toBe('Deck Password')
    const hits = searchSettings('alert')
    const firstKeywordOnly = hits.findIndex((e) => !e.label.toLowerCase().includes('alert'))
    expect(hits.slice(0, firstKeywordOnly).every((e) => e.label.toLowerCase().includes('alert'))).toBe(true)
  })

  it('finds the control for each task word', () => {
    expect(first('phone')).toMatchObject({ section: 'devices', page: 'connect' })
    expect(first('password')).toMatchObject({ section: 'devices', page: 'security' })
    expect(first('port')).toMatchObject({ section: 'devices', page: 'ports' })
    expect(first('scene')).toMatchObject({ section: 'agents', page: 'scenes' })
    expect(first('alert')).toMatchObject({ section: 'agents', page: 'alerts' })
  })

  it('returns nothing for an empty or unknown query', () => {
    expect(searchSettings('  ')).toEqual([])
    expect(searchSettings('zzzzqq')).toEqual([])
  })
})
