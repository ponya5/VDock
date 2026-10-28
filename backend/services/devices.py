"""Registry of devices signed in to the deck (DL-154).

Every login or pairing mints a device id that rides in the JWT (``did``).
Revoking an id makes that device's token fail on its next request, so one
lost phone can be cut off without signing out the rest. The list also lets
the Connect page show who is connected.

Stored in ``data/devices.json``; no raw User-Agent is kept, only a coarse
label ("iPhone", "Windows PC").
"""
import json
import re
import secrets
import time
from threading import Lock
from typing import Any, Dict, List, Optional

from config import Config
from utils.atomic import atomic_write_text

MAX_DEVICES = 50
_TOUCH_EVERY_S = 60

_lock = Lock()
_state: Dict[str, Any] = {'path': None, 'devices': {}}
_last_saved: Dict[str, float] = {}


def label_from_user_agent(user_agent: str) -> str:
    """A short human label for a browser's User-Agent."""
    ua = (user_agent or '').lower()
    model = re.search(r'android [\d.]+; ([^;)]+)', ua)
    name = model.group(1).strip() if model else ''
    # Chrome reduces the model to "K"; only a real model string is worth showing.
    if name and name != 'k' and len(name) > 2:
        return f'Android ({name.upper() if len(name) < 12 else name})'
    if 'iphone' in ua:
        return 'iPhone'
    if 'ipad' in ua:
        return 'iPad'
    if 'android' in ua:
        return 'Android phone' if 'mobile' in ua else 'Android tablet'
    if 'cros' in ua:
        return 'Chromebook'
    if 'macintosh' in ua or 'mac os x' in ua:
        return 'Mac'
    if 'windows' in ua:
        return 'Windows PC'
    if 'linux' in ua:
        return 'Linux PC'
    return 'Device'


def _path():
    return Config.DATA_DIR / 'devices.json'


def _devices() -> Dict[str, Dict[str, Any]]:
    """The in-memory registry, (re)loaded when the data directory changes."""
    path = _path()
    if _state['path'] != path:
        loaded: Dict[str, Dict[str, Any]] = {}
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(raw, dict):
                loaded = {k: v for k, v in raw.items() if isinstance(v, dict)}
        except (OSError, ValueError):
            pass
        _state['path'] = path
        _state['devices'] = loaded
        _last_saved.clear()
    return _state['devices']


def _save() -> None:
    try:
        atomic_write_text(_path(), json.dumps(_state['devices'], indent=2))
    except OSError:
        pass  # in-memory state still works until the next restart


MAX_LABEL = 40


CLIENT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{8,40}$')


def register(user_agent: str = '', ip: str = '', device_id: str = '') -> str:
    """Add a device and return its id.

    A device on this computer needs no name; any other starts unnamed and is
    asked for one on its first screen (see ``rename``).
    """
    now = time.time()
    device_id = device_id if CLIENT_ID_RE.match(device_id or '') else secrets.token_urlsafe(9)
    with _lock:
        devices = _devices()
        devices[device_id] = {
            'id': device_id,
            'label': label_from_user_agent(user_agent),
            'paired_at': now,
            'last_seen': now,
            'ip': ip or '',
            'named': ip in ('127.0.0.1', '::1'),
        }
        while len(devices) > MAX_DEVICES:
            oldest = min(devices, key=lambda k: devices[k].get('last_seen', 0))
            del devices[oldest]
        _save()
    return device_id


def seen(device_id: str, user_agent: str = '', ip: str = '') -> None:
    """A browser's own id hit the API: record it (first sight) or touch it.

    This is what lists a phone that connects with auth off, where no login
    ever happens. Loopback (this computer) is never listed.
    """
    if not CLIENT_ID_RE.match(device_id or '') or ip in ('127.0.0.1', '::1', ''):
        return
    with _lock:
        known = device_id in _devices()
    if known:
        touch(device_id, ip)
    elif not Config.REQUIRE_AUTH:  # with auth on, only a login lists (and a revoke sticks)
        register(user_agent, ip, device_id)


def is_active(device_id: str) -> bool:
    with _lock:
        return device_id in _devices()


def touch(device_id: Optional[str], ip: str = '') -> None:
    """Record activity, persisting at most once a minute per device."""
    if not device_id:
        return
    now = time.time()
    with _lock:
        device = _devices().get(device_id)
        if device is None:
            return
        device['last_seen'] = now
        if ip:
            device['ip'] = ip
        if now - _last_saved.get(device_id, 0) >= _TOUCH_EVERY_S:
            _last_saved[device_id] = now
            _save()


def list_devices() -> List[Dict[str, Any]]:
    """Most recently seen first."""
    with _lock:
        return sorted((dict(d) for d in _devices().values()),
                      key=lambda d: d.get('last_seen', 0), reverse=True)


def rename(device_id: str, label: str) -> bool:
    """Give a device a name the user recognises in the connected list."""
    label = ' '.join((label or '').split())[:MAX_LABEL]
    if not label:
        return False
    with _lock:
        device = _devices().get(device_id)
        if device is None:
            return False
        device['label'] = label
        device['named'] = True
        _save()
        return True


def revoke(device_id: str) -> bool:
    with _lock:
        devices = _devices()
        if device_id not in devices:
            return False
        del devices[device_id]
        _save()
        return True


def revoke_all() -> int:
    with _lock:
        devices = _devices()
        count = len(devices)
        devices.clear()
        _save()
        return count
