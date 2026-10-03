// DL-147 Task 2.3 - the phone as an approval remote: the needs-you count, the
// overflow-menu entry + badge, the device-local layout toggle, and waking the
// screensaver when a session asks for permission.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { computed, defineComponent, nextTick, ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import type { DeviceClass } from '@/composables/useDeviceClass'

const socketHandlers = new Map<string, (payload: unknown) => void>()
const apiGet = vi.fn()
const apiPut = vi.fn()

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (payload: unknown) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
  },
}))
vi.mock('@/api/client', () => ({
  default: { get: (...a: unknown[]) => apiGet(...a), put: (...a: unknown[]) => apiPut(...a), post: vi.fn(), delete: vi.fn() },
}))

const deviceClass = ref<DeviceClass>('phone')
vi.mock('@/composables/useDeviceClass', () => ({
  useDeviceClass: () => ({ deviceClass, layoutClass: computed(() => deviceClass.value) }),
}))

vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({ appScanningEnabled: false, agentWaitingGlowEnabled: true }),
}))
vi.mock('@/composables/useAppIntegrations', () => ({ useAppIntegrations: () => ref([]) }))
vi.mock('@/services/appDetection', () => ({
  startAppDetection: vi.fn(),
  stopAppDetection: vi.fn(),
  loadProfileMaps: vi.fn(),
  sceneAppIsLive: () => false,
  sceneLogo: () => null,
}))
vi.mock('@/composables/useElectron', () => ({
  useElectron: () => ({
    quitApp: vi.fn(),
    isElectron: () => false,
    toggleFullscreen: vi.fn().mockResolvedValue(false),
    isFullscreen: () => false,
  }),
}))
vi.mock('@/composables/useVdockRefresh', () => ({ refreshVdock: vi.fn() }))

import MobileDeckChrome from '@/components/MobileDeckChrome.vue'
import { useNeedsYouCount } from '@/composables/useNeedsYouCount'
import { useWakeOnPermission } from '@/composables/useWakeOnPermission'
import { initAgentState } from '@/services/agentState'
import { dismissAgentWaiting } from '@/services/agentWaiting'
import { useDevicePrefs } from '@/services/devicePrefs'
import { closeMissionControl, missionControlOpen } from '@/services/missionControl'

type Entry = { source: string; state: string; prompted?: boolean; ts: number; message: string; cwd: string; project: string }

function entry(source: string, state: string, over: Partial<Entry> = {}): Entry {
  return { source, state, prompted: true, ts: 1, message: '', cwd: '', project: '', ...over }
}

function pushStates(states: Record<string, Entry>) {
  socketHandlers.get('agent_state')?.({ states })
}

const mounted: VueWrapper[] = []

function mountChrome() {
  const wrapper = mount(MobileDeckChrome, {
    props: { scenes: [], currentSceneIndex: 0, totalPages: 1, currentPageIndex: 0 },
    global: { stubs: { FontAwesomeIcon: true } },
    attachTo: document.body,
  })
  mounted.push(wrapper)
  return wrapper
}

beforeEach(() => {
  localStorage.clear()
  apiGet.mockReset().mockResolvedValue({ data: { states: {} } })
  apiPut.mockReset()
  deviceClass.value = 'phone'
  useDevicePrefs().layout = 'fit'
  closeMissionControl()
  initAgentState()
  pushStates({})
})

afterEach(() => {
  while (mounted.length) mounted.pop()!.unmount()
})

describe('useNeedsYouCount', () => {
  it('counts permission prompts and prompted idle agents, not working or fresh ones', async () => {
    const count = useNeedsYouCount()
    expect(count.value).toBe(0)
    pushStates({
      claude: entry('claude', 'permission'),
      cursor: entry('cursor', 'ready'),
      codex: entry('codex', 'ready', { prompted: false }),
      devin: entry('devin', 'working'),
    })
    await nextTick()
    expect(count.value).toBe(2)
  })

  it('drops a snoozed idle agent', async () => {
    pushStates({ cursor: entry('cursor', 'ready', { ts: 7 }) })
    const count = useNeedsYouCount()
    expect(count.value).toBe(1)
    dismissAgentWaiting('cursor')
    await nextTick()
    expect(count.value).toBe(0)
  })
})

