import { describe, test, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { defineComponent, nextTick } from 'vue'
import BackgroundRenderer from '../components/backgrounds/BackgroundRenderer.vue'
import { useSettingsStore } from '../stores/settings'

describe('BackgroundRenderer', () => {
  test('renders a component background and swaps reactively, with no timers', async () => {
    setActivePinia(createPinia())
    const setInterval = vi.spyOn(globalThis, 'setInterval')

    const store = useSettingsStore()
    store.background = 'aurora'

    const wrapper = mount(BackgroundRenderer, {
      global: { stubs: { Aurora: true, Silk: true } },
    })
    await nextTick()
    expect(wrapper.findComponent({ name: 'Aurora' }).exists()).toBe(true)

    store.background = 'silk'
    await nextTick()
    expect(wrapper.findComponent({ name: 'Aurora' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'Silk' }).exists()).toBe(true)

    // The flicker came from polling the store. Reactivity must carry it now.
    expect(setInterval).not.toHaveBeenCalled()
  })

  test('renders nothing for a css-kind background', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    store.background = 'ocean-breeze'

    const wrapper = mount(BackgroundRenderer)
    await nextTick()
    expect(wrapper.find('.background-renderer').element.children.length).toBe(0)
  })

  test('falls back when a component background throws on init', async () => {
    setActivePinia(createPinia())
    const store = useSettingsStore()
    store.background = 'balatro'

    // Simulates a device where WebGL init throws (context refused/lost):
    // the ported components never call their declared onError, so the
    // throw must be captured by BackgroundHost — not escape uncaught.
    const ThrowingBalatro = defineComponent({
      name: 'Balatro',
      setup() {
        throw new Error('WebGL unavailable')
      },
    })
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(BackgroundRenderer, {
      global: { stubs: { Balatro: ThrowingBalatro } },
    })
    await nextTick()

    expect(wrapper.findComponent(ThrowingBalatro).exists()).toBe(false)
    expect(wrapper.find('.background-renderer__fallback').exists()).toBe(true)
    expect(warn).toHaveBeenCalledWith(
      '[background] fell back to gradient:',
      'balatro',
      expect.any(Error),
    )
    warn.mockRestore()
    error.mockRestore()
  })
})
