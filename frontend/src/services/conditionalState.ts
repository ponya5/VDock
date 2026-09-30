/**
 * Conditional-style state feed (DL-122).
 *
 * One reactive object aggregating every live source a button rule can
 * read: socket-fed state (system volume, now playing, agent states,
 * audio spectrum) plus the local clock. Subscriptions attach at import
 * time — `socketClient.on` queues listeners until connect — and live for
 * the app's lifetime; the payload this carries is small and shared by
 * every button, so per-button subscriptions would only multiply work.
 *
 * `timer` is intentionally NOT here: `timer.running` is per-button, so
 * callers compose it in (see `buttonRules.ts` / `DeckButton.vue`).
 */
import { reactive } from 'vue'
import socketClient from '@/api/socket'
import type { AgentStateEntry } from '@/services/agentState'

export interface ConditionalState {
  volume: { value: number | null; muted: boolean; seen: boolean }
  nowPlaying: {
    playing: boolean
    title: string
    artist: string
    source_app: string
    seen: boolean
  }
  agent: { states: Record<string, AgentStateEntry> }
  spectrum: { level: number; live: boolean; seen: boolean }
  time: { hour: number; minute: number }
}

export const conditionalState = reactive<ConditionalState>({
  volume: { value: null, muted: false, seen: false },
  nowPlaying: { playing: false, title: '', artist: '', source_app: '', seen: false },
  agent: { states: {} },
  spectrum: { level: 0, live: false, seen: false },
  time: { hour: new Date().getHours(), minute: new Date().getMinutes() },
})

socketClient.on('system_volume', (data: { value?: number; muted?: boolean }) => {
  if (typeof data?.value === 'number') conditionalState.volume.value = data.value
  if (typeof data?.muted === 'boolean') conditionalState.volume.muted = data.muted
  conditionalState.volume.seen = true
})

socketClient.on('now_playing', (data: any) => {
  if (!data) return
  conditionalState.nowPlaying.playing = data.playing === true
  conditionalState.nowPlaying.title = data.title ?? ''
  conditionalState.nowPlaying.artist = data.artist ?? ''
  conditionalState.nowPlaying.source_app = data.source_app ?? ''
  conditionalState.nowPlaying.seen = true
})

socketClient.on('agent_state', (data: { states?: Record<string, AgentStateEntry> }) => {
  conditionalState.agent.states = data?.states ?? {}
})

socketClient.on('audio_spectrum', (data: { level?: number; live?: boolean }) => {
  if (!data) return
  conditionalState.spectrum.level = typeof data.level === 'number' ? data.level : 0
  conditionalState.spectrum.live = data.live === true
  conditionalState.spectrum.seen = true
})

// Local clock for `time.hour`/`time.minute` rules — 15 s is well under a
// minute boundary and costs one Date allocation per tick.
setInterval(() => {
  const now = new Date()
  conditionalState.time.hour = now.getHours()
  conditionalState.time.minute = now.getMinutes()
}, 15_000)

export default conditionalState
