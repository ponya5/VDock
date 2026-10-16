// DL-007 - macOS drops VDock's keystrokes until Accessibility is granted. The
// setup status reports it up front (Overview "Needs attention") and Agent
// alerts offers the one-click route to the grant, instead of every Claude /
// Cursor button failing one by one.
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { settingsSource } from './helpers/settingsSource'

const client = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }))
vi.mock('@/api/client', () => ({ default: client }))

import { useSetupStatus } from '@/composables/useSetupStatus'

function answer(accessibility: boolean | null) {
  client.get.mockImplementation((url: string) => {
    if (url === '/system/permissions') return Promise.resolve({ data: { accessibility } })
    if (url === '/config/integrations') return Promise.resolve({ data: { items: [], env_file: '' } })
    return Promise.resolve({ data: { agents: {} } })
  })
}

beforeEach(() => vi.clearAllMocks())

describe('setup status: macOS keystroke permission', () => {
  it('flags a Mac without the Accessibility grant', async () => {
    answer(false)
    const status = useSetupStatus()
    await status.refresh()
    expect(status.keystrokesBlocked.value).toBe(true)
  })

  it('stays quiet once granted, and on Windows (nothing to grant)', async () => {
    const status = useSetupStatus()
    answer(true)
    await status.refresh()
    expect(status.keystrokesBlocked.value).toBe(false)
    answer(null)
    await status.refresh()
    expect(status.keystrokesBlocked.value).toBe(false)
  })
})

describe('settings UI', () => {
  const view = settingsSource()

  it('lists it under Needs attention and links to the fix', () => {
    expect(view).toContain("id: 'mac-accessibility'")
    expect(view).toContain('macOS is blocking VDock from pressing keys')
  })

  it('offers the grant from Agent alerts (this computer only)', () => {
    expect(view).toContain('data-testid="mac-accessibility"')
    expect(view).toContain("apiClient.post('/system/permissions/accessibility')")
    expect(view).toContain(':disabled="!isLocalDevice" @click="openAccessibilitySettings"')
  })
})
