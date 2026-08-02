/**
 * Composable for interacting with Electron API
 */

interface ElectronAPI {
  windowPin: (pinned: boolean) => Promise<boolean>
  windowDock: (side: 'left' | 'right' | 'top' | 'bottom' | 'none') => Promise<void>
  windowAlwaysOnTop: (enabled: boolean) => Promise<boolean>
  windowSummonToCursor: () => Promise<void>
  toggleFullscreen: () => Promise<boolean>
  isFullscreen: () => Promise<boolean>
  setKioskMode: (enabled: boolean) => Promise<boolean>
  toggleAutoLaunch: (enabled: boolean) => Promise<boolean>
  isAutoLaunchEnabled: () => Promise<boolean>
  platform: string
  isElectron: boolean
}

declare global {
  interface Window {
    electron?: ElectronAPI
    electronAPI?: ElectronAPI
  }
}

function getElectronApi(): ElectronAPI | undefined {
  return window.electron || window.electronAPI
}

export function useElectron() {
  const isElectron = () => {
    return getElectronApi()?.isElectron || false
  }

  const pinWindow = async (pinned: boolean): Promise<boolean> => {
    const electronApi = getElectronApi()
    if (!electronApi) return false
    return await electronApi.windowPin(pinned)
  }

  const dockWindow = async (side: 'left' | 'right' | 'top' | 'bottom' | 'none'): Promise<void> => {
    const electronApi = getElectronApi()
    if (!electronApi) return
    await electronApi.windowDock(side)
  }

  const setAlwaysOnTop = async (enabled: boolean): Promise<boolean> => {
    const electronApi = getElectronApi()
    if (!electronApi) return false
    return await electronApi.windowAlwaysOnTop(enabled)
  }

  const summonToCursor = async (): Promise<void> => {
    const electronApi = getElectronApi()
    if (!electronApi) return
    await electronApi.windowSummonToCursor()
  }

  const toggleFullscreen = async (): Promise<boolean> => {
    const electronApi = getElectronApi()
    if (electronApi?.toggleFullscreen) {
      return await electronApi.toggleFullscreen()
    }

    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
        return true
      }

      await document.exitFullscreen()
      return false
    } catch (error) {
      console.error('Failed to toggle fullscreen:', error)
      return false
    }
  }

  const isFullscreen = async (): Promise<boolean> => {
    const electronApi = getElectronApi()
    if (electronApi?.isFullscreen) {
      return await electronApi.isFullscreen()
    }

    return Boolean(document.fullscreenElement)
  }

  const setKioskMode = async (enabled: boolean): Promise<boolean> => {
    const electronApi = getElectronApi()
    if (!electronApi?.setKioskMode) return false
    return await electronApi.setKioskMode(enabled)
  }

  const getPlatform = (): string => {
    return getElectronApi()?.platform || 'web'
  }

  return {
    isElectron,
    pinWindow,
    dockWindow,
    setAlwaysOnTop,
    summonToCursor,
    toggleFullscreen,
    isFullscreen,
    setKioskMode,
    getPlatform
  }
}
