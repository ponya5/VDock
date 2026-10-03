/**
 * Where the Socket.IO client should dial (DL-146 follow-up).
 *
 * - `VITE_WS_URL` always wins.
 * - Built bundle: the Flask backend serves the page, so its own origin is the
 *   socket. The old "hostname + port 5000" guess dialled the wrong port (and
 *   showed "Can't reach VDock") whenever the backend ran on another `PORT`.
 * - Dev server: the page comes from Vite, the socket stays on the backend port.
 */
export interface SocketUrlInput {
  wsUrl?: string
  backendPort?: string
  isDev: boolean
  location: { protocol: string; hostname: string; origin: string }
}

export function resolveSocketUrl({ wsUrl, backendPort, isDev, location }: SocketUrlInput): string {
  if (wsUrl) return wsUrl
  if (!isDev) return location.origin
  return `${location.protocol}//${location.hostname}:${backendPort || '5000'}`
}
