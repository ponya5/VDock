// DL-165 — AI agent toasts are opted into per moment and never hidden by the app-level toast level.
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { describeAgentChange } from '@/services/agentToasts'
import { useSettingsStore } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'

const on = { agentToastIdle: true, agentToastPermission: true, agentToastWorking: true }
const off = { agentToastIdle: false, agentToastPermission: false, agentToastWorking: false }

describe('describeAgentChange', () => {
  it('toasts the three moments when enabled', () => {
    expect(describeAgentChange('working', 'ready', on)?.verb).toMatch(/waiting for you/)
    expect(describeAgentChange('working', 'permission', on)?.type).toBe('warning')
    expect(describeAgentChange('ready', 'working', on)?.verb).toMatch(/working/)
  })
  it('is silent when switched off, unchanged, or on first sighting', () => {
    expect(describeAgentChange('working', 'ready', off)).toBeNull()
    expect(describeAgentChange('ready', 'ready', on)).toBeNull()
    expect(describeAgentChange(undefined, 'ready', on)).toBeNull()
    expect(describeAgentChange(undefined, 'working', on)).toBeNull()
  })
})

describe('toast filtering', () => {
  beforeEach(() => setActivePinia(createPinia()))
  const add = (n: ReturnType<typeof useNotificationsStore>, type: 'success' | 'error', agent = false) =>
    n.addNotification({ type, title: 't', message: type + (agent ? '-agent' : ''), duration: 0, dismissible: true, agent })

  it('app level all / errors-only / off, with agent toasts always allowed', () => {
    const s = useSettingsStore(); const n = useNotificationsStore()
    add(n, 'success'); add(n, 'error'); add(n, 'success', true)
    s.toastLevel = 'all'
    expect(n.toasts.length).toBe(3)
    s.toastLevel = 'errors-only'
    expect(n.toasts.map(t => t.message).sort()).toEqual(['error', 'success-agent'])
    s.toastLevel = 'off'
    expect(n.toasts.map(t => t.message)).toEqual(['success-agent'])
  })
})
