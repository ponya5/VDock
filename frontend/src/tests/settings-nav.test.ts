// DL-146 3b: the mounted Settings shell - sections in the sidebar, legacy deep
// links, search and `?anchor=` scrolling all resolve through the registry.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

const mockGet = vi.hoisted(() => (url: string): unknown => {
  if (url.includes('profiles')) return { profiles: [] }
  if (url.includes('config/integrations')) {
    return { env_file: 'backend/.env', items: [{ id: 'GITHUB_TOKEN', label: 'GitHub token', kind: 'secret', configured: false, reason: '', help_url: 'https://github.com/settings/tokens', unlocks: 'Live PR and CI buttons' }] }
  }
  return {}
})

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn((url: string) => Promise.resolve({ data: mockGet(url) })),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}))
import SettingsView from '@/views/SettingsView.vue'

const scrollIntoView = vi.fn()
let wrapper: VueWrapper | undefined

async function openSettings(url: string) {
  setActivePinia(createPinia())
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: {} }, { path: '/settings', component: SettingsView }],
  })
  await router.push(url)
  await router.isReady()
  wrapper = mount(SettingsView, {
    attachTo: document.body, // the anchor lookup uses document.getElementById
    global: {
      plugins: [router],
      stubs: { FontAwesomeIcon: true, TouchModeSelector: true, AppShortcutManager: true },
    },
  })
  await flushPromises()
  return wrapper
}

const activeSection = (w: VueWrapper) => w.find('.nav-rail-item[aria-current="page"]').text()
const activePage = (w: VueWrapper) => w.find('.subtab[aria-selected="true"]').text()

beforeEach(() => {
  sessionStorage.clear()
  Element.prototype.scrollIntoView = scrollIntoView
  Element.prototype.scrollTo = vi.fn() as unknown as typeof Element.prototype.scrollTo
  scrollIntoView.mockClear()
})

afterEach(async () => {
  // A leaked SettingsView mount lets its async loads land after teardown.
  wrapper?.unmount()
  wrapper = undefined
  await new Promise((resolve) => setTimeout(resolve, 20))
})

describe('Settings shell navigation', () => {
  it('lists the seven sections plus the guide link', async () => {
    const w = await openSettings('/settings')
    const names = w.findAll('.nav-rail-item').map((el) => el.text())
    expect(names).toEqual(['Overview', 'Appearance', 'Agents & automation', 'Integrations', 'Devices & network', 'System', 'About', 'Guide'])
  })

  it('opens Devices > Connect for the legacy ?tab=connect link', async () => {
    const w = await openSettings('/settings?tab=connect')
    expect(activeSection(w)).toBe('Devices & network')
    expect(activePage(w)).toBe('Connect a device')
  })

  it('opens a page named by ?section=&page=', async () => {
    const w = await openSettings('/settings?section=agents&page=alerts')
    expect(activeSection(w)).toBe('Agents & automation')
    expect(activePage(w)).toBe('Agent alerts')
  })

  it('jumps to Security when the search result for "password" is picked', async () => {
    const w = await openSettings('/settings')
    await w.find('#setting-search').setValue('password')
    await w.find('.nav-result').trigger('click')
    await flushPromises()
    expect(activeSection(w)).toBe('Devices & network')
    expect(activePage(w)).toBe('Security')
  })

  it('scrolls to the panel named by ?anchor=', async () => {
    await openSettings('/settings?section=appearance&page=buttons&anchor=touch')
    expect(scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' })
  })

  it('lands on Overview and links a missing GitHub token to Accounts & keys', async () => {
    const w = await openSettings('/settings')
    expect(activeSection(w)).toBe('Overview')
    const row = w.find('.attention-row')
    expect(row.text()).toContain('GitHub token not set')
    await row.trigger('click')
    await flushPromises()
    expect(activeSection(w)).toBe('Integrations')
    expect(w.find('[data-key="GITHUB_TOKEN"]').text()).toContain('Not set')
  })

  it.each(['token', 'github'])('finds Accounts & keys when searching "%s"', async (word) => {
    const w = await openSettings('/settings')
    await w.find('#setting-search').setValue(word)
    await w.find('.nav-result').trigger('click')
    await flushPromises()
    expect(activeSection(w)).toBe('Integrations')
    expect(activePage(w)).toBe('Accounts & keys')
  })
})