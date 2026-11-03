/** Stable per-browser id so the computer can list (and name) this device. */
export function deviceId(): string {
  try {
    let id = localStorage.getItem('vdock.deviceId')
    if (!id) {
      id = (crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`).replace(/[^A-Za-z0-9_-]/g, '')
      localStorage.setItem('vdock.deviceId', id)
    }
    return id
  } catch {
    return ''
  }
}
