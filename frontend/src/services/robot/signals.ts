/**
 * DL-153 — adapts the deck's existing live services into one RobotSignals
 * snapshot for the mood engine. No new polling: agent state, now playing and
 * notifications are socket-fed; system stats and weather use their own
 * composables, started only while the robot saver is up.
 */
import { computed, onScopeDispose, ref, type ComputedRef } from 'vue'
import { agentStates } from '@/services/agentState'
import { useNowPlaying } from '@/services/nowPlaying'
import { useAudioSpectrum } from '@/services/audioSpectrum'
import { useSystemStats } from '@/composables/useSystemStats'
import { useWeather } from '@/composables/useWeather'
import { useNotificationsStore } from '@/stores/notifications'
import { useUpdateStore } from '@/stores/update'
import type { RobotMood } from '@/stores/settings'
import type { RobotSignals, WeatherKind } from './moodEngine'
import type { Mood } from './reactions'

const MOODS: Mood[] = ['funny', 'grumpy', 'sarcastic', 'sweet']
const RANDOM_KEY = 'vdock.robot.randomMood'

export function aggregateAgent(entries: Array<{ state: string; prompted?: boolean }>): RobotSignals['agent'] {
  if (entries.some(e => e.state === 'permission')) return 'permission'
  if (entries.some(e => e.state === 'working')) return 'working'
  if (entries.some(e => e.state === 'ready' && e.prompted === true)) return 'ready'
  return 'idle'
}

export function mapWeather(w: { code: number; temperature: number } | null): WeatherKind | null {
  if (!w) return null
  if (w.temperature <= 5) return 'cold'
  const c = w.code
  if ((c >= 71 && c <= 77) || c === 85 || c === 86) return 'snow'
  if ((c >= 51 && c <= 67) || (c >= 80 && c <= 82) || (c >= 95 && c <= 99)) return 'rain'
  if (c === 0 || c === 1) return 'sunny'
  return 'other'
}

export function resolveMood(
  setting: RobotMood, today: string,
  storage: Pick<Storage, 'getItem' | 'setItem'> | null = typeof localStorage !== 'undefined' ? localStorage : null,
  rand: () => number = Math.random,
): Mood {
  if (setting !== 'random') return setting
  try {
    const saved = JSON.parse(storage?.getItem(RANDOM_KEY) ?? 'null') as { day?: string; mood?: Mood } | null
    if (saved?.day === today && saved.mood && MOODS.includes(saved.mood)) return saved.mood
  } catch { /* storage unavailable or corrupt — pick fresh */ }
  const mood = MOODS[Math.floor(rand() * MOODS.length) % MOODS.length]
  try { storage?.setItem(RANDOM_KEY, JSON.stringify({ day: today, mood })) } catch { /* ignore */ }
  return mood
}

export function localDay(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function useRobotSignals(): { signals: ComputedRef<RobotSignals>; audioLevel: ComputedRef<number>; start(): void; stop(): void } {
  const nowPlaying = useNowPlaying()
  const spectrum = useAudioSpectrum() // attaches its socket listener itself
  const sys = useSystemStats()
  const weather = useWeather()
  const notifications = useNotificationsStore()
  const update = useUpdateStore()
  const clock = ref(new Date())
  let timer: ReturnType<typeof setInterval> | null = null

  const signals = computed<RobotSignals>(() => ({
    agent: aggregateAgent(Object.values(agentStates)),
    musicPlaying: nowPlaying.playing.value,
    cpuPercent: sys.stats.value?.cpuPercent ?? null,
    batteryPercent: sys.stats.value?.batteryPercent ?? null,
    batteryCharging: sys.stats.value?.batteryCharging ?? null,
    notificationCount: notifications.notifications.length,
    updateAvailable: Boolean(update.visible),
    weather: mapWeather(weather.weather.value),
    isDay: weather.weather.value?.isDay ?? true,
    hour: clock.value.getHours(),
    day: localDay(clock.value),
  }))

  const audioLevel = computed(() =>
    !nowPlaying.playing.value ? 0 : spectrum.live ? Math.min(1, spectrum.level / 100) : 0.5)

  function start(): void {
    sys.start()
    weather.start()
    if (!timer) timer = setInterval(() => { clock.value = new Date() }, 30_000)
  }
  function stop(): void {
    sys.stop()
    weather.stop()
    if (timer) { clearInterval(timer); timer = null }
  }
  onScopeDispose(stop)
  return { signals, audioLevel, start, stop }
}
