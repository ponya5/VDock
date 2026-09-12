"""Tests for RSS/Atom feed parsing behind the screensaver news widget.

Feature: ai-dev-integration-packs, Property 4: headlines work with no API key.

The widget previously called GNews, which needs a key the user has to sign up
for; without one it showed "News unavailable", which is what it was doing in
practice. Feeds need no key, but they are third-party XML, so the parser has to
survive malformed and hostile input rather than blanking the widget.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import rss  # noqa: E402

RSS_DOC = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Example News</title>
    <item>
      <title>First headline</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 01 Sep 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second &amp; headline</title>
      <link>https://example.com/2</link>
    </item>
  </channel>
</rss>"""

ATOM_DOC = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Source</title>
  <entry>
    <title>Atom headline</title>
    <link href="https://example.com/atom1"/>
    <updated>2026-09-01T10:00:00Z</updated>
  </entry>
</feed>"""


@pytest.fixture(autouse=True)
def clear_cache():
    rss.clear_cache()
    yield
    rss.clear_cache()


class FakeRaw:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self, n, decode_content=True):
        return self._payload[:n]


class FakeResponse:
    def __init__(self, payload: str, status=200, encoding='utf-8'):
        self.raw = FakeRaw(payload.encode('utf-8'))
        self.status_code = status
        self.encoding = encoding

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f'{self.status_code}')


def mock_feed(mocker, doc):
    import requests
    return mocker.patch.object(requests, 'get', return_value=FakeResponse(doc))


# --- parsing -----------------------------------------------------------------

def test_rss_items_are_parsed(mocker):
    mock_feed(mocker, RSS_DOC)

    items = rss.fetch_feed('https://example.com/feed.xml')

    assert [i.title for i in items] == ['First headline', 'Second & headline']
    assert items[0].source == 'Example News'
    assert items[0].url == 'https://example.com/1'
    assert 'Sep 2026' in items[0].published


def test_atom_entries_are_parsed(mocker):
    mock_feed(mocker, ATOM_DOC)

    items = rss.fetch_feed('https://example.com/atom.xml')

    assert [i.title for i in items] == ['Atom headline']
    assert items[0].source == 'Atom Source'
    assert items[0].url == 'https://example.com/atom1'


def test_html_tags_are_stripped_from_titles(mocker):
    doc = RSS_DOC.replace(
        '<title>First headline</title>',
        '<title>First &lt;b&gt;bold&lt;/b&gt;   headline</title>',
    )
    mock_feed(mocker, doc)

    items = rss.fetch_feed('https://example.com/feed.xml')

    assert items[0].title == 'First bold headline'


def test_items_without_a_title_are_skipped(mocker):
    doc = RSS_DOC.replace('<title>Second &amp; headline</title>', '')
    mock_feed(mocker, doc)

    items = rss.fetch_feed('https://example.com/feed.xml')

    assert len(items) == 1


# --- resilience --------------------------------------------------------------

def test_malformed_xml_yields_no_headlines_instead_of_raising(mocker):
    mock_feed(mocker, '<rss><channel><item><title>broken')

    assert rss.fetch_feed('https://example.com/bad.xml') == []


def test_unrecognised_format_yields_no_headlines(mocker):
    mock_feed(mocker, '<html><body>not a feed</body></html>')

    assert rss.fetch_feed('https://example.com/page.html') == []


def test_network_failure_yields_no_headlines(mocker):
    import requests
    mocker.patch.object(requests, 'get', side_effect=requests.Timeout())

    assert rss.fetch_feed('https://example.com/slow.xml') == []


def test_http_error_yields_no_headlines(mocker):
    import requests
    mocker.patch.object(requests, 'get',
                        return_value=FakeResponse(RSS_DOC, status=500))

    assert rss.fetch_feed('https://example.com/down.xml') == []


def test_oversized_feed_is_rejected(mocker):
    huge = '<rss><channel>' + ('<x/>' * 600_000) + '</channel></rss>'
    mock_feed(mocker, huge)

    assert rss.fetch_feed('https://example.com/huge.xml') == []


@pytest.mark.parametrize('url', [
    'file:///C:/Windows/win.ini',
    'ftp://example.com/feed',
    'javascript:alert(1)',
    'not a url',
])
def test_non_http_feed_urls_are_refused(url):
    assert rss.is_allowed_feed_url(url) is False
    assert rss.fetch_feed(url) == []


@pytest.mark.parametrize('url', [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'http://localhost:8080/feed.xml',
])
def test_http_feed_urls_are_allowed(url):
    assert rss.is_allowed_feed_url(url) is True


# --- merging -----------------------------------------------------------------

def test_feeds_are_interleaved_so_no_source_dominates(mocker):
    def make(title_prefix, count):
        items = ''.join(
            f'<item><title>{title_prefix}{i}</title>'
            f'<link>https://e/{title_prefix}{i}</link></item>'
            for i in range(count)
        )
        return (f'<?xml version="1.0"?><rss version="2.0"><channel>'
                f'<title>{title_prefix}</title>{items}</channel></rss>')

    import requests
    mocker.patch.object(requests, 'get', side_effect=[
        FakeResponse(make('A', 5)),
        FakeResponse(make('B', 5)),
    ])

    merged = rss.fetch_headlines(['https://a/feed', 'https://b/feed'])

    # Round-robin: A0, B0, A1, B1, ...
    assert [h.title for h in merged[:4]] == ['A0', 'B0', 'A1', 'B1']


def test_one_dead_feed_does_not_blank_the_widget(mocker):
    import requests
    mocker.patch.object(requests, 'get', side_effect=[
        requests.Timeout(),
        FakeResponse(RSS_DOC),
    ])

    merged = rss.fetch_headlines(['https://dead/feed', 'https://alive/feed'])

    assert [h.title for h in merged] == ['First headline', 'Second & headline']


def test_empty_feed_list_falls_back_to_defaults(mocker):
    mock_feed(mocker, RSS_DOC)

    merged = rss.fetch_headlines([])

    assert merged, 'should have used DEFAULT_FEEDS'


def test_total_items_are_capped(mocker):
    items = ''.join(
        f'<item><title>T{i}</title><link>https://e/{i}</link></item>'
        for i in range(50)
    )
    doc = (f'<?xml version="1.0"?><rss version="2.0"><channel><title>Big</title>'
           f'{items}</channel></rss>')
    mock_feed(mocker, doc)

    merged = rss.fetch_headlines(['https://big/feed'])

    assert len(merged) <= rss.MAX_TOTAL_ITEMS


# --- caching -----------------------------------------------------------------

def test_a_second_fetch_is_served_from_cache(mocker):
    get = mock_feed(mocker, RSS_DOC)

    rss.fetch_feed('https://example.com/feed.xml')
    rss.fetch_feed('https://example.com/feed.xml')

    assert get.call_count == 1


def test_cache_can_be_bypassed(mocker):
    get = mock_feed(mocker, RSS_DOC)

    rss.fetch_feed('https://example.com/feed.xml')
    rss.fetch_feed('https://example.com/feed.xml', use_cache=False)

    assert get.call_count == 2


# --- the HTTP route ----------------------------------------------------------

def test_news_endpoint_returns_headlines(mocker):
    import app as app_module
    mock_feed(mocker, RSS_DOC)

    body = app_module.app.test_client().get('/api/news').get_json()

    assert body['success'] is True
    assert body['count'] == len(body['headlines'])
    assert body['headlines'][0]['title'] == 'First headline'


def test_news_endpoint_reports_rejected_feeds(mocker):
    import app as app_module
    mock_feed(mocker, RSS_DOC)

    body = app_module.app.test_client().get(
        '/api/news?feeds=file:///etc/passwd,https://ok/feed'
    ).get_json()

    assert body['rejected_feeds'] == ['file:///etc/passwd']


def test_defaults_endpoint_lists_feeds():
    import app as app_module

    body = app_module.app.test_client().get('/api/news/defaults').get_json()

    assert body['feeds'] == list(rss.DEFAULT_FEEDS)
