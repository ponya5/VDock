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
  /** Present only while the app reports a position. */
  position_s?: number
  /** 0/undefined means unknown — the widget hides its progress bar then. */
  duration_s?: number
  has_art: boolean
  ts: number
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

function applyTrack(payload: NowPlayingTrack | null | undefined): void {
  state.track = payload && payload.title ? payload : null
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
  return { track, playing, available, artUrl }
}
