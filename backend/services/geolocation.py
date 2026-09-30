"""Machine geolocation from the public IP (weather "automatic" mode).

The backend runs on the machine VDock sits on, so resolving this host's
public IP is exactly "the local machine's location" — no browser
permission prompt, no GPS, works on the touch panel's kiosk webview.
ipwho.is is free, key-less and HTTPS; results are cached for hours
because an IP-derived fix barely moves.
"""
import json
import logging
import threading
import time
import urllib.request

logger = logging.getLogger(__name__)

_GEO_URL = 'https://ipwho.is/'
_CACHE_TTL_S = 6 * 3600
_NEG_CACHE_TTL_S = 60       # don't hammer the service while offline
_TIMEOUT_S = 5

_lock = threading.Lock()
_cache = None               # (expires_at, location dict) or None
_neg_until = 0.0            # suppress refetches for a minute after a miss


def _fetch_location():
    with urllib.request.urlopen(_GEO_URL, timeout=_TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if not data.get('success'):
        raise RuntimeError(f"IP geolocation failed: {data.get('message') or 'no fix'}")
    city = data.get('city')
    country = data.get('country_code') or data.get('country')
    label = ', '.join(p for p in (city, country) if p) or 'Current location'
    return {
        'latitude': float(data['latitude']),
        'longitude': float(data['longitude']),
        'label': label,
    }


def resolve():
    """Return {latitude, longitude, label} for this machine's public IP.
    Raises RuntimeError/URLError when no fix is available — callers decide
    how to fall back."""
    global _cache, _neg_until
    now = time.time()
    with _lock:
        if _cache is not None and _cache[0] > now:
            return _cache[1]
        if now < _neg_until:
            raise RuntimeError('IP geolocation temporarily unavailable')
    try:
        location = _fetch_location()
    except Exception:
        with _lock:
            _neg_until = now + _NEG_CACHE_TTL_S
        raise
    with _lock:
        _cache = (now + _CACHE_TTL_S, location)
        _neg_until = 0.0
    return location
