const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, screen, shell, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, execFileSync } = require('child_process')
const runtime = require('./backend-runtime')
// Detect development mode by checking if backend exists relative to electron
// directory. In a repo checkout that dir always exists, so the launcher passes
// VDOCK_PRODUCTION=1 when it skipped the Vite dev server and Electron should
// load the backend-served `dist` bundle instead (DL-112).
const isDev = process.env.VDOCK_PRODUCTION !== '1'
  && require('fs').existsSync(path.join(__dirname, '../../backend'))

// Separate profile (and DATA_DIR) on request - scratch/e2e runs of a packaged
// build must not touch the user's real VDock data. Must precede the lock.
if (process.env.VDOCK_USER_DATA_DIR) {
  app.setPath('userData', path.resolve(process.env.VDOCK_USER_DATA_DIR))
}

// One VDock per user: a second launch (Start menu, Dock, desktop icon) focuses
// the running window instead of starting a second app and backend (DL-010).
const gotSingleInstanceLock = app.requestSingleInstanceLock()
if (!gotSingleInstanceLock) {
  app.quit()
}

let mainWindow = null
let tray = null
let isQuitting = false
let windowPinned = false
let alwaysOnTop = false
let kioskMode = false
let backendProcess = null

// .ico only renders on Windows; Tray/BrowserWindow need PNG elsewhere.
const iconFile = process.platform === 'win32' ? 'vdock-icon.ico' : 'vdock-icon.png'

// Run from a source checkout, the window belongs to the stock Electron
// binary, so the OS would show Electron's atom icon. Packaged builds carry
// their own icon and have no ../public next to main.js, so this is a no-op there.
const APP_USER_MODEL_ID = 'com.vdock.app'

function applyVdockIdentity() {
  if (process.platform === 'win32') {
    app.setAppUserModelId(APP_USER_MODEL_ID)
    return
  }

  if (process.platform !== 'darwin' || !app.dock) return

  const dockIconPath = path.join(__dirname, '../public', 'vdock-icon.png')
  if (!fs.existsSync(dockIconPath)) return

  app.dock.setIcon(dockIconPath)
}

function findSmallestDisplay() {
  const displays = screen.getAllDisplays()
  return displays.reduce((smallest, display) => {
    const displayArea = display.workAreaSize.width * display.workAreaSize.height
    const smallestArea = smallest.workAreaSize.width * smallest.workAreaSize.height
    return displayArea < smallestArea ? display : smallest
  }, displays[0])
}

function resolveTargetDisplay() {
  const displays = screen.getAllDisplays()
  const preferredDisplayIndex = Number.parseInt(process.env.VDOCK_DISPLAY_INDEX || '', 10)

  if (!Number.isNaN(preferredDisplayIndex) && displays[preferredDisplayIndex]) {
    return displays[preferredDisplayIndex]
  }

  if (process.env.VDOCK_USE_SMALLEST_DISPLAY === '1') {
    return findSmallestDisplay()
  }

  return screen.getPrimaryDisplay()
}

// ---------------------------------------------------------------------------
// Backend process (DL-010)
// ---------------------------------------------------------------------------
// Packaged builds: Electron owns the backend. It picks the port (never
// AirPlay's 5000 on macOS), passes it as PORT, gives the backend the user's
// login-shell PATH on macOS/Linux, logs its output to DATA_DIR, backs off
// when it keeps dying and finally explains what happened instead of looping.

const backendState = {
  port: null,              // packaged builds: the port Electron chose
  scheme: 'http',          // https when the user turned on HTTPS in Settings
  startedAt: 0,
  recentOutput: [],        // tail of the current process's stdout/stderr
  logStream: null,
  policy: new runtime.RespawnPolicy(),
  respawnTimer: null,
  avoidPorts: [],          // ports a backend just failed to bind
  failed: false,           // gave up; the failure dialog owns the window
}

function backendDir() {
  return isDev
    ? path.join(__dirname, '../../backend')
    : path.join(process.resourcesPath, 'backend')
}

