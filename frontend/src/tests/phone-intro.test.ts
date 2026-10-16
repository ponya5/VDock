// DL-011: phones/tablets get a 3-card intro once per device; the desktop tour
// skips them and the welcome toast pointed at Settings they can't open.
import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PhoneIntro from '@/components/PhoneIntro.vue'

const opts = { global: { stubs: { FontAwesomeIcon: true, Teleport: true } } }

beforeEach(() => localStorage.clear())

describe('PhoneIntro', () => {
  it('walks three cards, then never shows again on this device', async () => {
    const w = mount(PhoneIntro, opts)
    expect(w.text()).toContain('Your deck, in your hand')
    await w.find('[data-action="intro-next"]').trigger('click')
    expect(w.text()).toContain('Your coding wingman')
    await w.find('[data-action="intro-next"]').trigger('click')
    expect(w.text()).toContain('Add to Home Screen')
    await w.find('[data-action="intro-next"]').trigger('click')
    expect(w.find('[data-testid="phone-intro"]').exists()).toBe(false)
    expect(mount(PhoneIntro, opts).find('[data-testid="phone-intro"]').exists()).toBe(false)
  })

  it('can be skipped from the first card', async () => {
    const w = mount(PhoneIntro, opts)
    await w.find('.pi-skip').trigger('click')
    expect(w.find('[data-testid="phone-intro"]').exists()).toBe(false)
    expect(localStorage.getItem('vdock.phoneIntroSeen')).toBe('1')
  })
})
