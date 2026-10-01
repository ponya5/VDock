import { computed, reactive, ref } from 'vue'
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

/** DL-136: session recent-tracks list — SMTC exposes no queue, so the
 *  Winamp-mode playlist renders what actually played this session.
 *  Newest first, deduped by title+artist, capped at 30. */
export interface RecentTrack {
  title: string
  artist: string
  duration_s?: number
  site?: string
  source_app: string
  ts: number
}
const recent = ref<RecentTrack[]>([])
const RECENT_CAP = 30

function applyTrack(payload: NowPlayingTrack | null | undefined): void {
  state.track = payload && payload.title ? payload : null
  const t = state.track
  if (t) {
    const key = `${t.title}|${t.artist}`
    const existing = recent.value.findIndex(
      r => `${r.title}|${r.artist}` === key)
    if (existing >= 0) recent.value.splice(existing, 1)
    recent.value.unshift({
      title: t.title,
      artist: t.artist,
      duration_s: t.duration_s,
      site: t.site,
      source_app: t.source_app,
      ts: t.ts,
    })
    if (recent.value.length > RECENT_CAP) recent.value.length = RECENT_CAP
  }
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
  const artUrl = computed(() => {
    const t = state.track
    return t?.has_art ? `/api/now-playing/art?ts=${t.ts}` : null
  })
  return { track, playing, available, artUrl, recent }
}
