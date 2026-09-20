import { ref } from 'vue'

/**
 * Promise-based confirm dialog, replacing native window.confirm() — which on
 * Electron renders an unthemed OS prompt (the "vdock-electron — OK/Cancel"
 * box) that clashes with the app's dark glass theme and can't be styled.
 *
 * Usage:
 *   import { confirmDialog } from '@/composables/useConfirm'
 *   if (await confirmDialog({ message: 'Delete this button?' })) { ... }
 *
 * <ConfirmDialog> is mounted once in App.vue and renders `pending`.
 */
export interface ConfirmOptions {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  /** Red confirm button for destructive actions (default true). */
  danger?: boolean
  icon?: string
}

export interface ConfirmRequest {
  title: string
  message: string
  confirmLabel: string
  cancelLabel: string
  danger: boolean
  icon: string
  resolve: (ok: boolean) => void
}

const pending = ref<ConfirmRequest | null>(null)

export function confirmDialog(options: ConfirmOptions | string): Promise<boolean> {
  const o = typeof options === 'string' ? { message: options } : options
  return new Promise(resolve => {
    // A second confirm while one is open answers the first "cancel" — same
    // outcome as a native dialog being superseded.
    pending.value?.resolve(false)
    pending.value = {
      title: o.title ?? 'Are you sure?',
      message: o.message,
      confirmLabel: o.confirmLabel ?? 'Delete',
      cancelLabel: o.cancelLabel ?? 'Cancel',
      danger: o.danger ?? true,
      icon: o.icon ?? 'trash',
      resolve,
    }
  })
}

export function useConfirmDialog() {
  return pending
}

export function settleConfirmDialog(ok: boolean) {
  pending.value?.resolve(ok)
  pending.value = null
}
