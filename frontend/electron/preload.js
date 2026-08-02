const { contextBridge, ipcRenderer } = require('electron')

const electronBridge = {
  // Window controls
  windowPin: (pinned) => ipcRenderer.invoke('window-pin', pinned),
  windowDock: (side) => ipcRenderer.invoke('window-dock', side),
  windowAlwaysOnTop: (enabled) => ipcRenderer.invoke('window-always-on-top', enabled),
  windowSummonToCursor: () => ipcRenderer.invoke('window-summon-to-cursor'),
  toggleFullscreen: () => ipcRenderer.invoke('window-toggle-fullscreen'),
  isFullscreen: () => ipcRenderer.invoke('window-is-fullscreen'),
  setKioskMode: (enabled) => ipcRenderer.invoke('window-set-kiosk', enabled),

  // Auto-launch controls
  toggleAutoLaunch: (enabled) => ipcRenderer.invoke('toggle-auto-launch', enabled),
  isAutoLaunchEnabled: () => ipcRenderer.invoke('is-auto-launch-enabled'),

  // Platform info
  platform: process.platform,
  isElectron: true
}

// Expose under both names for backward compatibility
contextBridge.exposeInMainWorld('electronAPI', electronBridge)
contextBridge.exposeInMainWorld('electron', electronBridge)

