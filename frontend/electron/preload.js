const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Window controls
  windowPin: (pinned) => ipcRenderer.invoke('window-pin', pinned),
  windowDock: (side) => ipcRenderer.invoke('window-dock', side),
  windowAlwaysOnTop: (enabled) => ipcRenderer.invoke('window-always-on-top', enabled),
  windowSummonToCursor: () => ipcRenderer.invoke('window-summon-to-cursor'),
  
  // Platform info
  platform: process.platform,
  isElectron: true
})