// DATA_DIR lands under Electron's per-user writable dir - the install dir
// itself may be read-only (Program Files, a read-only DMG mount).
function packagedDataDir() {
  return path.join(app.getPath('userData'), 'vdock-data')
}

function backendExePath() {
  return path.join(backendDir(), process.platform === 'win32' ? 'vdock-backend.exe' : 'vdock-backend')
}

function backendLogPath() {
  return isDev
    ? path.join(backendDir(), 'data', 'vdock-backend-electron.log')
    : path.join(packagedDataDir(), 'vdock-backend-electron.log')
}

function pidFilePath() {
  return path.join(packagedDataDir(), 'backend.pid')
}

function removePidFile(pid) {
  try {
    const record = JSON.parse(fs.readFileSync(pidFilePath(), 'utf8'))
    if (pid === undefined || record.pid === pid) fs.unlinkSync(pidFilePath())
  } catch {
    // no pid file
  }
}

function processCommandLine(pid) {
  try {
    if (process.platform === 'win32') {
      return execFileSync('tasklist', ['/FI', `PID eq ${pid}`, '/FO', 'CSV', '/NH'],
        { encoding: 'utf8', windowsHide: true, timeout: 5000 })
    }
    return execFileSync('ps', ['-p', String(pid), '-o', 'command='], { encoding: 'utf8', timeout: 5000 })
  } catch {
    return ''
  }
}

function processIsAlive(pid) {
  try {
    process.kill(pid, 0)
    return true
  } catch (error) {
    return error.code === 'EPERM'
  }
}

// A crashed or force-killed shell leaves its backend running on our port.
// Stop it - but only when the pid still belongs to a vdock-backend process.
async function stopOrphanBackend() {
  let record
  try {
    record = JSON.parse(fs.readFileSync(pidFilePath(), 'utf8'))
  } catch {
    return
  }
  const pid = Number(record.pid)
  if (!Number.isInteger(pid) || pid <= 0 || pid === process.pid || !processIsAlive(pid)) {
    removePidFile()
    return
  }
  if (!/vdock-backend/i.test(processCommandLine(pid))) {
    removePidFile()
    return
  }
  console.log('[backend] stopping a backend left over from a previous run, pid', pid)
  try { process.kill(pid) } catch { /* gone */ }
  await runtime.waitUntil(async () => !processIsAlive(pid), { intervalMs: 200, timeoutMs: 3000 })
  if (processIsAlive(pid)) {
    try { process.kill(pid, 'SIGKILL') } catch { /* gone */ }
  }
  removePidFile()
}

// Saved PORT (Settings > Ports writes DATA_DIR/.env) -> legacy config.json
// port when free -> first free port from 5001. Persists new choices.
async function preparePackagedPort() {
  const dataDir = packagedDataDir()
  const envPath = path.join(dataDir, '.env')

  // Older installs kept .env beside the exe; config.migrate_legacy_env only
  // copies it while DATA_DIR/.env is missing, so copy it before writing PORT.
  const legacyEnv = path.join(backendDir(), '.env')
  if (!fs.existsSync(envPath) && fs.existsSync(legacyEnv)) {
    try {
      fs.mkdirSync(dataDir, { recursive: true })
      fs.copyFileSync(legacyEnv, envPath)
    } catch (error) {
      console.error('[backend] could not migrate the legacy .env:', error.message)
    }
  }

  const envText = runtime.readTextIfExists(envPath) || ''
  const configJson = path.join(dataDir, 'config.json')
  const savedPort = runtime.readEnvPort(envText)
  const previousPort = backendState.port

  // Respawning on the port the last backend just released: give the OS a
  // moment before calling it busy, so a restart never moves the deck.
  const probe = async (port) => {
    let state = await runtime.probePort(port)
    for (let attempt = 0; state === 'busy' && port === previousPort && attempt < 6; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 500))
      state = await runtime.probePort(port)
    }
    return state
  }

  const choice = await runtime.choosePort({
    savedPort,
    legacyPort: runtime.readLegacyPort(configJson),
    probe,
    avoid: backendState.avoidPorts,
  })
  console.log(`[backend] port ${choice.port} (${choice.reason})`)
  if (choice.persist) {
    try {
      runtime.writeEnvKeys(envPath, { PORT: choice.port })
    } catch (error) {
      console.error('[backend] could not save PORT to', envPath, error.message)
    }
  }
  backendState.scheme = runtime.readUseSsl(configJson, envText) ? 'https' : 'http'
  return choice.port
}

