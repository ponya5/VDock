/**
 * Platform capability checks for the mobile fullscreen control (DL-067).
 *
 * iPhone Safari — unlike iPad Safari, desktop Safari, and every other
 * mobile browser — never implemented the Fullscreen API: `requestFullscreen`
 * is simply absent from `document.documentElement`, so calling it always
 * throws/rejects. There is no polyfill or workaround from web content; the
 * only real fix on that platform is launching the page from a Home Screen
 * icon, which drops Safari's chrome entirely via the
 * `apple-mobile-web-app-capable` meta tag already in `index.html`.
 */

/**
 * Whether the standard Fullscreen API is present on this browser. `false`
 * on iPhone Safari; `true` on iPad Safari (13+), desktop browsers, and
 * Android Chrome.
 */
export function supportsFullscreenApi(): boolean {
  if (typeof document === 'undefined') return false
  const rootElement = document.documentElement as HTMLElement & {
    requestFullscreen?: () => Promise<void>
  }
  return typeof rootElement.requestFullscreen === 'function'
}

/**
 * Whether the page is already running without browser chrome — launched
 * from an iOS Home Screen icon, or installed as a PWA on another platform.
 * In both cases the fullscreen control has nothing left to do.
 */
export function isRunningStandalone(): boolean {
  if (typeof window === 'undefined') return false
  const iosStandaloneNavigator = window.navigator as Navigator & { standalone?: boolean }
  const launchedFromIosHomeScreen = iosStandaloneNavigator.standalone === true
  const launchedAsInstalledPwa =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(display-mode: standalone)').matches
  return launchedFromIosHomeScreen || launchedAsInstalledPwa
}
