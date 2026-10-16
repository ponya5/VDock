import apiClient from '@/api/client'

export interface HealthInfo {
  uptimeS: number
  restartRequired: boolean
}

export async function getHealth(): Promise<HealthInfo> {
  const { data } = await apiClient.get('/health')
  return {
    uptimeS: Number(data?.uptime_s ?? 0),
    restartRequired: data?.restart_required === true,
  }
}

/** Restart the backend so startup-only switches (Allow LAN, HTTPS) apply (DL-007). */
export async function restartBackend(): Promise<void> {
  await apiClient.post('/system/restart')
}
