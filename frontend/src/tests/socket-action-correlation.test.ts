// Feature: ai-dev-integration-packs, Property 0.4: action results are matched
// to the action that produced them.
//
// The client used to resolve `actionCallbacks.get(actionIdCounter - 1)` on every
// `action_result`, i.e. always the most recently issued action. With two actions
// in flight, the first result settled the SECOND action's promise (with the
// wrong payload) and deleted its callback, so the second result was dropped and
// that promise hung until the 30s timeout.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { ActionResult } from '@/types'

type Handler = (...args: any[]) => void

const handlers = new Map<string, Handler>()
const emitted: Array<{ event: string; payload: any }> = []

const fakeSocket = {
  connected: true,
  on: (event: string, cb: Handler) => { handlers.set(event, cb) },
  off: vi.fn(),
  emit: (event: string, payload: any) => { emitted.push({ event, payload }) },
  disconnect: vi.fn()
}

vi.mock('socket.io-client', () => ({ io: () => fakeSocket }))

/** Emit a server-side `action_result`, as app.py now does. */
function serverReplies(requestId: number | undefined, result: Partial<ActionResult>) {
  handlers.get('action_result')!({ request_id: requestId, ...result })
}

let socketClient: any

beforeEach(async () => {
  handlers.clear()
  emitted.length = 0
  vi.resetModules()
  socketClient = (await import('@/api/socket')).default
  socketClient.connect()
})

afterEach(() => { vi.useRealTimers() })

describe('socket action result correlation', () => {
  it('tags each outgoing action with a request id', async () => {
    socketClient.executeAction({ type: 'hotkey' })
    socketClient.executeAction({ type: 'url' })

    const ids = emitted.map((e) => e.payload.request_id)
    expect(ids).toEqual([0, 1])
  })

  it('resolves each concurrent action with its own result', async () => {
    const first = socketClient.executeAction({ type: 'hotkey' })
    const second = socketClient.executeAction({ type: 'url' })

    // Results come back out of order, which is the whole point.
    serverReplies(1, { success: true, message: 'url done' })
    serverReplies(0, { success: true, message: 'hotkey done' })

    await expect(first).resolves.toMatchObject({ message: 'hotkey done' })
    await expect(second).resolves.toMatchObject({ message: 'url done' })
  })

  it('strips the transport-level request id from the resolved result', async () => {
    const pending = socketClient.executeAction({ type: 'hotkey' })
    serverReplies(0, { success: true, message: 'done' })

    const result = await pending
    expect(result).not.toHaveProperty('request_id')
    expect(result).toEqual({ success: true, message: 'done' })
  })

  it('ignores a result for an action it is not tracking', async () => {
    const pending = socketClient.executeAction({ type: 'hotkey' })

    serverReplies(99, { success: false, message: 'stale' })
    serverReplies(0, { success: true, message: 'mine' })

    await expect(pending).resolves.toMatchObject({ message: 'mine' })
  })

  it('clears the timeout once a result arrives', async () => {
    vi.useFakeTimers()
    const pending = socketClient.executeAction({ type: 'hotkey' })
    serverReplies(0, { success: true, message: 'done' })
    await expect(pending).resolves.toMatchObject({ message: 'done' })

    // Would reject on the 30s timer if it were still pending.
    vi.advanceTimersByTime(31_000)
    await expect(pending).resolves.toMatchObject({ message: 'done' })
  })
})
