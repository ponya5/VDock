"""News headline routes, backed by RSS/Atom feeds.

Thin dispatcher per the project's route conventions: the fetching and parsing
live in services/rss.py.
"""
from flask import Blueprint, jsonify, request

from auth import require_auth
from services import rss

news_bp = Blueprint('news', __name__)


@news_bp.route('/api/news', methods=['GET'])
@require_auth
def get_news():
    """Headlines from the configured feeds.

    Query params:
        feeds:   comma-separated feed URLs. Defaults to rss.DEFAULT_FEEDS.
        refresh: '1' to bypass the cache.
    """
    raw_feeds = (request.args.get('feeds') or '').strip()
    feeds = [f.strip() for f in raw_feeds.split(',') if f.strip()] or None

    rejected = [f for f in (feeds or []) if not rss.is_allowed_feed_url(f)]
    feeds = [f for f in (feeds or []) if rss.is_allowed_feed_url(f)] or None

    use_cache = request.args.get('refresh') != '1'
    headlines = rss.fetch_headlines(feeds, use_cache=use_cache)

    return jsonify({
        'success': True,
        'headlines': [h.to_dict() for h in headlines],
        'count': len(headlines),
        'rejected_feeds': rejected,
        'used_defaults': feeds is None,
    })


@news_bp.route('/api/news/defaults', methods=['GET'])
@require_auth
def get_default_feeds():
    """The feed list used when the user has not configured their own."""
    return jsonify({'success': True, 'feeds': list(rss.DEFAULT_FEEDS)})
