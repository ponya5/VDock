"""Broadcasts OS master-volume changes to connected clients.

The volume slider only read the system level once on mount, so a volume-key
press or Quick Settings drag left the deck showing a stale number. This
monitor polls the current default output and emits ``system_volume``::

    system_volume  { value: 0-100, muted: bool }

only when the tuple changes — the first successful read always emits.

Flask-SocketIO in threading mode drops emits from threads the server did
not spawn, so app.py must drive this with ``socketio.start_background_task``
via :func:`set_spawner`, the same contract as ``job_runner``.

Polling is deliberate rather than ``IAudioEndpointVolumeCallback``: the COM
callback needs an STA message pump, which the queue-based audio worker
(DL-058) does not run. A ~1.5 s read is effectively free on Windows and a
tiny subprocess on macOS/Linux.
"""
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from actions.cross_platform_action import read_output_volume

logger = logging.getLogger('vdock')

POLL_INTERVAL_SECONDS = 1.5


def _default_spawn(target: Callable[..., Any], *args: Any) -> Any:
    """Plain daemon thread, used until app.py supplies the Socket.IO spawner."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
    return thread


_emit: Optional[Callable[[str, Dict[str, Any]], None]] = None
_spawn: Callable[..., Any] = _default_spawn
_started = False
_lock = threading.Lock()


def set_emitter(emit: Callable[[str, Dict[str, Any]], None]) -> None:
    """Provide the Socket.IO broadcast function."""
    global _emit
    _emit = emit


def set_spawner(spawn: Callable[..., Any]) -> None:
    """Provide the task spawner — socketio.start_background_task in prod."""
    global _spawn
    _spawn = spawn


def start(interval: float = POLL_INTERVAL_SECONDS) -> bool:
    """Spawn the poll loop once. Returns False if already running."""
    global _started
    with _lock:
        if _started:
            return False
        _started = True
    _spawn(_loop, interval)
    return True


def _loop(interval: float) -> None:
    last = None
    while True:
        try:
            value, muted, _err = read_output_volume()
        except Exception as e:
            logger.error('Volume monitor read failed: %s', e)
            value, muted = None, None
        if value is not None:
            state = (value, muted)
            if state != last:
                last = state
                if _emit is not None:
                    try:
                        _emit('system_volume', {
                            'value': value,
                            'muted': bool(muted),
                        })
                    except Exception as e:  # pragma: no cover - transport
                        logger.error('Could not broadcast volume: %s', e)
        time.sleep(interval)
