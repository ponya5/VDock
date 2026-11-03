import apiClient from '@/api/client'

/** DL-160: one line of the "Why can't my phone connect?" report. */
export interface ConnectionCheckItem {
  id: string
  status: 'ok' | 'warn' | 'fail' | 'info'
  title: string
  detail: string
  fix?: { action: 'clear_deck_host' | 'set_deck_host', label: string, value?: string }
}

/** null when the server could not be asked. */
export async function fetchConnectionCheck(): Promise<ConnectionCheckItem[] | null> {
  try {
    const res = await apiClient.get('/config/connection-check')
    return Array.isArray(res.data?.checks) ? res.data.checks : null
  } catch {
    return null
  }
}

/** The two fixes only ever change the QR address override. */
export function fixPayload(fix: NonNullable<ConnectionCheckItem['fix']>): { deck_host: string } {
  return { deck_host: fix.action === 'set_deck_host' ? (fix.value ?? '') : '' }
}
