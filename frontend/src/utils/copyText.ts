/**
 * Copies text to the clipboard. `navigator.clipboard` needs a secure context,
 * and a LAN deck is served over http:// - so on a phone the API is undefined
 * entirely and the legacy textarea + execCommand path is the only one.
 */
export async function copyText(text: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch { /* fall through to the legacy path */ }
  }
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.cssText = 'position:fixed;opacity:0;pointer-events:none'
  document.body.appendChild(ta)
  ta.select()
  ta.setSelectionRange(0, ta.value.length) // iOS needs an explicit range
  try {
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    ta.remove()
  }
}
