"""Stock and crypto quotes for the screensaver market chip.

Why server-side: the browser already hits CoinGecko directly (it is
CORS-friendly), but stock quote endpoints are not -- Yahoo's chart API answers
plain GETs only when the request carries a browser-ish User-Agent and no
Origin header, which a fetch() cannot do. Proxying here mirrors the news RSS
route and keeps one response shape for both kinds of symbol.

No API key is needed. The earlier design reserved one because stock quote
APIs (Finnhub, Alpha Vantage) all want keys; the chart endpoint below is the
same one finance.yahoo.com's own frontend calls, so it does not.
"""
import logging
import re
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger('vdock')

FETCH_TIMEOUT = 8
CACHE_TTL_SECONDS = 120
MAX_SYMBOLS = 12

#: Tickers written the way users think of them -> CoinGecko ids.
CRYPTO_IDS: Dict[str, str] = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'DOGE': 'dogecoin',
    'XRP': 'ripple', 'ADA': 'cardano', 'DOT': 'polkadot', 'LTC': 'litecoin',
    'AVAX': 'avalanche-2', 'LINK': 'chainlink', 'MATIC': 'matic-network',
    'BNB': 'binancecoin', 'TON': 'the-open-network', 'TRX': 'tron',
}

_SYMBOL_RE = re.compile(r'^[A-Za-z0-9^.\-=]{1,15}$')

_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

_cache: Dict[str, Any] = {}


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    kind: str  # 'stock' | 'crypto'
    currency: str = 'USD'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_symbols(raw: str) -> List[str]:
    """Comma-separated user input -> clean, safe symbol list.

    Symbols go into a URL query, so they are restricted to the characters
    real tickers use (letters, digits, ^ for indexes, - and . for classes
    like BRK-B) -- anything else is dropped rather than escaped.
    """
    out: List[str] = []
    for tok in (raw or '').upper().split(','):
        tok = tok.strip()
        if tok and _SYMBOL_RE.match(tok) and tok not in out:
            out.append(tok)
    return out[:MAX_SYMBOLS]


def _cached(key: str) -> Optional[List[Quote]]:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _fetch_stock(symbol: str) -> Optional[Quote]:
    """One symbol via Yahoo's chart endpoint (the unauthenticated one)."""
    cached = _cached(f's:{symbol}')
    if cached is not None:
        return cached[0] if cached else None

    import requests
    quote = None
    try:
        resp = requests.get(
            f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}',
            params={'interval': '1d', 'range': '1d'},
            headers={'User-Agent': _UA},
            timeout=FETCH_TIMEOUT,
        )
        meta = (resp.json().get('chart', {}).get('result') or [{}])[0] \
            .get('meta', {})
        price = meta.get('regularMarketPrice')
        if isinstance(price, (int, float)):
            quote = Quote(
                symbol=meta.get('symbol') or symbol,
                price=round(float(price), 2),
                kind='stock',
                currency=meta.get('currency') or 'USD',
            )
    except Exception as e:
        logger.warning('Stock quote for %s failed: %s', symbol, e)

    _cache[f's:{symbol}'] = (time.time(), [quote] if quote else [])
    return quote


def _fetch_crypto(symbols: Sequence[str]) -> List[Quote]:
    """Crypto tickers via CoinGecko's keyless endpoint, one request for all."""
    ids = [CRYPTO_IDS[s] for s in symbols if s in CRYPTO_IDS]
    if not ids:
        return []
    key = 'c:' + ','.join(ids)
    cached = _cached(key)
    if cached is not None:
        return cached

    import requests
    quotes: List[Quote] = []
    try:
        resp = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': ','.join(ids), 'vs_currencies': 'usd'},
            headers={'User-Agent': _UA},
            timeout=FETCH_TIMEOUT,
        )
        data = resp.json()
        for sym in symbols:
            cid = CRYPTO_IDS.get(sym)
            price = data.get(cid, {}).get('usd')
            if isinstance(price, (int, float)):
                quotes.append(Quote(symbol=sym, price=float(price),
                                    kind='crypto'))
    except Exception as e:
        logger.warning('Crypto quotes failed: %s', e)

    _cache[key] = (time.time(), quotes)
    return quotes


def fetch_quotes(symbols: Sequence[str]) -> List[Quote]:
    """Stocks and crypto in the order the user listed them.

    A symbol in CRYPTO_IDS goes to CoinGecko (one batched request); the rest
    go to Yahoo, one request each in parallel.
    """
    crypto = [s for s in symbols if s in CRYPTO_IDS]
    stocks = [s for s in symbols if s not in CRYPTO_IDS]

    by_symbol: Dict[str, Quote] = {}
    for q in _fetch_crypto(crypto):
        by_symbol[q.symbol] = q

    if stocks:
        if len(stocks) == 1:
            results = [_fetch_stock(stocks[0])]
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(len(stocks), 6)) as pool:
                results = list(pool.map(_fetch_stock, stocks))
        for q in results:
            if q:
                by_symbol[q.symbol] = q

    return [by_symbol[s] for s in symbols if s in by_symbol]


def clear_cache() -> None:
    _cache.clear()
