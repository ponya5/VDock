// Feature: ai-dev-integration-packs, Property 1.3 (face half): a press is
// visible on the button itself.
//
// Buttons were fire-and-forget. That is fine for "volume up" and useless for a
// Claude prompt that runs for half a minute -- the deck looked like it had
// ignored the tap until a toast appeared. Widget buttons also had no way to
// show a value (a PR count, a CI result) on their face.
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useButtonStateStore } from '@/stores/buttonState'

beforeEach(() => {
  setActivePinia(createPinia())
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('button state', () => {
  it('starts with no state at all', () => {
    const store = useButtonStateStore()
    expect(store.get('btn_1')).toBeUndefined()
  })

  it('marks a button running while its action is in flight', () => {
    const store = useButtonStateStore()
    store.markRunning('btn_1')

    expect(store.get('btn_1')!.status).toBe('running')
    expect(store.runningCount).toBe(1)
  })

  it('flashes success and settles back to idle', () => {
    const store = useButtonStateStore()
    store.markRunning('btn_1')
    store.markFinished('btn_1', { success: true, message: 'Done' })

    expect(store.get('btn_1')!.status).toBe('success')

    vi.advanceTimersByTime(3000)
    expect(store.get('btn_1')!.status).toBe('idle')
  })

  it('flashes error and keeps the message for the tooltip', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_1', { success: false, message: 'gh not logged in' })

    const state = store.get('btn_1')!
    expect(state.status).toBe('error')
    expect(state.message).toBe('gh not logged in')
  })

  it('keeps a widget badge on the face instead of fading it', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_prs', {
      success: true,
      message: '3 open pull requests',
      data: { badge: '3', sublabel: 'open PRs', status: 'warning' }
    })

    vi.advanceTimersByTime(10_000)

    const state = store.get('btn_prs')!
    expect(state.badge).toBe('3')
    expect(state.sublabel).toBe('open PRs')
    expect(state.tone).toBe('warning')
    expect(state.status).toBe('success')
  })

  it('carries a critical tone through for a failing build', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_ci', {
      success: true,
      data: { badge: '✕', status: 'critical', sublabel: 'main' }
    })

    expect(store.get('btn_ci')!.tone).toBe('critical')
  })

  it('coerces a numeric badge to a string for rendering', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_n', { success: true, data: { badge: 0 } })

    expect(store.get('btn_n')!.badge).toBe('0')
  })

  it('clears a stale error when the button is pressed again', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_1', { success: false, message: 'boom' })
    store.markRunning('btn_1')

    expect(store.get('btn_1')!.message).toBeUndefined()
    expect(store.get('btn_1')!.status).toBe('running')
  })

  it('does not leave a pending fade after a re-press', () => {
    const store = useButtonStateStore()
    store.markFinished('btn_1', { success: true })
    store.markRunning('btn_1')

    // The first fade timer must not fire and reset a now-running button.
    vi.advanceTimersByTime(5000)
    expect(store.get('btn_1')!.status).toBe('running')
  })

  it('tracks several buttons independently', () => {
    const store = useButtonStateStore()
    store.markRunning('a')
    store.markRunning('b')
    store.markFinished('a', { success: true })

    expect(store.runningCount).toBe(1)
    expect(store.get('b')!.status).toBe('running')
  })

  it('ignores an empty button id', () => {
    const store = useButtonStateStore()
    store.markRunning('')
    store.markFinished('', { success: true })

    expect(Object.keys(store.states)).toHaveLength(0)
  })

  it('clears and resets', () => {
    const store = useButtonStateStore()
    store.markRunning('a')
    store.markRunning('b')

    store.clear('a')
    expect(store.get('a')).toBeUndefined()

    store.reset()
    expect(Object.keys(store.states)).toHaveLength(0)
  })
})