// Finder/Dock launches get launchd's PATH (/usr/bin:/bin:...), so claude, gh,
// cursor, node from Homebrew/mise/nvm would read as "not installed". Ask the
// user's login shell once, like setup.sh's VDock.app launcher does.
let userShellPathPromise = null
function userShellPath() {
  if (!userShellPathPromise) {
    userShellPathPromise = runtime.resolveLoginShellPath()
      .catch(() => null)
      .then((loginPath) => runtime.mergePathLists([
        loginPath,
        process.env.PATH,
        runtime.fallbackToolDirs().filter((dir) => fs.existsSync(dir)),
      ]))
  }
  return userShellPathPromise
}

function rememberBackendOutput(text) {
  const lines = String(text).split(/\r?\n/).filter((line) => line.trim())
  backendState.recentOutput.push(...lines)
  if (backendState.recentOutput.length > 60) {
    backendState.recentOutput.splice(0, backendState.recentOutput.length - 60)
  }
}

function writeBackendLog(text) {
  if (!backendState.logStream) return
  try {
    backendState.logStream.write(text)
  } catch {
    // never let logging kill the shell
  }
}

function openBackendLog() {
  if (backendState.logStream) return
  try {
    backendState.logStream = runtime.openCappedLog(backendLogPath())
    backendState.logStream.on('error', () => { backendState.logStream = null })
  } catch (error) {
    console.error('[backend] cannot open log', backendLogPath(), error.message)
  }
}

async function reportMissingBackend(exe) {
  backendState.failed = true
  const detail = `VDock cannot find its background service:\n${exe}\n\n`
    + 'Your antivirus may have quarantined it. Restore the file from quarantine '
    + '(and allow VDock), or reinstall VDock.'
  console.error('[backend]', detail)
  showStatusPage('VDock is missing a file', detail)
  const { response } = await dialog.showMessageBox(mainWindow && mainWindow.isVisible() ? mainWindow : undefined, {
    type: 'error',
    title: 'VDock',
    message: 'VDock is missing its background service',
    detail,
    buttons: ['Show Folder', 'Quit VDock'],
    defaultId: 1,
    cancelId: 1,
    noLink: true,
  })
  if (response === 0) {
    shell.openPath(backendDir())
  } else {
    quitApplication()
  }
}

async function showBackendFailure(quickFailures) {
  backendState.failed = true
  const logPath = backendLogPath()
  const addressInUse = runtime.isAddressInUse(backendState.recentOutput.join('\n'))
  const lastLines = backendState.recentOutput.slice(-3).join('\n')
  const reason = addressInUse && backendState.port
    ? `Port ${backendState.port} is already in use by another app.`
    : `It stopped ${quickFailures} times right after starting.`
  const detail = `${reason}\n\n${lastLines ? `Last output:\n${lastLines}\n\n` : ''}Log: ${logPath}`
  showStatusPage('VDock could not start', detail)

  for (;;) {
    const { response } = await dialog.showMessageBox(mainWindow && mainWindow.isVisible() ? mainWindow : undefined, {
      type: 'error',
      title: 'VDock',
      message: 'VDock could not start its background service',
      detail,
      buttons: ['Try Again', 'Open Log Folder', 'Quit VDock'],
      defaultId: 0,
      cancelId: 2,
      noLink: true,
    })
    if (response === 1) {
      shell.showItemInFolder(logPath)
      continue
    }
    if (response === 2) {
      quitApplication()
      return
    }
    backendState.failed = false
    backendState.policy.reset()
    if (await startBackend()) loadAppWhenReady()
    return
  }
}

