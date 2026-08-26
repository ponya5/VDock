import type { Router } from 'vue-router'

interface ElectronBridge {
  openExternal?: (url: string) => Promise<void>
}

export function buildStandaloneSettingsUrl(
  router: Router,
  query: Record<string, string> = {}
): string {
  const settingsRoute = router.resolve({
    name: 'settings',
    query: {
      standalone: '1',
      ...query,
    },
  })

  return new URL(settingsRoute.href, window.location.origin).href
}

export function isStandaloneSettingsRoute(route: { path: string; query: Record<string, unknown> }): boolean {
  return route.path === '/settings' && route.query.standalone === '1'
}

interface OpenStandaloneSettingsOptions {
  router: Router
  query?: Record<string, string>
  returnMainWindowToDashboard?: boolean
}

export function openStandaloneSettings({
  router,
  query = {},
  returnMainWindowToDashboard = false,
}: OpenStandaloneSettingsOptions): boolean {
  const settingsUrl = buildStandaloneSettingsUrl(router, query)
  const electronBridge = (window as Window & { electronAPI?: ElectronBridge }).electronAPI

  if (electronBridge?.openExternal) {
    void electronBridge.openExternal(settingsUrl)

    if (returnMainWindowToDashboard) {
      void router.push('/')
    }

    return true
  }

  const newTab = window.open(settingsUrl, '_blank', 'noopener,noreferrer')
  return !!newTab
}
