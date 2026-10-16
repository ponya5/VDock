// Backend runtime helpers for the Electron shell (DL-010).
//
// Pure / injectable so they can be unit-tested with plain `node` (see
// backend/tests/test_dl010_electron_runtime.py) without starting Electron.
// Nothing here may require('electron').
'use strict'

const fs = require('fs')
const http = require('http')
const https = require('https')
const net = require('net')
const os = require('os')
const path = require('path')
const { spawn } = require('child_process')

const MIN_PORT = 1024
const MAX_PORT = 65535
// 5000 is AirPlay Receiver on every Mac; fresh installs start one above it.
const FIRST_RUN_PORT = 5001
const PORT_SEARCH_SPAN = 200

function isValidPort(value) {
  const port = Number(value)
  return Number.isInteger(port) && port >= MIN_PORT && port <= MAX_PORT
}

// ---------------------------------------------------------------------------
// .env files (same subset python-dotenv reads: KEY=value, optional `export`,
// optional quotes, trailing `# comment`).
// ---------------------------------------------------------------------------

function readEnvValue(text, key) {
  if (typeof text !== 'string') return null
  const pattern = new RegExp(`^\\s*(?:export\\s+)?${key}\\s*=\\s*(.*)$`)
  let value = null
  for (const line of text.split(/\r?\n/)) {
    const match = pattern.exec(line)
    if (!match) continue
    let raw = match[1].trim()
    const quote = raw[0]
    if ((quote === '"' || quote === "'") && raw.indexOf(quote, 1) > 0) {
      raw = raw.slice(1, raw.indexOf(quote, 1))
    } else {
      raw = raw.replace(/\s+#.*$/, '').trim()
    }
    value = raw // last one wins, like dotenv
  }
  return value
}

function readEnvPort(text) {
  const value = readEnvValue(text, 'PORT')
  if (value === null || !/^\d+$/.test(value)) return null
  return isValidPort(value) ? Number(value) : null
}

// Replace KEY=... lines in place (first occurrence; later duplicates dropped)
// and append missing keys. Comments, blank lines and other keys survive.
function upsertEnvText(text, updates) {
  const lines = typeof text === 'string' && text.length ? text.split(/\r?\n/) : []
  if (lines.length && lines[lines.length - 1] === '') lines.pop()
  const pending = new Map(Object.entries(updates).map(([k, v]) => [k, String(v)]))
  const written = new Set()
  const out = []
  for (const line of lines) {
    const match = /^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=/.exec(line)
    const key = match && match[1]
    if (key && pending.has(key)) {
      if (written.has(key)) continue
      out.push(`${key}=${pending.get(key)}`)
      written.add(key)
      continue
    }
    out.push(line)
  }
  for (const [key, value] of pending) {
    if (!written.has(key)) out.push(`${key}=${value}`)
  }
  return out.join('\n') + '\n'
}

function readTextIfExists(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8')
  } catch {
    return null
  }
}

function writeEnvKeys(envPath, updates) {
  fs.mkdirSync(path.dirname(envPath), { recursive: true })
  const next = upsertEnvText(readTextIfExists(envPath) || '', updates)
  const tmp = `${envPath}.tmp-${process.pid}`
  fs.writeFileSync(tmp, next, 'utf8')
  fs.renameSync(tmp, envPath)
}

// The port an existing install served on before DL-010 (config.json mirror).
function readLegacyPort(configJsonPath) {
  const text = readTextIfExists(configJsonPath)
  if (!text) return null
  try {
    const port = JSON.parse(text).port
    return isValidPort(port) ? Number(port) : null
  } catch {
    return null
  }
}

function readUseSsl(configJsonPath, envText) {
  const text = readTextIfExists(configJsonPath)
  if (text) {
    try {
      const saved = JSON.parse(text).use_ssl
      if (typeof saved === 'boolean') return saved
    } catch {
      // fall through to .env
    }
  }
  return String(readEnvValue(envText || '', 'USE_SSL') || '').toLowerCase() === 'true'
}

// ---------------------------------------------------------------------------
// Port probing
// ---------------------------------------------------------------------------

function canConnect(host, port, timeoutMs = 500) {
  return new Promise((resolve) => {
    const socket = net.connect({ host, port })
    let settled = false
    const finish = (result) => {
      if (settled) return
      settled = true
      socket.destroy()
      resolve(result)
    }
    socket.setTimeout(timeoutMs, () => finish(false))
    socket.once('connect', () => finish(true))
    socket.once('error', () => finish(false))
  })
}

// Loopback only on purpose: listening on 0.0.0.0 from the Electron process
// would raise the Windows Defender / macOS firewall prompt for VDock itself.
function canBindLoopback(port) {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.unref()
    server.once('error', () => resolve(false))
    server.listen({ host: '127.0.0.1', port, exclusive: true }, () => {
      server.close(() => resolve(true))
    })
  })
}