function handleBackendExit(child, code, signal) {
  if (backendProcess === child) backendProcess = null
  if (!isDev) removePidFile(child.pid)
  const uptimeMs = Date.now() - backendState.startedAt
  const summary = `[backend] exited (code ${code}, signal ${signal}) after ${Math.round(uptimeMs / 1000)} s`
  console.log(summary)
  writeBackendLog(`${summary}\n`)

  if (code === 75) {
    // Exit 75 = the updater is replacing the app; quit instead of restarting.
    isQuitting = true
    app.quit()
    return
  }
  if (isQuitting) return

  if (!isDev && backendState.port && runtime.isAddressInUse(backendState.recentOutput.join('\n'))) {
    // Bound by something the loopback probe could not see (e.g. LAN on and
    // another app on 0.0.0.0): move to another port next time.
    backendState.avoidPorts.push(backendState.port)
  }

  const decision = backendState.policy.onExit({ uptimeMs })
  if (decision.giveUp) {
    showBackendFailure(decision.quickFailures)
    return
  }
  console.log(`[backend] restarting in ${decision.delayMs} ms`)
  clearTimeout(backendState.respawnTimer)
  backendState.respawnTimer = setTimeout(async () => {
    const previousPort = backendState.port
    if (await startBackend() && backendState.port !== previousPort) {
      // Settings > Ports changed it (or the old one was taken): follow it.
      loadAppWhenReady()
    }
  }, decision.delayMs)
}

// Start the backend. Resolves true once a process was spawned.
async function startBackend() {
  if (isQuitting) return false
  clearTimeout(backendState.respawnTimer)
  backendState.recentOutput = []

  const backendPath = backendDir()
  let command
  let args
  let env

  if (isDev) {
    // In development, run the venv Python directly (no shell activation chain).
    // The venv layout differs by OS: Windows uses venv\Scripts\python.exe,
    // macOS/Linux use venv/bin/python.
    command = path.join(
      backendPath, 'venv',
      process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'
    )
    args = [path.join(backendPath, 'app.py')]
    env = { ...process.env, VDOCK_ELECTRON: '1' }
  } else {
    // Production: the PyInstaller onedir bundle ships in extraResources as
    // resources/backend/ - self-contained, no Python needed on the host.
    command = backendExePath()
    args = []
    if (!fs.existsSync(command)) {
      await reportMissingBackend(command)
      return false
    }
    await stopOrphanBackend()
    const port = await preparePackagedPort()
    backendState.port = port
    env = {
      ...process.env,
      DATA_DIR: packagedDataDir(),
      VDOCK_ELECTRON: '1',
      // Beats DATA_DIR/.env (config.py loads .env without override), and the
      // file already holds the same value - Settings > Ports edits the file.
      PORT: String(port),
    }
    if (process.platform !== 'win32') {
      env.PATH = await userShellPath()
    }
  }
  if (isQuitting) return false

  openBackendLog()
  const header = `\n===== ${new Date().toISOString()} starting ${command}`
    + `${backendState.port ? ` on port ${backendState.port}` : ''} =====\n`
  console.log(header.trim())
  writeBackendLog(header)

  let child
  try {
    child = spawn(command, args, {
      cwd: backendPath,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
      windowsHide: true
    })
  } catch (error) {
    rememberBackendOutput(String(error && error.message))
    writeBackendLog(`spawn failed: ${error && error.message}\n`)
    backendState.startedAt = Date.now()
    handleBackendExit({ pid: undefined }, null, null)
    return false
  }

  backendProcess = child
  backendState.startedAt = Date.now()
  if (!isDev && child.pid) {
    try {
      fs.writeFileSync(pidFilePath(), JSON.stringify({ pid: child.pid, port: backendState.port, exe: command }))
    } catch {
      // DATA_DIR not writable yet; orphan cleanup just won't apply
    }
  }

  child.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`)
    writeBackendLog(data)
    rememberBackendOutput(data)
  })
  child.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`)
    writeBackendLog(data)
    rememberBackendOutput(data)
  })

  let exitHandled = false
  child.on('error', (error) => {
    console.error('Failed to start backend:', error)
    writeBackendLog(`backend error: ${error.message}\n`)
    rememberBackendOutput(error.message)
    // Only a failed spawn means the process is gone (a failed kill does not).
    if (!child.pid && !exitHandled) {
      exitHandled = true
      handleBackendExit(child, null, null)
    }
  })
  child.on('close', (code, signal) => {
    if (exitHandled) return
    exitHandled = true
    handleBackendExit(child, code, signal)
  })
  return true
}

