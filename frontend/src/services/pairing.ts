import type { Router } from 'vue-router'
import apiClient from '@/api/client'
import { exchangePairToken } from '@/services/auth'

/** Tokens live 10 minutes on the server; refresh the QR a minute early. */
export const PAIR_REFRESH_MS = 9 * 60 * 1000

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

  await exchangePairToken(token)
  const { pair: _used, ...rest } = route.query
  await router.replace({ path: route.path, query: rest, hash: route.hash })
}
