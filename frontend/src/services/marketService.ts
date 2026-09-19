/** Market quotes for the screensaver chip.
 *
 * Two paths:
 *  - crypto-only callers may still hit CoinGecko directly (CORS-friendly);
 *  - anything the user configured goes through GET /api/market, which proxies
 *    Yahoo for stock tickers and CoinGecko for known crypto tickers -- stock
 *    endpoints answer without CORS headers, so the backend has to fetch them.
 */
import apiClient from '@/api/client'

export interface CoinPrice {
  id: string
  symbol: string
  price: number
}

export interface Quote {
  symbol: string
  price: number
  kind: 'stock' | 'crypto'
  currency: string
}

const DEFAULT_COINS = ['bitcoin', 'ethereum']

export async function fetchCryptoPrices(coinIds: string[] = DEFAULT_COINS): Promise<CoinPrice[]> {
  const ids = coinIds.join(',')
  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(ids)}&vs_currencies=usd`
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Market request failed (${response.status})`)
  const data = await response.json()
  return coinIds
    .filter(id => data[id]?.usd !== undefined)
    .map(id => ({ id, symbol: id.slice(0, 3).toUpperCase(), price: data[id].usd }))
}

/** Stocks + crypto quotes for user-configured tickers via the backend. */
export async function fetchQuotes(symbols: string[]): Promise<Quote[]> {
  if (!symbols.length) return []
  const response = await apiClient.get('/market', {
    symbols: symbols.join(','),
  })
  const quotes = response?.data?.quotes
  if (!Array.isArray(quotes)) throw new Error('Market response had no quotes')
  return quotes
}

/** Split "AAPL, MSFT , btc" into ['AAPL', 'MSFT', 'BTC']. */
export function parseTickers(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.filter((t): t is string => typeof t === 'string' && !!t.trim())
      .map(t => t.trim().toUpperCase())
  }
  if (typeof raw !== 'string' || !raw.trim()) return []
  return raw.split(',')
    .map(t => t.trim().toUpperCase())
    .filter(Boolean)
}

export async function testMarketConnection(symbols: string[] = []): Promise<void> {
  if (symbols.length) {
    const quotes = await fetchQuotes(symbols)
    if (!quotes.length) throw new Error('No quotes returned for those tickers')
    return
  }
  const prices = await fetchCryptoPrices()
  if (prices.length === 0) throw new Error('No prices returned')
}
