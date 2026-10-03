"""Check that a saved key actually works, with one minimal real API call.

Used by the Settings "Test" button (``POST /api/config/integrations/<id>/test``).
The result carries a status and a short human message -- never the key itself,
and never a response body that could echo it.

Statuses:
    valid        the provider accepted the key
    invalid      the provider rejected it (wrong, revoked or expired)
    limited      accepted but refused right now (quota / rate limit / scope)
    unreachable  could not reach the provider (offline, DNS, timeout)
    unset        no key saved
    builtin      no key saved but the feature works through a free provider
"""
from typing import Any, Dict, Optional

import requests

from services import secrets

TIMEOUT_SECONDS = 10


def _result(status: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {'ok': status in ('valid', 'builtin'), 'status': status, 'message': message, **extra}


def _get(url: str, **kwargs: Any) -> Optional[requests.Response]:
    """GET, or None when the provider cannot be reached."""
    try:
        return requests.get(url, timeout=TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException:
        return None


def _unreachable(provider: str) -> Dict[str, Any]:
    return _result('unreachable', f'Could not reach {provider}. Check this PC\'s internet connection and try again.')


def _check_github(token: str) -> Dict[str, Any]:
    resp = _get(
        'https://api.github.com/user',
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
    )
    if resp is None:
        return _unreachable('GitHub')
    if resp.status_code == 200:
        try:
            login = str(resp.json().get('login') or '')
        except ValueError:
            login = ''
        return _result('valid', f'Valid - signed in as {login}.' if login else 'Valid.', account=login)
    if resp.status_code == 401:
        return _result('invalid', 'GitHub rejected this token. It may be wrong, revoked or expired.')
    if resp.status_code in (403, 429):
        return _result('limited', 'GitHub accepted the request but is limiting it right now (rate limit or token permissions).')
    return _result('invalid', f'GitHub answered with an unexpected status ({resp.status_code}).')


def _check_anthropic(key: str) -> Dict[str, Any]:
    # Listing models is free: it validates the key without spending tokens.
    resp = _get(
        'https://api.anthropic.com/v1/models',
        headers={'x-api-key': key, 'anthropic-version': '2023-06-01'},
        params={'limit': 1},
    )
    if resp is None:
        return _unreachable('Anthropic')
    if resp.status_code == 200:
        return _result('valid', 'Valid - Anthropic accepted this key.')
    if resp.status_code in (401, 403):
        return _result('invalid', 'Anthropic rejected this key. It may be wrong or revoked.')
    if resp.status_code == 429:
        return _result('limited', 'Anthropic accepted the key but is rate limiting it right now.')
    return _result('invalid', f'Anthropic answered with an unexpected status ({resp.status_code}).')


def _check_weatherapi(key: str) -> Dict[str, Any]:
    resp = _get('https://api.weatherapi.com/v1/current.json', params={'key': key, 'q': 'London', 'aqi': 'no'})
    if resp is None:
        return _unreachable('WeatherAPI.com')
    if resp.status_code == 200:
        return _result('valid', 'Valid - WeatherAPI.com accepted this key.')
    if resp.status_code == 401:
        return _result('invalid', 'WeatherAPI.com rejected this key. It may be wrong or disabled.')
    if resp.status_code == 403:
        return _result('limited', 'WeatherAPI.com accepted the key but its quota is used up or the key is disabled.')
    return _result('invalid', f'WeatherAPI.com answered with an unexpected status ({resp.status_code}).')


def _check_open_meteo() -> Dict[str, Any]:
    resp = _get('https://geocoding-api.open-meteo.com/v1/search', params={'name': 'London', 'count': 1})
    if resp is None:
        return _unreachable('Open-Meteo')
    if resp.status_code == 200:
        return _result('builtin', 'No key needed - the built-in Open-Meteo weather service is working.')
    return _result('unreachable', f'Open-Meteo answered with an unexpected status ({resp.status_code}).')


_CHECKERS = {
    'GITHUB_TOKEN': _check_github,
    'ANTHROPIC_API_KEY': _check_anthropic,
    'WEATHERAPI_KEY': _check_weatherapi,
}


def check(spec: secrets.SecretSpec) -> Dict[str, Any]:
    """Run the check for one registered secret."""
    value = secrets.get(spec)
    if value is None:
        if spec.builtin_label and spec.env_var == 'WEATHERAPI_KEY':
            return _check_open_meteo()
        return _result('unset', 'No key saved yet.')
    checker = _CHECKERS.get(spec.env_var)
    if checker is None:
        return _result('unset', 'This key cannot be tested automatically.')
    return checker(value)