// Stop backend server
function stopBackend() {
  clearTimeout(backendState.respawnTimer)
  if (backendProcess) {
    console.log('Stopping backend server...')
    const pid = backendProcess.pid
    backendProcess.kill('SIGTERM')
    backendProcess = null
    if (!isDev) removePidFile(pid)
  }
}

// ---------------------------------------------------------------------------
// Window content: a local status page until the backend answers (DL-010)
// ---------------------------------------------------------------------------

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]))
}

function showStatusPage(title, detail = '') {
  if (!mainWindow || mainWindow.isDestroyed()) return
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>VDock</title>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;
    font: 15px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif; background: #0f1115; color: #e6e8ee; }
  @media (prefers-color-scheme: light) { body { background: #f5f6f8; color: #1d2027; } }
  main { max-width: 560px; padding: 24px; text-align: center; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 12px; }
  pre { white-space: pre-wrap; word-break: break-word; text-align: left; opacity: .8; font: 12px/1.5 ui-monospace, Menlo, Consolas, monospace; }
</style></head><body><main><h1>${escapeHtml(title)}</h1>${detail ? `<pre>${escapeHtml(detail)}</pre>` : ''}</main></body></html>`
  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`).catch(() => {})
}

function appUrl() {
  if (isDev) {
    // Dev: load from Vite dev server (hot-reload).
    return `http://localhost:${process.env.VDOCK_FRONTEND_PORT || '3000'}`
  }
  // Prod: Flask serves the built dist. `localhost` (not 127.0.0.1) keeps the
  // origin - and so the saved sign-in/UI state - of earlier installs.
  const port = backendState.port || process.env.VDOCK_BACKEND_PORT || '5000'
  return `${backendState.scheme}://localhost:${port}`
}

function appIsReady() {
  if (isDev) {
    return runtime.httpGet(appUrl()).then((result) => Boolean(result && result.status < 500))
  }
  const port = backendState.port || process.env.VDOCK_BACKEND_PORT || '5000'
  return runtime.httpGet(`${backendState.scheme}://127.0.0.1:${port}/api/health`, { insecureLoopback: true })
    .then(runtime.looksLikeVdockHealth)
}

function isOwnBackendUrl(url) {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:'
      && ['localhost', '127.0.0.1'].includes(parsed.hostname)
      && Number(parsed.port) === Number(backendState.port)
  } catch {
    return false
  }
}

let loadGeneration = 0
let firstAppLoad = true

// Show "Starting VDock...", wait until the backend (or Vite) answers, then
// load the app. Re-entrant: a newer call cancels the older wait.
async function loadAppWhenReady() {
  if (!mainWindow || mainWindow.isDestroyed()) return
  const generation = ++loadGeneration
  const cancelled = () => generation !== loadGeneration || !mainWindow || mainWindow.isDestroyed() || backendState.failed

  showStatusPage('Starting VDock...')
  let ready = await runtime.waitUntil(appIsReady, { intervalMs: 500, timeoutMs: 30000, isCancelled: cancelled })
  if (!ready && !cancelled()) {
    showStatusPage('VDock is taking longer than usual to start...',
      `Waiting for ${appUrl()}\n\nLog: ${backendLogPath()}`)
    ready = await runtime.waitUntil(appIsReady, { intervalMs: 1000, isCancelled: cancelled })
  }
  if (!ready || cancelled()) return

  const url = appUrl()
  console.log('Loading URL:', url)
  try {
    await mainWindow.loadURL(url)
  } catch (error) {
    // did-fail-load schedules the retry
    console.error('Failed to load URL:', error.message)
    return
  }
  console.log('URL loaded successfully')
  if (firstAppLoad && mainWindow && !mainWindow.isDestroyed()) {
    firstAppLoad = false
    mainWindow.show()
    mainWindow.focus()
    mainWindow.setAlwaysOnTop(true)
    setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) mainWindow.setAlwaysOnTop(alwaysOnTop)
    }, 1000)
  }
}

