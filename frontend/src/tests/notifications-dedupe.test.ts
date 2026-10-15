import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationsStore } from '@/stores/notifications'

describe('notifications store: identical alerts', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('shows one toast when the same error repeats', () => {
    const store = useNotificationsStore()

    const firstId = store.error('Action Failed', 'Command failed: boom')
    const secondId = store.error('Action Failed', 'Command failed: boom')

    expect(secondId).toBe(firstId)
    expect(store.notifications).toHaveLength(1)
  })

  it('keeps different errors separate', () => {
    const store = useNotificationsStore()

    store.error('Action Failed', 'first problem')
    store.error('Action Failed', 'second problem')

    expect(store.notifications).toHaveLength(2)
  })

  it('shows the error again after the previous one was dismissed', () => {
    const store = useNotificationsStore()

    const firstId = store.error('Action Failed', 'boom')
    store.markAsRead(firstId)
    store.error('Action Failed', 'boom')

    expect(store.notifications).toHaveLength(2)
  })

  it('does not collapse repeated success messages', () => {
    const store = useNotificationsStore()

    store.success('Action Executed', 'Volume 50%')
    store.success('Action Executed', 'Volume 50%')

    expect(store.notifications).toHaveLength(2)
  })
})
