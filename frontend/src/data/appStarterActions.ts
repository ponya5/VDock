// Deck presets a new app scene starts with when the app has no keymap profile
// (backend/misc shortcuts cover IDEs, Chrome, ...). Keys: normalized process
// identity — "Spotify.exe" (Windows), "spotify" (macOS scan), "Spotify.app"
// (macOS foreground monitor) all resolve to 'spotify'.

import { exeKey } from '@/utils/appExe'

const MEDIA_PLAYER = ['play-stop', 'prev-track', 'next-track', 'volume-down', 'volume-up', 'mute', 'now-playing']

const STARTERS: Record<string, string[]> = {
  spotify: MEDIA_PLAYER,
  music: MEDIA_PLAYER,
  itunes: MEDIA_PLAYER,
  vlc: MEDIA_PLAYER,
}

export function starterPresetIds(exe: string): string[] {
  return STARTERS[exeKey(exe)] ?? []
}