describe('phone overflow menu', () => {
  it('shows no badge at 0 and the count above 0', async () => {
    const wrapper = mountChrome()
    expect(wrapper.find('.mc-more-badge').exists()).toBe(false)

    pushStates({ claude: entry('claude', 'permission'), cursor: entry('cursor', 'ready') })
    await nextTick()
    expect(wrapper.find('.mc-more-badge').exists()).toBe(true)

    await wrapper.find('.mc-more-btn').trigger('click')
    expect(wrapper.find('[data-testid="mc-menu-mission"]').text()).toContain('2')
  })

  it('opens Mission Control from the menu and closes the menu', async () => {
    const wrapper = mountChrome()
    await wrapper.find('.mc-more-btn').trigger('click')
    await wrapper.find('[data-testid="mc-menu-mission"]').trigger('click')
    expect(missionControlOpen.value).toBe(true)
    expect(wrapper.find('.mc-menu').exists()).toBe(false)
  })

  it('keeps the menu to six items (Add to Home Screen included in a browser tab)', async () => {
    const wrapper = mountChrome()
    await wrapper.find('.mc-more-btn').trigger('click')
    expect(wrapper.findAll('.mc-menu-item')).toHaveLength(6)
  })

  it('switches keep-awake on this device only', async () => {
    useDevicePrefs().keepAwake = true
    const wrapper = mountChrome()
    await wrapper.find('.mc-more-btn').trigger('click')
    const toggle = wrapper.find('[data-testid="mc-menu-keep-awake"]')
    expect(toggle.text()).toContain('On')

    await toggle.trigger('click')
    expect(useDevicePrefs().keepAwake).toBe(false)
    expect(apiPut).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="mc-menu-keep-awake"]').text()).toContain('Off')
    useDevicePrefs().keepAwake = true
  })

  it('flips the device layout pref without any settings write', async () => {
    const wrapper = mountChrome()
    await wrapper.find('.mc-more-btn').trigger('click')
    const toggle = wrapper.find('[data-testid="mc-menu-layout"]')
    expect(toggle.text()).toContain('Fit to screen')

    await toggle.trigger('click')
    await flushPromises()
    expect(useDevicePrefs().layout).toBe('designed')
    expect(JSON.parse(localStorage.getItem('vdock_device_prefs') ?? '{}').layout).toBe('designed')
    expect(apiPut).not.toHaveBeenCalled()

    await wrapper.find('.mc-more-btn').trigger('click')
    expect(wrapper.find('[data-testid="mc-menu-layout"]').text()).toContain('As designed')
  })
})

describe('wake the screensaver on a permission prompt', () => {
  function mountWake(wake: () => void) {
    const wrapper = mount(defineComponent({ setup() { useWakeOnPermission(wake); return () => null } }))
    mounted.push(wrapper)
    return wrapper
  }

  it('wakes on phone and tablet classes', async () => {
    for (const cls of ['phone', 'tablet'] as const) {
      pushStates({})
      deviceClass.value = cls
      const wake = vi.fn()
      mountWake(wake)
      pushStates({ claude: entry('claude', 'permission', { ts: 5 }) })
      await nextTick()
      expect(wake).toHaveBeenCalledTimes(1)
    }
  })

  it('does nothing on desktop or the panel (unchanged)', async () => {
    for (const cls of ['desktop', 'panel'] as const) {
      pushStates({})
      deviceClass.value = cls
      const wake = vi.fn()
      mountWake(wake)
      pushStates({ claude: entry('claude', 'permission', { ts: 5 }) })
      await nextTick()
      expect(wake).not.toHaveBeenCalled()
    }
  })

  it('ignores states that are not a permission prompt', async () => {
    const wake = vi.fn()
    mountWake(wake)
    pushStates({ claude: entry('claude', 'ready') })
    await nextTick()
    expect(wake).not.toHaveBeenCalled()
  })
})
