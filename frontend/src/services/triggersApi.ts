import apiClient from '@/api/client'

/**
 * Triggers API (DL-120) — thin wrapper over /api/triggers.
 *
 * A trigger is {id, label, enabled, event, action}; see
 * design-log/collab/contracts/rest-api.md for the route contract and
 * backend/services/triggers.py for the event/action vocabularies.
 */

export type TriggerEventType = 'time' | 'app_foreground' | 'agent_state' | 'webhook'
export type TriggerActionType = 'execute_action' | 'switch_scene' | 'show_notification'

export interface TriggerEvent {
  type: TriggerEventType
  /** 'HH:MM' — time events */
  at?: string
  /** 0-6, 0 = Monday — time events */
  days?: number[]
  /** e.g. 'spotify.exe' — app_foreground events */
  exe?: string
  /** 'claude' | 'cursor' | 'devin' | 'antigravity' | 'generic' — agent_state */
  source?: string
  /** 'ready' | 'working' | 'permission' — agent_state */
  state?: string
  /** webhook events — POST /api/triggers/fire/<key> */
  key?: string
}

export interface TriggerAction {
  type: TriggerActionType
  /** execute_action: nested {type, config} run through the action executor */
  action?: { type: string; config?: Record<string, any> }
  /** switch_scene: target scene name */
  scene?: string
  /** show_notification */
  title?: string
  message?: string
}

export interface Trigger {
  id: string
  label: string
  enabled: boolean
  event: TriggerEvent
  action: TriggerAction
}

export type TriggerDraft = Omit<Trigger, 'id'>

export interface TriggerTestResult {
  ok: boolean
  detail: string
}

export interface TriggersState {
  /** Master switch — false pauses the whole engine, not just one row. */
  enabled: boolean
  triggers: Trigger[]
}

export async function listTriggers(): Promise<Trigger[]> {
  const response = await apiClient.get('/triggers')
  return response.data?.triggers ?? []
}

export async function fetchTriggersState(): Promise<TriggersState> {
  const response = await apiClient.get('/triggers')
  return {
    enabled: response.data?.enabled !== false,
    triggers: response.data?.triggers ?? [],
  }
}

export async function setTriggersEnabled(enabled: boolean): Promise<boolean> {
  const response = await apiClient.put('/triggers/enabled', { enabled })
  return response.data?.enabled !== false
}

export async function createTrigger(draft: TriggerDraft): Promise<Trigger> {
  const response = await apiClient.post('/triggers', draft)
  return response.data.trigger
}

export async function updateTrigger(id: string, patch: Partial<TriggerDraft>): Promise<Trigger> {
  const response = await apiClient.put(`/triggers/${id}`, patch)
  return response.data.trigger
}

export async function removeTrigger(id: string): Promise<void> {
  await apiClient.delete(`/triggers/${id}`)
}

export async function testTrigger(id: string): Promise<TriggerTestResult> {
  const response = await apiClient.post(`/triggers/${id}/test`)
  return { ok: !!response.data?.ok, detail: String(response.data?.detail ?? '') }
}
