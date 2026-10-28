import type { Router } from 'vue-router'
import apiClient from '@/api/client'
import { authState, exchangePairToken } from '@/services/auth'

/** Tokens live 3 minutes on the server; refresh the QR 30 s early. */
export const PAIR_REFRESH_MS = 150 * 1000

/** A pairing token from the signed-in desktop, or null when none is needed/possible. */
export async function requestPairToken(): Promise<string | null> {
  try {
    const res = await apiClient.post('/auth/pair-token')
    return typeof res.data?.token === 'string' ? res.data.token : null
  } catch {
    return null
  }
}

/** The address the QR encodes: the deck URL plus the one-time token. */
export function buildPairUrl(lanUrl: string, token: string): string {
  return `${lanUrl}/?pair=${encodeURIComponent(token)}`
}

/**
 * First thing on a freshly scanned phone: trade `?pair=<token>` for a login,
 * then drop it from the address bar so it never lingers in history or a
 * shared link. A used/expired token just leaves the normal lock screen.
 */
export async function consumePairQuery(router: Router): Promise<void> {
  await router.isReady()
  const route = router.currentRoute.value
  const token = route.query.pair
  if (typeof token !== 'string' || !token) return

  // A used/expired code used to leave a bare lock screen; say why (DL-011).
  authState.pairFailed = !(await exchangePairToken(token))
  const { pair: _used, ...rest } = route.query
  await router.replace({ path: route.path, query: rest, hash: route.hash })
}

export interface PairedDevice {
  id: string
  label: string
  paired_at: number
  last_seen: number
  ip: string
  named?: boolean
  current?: boolean
}

/** Devices signed in to this deck, most recently seen first; null when unavailable. */
export async function fetchDevices(): Promise<PairedDevice[] | null> {
  try {
    const res = await apiClient.get('/auth/devices')
    return Array.isArray(res.data?.devices) ? res.data.devices : null
  } catch {
    return null
  }
}

export async function renameDevice(id: string, label: string): Promise<boolean> {
  try {
    await apiClient.patch(`/auth/devices/${encodeURIComponent(id)}`, { label })
    return true
  } catch {
    return false
  }
}

export async function revokeDevice(id: string): Promise<boolean> {
  try {
    await apiClient.delete(`/auth/devices/${encodeURIComponent(id)}`)
    return true
  } catch {
    return false
  }
}

export async function revokeAllDevices(): Promise<boolean> {
  try {
    await apiClient.delete('/auth/devices')
    return true
  } catch {
    return false
  }
}

/** "just now", "5 min ago", "3 h ago", "2 d ago" for a unix-seconds timestamp. */
export function timeAgo(unixSeconds: number, nowMs: number = Date.now()): string {
  const seconds = Math.max(0, Math.round(nowMs / 1000 - unixSeconds))
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`
  return `${Math.floor(seconds / 86400)} d ago`
}
