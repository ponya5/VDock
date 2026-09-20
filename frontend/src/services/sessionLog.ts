/**
 * DL-029 — capture frontend errors and lifecycle events into the backend's
 * bounded frontend.log so the Settings → Logs tab can surface them.
 *
 * Captures: Vue render errors, window.onerror, unhandled promise rejections,
 * console.error/console.warn, and explicit logEvent() calls. Events buffer in
 * memory and flush via POST /api/logs/client every few seconds (sendBeacon on
 * pagehide). Transport failures back off so an unreachable backend never
 * turns logging itself into a spam source.
 */

export type SessionLogLevel = 'error' | 'warn' | 'info'

interface SessionLogEvent {
  ts: string
  level: SessionLogLevel
  source: string
  message: string
}

const queue: SessionLogEvent[] = []
const FLUSH_INTERVAL_MS = 5000
const FLUSH_THRESHOLD = 20
const FAILURE_BACKOFF_MS = 60_000
const MAX_QUEUE = 500
const MAX_MESSAGE = 1500

let installed = false
let flushTimer: ReturnType<typeof setInterval> | null = null
let backoffUntil = 0
let flushing = false

function push(level: SessionLogLevel, source: string, message: unknown) {
  let text: string
  try {
    text = typeof message === 'string' ? message : JSON.stringify(message)
  } catch {
    text = String(message)
  }
  if (!text) return
  queue.push({
    ts: new Date().toISOString(),
    level,
    source: source.slice(0, 60),
    message: text.slice(0, MAX_MESSAGE)
  })
  if (queue.length > MAX_QUEUE) queue.splice(0, queue.length - MAX_QUEUE)
  if (queue.length >= FLUSH_THRESHOLD) void flush()
}

/** Record an app event worth seeing in the logs tab. */
export function logEvent(message: string, source = 'app', level: SessionLogLevel = 'info') {
  push(level, source, message)
}

function describeError(err: unknown): string {
  if (err instanceof Error) return `${err.message}${err.stack ? `\n${err.stack}` : ''}`
  if (typeof err === 'string') return err
  try { return JSON.stringify(err) } catch { return String(err) }
}

async function flush() {
  if (!queue.length || flushing || Date.now() < backoffUntil) return
  flushing = true
  const batch = queue.splice(0, 100)
  try {
    const response = await fetch('/api/logs/client', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: batch })
    })
    if (!response.ok) throw new Error(String(response.status))
  } catch {
    // Backend unreachable or rejecting — keep events, retry after backoff.
    queue.unshift(...batch)
    if (queue.length > MAX_QUEUE) queue.splice(0, queue.length - MAX_QUEUE)
    backoffUntil = Date.now() + FAILURE_BACKOFF_MS
  } finally {
    flushing = false
  }
}

function flushBeacon() {
  if (!queue.length) return
  const batch = queue.splice(0, 100)
  try {
    navigator.sendBeacon('/api/logs/client', JSON.stringify({ events: batch }))
  } catch { /* page is going away anyway */ }
}

export function installSessionLog(app: { config: { errorHandler?: (err: unknown, instance: unknown, info: string) => void } }) {
  if (installed) return
  installed = true

  app.config.errorHandler = (err, _instance, info) => {
    push('error', 'vue', `${describeError(err)}\n[${info}]`)
  }

  window.addEventListener('error', (event) => {
    push('error', 'window', `${event.message} @ ${event.filename}:${event.lineno}`)
  })

  window.addEventListener('unhandledrejection', (event) => {
    push('error', 'promise', describeError(event.reason))
  })

  for (const method of ['error', 'warn'] as const) {
    const original = console[method].bind(console)
    console[method] = (...args: unknown[]) => {
      original(...args)
      push(method, 'console', args.map(describeError).join(' '))
    }
  }

  window.addEventListener('pagehide', flushBeacon)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flushBeacon()
  })

  flushTimer = setInterval(() => void flush(), FLUSH_INTERVAL_MS)
  push('info', 'app', `VDock session started (${window.location.href})`)
}
