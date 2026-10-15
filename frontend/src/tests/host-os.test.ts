// DL-006: shortcuts follow the OS the backend runs on.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const host = vi.hoisted(() => ({ os: 'macos' }))

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn((url: string) => Promise.resolve({
      data: url === '/system/host'
        ? { os: host.os, primary_modifier: host.os === 'macos' ? 'cmd' : 'ctrl' }
        : { success: true, categories: {} },
    })),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}))

import { nativeKeys } from '@/composables/useHostOs'

describe('nativeKeys', () => {
  it('maps Ctrl to Cmd on macOS only', () => {
    expect(nativeKeys(['ctrl', 's'], 'macos')).toEqual(['cmd', 's'])
    expect(nativeKeys(['ctrl', 's'], 'windows')).toEqual(['ctrl', 's'])
    expect(nativeKeys(['ctrl', 's'], 'linux')).toEqual(['ctrl', 's'])
    expect(nativeKeys(['ctrl', 's'], 'unknown')).toEqual(['ctrl', 's'])
  })

  it('leaves backtick and Alt chords alone, like the backend', () => {
    expect(nativeKeys(['ctrl', '`'], 'macos')).toEqual(['ctrl', '`'])
    expect(nativeKeys(['ctrl', 'alt', 'down'], 'macos')).toEqual(['ctrl', 'alt', 'down'])
    expect(nativeKeys(['f12'], 'macos')).toEqual(['f12'])
  })
})

describe('welcome modal OS note', () => {
  beforeEach(() => { vi.resetModules(); setActivePinia(createPinia()) })

  async function note(os: string) {
    host.os = os
    const { default: WelcomeModal } = await import('@/components/WelcomeModal.vue')
    const wrapper = mount(WelcomeModal, { global: { stubs: { TemplateGallery: true, FontAwesomeIcon: true } } })
    await flushPromises()
    return wrapper.find('[data-test="host-os-note"]')
  }

  it('shows the detected macOS setup', async () => {
    const el = await note('macos')
    expect(el.text()).toContain('macOS')
    expect(el.text()).toContain('Cmd')
  })

  it('shows the detected Windows setup', async () => {
    const el = await note('windows')
    expect(el.text()).toContain('Windows')
    expect(el.text()).toContain('Ctrl')
  })
})
