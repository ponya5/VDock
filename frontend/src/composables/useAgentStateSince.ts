import { getCurrentScope, onScopeDispose, ref, watch, type Ref } from 'vue'

/**
 * DL-166: how long the agent has been in its current state, as the client saw it.
 *
 * `AgentStateEntry.ts` is the last hook event (bumped on every event), not the
 * moment the state began, so the start is the first time this browser observed
 * the state. That under-counts after a reload; the DL accepts the approximation.
 * Observations are keyed by source+session and live at module level, so
 * switching scenes does not restart the clock.
 */

const observed = new Map<string, { state: string; since: number }>()

/** Epoch ms when `state` was first observed for `key`; resets when the state changes. */
export function useAgentStateSince(key: Ref<string>, state: Ref<string>): Ref<number | null> {
  const since = ref<number | null>(null)
  watch(
    [key, state],
    ([k, s]) => {
      const prev = observed.get(k)
      if (!prev || prev.state !== s) observed.set(k, { state: s, since: Date.now() })
      since.value = observed.get(k)!.since
    },
    { immediate: true, flush: 'sync' },
  )
  return since
}

/** Test hook. */
export function resetAgentStateSince(): void {
  observed.clear()
}

// --- one shared clock for every mounted banner -------------------------------------------------
export const agentNow = ref(Date.now())
const fastSubs = new Set<symbol>()
const slowSubs = new Set<symbol>()
let timer: ReturnType<typeof setInterval> | undefined

function reschedule(): void {
  if (timer !== undefined) { clearInterval(timer); timer = undefined }
  if (!fastSubs.size && !slowSubs.size) return
  agentNow.value = Date.now()
  timer = setInterval(() => { agentNow.value = Date.now() }, fastSubs.size ? 1000 : 30_000)
}

/**
 * Subscribe to the shared clock: it ticks every second while any subscriber is `fast`
 * (working / permission), else every 30s, and stops when nobody is subscribed.
 */
export function useAgentClock(fast: Ref<boolean>) {
  const id = Symbol('agent-clock')
  function drop(): void {
    fastSubs.delete(id)
    slowSubs.delete(id)
  }
  watch(
    fast,
    (isFast) => {
      drop()
      ;(isFast ? fastSubs : slowSubs).add(id)
      reschedule()
    },
    { immediate: true, flush: 'sync' },
  )
  if (getCurrentScope()) {
    onScopeDispose(() => {
      drop()
      reschedule()
    })
  }
  return agentNow
}

/** `2:14` under an hour, `1h 05m` above. */
export function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h >= 1) return `${h}h ${String(m).padStart(2, '0')}m`
  return `${m}:${String(s).padStart(2, '0')}`
}
