// Reactive mirror of the `appIntegrations` localStorage blob.
//
// Settings owns the list (which running app maps to which scene), but the
// dashboard render path also reads it — to give scenes assigned to an app a
// default background. A shared module ref keeps every reader consistent, and
// the `storage` listener picks up edits made in a separate settings window.

import { ref, type Ref } from 'vue'
import type { AppIntegration } from '@/types'

const STORAGE_KEY = 'appIntegrations'

function load(): AppIntegration[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

const appIntegrations: Ref<AppIntegration[]> = ref(load())

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY || event.key === null) {
      appIntegrations.value = load()
    }
  })
}

/** The live app-integration list. Mutate it, then call `setAppIntegrations`. */
export function useAppIntegrations(): Ref<AppIntegration[]> {
  return appIntegrations
}

/** Persist and publish a new integration list. */
export function setAppIntegrations(list: AppIntegration[]): void {
  appIntegrations.value = list
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

/** Re-read from localStorage (e.g. after an out-of-band write). */
export function reloadAppIntegrations(): void {
  appIntegrations.value = load()
}
