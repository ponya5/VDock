// DL-147 Task 4.4 + Phase 3 leftover (c) - install guidance one tap away on a
// phone, honest about plain HTTP, and the keep-awake toggle explains itself.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it, expect, afterEach } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { settingsSource } from './helpers/settingsSource'
import { installNote, installPlatform, installSteps } from '@/utils/installCopy'
import InstallSheet from '@/components/InstallSheet.vue'

const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1'
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36'
const IPAD_AS_MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15'

describe('installCopy', () => {
  it('tells iOS, Android and everything else apart', () => {
    expect(installPlatform(IPHONE)).toBe('ios')
    expect(installPlatform(IPAD_AS_MAC, 5)).toBe('ios')
    expect(installPlatform(IPAD_AS_MAC, 0)).toBe('other')
    expect(installPlatform(ANDROID)).toBe('android')
  })

  it('gives iOS the Share route and Android the menu route', () => {
    expect(installSteps('ios').join(' ')).toContain('Share')
    expect(installSteps('android').join(' ')).toContain('⋮')
  })

  it('is honest about plain http on Android, without jargon (DL-011)', () => {
    expect(installNote('android', false)).toContain('shortcut')
    expect(installNote('android', false)).not.toContain('USE_SSL')
    expect(installNote('android', true)).toBeNull()
  })

  it('warns iOS users that the Home Screen app signs in on its own (DL-011)', () => {
    expect(installNote('ios', false)).toContain('signs in on its own')
    expect(installNote('ios', true)).toContain('signs in on its own')
  })
})

describe('InstallSheet', () => {
  const mounted: VueWrapper[] = []
  afterEach(() => mounted.splice(0).forEach(w => w.unmount()))

  it('shows the steps for this device and closes on Got it', async () => {
    const wrapper = mount(InstallSheet)
    mounted.push(wrapper)
    expect(wrapper.findAll('li').length).toBeGreaterThan(0)
    await wrapper.find('.install-done').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})

describe('phone menu wiring', () => {
  const chrome = readFileSync(resolve(__dirname, '..', 'components', 'MobileDeckChrome.vue'), 'utf-8')

  it('offers Add to Home Screen only outside standalone mode', () => {
    expect(chrome).toContain('v-if="!isStandalone"')
    expect(chrome).toContain('data-testid="mc-menu-install"')
    expect(chrome).toContain('<InstallSheet v-if="showInstall"')
  })

  it('explains keep-awake without jargon when the real Wake Lock is missing (DL-011)', () => {
    expect(chrome).toContain('const keepAwakeNeedsApp = !hasWakeLockApi()')
    expect(chrome).toContain("raise Auto-Lock / Screen timeout in the phone's settings")
    expect(chrome).not.toContain('USE_SSL')
  })

  it('reuses the single install copy for the Connect page step', () => {
    expect(settingsSource()).toContain('CONNECT_INSTALL_STEP')
  })
})