function httpGet(url, { timeoutMs = 1500, insecureLoopback = false } = {}) {
  return new Promise((resolve) => {
    const client = url.startsWith('https:') ? https : http
    const options = insecureLoopback ? { rejectUnauthorized: false } : {}
    const request = client.get(url, { ...options, timeout: timeoutMs }, (response) => {
      let body = ''
      response.setEncoding('utf8')
      response.on('data', (chunk) => {
        if (body.length < 65536) body += chunk
      })
      response.on('end', () => resolve({ status: response.statusCode, body }))
    })
    request.on('timeout', () => request.destroy(new Error('timeout')))
    request.on('error', () => resolve(null))
  })
}

function looksLikeVdockHealth(result) {
  if (!result || result.status !== 200) return false
  try {
    const payload = JSON.parse(result.body)
    return Boolean(payload && typeof payload === 'object' && 'uptime_s' in payload)
  } catch {
    return false
  }
}

async function servesVdock(port) {
  for (const scheme of ['http', 'https']) {
    const result = await httpGet(`${scheme}://127.0.0.1:${port}/api/health`, { insecureLoopback: true })
    if (looksLikeVdockHealth(result)) return true
  }
  return false
}

// 'free' | 'vdock' | 'busy'. Anything that answers on loopback (IPv4 or IPv6)
// is "served by something else" - AirPlay holds *:5000 and answers 403.
async function probePort(port) {
  if (!isValidPort(port)) return 'busy'
  const answers = (await canConnect('127.0.0.1', port)) || (await canConnect('::1', port))
  if (answers) return (await servesVdock(port)) ? 'vdock' : 'busy'
  return (await canBindLoopback(port)) ? 'free' : 'busy'
}

async function firstFreePort(start, probe, span = PORT_SEARCH_SPAN, skip = new Set()) {
  for (let port = Math.max(start, MIN_PORT); port <= Math.min(start + span, MAX_PORT); port++) {
    if (skip.has(port)) continue
    if ((await probe(port)) === 'free') return port
  }
  return null
}

// Decide the backend port. Returns { port, persist, reason }.
//   savedPort  - PORT from DATA_DIR/.env (Settings > Ports writes it)
//   legacyPort - port an older install served on (config.json), kept so
//                phones' bookmarks survive the upgrade when it is free
//   avoid      - ports that just failed to bind (Address already in use)
async function choosePort({ savedPort, legacyPort, probe = probePort, start = FIRST_RUN_PORT, avoid = [] }) {
  const skip = new Set(avoid.filter(isValidPort).map(Number))

  if (isValidPort(savedPort)) {
    const port = Number(savedPort)
    const state = skip.has(port) ? 'busy' : await probe(port)
    if (state === 'free') return { port, persist: false, reason: 'saved' }
    const next = await firstFreePort(port + 1, probe, PORT_SEARCH_SPAN, skip)
    if (next === null) return { port, persist: false, reason: `saved port ${port} is ${state}; no free port found` }
    // Another VDock (source checkout) on it is temporary: keep the user's
    // choice. A foreign app squatting on it is not: move for good.
    return { port: next, persist: state !== 'vdock', reason: `saved port ${port} is ${state}` }
  }

  if (isValidPort(legacyPort) && !skip.has(Number(legacyPort))) {
    if ((await probe(Number(legacyPort))) === 'free') {
      return { port: Number(legacyPort), persist: true, reason: 'legacy' }
    }
  }

  const next = await firstFreePort(start, probe, PORT_SEARCH_SPAN, skip)
  if (next === null) return { port: start, persist: false, reason: 'no free port found' }
  return { port: next, persist: true, reason: 'first-run' }
}

function isAddressInUse(text) {
  return /Address already in use|Errno 48|Errno 98|WinError 10048|EADDRINUSE|only one usage of each socket address/i
    .test(String(text || ''))
}

// ---------------------------------------------------------------------------
// Respawn policy: back off on quick deaths, give up after a few.
// ---------------------------------------------------------------------------

class RespawnPolicy {
  constructor({ quickMs = 15000, maxQuickFailures = 3, baseDelayMs = 1000, maxDelayMs = 30000, restartDelayMs = 500 } = {}) {
    this.quickMs = quickMs
    this.maxQuickFailures = maxQuickFailures
    this.baseDelayMs = baseDelayMs
    this.maxDelayMs = maxDelayMs
    this.restartDelayMs = restartDelayMs
    this.quickFailures = 0
  }

  // -> { giveUp: boolean, delayMs: number, quickFailures: number }
  onExit({ uptimeMs }) {
    if (uptimeMs >= this.quickMs) {
      // Ran fine for a while: a deliberate restart (Settings) or a late crash.
      this.quickFailures = 0
      return { giveUp: false, delayMs: this.restartDelayMs, quickFailures: 0 }
    }
    this.quickFailures += 1
    if (this.quickFailures >= this.maxQuickFailures) {
      return { giveUp: true, delayMs: 0, quickFailures: this.quickFailures }
    }
    const delayMs = Math.min(this.baseDelayMs * 2 ** this.quickFailures, this.maxDelayMs)
    return { giveUp: false, delayMs, quickFailures: this.quickFailures }
  }

