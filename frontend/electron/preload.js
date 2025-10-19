const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  windowPin: (pinned) => ipcRenderer.invoke('window-pin', pinned),
  windowDock: (side) => ipcRenderer.invoke('window-dock', side),
  windowAlwaysOnTop: (enabled) => ipcRenderer.invoke('window-always-on-top', enabled),
  windowSummonToCursor: () => ipcRenderer.invoke('window-summon-to-cursor'),
  
  // Auto-launch controls
  toggleAutoLaunch: (enabled) => ipcRenderer.invoke('toggle-auto-launch', enabled),
  isAutoLaunchEnabled: () => ipcRenderer.invoke('is-auto-launch-enabled'),
  
  // Platform info
  platform: process.platform,
  isElectron: true
})

