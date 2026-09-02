/** Top headline via GNews.io — requires a user-supplied free API key. */

export interface NewsHeadline {
  title: string
  source: string
  url: string
}

export async function fetchTopHeadline(apiKey: string): Promise<NewsHeadline> {
  const url = `https://gnews.io/api/v4/top-headlines?lang=en&max=1&apikey=${encodeURIComponent(apiKey)}`
  const response = await fetch(url)
  if (!response.ok) throw new Error(`News request failed (${response.status})`)
  const data = await response.json()
  const article = data.articles?.[0]
  if (!article) throw new Error('No headlines returned')
  return { title: article.title, source: article.source?.name ?? 'News', url: article.url }
}

export async function testNewsConnection(apiKey: string): Promise<void> {
  await fetchTopHeadline(apiKey)
}
