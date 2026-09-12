// Feature: ai-dev-integration-packs, Property 1.1: the picker is generated from
// the backend catalog, so it cannot offer an action the backend cannot run.
//
// ButtonActionsSidebar.vue used to hardcode 46 action strings; 22 named an
// action type ActionExecutor had no handler for and failed on press. Most were
// not missing features -- `volume_up` and `media_play_pause` are `cross_platform`
// configs, not action types, and emitting the entry id as the type is what broke
// them. These tests pin that distinction down.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useActionCatalogStore, type ActionSpec } from '@/stores/actionCatalog'
import ButtonActionsSidebar from '@/components/ButtonActionsSidebar.vue'

const get = vi.fn()
vi.mock('@/api/client', () => ({ default: { get: (...a: any[]) => get(...a) } }))

function spec(overrides: Partial<ActionSpec> = {}): ActionSpec {
  return {
    id: 'volume_up',
    label: 'Volume Up',
    category: 'media',
    icon: ['fas', 'volume-up'],
    action_type: 'cross_platform',
    description: 'Raise system volume.',
    default_config: { action: 'volume_up' },
    config_fields: [],
    runs_on: 'backend',
    display_only: false,
    long_running: false,
    keywords: ['sound', 'louder'],
    ...overrides
  }
}

const CATALOG = {
  categories: [
    { id: 'media', label: 'Media Control', icon: ['fas', 'music'] },
    { id: 'metrics', label: 'System Metrics', icon: ['fas', 'chart-line'] },
    { id: 'empty', label: 'Nothing Here', icon: ['fas', 'ban'] }
  ],
  actions: [
    spec(),
    spec({ id: 'volume_mute', label: 'Mute', default_config: { action: 'volume_mute' } }),
    spec({
      id: 'metric_cpu_usage',
      label: 'CPU Usage',
      category: 'metrics',
      action_type: 'metric_cpu_usage',
      default_config: {},
      runs_on: 'widget',
      display_only: true,
      keywords: ['cpu']
    })
  ]
}

beforeEach(() => {
  setActivePinia(createPinia())
  get.mockReset()
  get.mockResolvedValue({ data: CATALOG })
})

describe('action catalog store', () => {
  it('loads actions and categories from the API', async () => {
    const store = useActionCatalogStore()
    await store.load()

    expect(get).toHaveBeenCalledWith('/actions/catalog')
    expect(store.actions).toHaveLength(3)
    expect(store.categories).toHaveLength(3)
  })

  it('does not refetch once loaded', async () => {
    const store = useActionCatalogStore()
    await store.load()
    await store.load()

    expect(get).toHaveBeenCalledTimes(1)
  })

  it('refetches when forced', async () => {
    const store = useActionCatalogStore()
    await store.load()
    await store.load(true)

    expect(get).toHaveBeenCalledTimes(2)
  })

  it('records an error instead of throwing when the request fails', async () => {
    get.mockRejectedValue(new Error('backend down'))
    const store = useActionCatalogStore()

    await store.load()

    expect(store.error).toBe('backend down')
    expect(store.actions).toEqual([])
  })

  it('builds the action type AND config from an entry', async () => {
    // The heart of the old bug: volume_up is a cross_platform config.
    const store = useActionCatalogStore()
    await store.load()

    expect(store.toButtonAction(store.byId.volume_up)).toEqual({
      type: 'cross_platform',
      config: { action: 'volume_up' }
    })
  })

  it('copies the default config so entries are not mutated', async () => {
    const store = useActionCatalogStore()
    await store.load()

    const action = store.toButtonAction(store.byId.volume_up)
    ;(action.config as Record<string, unknown>).action = 'tampered'

    expect(store.byId.volume_up.default_config.action).toBe('volume_up')
  })

  it('reports widget types as display-only', async () => {
    const store = useActionCatalogStore()
    await store.load()

    expect(store.displayOnlyTypes.has('metric_cpu_usage')).toBe(true)
    expect(store.displayOnlyTypes.has('cross_platform')).toBe(false)
  })

  it('falls back to a naming convention before the catalog loads', () => {
    const store = useActionCatalogStore()

    // Backend unreachable: widgets must still not dispatch.
    expect(store.displayOnlyTypes.has('metric_cpu_temperature')).toBe(true)
    expect(store.displayOnlyTypes.has('metric_cpu_power')).toBe(true)
    expect(store.displayOnlyTypes.has('time_timer')).toBe(true)
    expect(store.displayOnlyTypes.has('weather')).toBe(true)
    expect(store.displayOnlyTypes.has('calendar')).toBe(true)
    // ...and real actions must still dispatch.
    expect(store.displayOnlyTypes.has('cross_platform')).toBe(false)
    expect(store.displayOnlyTypes.has('hotkey')).toBe(false)
  })

  it('drops categories with no actions', async () => {
    const store = useActionCatalogStore()
    await store.load()

    expect(store.populatedCategories.map((c) => c.id)).toEqual(['media', 'metrics'])
  })

  it('searches label, description and keywords', async () => {
    const store = useActionCatalogStore()
    await store.load()

    expect(store.search('mute').map((a) => a.id)).toEqual(['volume_mute'])
    expect(store.search('louder').map((a) => a.id)).toContain('volume_up')
    expect(store.search('raise system').map((a) => a.id)).toContain('volume_up')
    expect(store.search('')).toHaveLength(3)
  })
})

