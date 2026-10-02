import { ref } from 'vue'
import { confirmDialog } from '@/composables/useConfirm'
import { pollableButton } from '@/composables/useWidgetPolling'
import { useActionCatalogStore } from '@/stores/actionCatalog'
import { useButtonStateStore, type LiveMenuItem } from '@/stores/buttonState'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import type { ActionResult, Button } from '@/types'

/**
 * The press menu of a live button (DL-145).
 *
 * A `press: 'menu'` action (change review, and later git / dev servers /
 * Docker) paints a face from its polled status and lists what you can do
 * from there in `data.menu`. Tapping the button opens this sheet instead of
 * running anything; choosing a row re-dispatches the same action with
 * `config.op = item.id`.
 */

export interface LiveMenuState {
  button: Button
  items: LiveMenuItem[]
  /** Log tail / failure excerpt returned by the last chosen item. */
  panelText?: string
  /** Backend-supplied copy for an empty menu ("No changes this turn"). */
  message?: string
}

export const liveMenu = ref<LiveMenuState | null>(null)

function withOp(button: Button, op: string): Button {
  if (!button.action) return button
  return { ...button, action: { ...button.action, config: { ...button.action.config, op } } }
}

/** Re-run the action's status read and paint the result on the button face. */
async function refreshFace(button: Button): Promise<ActionResult | undefined> {
  const catalog = useActionCatalogStore()
  const spec = button.action ? catalog.byActionType[button.action.type] : undefined
  const result = await useDashboardStore().executeButtonAction(pollableButton(button, spec))
  if (result) useButtonStateStore().markFinished(button.id, result)
  return result
}

export async function openLiveMenu(button: Button): Promise<void> {
  const buttonState = useButtonStateStore()
  let message: string | undefined
  if (!buttonState.states[button.id]?.menu) {
    try {
      message = (await refreshFace(button))?.message
    } catch {
      message = 'Could not load this button right now.'
    }
  }
  const state = buttonState.states[button.id]
  liveMenu.value = { button, items: state?.menu ?? [], panelText: state?.panelText, message }
}

export function closeLiveMenu(): void {
  liveMenu.value = null
}

function report(result: ActionResult): void {
  const notifications = useNotificationsStore()
  if (result.success) notifications.success('Action Executed', result.message)
  else notifications.error('Action Failed', result.message, result.details)
}

export async function chooseLiveMenuItem(item: LiveMenuItem): Promise<void> {
  const current = liveMenu.value
  if (!current) return
  if (item.confirm && !(await confirmDialog({ message: item.confirm }))) return

  const { button } = current
  const dashboard = useDashboardStore()
  const buttonState = useButtonStateStore()
  buttonState.markRunning(button.id)

  let result: ActionResult | undefined
  try {
    result = await dashboard.executeButtonAction(withOp(button, item.id))
  } catch (error) {
    result = { success: false, message: error instanceof Error ? error.message : 'Action failed' }
  }
  if (!result) return
  report(result)

  const url = result.success ? result.data?.url : undefined
  if (url) void dashboard.executeAction({ type: 'url', config: { url } }, button.id)

  // An op result only repaints the face when it carries a badge of its own;
  // otherwise ask for fresh status so the face and menu reflect what changed.
  if (result.data?.badge !== undefined) buttonState.markFinished(button.id, result)
  else await refreshFace(button).catch(() => undefined)

  const panelText = result.data?.panel_text
  if (typeof panelText === 'string' && panelText) {
    liveMenu.value = {
      button,
      items: buttonState.states[button.id]?.menu ?? current.items,
      panelText,
    }
  } else {
    closeLiveMenu()
  }
}
