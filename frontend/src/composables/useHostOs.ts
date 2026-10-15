// The OS the backend runs on (it is the machine that presses the keys), so
// shortcuts created here match what the host expects (DL-006). Detected by the
// backend on every launch, never chosen or stored by the user.

import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export type HostOs = 'macos' | 'windows' | 'linux' | 'unknown'

const hostOs = ref<HostOs>('unknown')
let loading: Promise<void> | null = null

/** Fetch once; later callers share the same request. Failure leaves 'unknown'. */
export function loadHostOs(): Promise<void> {
  if (!loading) {
    loading = apiClient.get('/system/host')
      .then((response) => {
        const os = response.data?.os
        hostOs.value = os === 'macos' || os === 'windows' || os === 'linux' ? os : 'unknown'
      })
      .catch(() => { loading = null })
  }
  return loading
}

/**
 * A Windows-form chord as `os` expects it. Mirrors backend `localize_keys`:
 * on macOS Ctrl becomes Cmd, except backtick chords and Alt chords.
 */
export function nativeKeys(keys: string[], os: HostOs): string[] {
  if (os !== 'macos' || keys.includes('`') || keys.includes('alt')) return keys
  return keys.map(key => (key === 'ctrl' ? 'cmd' : key))
}

export function useHostOs() {
  void loadHostOs()
  return {
    hostOs,
    isMac: computed(() => hostOs.value === 'macos'),
    label: computed(() => ({ macos: 'macOS', windows: 'Windows', linux: 'Linux', unknown: '' }[hostOs.value]))
  }
}