describe('ButtonActionsSidebar', () => {
  async function mountSidebar() {
    const wrapper = mount(ButtonActionsSidebar, {
      props: { isOpen: true },
      global: { stubs: { FontAwesomeIcon: true } }
    })
    await useActionCatalogStore().load()
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('renders a row per catalog action', async () => {
    const wrapper = await mountSidebar()

    expect(wrapper.findAll('.action-item')).toHaveLength(3)
    expect(wrapper.text()).toContain('Volume Up')
    expect(wrapper.text()).toContain('CPU Usage')
  })

  it('renders only categories that have actions', async () => {
    const wrapper = await mountSidebar()

    expect(wrapper.text()).toContain('Media Control')
    expect(wrapper.text()).not.toContain('Nothing Here')
  })

  it('emits the whole spec, not a bare action-type string', async () => {
    const wrapper = await mountSidebar()

    await wrapper.findAll('.action-item')[0].trigger('click')

    const [emitted] = wrapper.emitted('selectAction')![0] as [ActionSpec]
    expect(emitted.action_type).toBe('cross_platform')
    expect(emitted.default_config).toEqual({ action: 'volume_up' })
  })

  it('filters by search across categories', async () => {
    const wrapper = await mountSidebar()

    await wrapper.find('.search-input').setValue('cpu')

    const labels = wrapper.findAll('.action-item').map((i) => i.text())
    expect(labels).toHaveLength(1)
    expect(labels[0]).toContain('CPU Usage')
  })

  it('disables an action whose integration is unavailable', async () => {
    get.mockResolvedValue({
      data: {
        categories: CATALOG.categories,
        actions: [spec({ unavailable_reason: 'gh CLI not found on PATH' })]
      }
    })
    const wrapper = await mountSidebar()

    const item = wrapper.find('.action-item')
    expect(item.attributes('disabled')).toBeDefined()
    expect(item.attributes('title')).toBe('gh CLI not found on PATH')

    await item.trigger('click')
    expect(wrapper.emitted('selectAction')).toBeUndefined()
  })

  it('surfaces a load failure with a retry', async () => {
    get.mockRejectedValue(new Error('backend down'))
    const wrapper = await mountSidebar()

    expect(wrapper.find('.catalog-error').text()).toContain('backend down')
    expect(wrapper.find('.retry-btn').exists()).toBe(true)
  })
})
