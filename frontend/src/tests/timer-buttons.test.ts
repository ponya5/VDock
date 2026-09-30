// Feature: DL-122 — the shared timer engine behind time_timer /
// time_stopwatch buttons. Timers live in a module-level map (they must
// survive scene switches), tick on one shared interval, and on expiry can
// flash + toast + dispatch a nested on_finish action over the socket.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const executeAction = vi.fn((_action: any) =>
  Promise.resolve({ success: true, message: 'ok' })
)

vi.mock('@/api/socket', () => ({
  default: {
    executeAction: (...a: any[]) => executeAction(...a),
    on: vi.fn(),
    off: vi.fn(),
    isConnected: () => true,
  },
}))

import timerButtons from '@/services/timerButtons'
import { useNotificationsStore } from '@/stores/notifications'

beforeEach(() => {
  setActivePinia(createPinia())
  vi.useFakeTimers()
  timerButtons._resetAll()
  executeAction.mockClear()
})

afterEach(() => {
  timerButtons._resetAll()
  vi.useRealTimers()
})

describe('timerButtons engine', () => {
  it('starts a countdown and ticks down', () => {
    const result = timerButtons.toggle('b1', { mode: 'countdown', duration_s: 60 })
    expect(result.success).toBe(true)

    const t = timerButtons.getTimer('b1')!
    expect(t.running).toBe(true)
    expect(t.mode).toBe('countdown')

    vi.advanceTimersByTime(10_000)
    expect(t.remainingS).toBeGreaterThan(49)
    expect(t.remainingS).toBeLessThanOrEqual(51)
  })

  it('toggles pause and resume without losing elapsed time', () => {
    timerButtons.toggle('b1', { mode: 'countdown', duration_s: 60 })
    vi.advanceTimersByTime(10_000)

    const paused = timerButtons.toggle('b1', { mode: 'countdown', duration_s: 60 })
    expect(paused.message).toContain('paused')
    const t = timerButtons.getTimer('b1')!
    expect(t.running).toBe(false)

    // A paused timer doesn't move.
    const frozen = t.remainingS
    vi.advanceTimersByTime(5_000)
    expect(t.remainingS).toBe(frozen)

    timerButtons.toggle('b1', { mode: 'countdown', duration_s: 60 })
    expect(t.running).toBe(true)
    vi.advanceTimersByTime(10_000)
    expect(t.remainingS).toBeLessThanOrEqual(41)
  })

  it('expires: flashes, toasts, and dispatches on_finish once', () => {
    const onFinish = { type: 'cross_platform', config: { action: 'volume_mute' } }
    timerButtons.toggle('b1', {
      mode: 'countdown', duration_s: 5, alarm: true, on_finish: onFinish,
    }, 'Tea')

    vi.advanceTimersByTime(6_000)

    const t = timerButtons.getTimer('b1')!
    expect(t.expired).toBe(true)
    expect(t.running).toBe(false)
    expect(t.flashing).toBe(true)
    expect(t.remainingS).toBe(0)

    const notifications = useNotificationsStore().notifications
    expect(notifications.some((n) => n.title === 'Timer finished')).toBe(true)

    expect(executeAction).toHaveBeenCalledTimes(1)
    expect(executeAction).toHaveBeenCalledWith(onFinish)

    // The flash window closes ~10s after expiry.
    vi.advanceTimersByTime(11_000)
    expect(t.flashing).toBe(false)

    // Tapping an expired timer acknowledges and re-arms (stopped).
    const result = timerButtons.toggle('b1', { mode: 'countdown', duration_s: 5 }, 'Tea')
    expect(result.message).toContain('re-armed')
    expect(t.expired).toBe(false)
    expect(t.running).toBe(false)
    expect(t.remainingS).toBe(5)
  })

  it('stopwatch mode counts up and never expires', () => {
    timerButtons.toggle('sw1', { mode: 'stopwatch' })
    const t = timerButtons.getTimer('sw1')!
    expect(t.mode).toBe('stopwatch')

    vi.advanceTimersByTime(90_000)
    expect(t.elapsedS).toBeGreaterThan(89)
    expect(t.expired).toBe(false)
    expect(executeAction).not.toHaveBeenCalled()
  })

  it('time_stopwatch action type forces stopwatch mode', () => {
    const cfg = timerButtons.normalizeConfig({ mode: 'countdown', duration_s: 60 }, 'time_stopwatch')
    expect(cfg.mode).toBe('stopwatch')
  })

  it('normalises the legacy timer_duration schema', () => {
    expect(timerButtons.normalizeConfig({ timer_duration: 300 }).mode).toBe('countdown')
    expect(timerButtons.normalizeConfig({ timer_duration: 300 }).duration_s).toBe(300)
    expect(timerButtons.normalizeConfig({ timer_duration: 0 }).mode).toBe('stopwatch')
  })

  it('auto_start begins the timer on first mount only', () => {
    timerButtons.ensureMounted('b2', { mode: 'countdown', duration_s: 30, auto_start: true })
    const t = timerButtons.getTimer('b2')!
    expect(t.running).toBe(true)

    // Remounting a paused timer must NOT restart it.
    timerButtons.pause('b2')
    timerButtons.ensureMounted('b2', { mode: 'countdown', duration_s: 30, auto_start: true })
    expect(t.running).toBe(false)
  })

  it('alarm:false still expires but without toast or flash', () => {
    timerButtons.toggle('b3', { mode: 'countdown', duration_s: 2, alarm: false })
    vi.advanceTimersByTime(3_000)

    const t = timerButtons.getTimer('b3')!
    expect(t.expired).toBe(true)
    expect(t.flashing).toBe(false)
    expect(useNotificationsStore().notifications).toHaveLength(0)
  })

  it('reset returns a countdown to its armed duration', () => {
    timerButtons.toggle('b4', { mode: 'countdown', duration_s: 30 })
    vi.advanceTimersByTime(10_000)
    timerButtons.reset('b4')

    const t = timerButtons.getTimer('b4')!
    expect(t.running).toBe(false)
    expect(t.remainingS).toBe(30)
  })

  it('keeps independent state per button id', () => {
    timerButtons.toggle('a', { mode: 'countdown', duration_s: 10 })
    timerButtons.toggle('b', { mode: 'stopwatch' })

    vi.advanceTimersByTime(5_000)
    expect(timerButtons.isRunning('a')).toBe(true)
    expect(timerButtons.isRunning('b')).toBe(true)
    expect(timerButtons.getTimer('a')!.remainingS).toBeLessThan(6)
    expect(timerButtons.getTimer('b')!.elapsedS).toBeGreaterThan(4)
  })

  it('works without an active pinia (toast skipped, expiry still lands)', () => {
    setActivePinia(undefined as any)
    timerButtons.toggle('b5', { mode: 'countdown', duration_s: 2, alarm: true })
    vi.advanceTimersByTime(3_000)
    expect(timerButtons.getTimer('b5')!.expired).toBe(true)
  })
})
