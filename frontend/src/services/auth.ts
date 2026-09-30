import { reactive } from 'vue'
import axios from 'axios'

/**
 * Authentication session state (DL-126).
 *
 * The server is single-password: enabling `require_auth` makes every REST
 * route and the Socket.IO handshake demand `Authorization: Bearer <jwt>`.
 * This module owns the token (persisted in localStorage so a panel reload
 * stays unlocked) and the one question the UI needs:
 *
 *   state.required && !state.unlocked  → show the lock screen
 *
 * It deliberately does NOT import apiClient — the login probe runs before
 * the client's interceptors are meaningful and must not pop error toasts.
 * Socket.IO is notified via onTokenChanged listeners instead of an import,
 * keeping this module dependency-free.
 */

const TOKEN_KEY = 'vdock.authToken'

interface AuthState {
  /** Server demands authentication (probe saw 401 / config.require_auth). */
  required: boolean
  /** We hold a token the server accepts. */
  unlocked: boolean
  /** First probe completed — App.vue waits on this before deciding anything. */
  checked: boolean
}

export const authState = reactive<AuthState>({
  required: false,
  unlocked: false,
  checked: false,
})

let token: string | null = null
try {
  token = localStorage.getItem(TOKEN_KEY)
} catch {
  // Storage can be unavailable in odd kiosk contexts — session still works,
  // the token just won't survive a reload.
}

const tokenListeners = new Set<() => void>()

/** Subscribe to token set/clear — socket.ts reconnects on this. */
export function onAuthTokenChanged(listener: () => void) {
  tokenListeners.add(listener)
}

export function getAuthToken(): string | null {
  return token
}

export function setAuthToken(value: string) {
  token = value
  try {
    localStorage.setItem(TOKEN_KEY, value)
  } catch { /* same caveat as the load path */ }
  for (const fn of tokenListeners) fn()
}

export function clearAuthToken() {
  const had = token !== null
  token = null
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch { /* ignore */ }
  if (had) for (const fn of tokenListeners) fn()
}

/**
 * Any 401 outside the login attempt means the token we hold is stale —
 * drop it and surface the lock screen.
 */
export function markUnauthorized() {
  clearAuthToken()
  authState.required = true
  authState.unlocked = false
}

/**
 * One quiet probe at boot: is auth required, and does our stored token
 * still work? Uses raw axios on purpose — going through apiClient would
 * show "Unauthorized" toasts for the exact state we are about to fix.
 */
export async function probeAuth() {
  try {
    const res = await axios.get('/api/config', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      timeout: 8000,
    })
    const required = !!res.data?.config?.require_auth
    authState.required = required
    // 200 while auth is on means the stored token was accepted.
    authState.unlocked = !required || !!token
  } catch (err: any) {
    if (err?.response?.status === 401) {
      // Stored token rejected (expired or a stale SECRET_KEY) — drop it.
      markUnauthorized()
    }
    // Network/other errors: leave state alone — existing offline handling
    // owns that failure mode.
  } finally {
    authState.checked = true
  }
}

export interface LoginResult {
  ok: boolean
  error?: string
}

export async function login(password: string): Promise<LoginResult> {
  try {
    const res = await axios.post('/api/auth/login', { password }, { timeout: 10000 })
    const issued = res.data?.token
    if (!issued) return { ok: false, error: 'Server returned no token' }
    setAuthToken(issued)
    authState.required = true
    authState.unlocked = true
    return { ok: true }
  } catch (err: any) {
    const status = err?.response?.status
    const serverMsg = err?.response?.data?.error
    if (status === 401) return { ok: false, error: 'Wrong password' }
    if (status === 429) return { ok: false, error: serverMsg || 'Too many attempts — try again in a minute' }
    return { ok: false, error: serverMsg || 'Could not reach the server' }
  }
}
