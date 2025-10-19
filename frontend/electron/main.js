const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, screen } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const AutoLaunch = require('auto-launch')
const isDev = process.env.NODE_ENV === 'development'

let mainWindow = null
let tray = null
let isQuitting = false
let windowPinned = false
let alwaysOnTop = false
let backendProcess = null
let autoLaunch = null

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
  
  const pythonPath = isDev 
    ? 'python' 
    : path.join(backendPath, 'python', 'python.exe')
  
  const appPath = path.join(backendPath, 'app.py')
  
  console.log('Starting backend server...')
  console.log('Backend path:', backendPath)
  console.log('Python path:', pythonPath)
  console.log('App path:', appPath)
  
  backendProcess = spawn(pythonPath, [appPath], {
    cwd: backendPath,
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false
  })
  
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
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    frame: true,
    transparent: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/icon.png')
  })

  // Load app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    // Wait for backend to start, then load the app
    setTimeout(() => {
      mainWindow.loadURL('http://localhost:5000')
    }, 3000)
  }

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

function createTray() {
  const iconPath = path.join(__dirname, '../public/icon.png')
  tray = new Tray(iconPath)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show VDock',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.focus()
        }
      }
    },
    {
      label: 'Toggle Always on Top',
      type: 'checkbox',
      checked: alwaysOnTop,
      click: (item) => {
        alwaysOnTop = item.checked
        if (mainWindow) {
          mainWindow.setAlwaysOnTop(alwaysOnTop)
        }
      }
    },
    {
      label: 'Start with Windows',
      type: 'checkbox',
      checked: false,
      click: async (item) => {
        try {
          if (item.checked) {
            await autoLaunch.enable()
          } else {
            await autoLaunch.disable()
          }
        } catch (err) {
          console.error('Failed to toggle auto-launch:', err)
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('VDock - Virtual Stream Deck')
  tray.setContextMenu(contextMenu)

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

// App event handlers
app.whenReady().then(async () => {
  initializeAutoLaunch()
  startBackend()
  createWindow()
  createTray()
  registerGlobalShortcuts()
  
  // Check if auto-launch is enabled
  try {
    const isEnabled = await autoLaunch.isEnabled()
    console.log('Auto-launch enabled:', isEnabled)
  } catch (err) {
    console.error('Failed to check auto-launch status:', err)
  }
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