  reset() {
    this.quickFailures = 0
  }
}

// ---------------------------------------------------------------------------
// Login-shell PATH (macOS/Linux GUI launches get launchd's minimal PATH)
// ---------------------------------------------------------------------------

const PATH_MARKER = '__VDOCK_PATH__'

function extractMarkedPath(output) {
  const text = String(output || '')
  const start = text.indexOf(PATH_MARKER)
  if (start < 0) return null
  const end = text.indexOf(PATH_MARKER, start + PATH_MARKER.length)
  if (end < 0) return null
  const value = text.slice(start + PATH_MARKER.length, end).trim()
  return value || null
}

function resolveLoginShellPath({ shell = process.env.SHELL || '/bin/zsh', timeoutMs = 4000, env = process.env } = {}) {
  return new Promise((resolve) => {
    let child
    try {
      child = spawn(shell, ['-ilc', `printf '${PATH_MARKER}%s${PATH_MARKER}' "$PATH"`], {
        stdio: ['ignore', 'pipe', 'ignore'],
        // oh-my-zsh & co. must not stop to ask about updates.
        env: { ...env, DISABLE_AUTO_UPDATE: 'true', DISABLE_UPDATE_PROMPT: 'true' },
        // Own session: an interactive shell must never grab (and stop on) a
        // terminal VDock was started from, and a timeout can kill everything
        // the profile started, not just the shell.
        detached: true,
      })
    } catch {
      resolve(null)
      return
    }
    let output = ''
    const timer = setTimeout(() => {
      try {
        process.kill(-child.pid, 'SIGKILL')
      } catch {
        try { child.kill('SIGKILL') } catch { /* already gone */ }
      }
      child.stdout.destroy()
      resolve(extractMarkedPath(output))
    }, timeoutMs)
    child.stdout.on('data', (chunk) => {
      if (output.length < 65536) output += chunk
    })
    child.on('error', () => {
      clearTimeout(timer)
      resolve(null)
    })
    child.on('close', () => {
      clearTimeout(timer)
      resolve(extractMarkedPath(output))
    })
  })
}

function mergePathLists(lists, delimiter = path.delimiter) {
  const seen = new Set()
  const merged = []
  for (const list of lists) {
    if (!list) continue
    const entries = Array.isArray(list) ? list : String(list).split(delimiter)
    for (const entry of entries) {
      const trimmed = String(entry).trim()
      if (!trimmed || seen.has(trimmed)) continue
      seen.add(trimmed)
      merged.push(trimmed)
    }
  }
  return merged.join(delimiter)
}

function fallbackToolDirs(home = os.homedir()) {
  return ['/opt/homebrew/bin', '/opt/homebrew/sbin', '/usr/local/bin', path.join(home, '.local', 'bin')]
}

// ---------------------------------------------------------------------------
// Readiness polling
// ---------------------------------------------------------------------------

// Resolves true once `check()` does; false after timeoutMs (Infinity = never).
async function waitUntil(check, { intervalMs = 500, timeoutMs = Infinity, isCancelled = () => false } = {}) {
  const deadline = Date.now() + timeoutMs
  while (!isCancelled()) {
    if (await check()) return true
    if (Date.now() >= deadline) return false
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  return false
}

// Small, append-only log with a size cap (same idea as the Python launcher).
function openCappedLog(logPath, { maxBytes = 1024 * 1024, keepBytes = 256 * 1024 } = {}) {
  fs.mkdirSync(path.dirname(logPath), { recursive: true })
  try {
    const { size } = fs.statSync(logPath)
    if (size > maxBytes) {
      const fd = fs.openSync(logPath, 'r')
      const buffer = Buffer.alloc(keepBytes)
      fs.readSync(fd, buffer, 0, keepBytes, size - keepBytes)
      fs.closeSync(fd)
      fs.writeFileSync(logPath, Buffer.concat([Buffer.from('... [older log truncated] ...\n'), buffer]))
    }
  } catch {
    // no log yet
  }
  return fs.createWriteStream(logPath, { flags: 'a' })
}

module.exports = {
  FIRST_RUN_PORT,
  PATH_MARKER,
  RespawnPolicy,
  canBindLoopback,
  canConnect,
  choosePort,
  extractMarkedPath,
  fallbackToolDirs,
  firstFreePort,
  httpGet,
  isAddressInUse,
  isValidPort,
  looksLikeVdockHealth,
  mergePathLists,
  openCappedLog,
  probePort,
  readEnvPort,
  readEnvValue,
  readLegacyPort,
  readTextIfExists,
  readUseSsl,
  resolveLoginShellPath,
  servesVdock,
  upsertEnvText,
  waitUntil,
  writeEnvKeys,
}
