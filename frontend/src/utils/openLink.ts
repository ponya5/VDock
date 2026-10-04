/** Open an external URL via the Electron bridge, or a new tab in a browser. */
export function openLink(url: string | null | undefined): void {
  if (!url) return
  const bridge = (window as Window & {
    electronAPI?: { openExternal?: (url: string) => Promise<void> }
  }).electronAPI
  if (bridge?.openExternal) void bridge.openExternal(url)
  else window.open(url, '_blank', 'noopener,noreferrer')
}
