const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, screen, shell } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const AutoLaunch = require('auto-launch')
// Detect development mode by checking if backend exists relative to electron directory
const isDev = require('fs').existsSync(path.join(__dirname, '../../backend'))

let mainWindow = null
let tray = null
let isQuitting = false
let windowPinned = false
let alwaysOnTop = false
let kioskMode = false
let backendProcess = null
let autoLaunch = null

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

// Initialize auto-launch
function initializeAutoLaunch() {
  autoLaunch = new AutoLaunch({
    name: 'VDock',
    path: app.getPath('exe'),
    isHidden: true
  })
}

// Start backend server
function startBackend() {
  const backendPath = isDev
    ? path.join(__dirname, '../../backend')
    : path.join(process.resourcesPath, 'backend')

  const appPath = path.join(backendPath, 'app.py')

  console.log('========================================')
  console.log('Starting backend server...')
  console.log('Development mode:', isDev)
  console.log('Backend path:', backendPath)
  console.log('App path:', appPath)
  console.log('========================================')

  // In development, run the venv Python directly (no shell activation chain)
  if (isDev) {
    const venvPython = path.join(backendPath, 'venv', 'Scripts', 'python.exe')

    console.log('Using venv Python:', venvPython)

    backendProcess = spawn(venvPython, [appPath], {
      cwd: backendPath,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
      windowsHide: true
    })
  } else {
    // In production, use bundled python
    const pythonPath = path.join(process.resourcesPath, 'backend', 'python.exe')
    backendProcess = spawn(pythonPath, [appPath], {
      cwd: backendPath,
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: false
    })
  }
  
  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`)
  })
  
  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`)
  })
  
  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
    if (!isQuitting) {
      // Restart backend if it crashes
      setTimeout(() => {
        startBackend()
      }, 5000)
    }
  })
  
  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err)
  })
}

// Stop backend server
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend server...')
    backendProcess.kill('SIGTERM')
    backendProcess = null
  }
}

function createWindow() {
  const targetDisplay = resolveTargetDisplay()
  const workArea = targetDisplay.workArea
  const isCompactDisplay = workArea.width <= 1100 || workArea.height <= 650
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
    icon: path.join(__dirname, '../public/vdock-icon.ico')
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

  // Load app
  // Dev: load from Vite dev server (hot-reload). Prod: load from Flask which serves built dist.
  const appUrl = isDev ? 'http://localhost:3000' : 'http://localhost:5000'
  setTimeout(() => {
    console.log('Loading URL:', appUrl)
    mainWindow.loadURL(appUrl).then(() => {
      console.log('URL loaded successfully')
      // Force show and focus after load
      mainWindow.show()
      mainWindow.focus()
      mainWindow.setAlwaysOnTop(true)
      setTimeout(() => mainWindow.setAlwaysOnTop(false), 1000)
      console.log('Window should be on top now')
    }).catch((err) => {
      console.error('Failed to load URL:', err)
      // Show error in window
      mainWindow.loadURL(`data:text/html,<html><body style="font-family: Arial; padding: 20px;"><h1>Failed to load VDock</h1><p>Error: ${err.message}</p><p>Please ensure the server is running on ${appUrl}</p></body></html>`)
    })

    // DevTools can be opened manually with F12 if needed
    // if (isDev) {
    //   mainWindow.webContents.openDevTools()
    // }

    // Add console logging for page load events
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

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error('Page failed to load:', errorCode, errorDescription)
    })

    mainWindow.webContents.on('console-message', (event) => {
      const message = event?.message ?? event
      if (message) {
        console.log(`[Renderer] ${message}`)
      }
    })
  }, 3000)

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
  if (mainWindow) {
    mainWindow.destroy()
  }
  app.quit()
}

function fixFirewall() {
  const { dialog } = require('electron')
  const { exec } = require('child_process')

  // Show confirmation dialog
  dialog.showMessageBox(mainWindow, {
    type: 'question',
    buttons: ['Yes', 'Cancel'],
    defaultId: 0,
    title: 'Fix Windows Firewall',
    message: 'Add VDock to Windows Firewall exclusions?',
    detail: 'This will add VDock launcher files to Windows Firewall exceptions to prevent connection issues.\n\nThis requires administrator privileges.'
  }).then(result => {
    if (result.response === 0) {
      // User clicked Yes
      const launcherPath = process.execPath
      const pythonPath = path.join(__dirname, '../../backend/venv/Scripts/python.exe')

      // Add firewall rules
      const commands = [
        `netsh advfirewall firewall add rule name="VDock Electron" dir=in action=allow program="${launcherPath}" enable=yes`,
        `netsh advfirewall firewall add rule name="VDock Python Backend" dir=in action=allow program="${pythonPath}" enable=yes`
      ]

      // Execute firewall commands with admin privileges
      const psCommand = commands.map(cmd => `Start-Process -Verb RunAs -FilePath "cmd" -ArgumentList "/c", "${cmd.replace(/"/g, '\\"')}" -Wait`).join('; ')

      exec(`powershell -Command "${psCommand}"`, (error, stdout, stderr) => {
        if (error) {
          dialog.showErrorBox('Firewall Fix Failed', `Failed to add firewall rules:\n${error.message}\n\nPlease run VDock as administrator or add the rules manually.`)
        } else {
          dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Firewall Fixed',
            message: 'VDock has been added to Windows Firewall exclusions successfully!',
            detail: 'You should no longer experience connection issues.'
          })
        }
      })
    }
  })
}

