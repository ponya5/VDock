// DL-147 Task 3.3 - the Settings "Touch mode" row is per device on phones and
// tablets (device pref, never the shared setting) and unchanged elsewhere.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import type { DeviceClass } from '@/composables/useDeviceClass'

const deviceClass = ref<DeviceClass>('tablet')
vi.mock('@/composables/useDeviceClass', () => ({
  useDeviceClass: () => ({
    deviceClass,
    layoutClass: deviceClass,
    orientation: ref('portrait'),
    viewportWidth: ref(820),
    isTouch: ref(true),
    isCompactTouch: ref(false),
    isStandalone: ref(false),
  }),
}))

import AppearanceButtons from '@/components/settings/panels/AppearanceButtons.vue'
import { useDevicePrefs } from '@/services/devicePrefs'
import { useSettingsStore } from '@/stores/settings'

const mounted: VueWrapper[] = []

function mountRow() {
  const wrapper = mount(AppearanceButtons, {
    props: { animation: 'none', iconLoop: 'none', effect: 'none' },
    global: { stubs: { DeckButton: true, ButtonDesignPicker: true, Collapse: true, FontAwesomeIcon: true } },
    attachTo: document.body,
  })
  mounted.push(wrapper)
  return wrapper
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  useDevicePrefs().touchMode = 'auto'
})

afterEach(() => {
  while (mounted.length) mounted.pop()!.unmount()
})

describe('Touch mode row', () => {
  it.each<DeviceClass>(['phone', 'tablet'])('binds to the device pref on a %s', async (cls) => {
    deviceClass.value = cls
    const settings = useSettingsStore()
    const shared = settings.touchMode
    const wrapper = mountRow()

    const group = wrapper.find('[aria-label="Touch mode (this device)"]')
    expect(group.exists()).toBe(true)
    expect(group.findAll('input').map((i) => i.attributes('value'))).toEqual(['auto', 'normal', 'touch-friendly', 'tablet'])

    await group.find('input[value="tablet"]').setValue(true)
    expect(useDevicePrefs().touchMode).toBe('tablet')
    expect(settings.touchMode).toBe(shared)
  })

  it('shows the resolved multiplier on Auto for the device class', () => {
    deviceClass.value = 'tablet'
    const auto = mountRow().find('[aria-label="Touch mode (this device)"] input[value="auto"]').element.closest('label')!
    expect(auto.textContent).toContain('1.5×')
  })

  it.each<DeviceClass>(['desktop', 'panel'])('keeps the shared control on the %s', async (cls) => {
    deviceClass.value = cls
    const settings = useSettingsStore()
    const wrapper = mountRow()

    expect(wrapper.find('[aria-label="Touch mode (this device)"]').exists()).toBe(false)
    const group = wrapper.find('[aria-label="Touch mode"]')
    expect(group.findAll('input').map((i) => i.attributes('value'))).toEqual(['normal', 'touch-friendly', 'tablet'])

    await group.find('input[value="touch-friendly"]').setValue(true)
    expect(settings.touchMode).toBe('touch-friendly')
    expect(useDevicePrefs().touchMode).toBe('auto')
  })
})
