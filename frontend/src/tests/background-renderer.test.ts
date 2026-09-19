import { describe, test, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
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
})