function showMainWindow() {
  if (!app.isReady()) return
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow()
    if (!backendState.failed) loadAppWhenReady()
    return
  }
  if (mainWindow.isMinimized()) mainWindow.restore()
  mainWindow.show()
  mainWindow.focus()
}

function createWindow() {
  const targetDisplay = resolveTargetDisplay()
  const workArea = targetDisplay.workArea
  // Both dimensions must be small — a portrait monitor (narrow but tall) or an
  // ultrawide-but-short one is a normal display, not a tiny embedded touch panel.
  const isCompactDisplay = workArea.width <= 1100 && workArea.height <= 650
  const shouldStartFullscreen =
    process.env.VDOCK_FULLSCREEN === '1' ||
    process.env.VDOCK_KIOSK === '1' ||
    isCompactDisplay

  kioskMode = process.env.VDOCK_KIOSK === '1' || (shouldStartFullscreen && isCompactDisplay)

  console.log('[OK] Target display:', {
    id: targetDisplay.id,
    bounds: targetDisplay.bounds,
    workArea,
    scaleFactor: targetDisplay.scaleFactor
  })

  mainWindow = new BrowserWindow({
    x: workArea.x,
    y: workArea.y,
    width: workArea.width,
    height: workArea.height,
    minWidth: isCompactDisplay ? workArea.width : 800,
    minHeight: isCompactDisplay ? workArea.height : 600,
    frame: !kioskMode,
    fullscreen: false,
    fullscreenable: true,
    autoHideMenuBar: true,
    transparent: false,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public', iconFile)
  })

  mainWindow.setBounds({
    x: workArea.x,
    y: workArea.y,
    width: workArea.width,
    height: workArea.height
  })

  mainWindow.once('ready-to-show', () => {
    if (shouldStartFullscreen) {
      mainWindow.setFullScreen(true)
      mainWindow.setMenuBarVisibility(false)
    }

    mainWindow.show()
    mainWindow.focus()

    console.log('[OK] Window created and shown')
    console.log('Window visible:', mainWindow.isVisible())
    console.log('Window minimized:', mainWindow.isMinimized())
    console.log('Window bounds:', mainWindow.getBounds())
    console.log('Window full screen:', mainWindow.isFullScreen())
  })

  // Content arrives through loadAppWhenReady(): a local "Starting VDock..."
  // page first, the app once the backend (or Vite) answers (DL-010).
  // DevTools can be opened manually with F12 if needed.
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page finished loading')
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.includes('/settings')) {
      void shell.openExternal(url)
      return { action: 'deny' }
    }

    return { action: 'allow' }
  })

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    console.error('Page failed to load:', errorCode, errorDescription, validatedURL)
    // -3 = ERR_ABORTED: a newer navigation replaced this one, nothing to retry.
    if (!isMainFrame || errorCode === -3 || String(validatedURL).startsWith('data:')) return
    if (backendState.failed || isQuitting) return
    // The backend restarted mid-load (Settings restart, crash): wait and retry.
    setTimeout(() => loadAppWhenReady(), 1000)
  })

  mainWindow.webContents.on('console-message', (event) => {
    const message = event?.message ?? event
    if (message) {
      console.log(`[Renderer] ${message}`)
    }
  })

  // Window event handlers
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault()
      mainWindow.hide()
      return false
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Set always on top if enabled
  mainWindow.setAlwaysOnTop(alwaysOnTop)
}

