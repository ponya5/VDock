// Feature: ai-dev-integration-packs, Property 1.3 (client half): a long action
// still reports its result.
//
// A long action returns 202 with a job id rather than a result, because it
// cannot finish inside axios's 30s timeout. The client then has to discover
// the outcome itself.
//
// Polling is the mechanism, not a fallback: measured against the real server
// (Flask-SocketIO 5.3.5, threading mode, Werkzeug), a connected client receives
// events emitted from inside a Socket.IO handler but never events emitted from
// an HTTP handler or a background thread -- so the action_job broadcast never
// arrives. These tests pin the polling path down, and keep the socket path
// working for the day the server runs under an async worker.
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const post = vi.fn()
const get = vi.fn()
const socketHandlers = new Map<string, (p: any) => void>()

vi.mock('@/api/client', () => ({
  default: {
    post: (...a: any[]) => post(...a),
    get: (...a: any[]) => get(...a)
  }
}))

vi.mock('@/api/socket', () => ({
  default: {
    on: (event: string, cb: (p: any) => void) => socketHandlers.set(event, cb),
    off: (event: string) => socketHandlers.delete(event),
    isConnected: () => true
  }
}))

vi.mock('@/stores/settings', () => ({
  useSettingsStore: () => ({})
}))

let useDashboardStore: any

const BUTTON = {
  id: 'btn_1',
  label: 'GH Status',
  shape: 'rounded',
  position: { row: 0, col: 0 },
  size: { rows: 1, cols: 1 },
  enabled: true,
  action: { type: 'gh_status', config: {} }
}

beforeEach(async () => {
  setActivePinia(createPinia())
  post.mockReset()
  get.mockReset()
  socketHandlers.clear()
  vi.resetModules()
  useDashboardStore = (await import('@/stores/dashboard')).useDashboardStore
})

afterEach(() => {
  vi.useRealTimers()
})

describe('background action jobs', () => {
  it('sends the button id so progress can be attributed', async () => {
    post.mockResolvedValue({ data: { success: true, message: 'done' } })

    await useDashboardStore().executeButtonAction(BUTTON)

    expect(post).toHaveBeenCalledWith('/actions/execute', {
      action: BUTTON.action,
      button_id: 'btn_1'
    })
  })

  it('returns a short action result directly, without polling', async () => {
    post.mockResolvedValue({ data: { success: true, message: 'immediate' } })

    const result = await useDashboardStore().executeButtonAction(BUTTON)

    expect(result).toMatchObject({ message: 'immediate' })
    expect(get).not.toHaveBeenCalled()
  })

  it('polls immediately rather than waiting out an interval', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'job1' } })
    get.mockResolvedValue({
      data: { status: 'succeeded', result: { success: true, message: 'polled' } }
    })

    const result = await useDashboardStore().executeButtonAction(BUTTON)

    expect(get).toHaveBeenCalledWith('/actions/jobs/job1')
    expect(result).toMatchObject({ success: true, message: 'polled' })
  })

  it('keeps polling while the job is still running', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'job2' } })
    get
      .mockResolvedValueOnce({ data: { status: 'running' } })
      .mockResolvedValueOnce({ data: { status: 'running' } })
      .mockResolvedValue({
        data: { status: 'succeeded', result: { success: true, message: 'late' } }
      })

    const result = await useDashboardStore().executeButtonAction(BUTTON)

    expect(get.mock.calls.length).toBeGreaterThanOrEqual(3)
    expect(result).toMatchObject({ message: 'late' })
  })

  it('surfaces a failed job as a failure', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'job3' } })
    get.mockResolvedValue({
      data: {
        status: 'failed',
        result: { success: false, message: 'gh command failed' }
      }
    })

    const result = await useDashboardStore().executeButtonAction(BUTTON)

    expect(result).toMatchObject({ success: false, message: 'gh command failed' })
  })

  it('survives a transient polling error', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'job4' } })
    get
      .mockRejectedValueOnce(new Error('network blip'))
      .mockResolvedValue({
        data: { status: 'succeeded', result: { success: true, message: 'ok' } }
      })

    const result = await useDashboardStore().executeButtonAction(BUTTON)

    expect(result).toMatchObject({ success: true, message: 'ok' })
  })

  it('still resolves from the socket event when one does arrive', async () => {
    // Keeps the path honest for a future async-worker deployment.
    post.mockResolvedValue({ data: { pending: true, job_id: 'job5' } })
    get.mockResolvedValue({ data: { status: 'running' } })

    const pending = useDashboardStore().executeButtonAction(BUTTON)
    await Promise.resolve()

    socketHandlers.get('action_job')?.({
      job_id: 'job5',
      status: 'succeeded',
      result: { success: true, message: 'via socket' }
    })

    await expect(pending).resolves.toMatchObject({ message: 'via socket' })
  })

  it('ignores socket events for a different job', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'mine' } })
    get.mockResolvedValue({ data: { status: 'running' } })

    const pending = useDashboardStore().executeButtonAction(BUTTON)
    await Promise.resolve()

    socketHandlers.get('action_job')?.({
      job_id: 'someone_else',
      status: 'succeeded',
      result: { success: true, message: 'not mine' }
    })
    socketHandlers.get('action_job')?.({
      job_id: 'mine',
      status: 'succeeded',
      result: { success: true, message: 'mine' }
    })

    await expect(pending).resolves.toMatchObject({ message: 'mine' })
  })

  it('ignores a running socket event and waits for the terminal one', async () => {
    post.mockResolvedValue({ data: { pending: true, job_id: 'job6' } })
    get.mockResolvedValue({ data: { status: 'running' } })

    const pending = useDashboardStore().executeButtonAction(BUTTON)
    await Promise.resolve()

    socketHandlers.get('action_job')?.({ job_id: 'job6', status: 'running' })
    socketHandlers.get('action_job')?.({
      job_id: 'job6',
      status: 'succeeded',
      result: { success: true, message: 'final' }
    })

    await expect(pending).resolves.toMatchObject({ message: 'final' })
  })
})