async function openSettings() {
  // Get current auto-launch status
  const isAutoLaunchEnabled = await autoLaunch.isEnabled().catch(() => false)

  // Create a simple settings window
  const settingsWindow = new BrowserWindow({
    width: 400,
    height: 300,
    parent: mainWindow,
    modal: true,
    show: false,
    frame: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/vdock-icon.ico')
  })

  // Create HTML content for settings
  const settingsHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>VDock Settings</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .setting { margin: 15px 0; }
        .setting label { display: block; margin-bottom: 5px; font-weight: bold; }
        .setting input[type="checkbox"] { margin-right: 8px; }
        button { padding: 8px 16px; margin: 10px 5px 0 0; border: none; border-radius: 4px; cursor: pointer; }
        .save { background: #007acc; color: white; }
        .cancel { background: #ccc; color: black; }
      </style>
    </head>
    <body>
      <h2>VDock Settings</h2>

      <div class="setting">
        <label>
          <input type="checkbox" id="alwaysOnTop" ${alwaysOnTop ? 'checked' : ''}>
          Always on Top
        </label>
      </div>

      <div class="setting">
        <label>
          <input type="checkbox" id="startWithWindows" ${isAutoLaunchEnabled ? 'checked' : ''}>
          Start with Windows
        </label>
      </div>

      <div class="setting">
        <label for="theme">Theme:</label>
        <select id="theme">
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <button class="save" onclick="saveSettings()">Save</button>
      <button class="cancel" onclick="closeSettings()">Cancel</button>

      <script>
        function saveSettings() {
          const alwaysOnTop = document.getElementById('alwaysOnTop').checked;
          const startWithWindows = document.getElementById('startWithWindows').checked;

          // Send settings to main process
          window.postMessage({
            type: 'settings-update',
            alwaysOnTop: alwaysOnTop,
            startWithWindows: startWithWindows
          }, '*');

          window.close();
        }

        function closeSettings() {
          window.close();
        }
      </script>
    </body>
    </html>
  `

  settingsWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(settingsHtml)}`)
  settingsWindow.show()
}

async function createTrayMenu() {
  const isAutoLaunchEnabled = await autoLaunch.isEnabled().catch(() => false)

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
        // Open settings window or dialog
        openSettings()
      }
    },
    {
      label: 'Fix Firewall',
      click: () => {
        fixFirewall()
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
  const iconPath = path.join(__dirname, '../public/vdock-icon.ico')
  tray = new Tray(iconPath)

  tray.setToolTip('VDock - Virtual Stream Deck')

  // Set initial menu
  createTrayMenu().then(menu => {
    tray.setContextMenu(menu)
  })

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

async function updateTrayMenu() {
  if (tray) {
    const menu = await createTrayMenu()
    tray.setContextMenu(menu)
  }
}

function registerGlobalShortcuts() {
  // Global shortcut to summon window (Ctrl+Shift+D)
  globalShortcut.register('CommandOrControl+Shift+D', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide()
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

ipcMain.handle('settings-update', async (event, settings) => {
  try {
    alwaysOnTop = settings.alwaysOnTop
    if (mainWindow) {
      mainWindow.setAlwaysOnTop(alwaysOnTop)
    }

    if (settings.startWithWindows) {
      await autoLaunch.enable()
    } else {
      await autoLaunch.disable()
    }

    // Update tray menu to reflect changes
    updateTrayMenu()

    return true
  } catch (err) {
    console.error('Failed to update settings:', err)
    return false
  }
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
  if (!mainWindow) return false

  const enteringFullscreen = !mainWindow.isFullScreen()
  mainWindow.setFullScreen(enteringFullscreen)
  mainWindow.setMenuBarVisibility(!enteringFullscreen)

  if (enteringFullscreen) {
    mainWindow.setAlwaysOnTop(false)
  }

  return enteringFullscreen
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

// Auto-launch IPC handlers
ipcMain.handle('toggle-auto-launch', async (event, enabled) => {
  try {
    if (enabled) {
      await autoLaunch.enable()
    } else {
      await autoLaunch.disable()
    }
    return true
  } catch (err) {
    console.error('Failed to toggle auto-launch:', err)
    return false
  }
})

ipcMain.handle('is-auto-launch-enabled', async () => {
  try {
    return await autoLaunch.isEnabled()
  } catch (err) {
    console.error('Failed to check auto-launch status:', err)
    return false
  }
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

// App event handlers
app.whenReady().then(async () => {
  console.log('========================================')
  console.log('Electron app ready - initializing VDock')
  console.log('========================================')

  initializeAutoLaunch()
  console.log('[OK] Auto-launch initialized')

  if (process.env.VDOCK_SKIP_BACKEND_SPAWN === '1') {
    console.log('[OK] Backend already started by launcher — skipping spawn')
  } else {
    startBackend()
    console.log('[OK] Backend starting...')
  }

  createWindow()
  console.log('[OK] Window created')

  createTray()
  console.log('[OK] Tray icon created')

  registerGlobalShortcuts()
  console.log('[OK] Global shortcuts registered')

  // Check if auto-launch is enabled
  try {
    const isEnabled = await autoLaunch.isEnabled()
    console.log('Auto-launch enabled:', isEnabled)
  } catch (err) {
    console.error('Failed to check auto-launch status:', err)
  }

  console.log('========================================')
  console.log('VDock initialization complete!')
  console.log('Window should be visible now')
  console.log('========================================')
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll()
  // Stop backend server
  stopBackend()
})

// Auto-launch on system startup (optional)
app.setLoginItemSettings({
  openAtLogin: false, // Can be toggled via settings
  openAsHidden: true
})

