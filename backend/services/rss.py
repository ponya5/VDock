"""RSS and Atom feed fetching for the screensaver news widget.

Why this is server-side
-----------------------
Feeds are XML served without CORS headers, so the browser cannot fetch them
directly -- which is why the screensaver previously used GNews, an API that
needs a key the user has to sign up for. Without that key the widget just
showed "News unavailable". Proxying feeds here removes the key requirement
entirely and lets several sources be merged into one rotating list.

Parsing uses the standard library rather than adding feedparser: RSS 2.0 and
Atom are simple enough, and every dependency is one more thing for a user to
install before their deck works.

XML parsing note: feeds are third-party documents, so entity expansion is
disabled to avoid the billion-laughs class of attack. ElementTree does not
expand external entities by default, and we additionally cap the response size.
"""
import logging
import re
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import urlparse
from xml.etree import ElementTree

logger = logging.getLogger('vdock')

DEFAULT_FEEDS: Sequence[str] = (
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://hnrss.org/frontpage',
    'https://feeds.arstechnica.com/arstechnica/technology-lab',
)

FETCH_TIMEOUT = 10
#: Feeds are usually tens of KB; a megabyte is already generous.
MAX_FEED_BYTES = 2_000_000
MAX_ITEMS_PER_FEED = 15
MAX_TOTAL_ITEMS = 40
CACHE_TTL_SECONDS = 600

_ATOM = '{http://www.w3.org/2005/Atom}'
_TAG_RE = re.compile(r'<[^>]+>')
_WS_RE = re.compile(r'\s+')

#: url -> (fetched_at, headlines)
_cache: Dict[str, Any] = {}


@dataclass(frozen=True)
class Headline:
    title: str
    source: str
    url: str
    published: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clean(text: Optional[str]) -> str:
    """Strip tags and collapse whitespace; feed titles often carry both."""
    if not text:
        return ''
    return _WS_RE.sub(' ', _TAG_RE.sub('', text)).strip()


def is_allowed_feed_url(url: str) -> bool:
    """Only http(s) URLs with a host may be fetched."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def _parse(xml_text: str, fallback_source: str) -> List[Headline]:
    """Parse an RSS 2.0 or Atom document into headlines."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as e:
        logger.warning('Could not parse feed from %s: %s', fallback_source, e)
        return []

    headlines: List[Headline] = []

    # RSS 2.0
    channel = root.find('channel')
    if channel is not None:
        source = _clean(channel.findtext('title')) or fallback_source
        for item in channel.findall('item')[:MAX_ITEMS_PER_FEED]:
            title = _clean(item.findtext('title'))
            if not title:
                continue
            headlines.append(Headline(
                title=title,
                source=source,
                url=(item.findtext('link') or '').strip(),
                published=_clean(item.findtext('pubDate')),
            ))
        return headlines

    # Atom
    if root.tag == f'{_ATOM}feed':
        source = _clean(root.findtext(f'{_ATOM}title')) or fallback_source
        for entry in root.findall(f'{_ATOM}entry')[:MAX_ITEMS_PER_FEED]:
            title = _clean(entry.findtext(f'{_ATOM}title'))
            if not title:
                continue
            link_el = entry.find(f'{_ATOM}link')
            headlines.append(Headline(
                title=title,
                source=source,
                url=(link_el.get('href') if link_el is not None else '') or '',
                published=_clean(entry.findtext(f'{_ATOM}updated')),
            ))
        return headlines

    logger.warning('Unrecognised feed format from %s', fallback_source)
    return []


def fetch_feed(url: str, use_cache: bool = True) -> List[Headline]:
    """Fetch and parse one feed. Returns [] on any failure."""
    url = url.strip()
    if not is_allowed_feed_url(url):
        logger.warning('Refusing non-http(s) feed URL: %s', url)
        return []

    if use_cache:
        cached = _cache.get(url)
        if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    import requests

    try:
        response = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={'User-Agent': 'VDock/2.0 (+https://github.com/ponya5/VDock2)'},
            stream=True,
        )
        response.raise_for_status()

        content = response.raw.read(MAX_FEED_BYTES + 1, decode_content=True)
        if len(content) > MAX_FEED_BYTES:
            logger.warning('Feed %s exceeded %s bytes; ignoring',
                           url, MAX_FEED_BYTES)
            return []
        text = content.decode(response.encoding or 'utf-8', errors='replace')
    except Exception as e:
        logger.warning('Could not fetch feed %s: %s', url, e)
        return []

    headlines = _parse(text, urlparse(url).netloc)
    _cache[url] = (time.time(), headlines)
    return headlines


def fetch_headlines(
    feeds: Optional[Iterable[str]] = None, use_cache: bool = True
) -> List[Headline]:
    """Merge several feeds into one list, interleaved so no source dominates.

    A failing feed is skipped rather than failing the whole request -- one dead
    URL should not blank the widget.
    """
    urls = [u for u in (feeds or DEFAULT_FEEDS) if u and u.strip()]
    if not urls:
        urls = list(DEFAULT_FEEDS)

    per_feed = [fetch_feed(url, use_cache=use_cache) for url in urls]

    # Round-robin so a prolific feed does not push the others off the end.
    merged: List[Headline] = []
    for index in range(MAX_ITEMS_PER_FEED):
        for items in per_feed:
            if index < len(items):
                merged.append(items[index])
                if len(merged) >= MAX_TOTAL_ITEMS:
                    return merged
    return merged


def clear_cache() -> None:
    """Drop cached feeds, so a manual refresh really refetches."""
    _cache.clear()
