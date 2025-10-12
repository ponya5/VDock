/**
 * Composable for interacting with Electron API
 */

interface ElectronAPI {
  windowPin: (pinned: boolean) => Promise<boolean>
  windowDock: (side: 'left' | 'right' | 'top' | 'bottom' | 'none') => Promise<void>
  windowAlwaysOnTop: (enabled: boolean) => Promise<boolean>
  windowSummonToCursor: () => Promise<void>
  platform: string
  isElectron: boolean
}

declare global {
  interface Window {
    electron?: ElectronAPI
  }
}

export function useElectron() {
  const isElectron = () => {
    return window.electron?.isElectron || false
  }

  const pinWindow = async (pinned: boolean): Promise<boolean> => {
    if (!window.electron) return false
    return await window.electron.windowPin(pinned)
  }

  const dockWindow = async (side: 'left' | 'right' | 'top' | 'bottom' | 'none'): Promise<void> => {
    if (!window.electron) return
    await window.electron.windowDock(side)
  }

  const setAlwaysOnTop = async (enabled: boolean): Promise<boolean> => {
    if (!window.electron) return false
    return await window.electron.windowAlwaysOnTop(enabled)
  }

  const summonToCursor = async (): Promise<void> => {
    if (!window.electron) return
    await window.electron.windowSummonToCursor()
  }

  const getPlatform = (): string => {
    return window.electron?.platform || 'web'
  }

  return {
    isElectron,
    pinWindow,
    dockWindow,
    setAlwaysOnTop,
    summonToCursor,
    getPlatform
  }
}