function quitApplication() {
  isQuitting = true
  // Defer the actual window teardown by a tick so any pending IPC reply
  // (e.g. the 'quit-app' invoke() the renderer is awaiting) has a chance to
  // flush over the webContents channel before it gets destroyed. Destroying
  // the window synchronously here could otherwise leave the renderer's
  // promise hanging/rejecting mid-flight.
  setImmediate(() => {
    if (mainWindow) {
      mainWindow.destroy()
      mainWindow = null
    }
    app.quit()
    // Fallback in case something (e.g. a lingering tray reference) keeps the
    // process alive after app.quit() — force-terminate as a last resort.
    setTimeout(() => app.exit(0), 1000)
  })
}

function openSettingsPage() {
  // Route the existing main window to the in-app settings — the old modal
  // settings window was a dead duplicate of the real settings surface.
  if (!mainWindow) return
  mainWindow.show()
  mainWindow.focus()
  mainWindow.webContents.send('navigate-to', '/settings')
}

function createTrayMenu() {
  return Menu.buildFromTemplate([
    {
      label: 'Show VDock',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.focus()
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        openSettingsPage()
      }
    },
    { type: 'separator' },
    {
      label: 'Exit',
      click: () => {
        quitApplication()
      }
    }
  ])
}

function createTray() {
  const iconPath = path.join(__dirname, '../public', iconFile)
  tray = new Tray(iconPath)

  tray.setToolTip('VDock - Virtual Stream Deck')

  tray.setContextMenu(createTrayMenu())

  // Double-click to show/hide
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide()
      } else {
        mainWindow.show()
        mainWindow.focus()
      }
    }
  })
}

function toggleFullscreen() {
  if (!mainWindow) return false

  const enteringFullscreen = !mainWindow.isFullScreen()
  mainWindow.setFullScreen(enteringFullscreen)
  mainWindow.setMenuBarVisibility(!enteringFullscreen)

  if (enteringFullscreen) {
    mainWindow.setAlwaysOnTop(false)
  }

  return enteringFullscreen
}

function registerGlobalShortcuts() {
  // Global shortcut so fullscreen can always be escaped even when the deck
  // header (which holds the in-app toggle button) is collapsed/hidden.
  globalShortcut.register('CommandOrControl+Shift+F', () => {
    toggleFullscreen()
  })

  // Global shortcut to summon the deck at the cursor (Ctrl+Shift+D). On show it
  // also opens the quick-deck overlay — press a key, it dismisses itself.
  globalShortcut.register('CommandOrControl+Shift+D', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.webContents.send('quick-deck-toggle')
      } else {
        // Show at cursor position
        const cursorPosition = screen.getCursorScreenPoint()
        const bounds = mainWindow.getBounds()

        mainWindow.setPosition(
          cursorPosition.x - bounds.width / 2,
          cursorPosition.y - bounds.height / 2
        )

        mainWindow.show()
        mainWindow.focus()
        mainWindow.webContents.send('quick-deck-toggle')
      }
    }
  })
}

// IPC handlers
ipcMain.handle('window-pin', (event, pinned) => {
  windowPinned = pinned
  // Implement pin logic (prevent window from being moved)
  return windowPinned
})

ipcMain.handle('window-dock', (event, side) => {
  if (!mainWindow) return

  const { width, height } = screen.getPrimaryDisplay().workAreaSize
  const windowWidth = 400
  const windowHeight = height

  let x = 0, y = 0

  switch (side) {
    case 'left':
      x = 0
      y = 0
      break
    case 'right':
      x = width - windowWidth
      y = 0
      break
    case 'top':
      x = 0
      y = 0
      break
    case 'bottom':
      x = 0
      y = height - 400
      break
    default:
      return
  }

  mainWindow.setBounds({
    x,
    y,
    width: side === 'left' || side === 'right' ? windowWidth : width,
    height: side === 'top' || side === 'bottom' ? 400 : windowHeight
  })
})

