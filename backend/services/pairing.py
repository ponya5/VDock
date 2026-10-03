"""Single-use pairing tokens for the "scan the QR, skip the password" flow (DL-147).

A signed-in desktop window asks for a token, shows it inside the QR, and the
phone trades it once for a normal login JWT. Tokens live in memory only (a
restart invalidates them), expire after ``TTL_S`` and are never logged.
"""
import secrets
import time
from collections import OrderedDict
from threading import Lock
from typing import Callable

TTL_S = 600
MAX_LIVE = 5

_lock = Lock()
_tokens: "OrderedDict[str, float]" = OrderedDict()


def issue(clock: Callable[[], float] = time.time) -> str:
    """Mint a token. Beyond ``MAX_LIVE`` live tokens the oldest is evicted."""
    now = clock()
    token = secrets.token_urlsafe(32)
    with _lock:
        _purge_expired(now)
        _tokens[token] = now + TTL_S
        while len(_tokens) > MAX_LIVE:
            _tokens.popitem(last=False)
    return token


def redeem(token: str, clock: Callable[[], float] = time.time) -> bool:
    """True exactly once for a live token; it is consumed either way."""
    now = clock()
    with _lock:
        _purge_expired(now)
        return _tokens.pop(token, None) is not None


def _purge_expired(now: float) -> None:
    for stale in [t for t, expires in _tokens.items() if expires <= now]:
        del _tokens[stale]
