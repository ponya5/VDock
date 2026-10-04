import apiClient from '@/api/client'

export type UpdateState = 'idle' | 'downloading' | 'installing' | 'restarting' | 'error'

export interface UpdateStatus {
  current: string
  latest: string | null
  available: boolean
  notes: string | null
  releaseUrl: string | null
  downloadUrl: string | null
  installKind: string
  canAutoInstall: boolean
  checkedAt: number | string | null
  error: string | null
  state: UpdateState
  stateMessage?: string | null
}

export async function getUpdateStatus(force = false): Promise<UpdateStatus> {
  const { data } = await apiClient.get('/update/status', force ? { force: 1 } : undefined)
  return data as UpdateStatus
}

export async function installUpdate(): Promise<{ state: UpdateState }> {
  const { data } = await apiClient.post('/update/install')
  return data
}

export async function getHealthVersion(): Promise<string> {
  const { data } = await apiClient.get('/health')
  return String(data?.version ?? '')
}
