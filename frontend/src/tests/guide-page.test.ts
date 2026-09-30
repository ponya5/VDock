// Dedicated /guide landing page (DL-132): search filtering, sections,
// footer wiring, and the SettingsView hand-off (nav item opens /guide
// in a new window; the embedded guide tab is gone).
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineComponent, h } from 'vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: defineComponent({
    props: ['to'],
    setup: (p, { slots }) => () =>
      h('a', { href: String(p.to) }, slots.default?.()),
  }),
}))

const settingsSrc = readFileSync(
  resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')
const routerSrc = readFileSync(
  resolve(__dirname, '../router/index.ts'), 'utf-8')
const guideSrc = readFileSync(
  resolve(__dirname, '../views/GuideView.vue'), 'utf-8')

async function mountGuide() {
  vi.resetModules()
  const { default: GuideView } = await import('@/views/GuideView.vue')
  return mount(GuideView, {
    global: {
      stubs: { FontAwesomeIcon: true, RouterLink: true },
    },
  })
}

describe('GuideView landing page', () => {
  beforeEach(() => setActivePinia(createPinia()))
  afterEach(() => document.body.innerHTML = '')

  it('renders every feature section', async () => {
    const w = await mountGuide()
    const sections = w.findAll('section.feature')
    expect(sections.length).toBeGreaterThanOrEqual(10)
    expect(w.find('.site-footer').exists()).toBe(true)
  })

  it('smart search filters sections and reports the count', async () => {
    const w = await mountGuide()
    const input = w.find('.search-input')
    await input.setValue('mcp')
    const sections = w.findAll('section.feature')
    expect(sections.length).toBeGreaterThanOrEqual(1)
    expect(sections.length).toBeLessThan(5)
    expect(w.text()).toContain('MCP Server')
    expect(w.find('.search-status').text()).toContain('match')
  })

  it('multi-token search requires every token', async () => {
    const w = await mountGuide()
    await w.find('.search-input').setValue('agent scene')
    const titles = w.findAll('section.feature h2').map(e => e.text())
    expect(titles.some(t => /agent|scene/i.test(t))).toBe(true)
  })

  it('empty query restores all sections; nonsense shows none', async () => {
    const w = await mountGuide()
    const input = w.find('.search-input')
    await input.setValue('zzzqqq')
    expect(w.findAll('section.feature').length).toBe(0)
    await input.setValue('')
    expect(w.findAll('section.feature').length).toBeGreaterThanOrEqual(10)
  })

  it('screenshots live under /guide/ and lazy-load', async () => {
    const w = await mountGuide()
    const imgs = w.findAll('.feature-shot img')
    expect(imgs.length).toBeGreaterThanOrEqual(5)
    for (const img of imgs) {
      expect(img.attributes('src')).toMatch(/^\/guide\/[\w-]+\.png$/)
      expect(img.attributes('loading')).toBe('lazy')
    }
  })
})

describe('SettingsView guide hand-off', () => {
  it('guide is a /guide route, not a settings tab', () => {
    expect(routerSrc).toContain("path: '/guide'")
    expect(routerSrc).toContain('canBeStandalone: true')
    expect(routerSrc).not.toContain("to.path !== '/settings'")
    expect(settingsSrc).not.toContain("id: 'guide', name: 'Guide'")
    expect(settingsSrc).not.toContain("import UserGuide")
    expect(settingsSrc).not.toContain("activeTab = 'guide'")
  })

  it('nav item opens /guide in a new window', () => {
    expect(settingsSrc).toContain('function openGuide()')
    expect(settingsSrc).toContain("window.open(`${window.location.origin}/guide`")
    expect(settingsSrc).toContain('@click="openGuide"')
  })

  it('search and deep links still reach the guide', () => {
    expect(settingsSrc).toContain("match.tabId === 'guide'")
    expect(settingsSrc).toContain("tabQuery === 'guide'")
  })

  it('footer is the shared SiteFooter', () => {
    expect(settingsSrc).toContain("import SiteFooter from '@/components/SiteFooter.vue'")
    expect(settingsSrc).toContain('<SiteFooter class="settings-dock" />')
    expect(guideSrc).toContain('<SiteFooter />')
  })
})
