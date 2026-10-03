/**
 * Words for "put VDock on the Home Screen" (DL-147, built on the DL-067
 * callout). One source for the fullscreen callout, the phone ⋮ menu sheet and
 * the Connect page step, so the three never drift apart.
 */
export type InstallPlatform = 'ios' | 'android' | 'other'

export const IOS_FULLSCREEN_CALLOUT = 'Add to Home Screen for fullscreen (Share → Add to Home Screen)'
export const CONNECT_INSTALL_STEP = 'on the device, add VDock to the Home Screen for a full-screen deck with no browser bars.'

export function installPlatform(userAgent: string, maxTouchPoints = 0): InstallPlatform {
  if (/iPhone|iPad|iPod/i.test(userAgent) || (/Macintosh/i.test(userAgent) && maxTouchPoints > 1)) return 'ios'
  if (/Android/i.test(userAgent)) return 'android'
  return 'other'
}

export function installSteps(platform: InstallPlatform): string[] {
  switch (platform) {
    case 'ios':
      return ['Tap the Share button in Safari.', 'Choose Add to Home Screen.', 'Open VDock from the new icon: it launches full-screen.']
    case 'android':
      return ['Tap ⋮ in Chrome.', 'Choose Add to Home screen (or Install app).', 'Open VDock from the new icon.']
    default:
      return ['Open your browser menu.', 'Choose Add to Home screen or Install app.']
  }
}

/** Honest about plain HTTP: Android then makes a shortcut, not a real install. */
export function installNote(platform: InstallPlatform, secureContext: boolean): string | null {
  if (platform === 'ios') return null
  return secureContext
    ? null
    : 'Over plain Wi-Fi (http) this adds a shortcut that opens in the browser. For a real installed app, turn on HTTPS (USE_SSL) on the PC.'
}
