import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useButtonStateStore } from '@/stores/buttonState'
import { useNotificationsStore } from '@/stores/notifications'
import { rejectedKeys } from '@/composables/useSetupStatus'

// DL-167: a widget whose saved key was rejected must say so, once.
describe('button state: rejected key', () => {
  beforeEach(() => { setActivePinia(createPinia()); rejectedKeys.value = {} })

  it('raises one warning toast and flags the key, even across several widgets', () => {
    const buttons = useButtonStateStore()
    const notes = useNotificationsStore()
    const result = { success: false, message: 'GitHub token rejected', data: { badge: '!', status: 'error', auth_error: 'GITHUB_TOKEN' } }

    buttons.markFinished('a', result)
    buttons.markFinished('b', result)

    expect(rejectedKeys.value.GITHUB_TOKEN).toBe(true)
    const warnings = notes.notifications.filter((n) => n.title === 'GitHub token rejected')
    expect(warnings).toHaveLength(1)
    expect(warnings[0].type).toBe('warning')
  })
})
