// DL-147 Task 1.6 - hold keys own their touch (no browser pan, so no
// pointercancel mid-sentence) and a touch long-press can never open the
// button editor; phones never open it at all.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const dashboardState = { isEditMode: false }

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    currentProfile: null, currentScene: null, currentPage: null,
    get isEditMode() { return dashboardState.isEditMode },
    executeAction: vi.fn(() => Promise.resolve({ success: false })),
    executeButtonAction: vi.fn(() => Promise.resolve({ success: false })),
  }),
}))

import DeckButton from '@/components/DeckButton.vue'
import { useActionCatalogStore } from '@/stores/actionCatalog'
import type { Button } from '@/types'

const spec = (action_type: string, press: string) => ({
  id: action_type, action_type, press, label: action_type, category: 'ai',
  icon: ['fas', 'microphone'], description: '', default_config: {},
  config_fields: [], runs_on: 'backend', display_only: false,
  long_running: false, keywords: [],
})

function makeButton(action: Record<string, unknown>): Button {
  return {
    id: 'b1', label: 'Key', secondary_label: '', icon: ['fas', 'microphone'],
    icon_type: 'fontawesome', shape: 'rounded', position: { col: 0, row: 0 },
    size: { cols: 1, rows: 1 }, enabled: true, action,
  } as Button
}

const mounted: VueWrapper[] = []

function mountKey(action: Record<string, unknown>) {
  setActivePinia(createPinia())
  useActionCatalogStore().actions = [spec('agent_dictate', 'hold'), spec('agent_prompt', 'run')] as any
  const wrapper = mount(DeckButton, {
    props: { button: makeButton(action) },
    global: { stubs: { FontAwesomeIcon: true } },
  })
  wrapper.element.setPointerCapture = () => {}
  mounted.push(wrapper)
  return wrapper
}

afterEach(() => {
  while (mounted.length) mounted.pop()!.unmount()
  dashboardState.isEditMode = false
})

describe('is-hold class', () => {
  it('marks catalog hold actions, release_action keys and press-trigger keys', () => {
    expect(mountKey({ type: 'agent_dictate', config: {} }).classes()).toContain('is-hold')
    expect(mountKey({ type: 'agent_prompt', config: {}, release_action: { type: 'agent_prompt', config: {} } }).classes()).toContain('is-hold')
    expect(mountKey({ type: 'agent_prompt', config: {}, trigger: 'press' }).classes()).toContain('is-hold')
  })

  it('leaves plain keys and sliders alone', () => {
    expect(mountKey({ type: 'agent_prompt', config: {} }).classes()).not.toContain('is-hold')
    expect(mountKey({ type: 'slider', config: {}, trigger: 'press' }).classes()).not.toContain('is-hold')
  })
})

describe('contextmenu (long-press) gate', () => {
  it('a touch long-press never emits edit and is default-prevented', async () => {
    const wrapper = mountKey({ type: 'agent_dictate', config: {} })
    await wrapper.trigger('pointerdown', { pointerId: 1, pointerType: 'touch' })
    const event = new Event('contextmenu', { cancelable: true, bubbles: true })
    wrapper.element.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
    expect(wrapper.emitted('edit')).toBeUndefined()
  })

  it('a mouse right-click still opens the editor on desktop', async () => {
    const wrapper = mountKey({ type: 'agent_prompt', config: {} })
    await wrapper.trigger('pointerdown', { pointerId: 1, pointerType: 'mouse' })
    await wrapper.trigger('contextmenu')
    expect(wrapper.emitted('edit')).toHaveLength(1)
  })

  it('a contextmenu with no preceding pointer (not a mouse) does not edit', async () => {
    const wrapper = mountKey({ type: 'agent_prompt', config: {} })
    await wrapper.trigger('contextmenu')
    expect(wrapper.emitted('edit')).toBeUndefined()
  })
})

describe('hold key safety', () => {
  it('pointercancel still releases a held key (never wedged)', async () => {
    const wrapper = mountKey({ type: 'agent_dictate', config: {} })
    await wrapper.trigger('pointerdown', { pointerId: 1, pointerType: 'touch' })
    await wrapper.trigger('pointercancel')
    await wrapper.trigger('pointercancel')
    expect(wrapper.emitted('press')).toHaveLength(1)
    expect(wrapper.emitted('release')).toHaveLength(1)
  })
})

describe('useButtonActions.handleButtonEdit', () => {
  let setPhone: (phone: boolean) => Promise<ReturnType<typeof import('@/composables/useButtonActions').useButtonActions>>

  beforeEach(() => {
    setPhone = async (phone) => {
      vi.resetModules()
      const size = phone ? 390 : 1400
      Object.defineProperty(window, 'innerWidth', { value: size, configurable: true })
      Object.defineProperty(window, 'innerHeight', { value: phone ? 844 : 900, configurable: true })
      Object.defineProperty(window, 'screen', { value: { width: size, height: phone ? 844 : 900 }, configurable: true })
      Object.defineProperty(navigator, 'maxTouchPoints', { value: phone ? 5 : 0, configurable: true })
      window.matchMedia = vi.fn().mockImplementation((q: string) => ({
        matches: phone && q === '(pointer: coarse)',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })) as unknown as typeof window.matchMedia
      setActivePinia(createPinia())
      return (await import('@/composables/useButtonActions')).useButtonActions()
    }
  })

  it('is a no-op on the phone class outside edit mode', async () => {
    const actions = await setPhone(true)
    actions.handleButtonEdit(makeButton({ type: 'agent_prompt', config: {} }))
    expect(actions.editingButton.value).toBeNull()
  })

  it('opens the editor on desktop', async () => {
    const actions = await setPhone(false)
    actions.handleButtonEdit(makeButton({ type: 'agent_prompt', config: {} }))
    expect(actions.editingButton.value?.id).toBe('b1')
  })
})
