/** Crypto prices via CoinGecko's free, keyless, CORS-friendly public endpoint. */

export interface CoinPrice {
  id: string
  symbol: string
  price: number
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

export async function testMarketConnection(): Promise<void> {
  const prices = await fetchCryptoPrices()
  if (prices.length === 0) throw new Error('No prices returned')
}
