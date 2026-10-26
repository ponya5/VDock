/**
 * Executable-identity normalization.
 *
 * Two "exe" conventions exist and they never compare equal raw:
 * the running-apps scan stores the process name ('spotify', 'Spotify.exe'),
 * while the macOS foreground monitor reports the bundle name
 * ('Spotify.app', 'Google Chrome.app'). Every app↔exe comparison must go
 * through exeKey(), not raw string equality, or macOS silently never matches.
 */

/** Comparison key: 'Spotify.app' / 'spotify' / 'Spotify.exe' → 'spotify'. */
export function exeKey(value?: string | null): string {
  return (value ?? '')
    .toLowerCase()
    .replace(/\.(app|exe)$/, '')
    .replace(/[^a-z0-9]/g, '')
}

/** Outer `.app` bundle name inside a path — helpers nested in a bundle count
 * as their parent app ('…/Spotify.app/Contents/MacOS/x' → 'Spotify.app'). */
function bundleIdentity(path?: string | null): string | null {
  const match = String(path ?? '').match(/([^/\\]+\.app)(?=\/|$)/i)
  return match ? match[1] : null
}

/** Every identity a running app can be known by, as exeKeys. */
export function appExeKeys(app: {
  exe?: string | null
  name?: string | null
  path?: string | null
}): Set<string> {
  const keys = new Set<string>()
  for (const value of [app.exe, app.name, bundleIdentity(app.path)]) {
    const key = exeKey(value)
    if (key) keys.add(key)
  }
  return keys
}

/** True when the running app matches any of the given exe/name identities. */
export function appMatchesExe(
  app: { exe?: string | null; name?: string | null; path?: string | null },
  ...exes: Array<string | undefined | null>
): boolean {
  const keys = appExeKeys(app)
  return exes.some(exe => {
    const key = exeKey(exe)
    return key !== '' && keys.has(key)
  })
}