ipcMain.handle('window-always-on-top', (event, enabled) => {
  alwaysOnTop = enabled
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(alwaysOnTop)
  }
  return alwaysOnTop
})

ipcMain.handle('window-summon-to-cursor', () => {
  if (!mainWindow) return

  const cursorPosition = screen.getCursorScreenPoint()
  const bounds = mainWindow.getBounds()
  
  mainWindow.setPosition(
    cursorPosition.x - bounds.width / 2,
    cursorPosition.y - bounds.height / 2
  )
  
  mainWindow.show()
  mainWindow.focus()
})

ipcMain.handle('window-toggle-fullscreen', () => {
  return toggleFullscreen()
})

ipcMain.handle('window-is-fullscreen', () => {
  if (!mainWindow) return false
  return mainWindow.isFullScreen()
})

ipcMain.handle('window-set-kiosk', (event, enabled) => {
  if (!mainWindow) return false

  kioskMode = Boolean(enabled)
  mainWindow.setFullScreen(kioskMode)
  mainWindow.setKiosk(kioskMode)
  mainWindow.setMenuBarVisibility(!kioskMode)

  return kioskMode
})

ipcMain.handle('open-external-url', async (_event, url) => {
  if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) {
    throw new Error('Invalid external URL')
  }

  await shell.openExternal(url)
})

ipcMain.handle('quit-app', async () => {
  quitApplication()
})

// Native file picker for per-app executable overrides (DL-084). Returns the
// chosen absolute path, or null when cancelled. Filters are platform-aware:
// .app is a directory bundle, so macOS needs it as an explicit filter.
ipcMain.handle('pick-executable', async () => {
  const filters = process.platform === 'win32'
    ? [{ name: 'Executables', extensions: ['exe', 'cmd', 'bat', 'com'] },
       { name: 'All files', extensions: ['*'] }]
    : process.platform === 'darwin'
      ? [{ name: 'Applications', extensions: ['app'] },
         { name: 'All files', extensions: ['*'] }]
      : [{ name: 'All files', extensions: ['*'] }]
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Choose application executable',
    properties: ['openFile'],
    filters,
  })
  return result.canceled ? null : (result.filePaths[0] ?? null)
})

// App event handlers
app.on('second-instance', () => {
  // Someone launched VDock again: bring the running window forward.
  showMainWindow()
})

// HTTPS (Settings) uses a self-signed certificate. Trust it for our own
// loopback backend only; every other certificate error stays an error.
app.on('certificate-error', (event, _webContents, url, _error, _certificate, callback) => {
  if (backendState.scheme === 'https' && isOwnBackendUrl(url)) {
    event.preventDefault()
    callback(true)
    return
  }
  callback(false)
})

app.whenReady().then(async () => {
  if (!gotSingleInstanceLock) return

  console.log('========================================')
  console.log('Electron app ready - initializing VDock')
  console.log('========================================')

  applyVdockIdentity()

  createWindow()
  showStatusPage('Starting VDock...')
  console.log('[OK] Window created')

  createTray()
  console.log('[OK] Tray icon created')

  registerGlobalShortcuts()
  console.log('[OK] Global shortcuts registered')

  if (process.env.VDOCK_SKIP_BACKEND_SPAWN === '1') {
    console.log('[OK] Backend already started by launcher — skipping spawn')
    loadAppWhenReady()
  } else if (await startBackend()) {
    console.log('[OK] Backend starting...')
    loadAppWhenReady()
  }

  console.log('========================================')
  console.log('VDock initialization complete!')
  console.log('========================================')
})

// Every real quit - Cmd+Q / app menu, SIGTERM, logout or shutdown, the
// updater - must get past the window's hide-to-tray close handler; before
// this, only the tray's Exit did, so Cmd+Q and a logout were silently
// cancelled (DL-010). The window's X still just hides it.
app.on('before-quit', () => {
  isQuitting = true
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // Dock click: the window may only be hidden (close hides it), not gone.
  showMainWindow()
})

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll()
  // Stop backend server
  stopBackend()
})
