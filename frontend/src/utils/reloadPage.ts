/** Full page reload; a module seam so tests can observe it. */
export function reloadPage(): void {
  window.location.reload()
}
