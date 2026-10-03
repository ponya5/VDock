import { computed, reactive } from 'vue'
import socketClient from '@/api/socket'
import apiClient from '@/api/client'

/**
 * Now Playing (DL-116): what the OS media flyout shows — track, artist,
 * source app, play state — pushed by the backend SMTC monitor as
 * `now_playing` on change only. GET /api/now-playing re-syncs a freshly
 * loaded or reconnected client; album art stays out of the payload and is
 * fetched from GET /api/now-playing/art (cache-busted by the track's ts).
 */

export interface NowPlayingTrack {
  playing: boolean
  title: string
  artist: string
  album: string
  source_app: string
  /** DL-135 session: detected content site — 'youtube', 'spotify',
      'netflix', 'twitch', … — '' when it can't be attributed (browsers
      only say "chrome.exe"; the backend reads window titles). */
  site?: string
  /** Present only while the app reports a position. */
  position_s?: number
  /** 0/undefined means unknown — the widget hides its progress bar then. */
  duration_s?: number
  has_art: boolean
  ts: number
}

export type NowPlayingIcon = readonly [string, string]

// Sites that have a recognizable brand glyph in free-brands (Netflix has
// none — it stays on the generic/app fallback).
const SITE_ICONS: Record<string, NowPlayingIcon> = {
  youtube: ['fab', 'youtube'],
  spotify: ['fab', 'spotify'],
  twitch: ['fab', 'twitch'],
}

const SITE_LABELS: Record<string, string> = {
  youtube: 'YouTube',
  spotify: 'Spotify',
  netflix: 'Netflix',
  twitch: 'Twitch',
}

// When the site couldn't be detected, the source *app* still maps to a
// brand icon for the usual players.
const APP_ICONS: [hint: string, icon: NowPlayingIcon][] = [
  ['spotify', ['fab', 'spotify']],
  ['youtube', ['fab', 'youtube']],
  ['chrome', ['fab', 'chrome']],
  ['msedge', ['fab', 'edge']],
  ['edge', ['fab', 'edge']],
  ['firefox', ['fab', 'firefox-browser']],
  ['brave', ['fab', 'brave']],
  ['opera', ['fab', 'opera']],
]

/** Brand icon for the track's origin — site first, then the app. Null
 *  means "no brand known" → callers fall back to the music note. */
export function nowPlayingIcon(
  track: NowPlayingTrack | null | undefined,
): NowPlayingIcon | null {
  if (!track) return null
  const site = (track.site || '').toLowerCase()
  if (site && SITE_ICONS[site]) return SITE_ICONS[site]
  const app = (track.source_app || '').toLowerCase()
  for (const [hint, icon] of APP_ICONS) {
    if (app.includes(hint)) return icon
  }
  return null
}

/** Human label for the kicker — "YouTube" beats "chrome.exe". */
export function nowPlayingSourceLabel(
  track: NowPlayingTrack | null | undefined,
): string {
  if (!track) return ''
  const site = (track.site || '').toLowerCase()
  if (site && SITE_LABELS[site]) return SITE_LABELS[site]
  const raw = (track.source_app || '').trim()
  if (!raw) return ''
  const cleaned = raw.replace(/\.exe$/i, '').split(/[!_.]/)[0] || raw
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

interface NowPlayingState {
  /** null until the first socket event or REST sync — the widget's
      "still loading" signal, distinct from a definitive unsupported. */
  available: boolean | null
  /** Normalized: the empty "nothing plays" payload becomes null. */
  track: NowPlayingTrack | null
}

const state = reactive<NowPlayingState>({ available: null, track: null })
let initialized = false

// An <img src> can't send the Bearer header, so with the deck locked the art
// endpoint 401s and the image breaks. Fetch it through apiClient and expose
// a blob: URL instead.
const art = reactive<{ src: string | null, key: string }>({ src: null, key: '' })

function clearArt(): void {
  if (art.src) URL.revokeObjectURL(art.src)
  art.src = null
  art.key = ''
}

async function loadArt(track: NowPlayingTrack): Promise<void> {
  const key = `${track.ts}`
  if (art.key === key) return
  art.key = key
  try {
    const response = await apiClient.get(
      '/now-playing/art',
      { ts: track.ts },
      { responseType: 'blob' },
    )
    if (art.key !== key) return // a newer track superseded this fetch
    if (art.src) URL.revokeObjectURL(art.src)
    art.src = URL.createObjectURL(response.data as Blob)
  } catch (error) {
    if (art.key !== key) return
    console.warn('Could not load now-playing art:', error)
    clearArt()
  }
}

function applyTrack(payload: NowPlayingTrack | null | undefined): void {
  state.track = payload && payload.title ? payload : null
  if (state.track?.has_art) void loadArt(state.track)
  else clearArt()
}

async function syncFromBackend(): Promise<void> {
  try {
    const response = await apiClient.get('/now-playing')
    state.available = Boolean(response.data?.available)
    applyTrack(response.data?.track)
  } catch (error) {
    // Keep whatever we had — a stale reading beats an empty widget.
    console.warn('Could not load now-playing state:', error)
  }
}

export function initNowPlaying(): void {
  if (initialized) return
  initialized = true
  socketClient.on('now_playing', (payload: NowPlayingTrack) => {
    // The monitor only emits where SMTC works — an event implies available.
    state.available = true
    applyTrack(payload)
  })
  socketClient.on('connect', () => { void syncFromBackend() })
  void syncFromBackend()
}

export function useNowPlaying() {
  initNowPlaying()
  const track = computed(() => state.track)
  const playing = computed(() => Boolean(state.track?.playing))
  const available = computed(() => state.available)
  const artUrl = computed(() => (state.track?.has_art ? art.src : null))
  return { track, playing, available, artUrl }
}
