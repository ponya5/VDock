/**
 * Headlines from RSS/Atom feeds, proxied by the backend.
 *
 * This used to call GNews directly, which needed an API key the user had to
 * sign up for -- without one the screensaver widget just showed "News
 * unavailable", which is what it was doing. Feeds are XML served without CORS
 * headers, so the browser cannot read them directly; the backend fetches,
 * parses and merges several sources at GET /api/news.
 */
import apiClient from '@/api/client'

export interface NewsHeadline {
  title: string
  source: string
  url: string
  published?: string
}

/**
 * Built-in sports feeds — used when the user has not configured their own
 * sports list. Same keyless RSS proxy path as the regular headlines.
 */
export const DEFAULT_SPORTS_FEEDS: string[] = [
  'https://www.espn.com/espn/rss/news',
  'https://feeds.bbci.co.uk/sport/rss.xml',
  'https://www.skysports.com/rss/12040',
]

/**
 * Split a user-entered feed list into URLs.
 *
 * Accepts one URL per line, and tolerates commas, because people paste both.
 * Shared by the settings form and the screensaver composable so they can never
 * disagree about what the user typed.
 */
export function parseFeedList(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.filter((f): f is string => typeof f === 'string' && !!f.trim())
      .map((f) => f.trim())
  }
  if (typeof raw !== 'string' || !raw.trim()) return []

  const NEWLINE = String.fromCharCode(10)
  return raw
    .split(NEWLINE)
    .flatMap((line) => line.split(','))
    .map((f) => f.trim())
    .filter(Boolean)
}

/** Fetch merged headlines. `feeds` overrides the backend defaults. */
export async function fetchHeadlines(
  feeds: string[] = [],
  refresh = false
): Promise<NewsHeadline[]> {
  const params: Record<string, string> = {}
  if (feeds.length) params.feeds = feeds.join(',')
  if (refresh) params.refresh = '1'

  const response = await apiClient.get('/news', params)
  const headlines = response?.data?.headlines
  if (!Array.isArray(headlines)) {
    throw new Error('News response did not contain headlines')
  }
  return headlines
}

/** The feed list used when the user has not configured their own. */
export async function fetchDefaultFeeds(): Promise<string[]> {
  const response = await apiClient.get('/news/defaults')
  return response?.data?.feeds ?? []
}

/**
 * Verify a feed list works, for the "Test" button in Settings.
 * Resolves with the number of headlines found.
 */
export async function testNewsConnection(feeds: string[] = []): Promise<number> {
  const headlines = await fetchHeadlines(feeds, true)
  if (!headlines.length) {
    throw new Error('No headlines returned from those feeds')
  }
  return headlines.length
}

/** Kept so an existing single-headline caller keeps working. */
export async function fetchTopHeadline(): Promise<NewsHeadline> {
  const [first] = await fetchHeadlines()
  if (!first) throw new Error('No headlines returned')
  return first
}
