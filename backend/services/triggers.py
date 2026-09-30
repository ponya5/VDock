"""Persistent trigger engine — "when X, do Y" for the deck (DL-120).

Triggers live in ``Config.DATA_DIR / 'triggers.json'`` and are evaluated by
a single ~1 s loop with the same injected seams as ``volume_monitor`` /
``job_runner`` (emitter + spawner, plus an action executor). Event types:

  * ``time``           ``{at:'HH:MM', days?:[0-6]}`` — fires once per
                       matching minute; ``days`` uses Python ``weekday()``
                       numbering (0 = Monday). Edge-tracked per minute.
  * ``app_foreground`` ``{exe:'spotify.exe'}`` — polls
                       ``utils.app_monitor.get_current_active_app()`` (a
                       one-shot getter, so no monitor thread is required)
                       and fires on the observed transition *into* the exe.
  * ``agent_state``    ``{source:'claude', state:'permission'}`` — polls
                       ``integrations.agent_state.snapshot()`` and fires on
                       the observed transition *into* the state; leaving the
                       state re-arms it.
  * ``webhook``        ``{key:'…'}`` — never polled; the route calls
                       :func:`fire_webhook_key` when
                       ``POST /api/triggers/fire/<key>`` arrives.

The first observation of a polled condition is a baseline, not a fire —
otherwise every backend restart while the app/state already matches would
re-run the action (a "switch scene when Spotify is focused" trigger firing
on every launch while Spotify is focused is a bug, not a feature). For the
same reason ``update_trigger`` clears a trigger's edge state: an edited
trigger behaves like a new one and must see a real entry.

Every fire — success or failure — broadcasts::

    trigger_fired  {id, label, ok, detail, ts}

per contracts/socket-events.md. Dispatch is fully wrapped: a throwing
executor degrades to ``ok:false`` and can never kill the loop.

Flask-SocketIO in threading mode drops emits from threads it did not
spawn, so ``app.py`` must drive this via ``socketio.start_background_task``
through :func:`set_spawner`.
"""
import copy
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from config import Config
from integrations import agent_state

logger = logging.getLogger('vdock')

TRIGGER_FILENAME = 'triggers.json'
POLL_INTERVAL_SECONDS = 1.0

EVENT_TIME = 'time'
EVENT_APP = 'app_foreground'
EVENT_AGENT = 'agent_state'
EVENT_WEBHOOK = 'webhook'
EVENT_TYPES = frozenset({EVENT_TIME, EVENT_APP, EVENT_AGENT, EVENT_WEBHOOK})

ACTION_EXECUTE = 'execute_action'
ACTION_SCENE = 'switch_scene'
ACTION_NOTIFY = 'show_notification'
ACTION_TYPES = frozenset({ACTION_EXECUTE, ACTION_SCENE, ACTION_NOTIFY})

AGENT_SOURCES = frozenset({'claude', 'cursor', 'devin', 'antigravity', 'generic'})
AGENT_STATES = frozenset({'ready', 'working', 'permission'})

_TIME_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
#: The key lands in a URL path — keep it slug-safe.
_KEY_RE = re.compile(r'^[A-Za-z0-9_-]{1,64}$')

#: Marker for "no observation yet" — distinct from an observed None (e.g.
#: an agent source absent from the snapshot), which does count as outside.
_UNSET = object()

# ---------------------------------------------------------------------------
# Store — whole dict guarded by one lock; writes are tmp + os.replace.
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_triggers: Optional[Dict[str, Dict[str, Any]]] = None  # None = not loaded yet
_runtime: Dict[str, Dict[str, Any]] = {}              # edge state (loop only)
_engine_enabled = True                                # master pause switch


def _store_path() -> Path:
    """Resolved per access so tests can repoint Config.DATA_DIR."""
    return Config.DATA_DIR / TRIGGER_FILENAME


def _load_locked() -> None:
    """Read the store once, lazily. Caller holds ``_lock``.

    A corrupt or missing file is an empty store, never a crash — a broken
    JSON must not take the engine down with it.
    """
    global _triggers, _engine_enabled
    if _triggers is not None:
        return
    _triggers = {}
    try:
        raw = json.loads(_store_path().read_text(encoding='utf-8'))
    except FileNotFoundError:
        return
    except (OSError, ValueError) as e:  # ValueError covers JSONDecodeError
        logger.error('Could not read triggers store: %s', e)
        return
    if isinstance(raw, dict):
        _engine_enabled = bool(raw.get('enabled', True))
    items = raw.get('triggers') if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, dict) and isinstance(item.get('id'), str):
            _triggers[item['id']] = item


def _save_locked() -> None:
    """Persist the store atomically. Caller holds ``_lock``.

    tmp + ``os.replace`` — a crash mid-write leaves the old file intact,
    which matters on a device that is power-cycled rather than shut down.
    """
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + '.tmp')
    tmp.write_text(
        json.dumps({'enabled': _engine_enabled,
                    'triggers': list(_triggers.values())}, indent=2),
        encoding='utf-8',
    )
    os.replace(tmp, path)


def _new_id() -> str:
    return f'trg_{uuid.uuid4().hex[:10]}'


# ---------------------------------------------------------------------------
# Validation — ValueError here maps to HTTP 400 in the route.
# ---------------------------------------------------------------------------

def _validate_event(event: Any) -> Dict[str, Any]:
    """Validate + normalize an event spec; returns the clean dict."""
    if not isinstance(event, dict):
        raise ValueError('event must be an object')
    etype = event.get('type')

    if etype == EVENT_TIME:
        at = str(event.get('at') or '')
        if not _TIME_RE.fullmatch(at):
            raise ValueError("time event needs 'at' as HH:MM")
        out: Dict[str, Any] = {'type': etype, 'at': at}
        days = event.get('days')
        if days is not None:
            if not isinstance(days, list) or any(
                not isinstance(d, int) or isinstance(d, bool) or d < 0 or d > 6
                for d in days
            ):
                raise ValueError('days must be a list of integers 0-6 (0 = Monday)')
            out['days'] = sorted(set(days))
        return out

    if etype == EVENT_APP:
        exe = str(event.get('exe') or '').strip()
        if not exe:
            raise ValueError("app_foreground event needs an 'exe'")
        return {'type': etype, 'exe': exe[:260]}

    if etype == EVENT_AGENT:
        source = str(event.get('source') or '').strip()
        state = str(event.get('state') or '').strip()
        if source not in AGENT_SOURCES:
            raise ValueError(
                f'agent_state source must be one of {sorted(AGENT_SOURCES)}'
            )
        if state not in AGENT_STATES:
            raise ValueError(
                f'agent_state state must be one of {sorted(AGENT_STATES)}'
            )
        return {'type': etype, 'source': source, 'state': state}

    if etype == EVENT_WEBHOOK:
        key = str(event.get('key') or '').strip() or f'whk_{uuid.uuid4().hex[:16]}'
        if not _KEY_RE.fullmatch(key):
            raise ValueError('webhook key must be 1-64 chars of A-Z a-z 0-9 _ -')
        return {'type': etype, 'key': key}

    raise ValueError(f'Unknown event type: {etype}')


def _validate_action(action: Any) -> Dict[str, Any]:
    """Validate + normalize an action spec; returns the clean dict."""
    if not isinstance(action, dict):
        raise ValueError('action must be an object')
    atype = action.get('type')

    if atype == ACTION_EXECUTE:
        inner = action.get('action')
        if not isinstance(inner, dict) or not str(inner.get('type') or '').strip():
            raise ValueError("execute_action needs an action {type, config?}")
        config = inner.get('config', {})
        if not isinstance(config, dict):
            raise ValueError('execute_action config must be an object')
        return {
            'type': atype,
            'action': {'type': str(inner['type']).strip()[:64], 'config': config},
        }

    if atype == ACTION_SCENE:
        scene = str(action.get('scene') or '').strip()
        if not scene:
            raise ValueError("switch_scene needs a 'scene' name")
        return {'type': atype, 'scene': scene[:120]}

    if atype == ACTION_NOTIFY:
        title = str(action.get('title') or '').strip()
        if not title:
            raise ValueError("show_notification needs a 'title'")
        # Caps mirror the panel_notification contract.
        return {
            'type': atype,
            'title': title[:80],
            'message': str(action.get('message') or '')[:300],
        }

    raise ValueError(f'Unknown action type: {atype}')


def _derive_label(event: Dict[str, Any], action: Dict[str, Any]) -> str:
    """Fallback label so a trigger never renders nameless in the list."""
    etype = event.get('type')
    if etype == EVENT_TIME:
        when = f"at {event.get('at')}"
        if event.get('days'):
            when += ' on selected days'
    elif etype == EVENT_APP:
        when = f"when {event.get('exe')} is focused"
    elif etype == EVENT_AGENT:
        when = f"when {event.get('source')} is {event.get('state')}"
    else:
        when = 'on webhook'
    atype = action.get('type')
    if atype == ACTION_SCENE:
        does = f"switch to {action.get('scene')}"
    elif atype == ACTION_NOTIFY:
        does = f"show '{action.get('title')}'"
    else:
        does = f"run {((action.get('action') or {}).get('type')) or 'action'}"
    return f'{when} — {does}'


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def list_triggers() -> List[Dict[str, Any]]:
    with _lock:
        _load_locked()
        # Deep copies — nested event/action dicts must not alias the store,
        # or a caller mutating a returned trigger corrupts it.
        return copy.deepcopy(list(_triggers.values()))


def get_trigger(trigger_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        _load_locked()
        trigger = _triggers.get(trigger_id)
        return copy.deepcopy(trigger) if trigger is not None else None


def add_trigger(data: Any) -> Dict[str, Any]:
    """Validate + persist a new trigger. Raises ValueError on bad input."""
    if not isinstance(data, dict):
        raise ValueError('Trigger body must be an object')
    event = _validate_event(data.get('event'))
    action = _validate_action(data.get('action'))
    label = str(data.get('label') or '').strip()[:120] or _derive_label(event, action)
    trigger = {
        'id': _new_id(),
        'label': label,
        'enabled': bool(data.get('enabled', True)),
        'event': event,
        'action': action,
    }
    with _lock:
        _load_locked()
        while trigger['id'] in _triggers:
            trigger['id'] = _new_id()
        _triggers[trigger['id']] = trigger
        _save_locked()
    return copy.deepcopy(trigger)


def update_trigger(trigger_id: str, patch: Any) -> Optional[Dict[str, Any]]:
    """Partial update — event/action are whole-object replacements.

    Returns None when the id is unknown; raises ValueError on bad input.
    Edge state is dropped so an edited trigger re-baselines instead of
    comparing against the old target's history.
    """
    if not isinstance(patch, dict):
        raise ValueError('Patch must be an object')
    # Validate first: malformed input is a 400 even for an unknown id.
    clean: Dict[str, Any] = {}
    if 'event' in patch:
        clean['event'] = _validate_event(patch['event'])
    if 'action' in patch:
        clean['action'] = _validate_action(patch['action'])
    if 'enabled' in patch:
        clean['enabled'] = bool(patch['enabled'])
    with _lock:
        _load_locked()
        current = _triggers.get(trigger_id)
        if current is None:
            return None
        merged = dict(current)
        merged.update(clean)
        if 'label' in patch:
            merged['label'] = (
                str(patch.get('label') or '').strip()[:120] or current['label']
            )
        _triggers[trigger_id] = merged
        _runtime.pop(trigger_id, None)
        _save_locked()
        return copy.deepcopy(merged)


def remove_trigger(trigger_id: str) -> bool:
    with _lock:
        _load_locked()
        if trigger_id not in _triggers:
            return False
        del _triggers[trigger_id]
        _runtime.pop(trigger_id, None)
        _save_locked()
        return True


def is_enabled() -> bool:
    """Master switch — when off the engine pauses and webhooks no-op.

    Per-trigger ``enabled`` still applies on top; manual test-fires keep
    working so the panel's smoke-test button stays honest.
    """
    with _lock:
        _load_locked()
        return _engine_enabled


def set_enabled(flag: bool) -> bool:
    """Pause/resume every trigger at once; persisted with the store."""
    global _engine_enabled
    with _lock:
        _load_locked()
        _engine_enabled = bool(flag)
        _runtime.clear()  # re-baseline edges so nothing fires on resume
        _save_locked()
        return _engine_enabled


def reset() -> None:
    """Drop in-memory state (loaded store + edge tracking). Tests only."""
    global _triggers, _started, _engine_enabled
    with _lock:
        _triggers = None
        _runtime.clear()
        _engine_enabled = True
    with _start_lock:
        _started = False
    _stop.set()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _default_spawn(target: Callable[..., Any], *args: Any) -> Any:
    """Plain daemon thread, used until app.py supplies the Socket.IO spawner."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
    return thread


_emit: Optional[Callable[[str, Dict[str, Any]], None]] = None
_spawn: Callable[..., Any] = _default_spawn
_executor: Optional[Any] = None
_started = False
#: Each start() hands the loop a fresh Event, so a loop left over from a
#: previous generation can never be resurrected by a later start()'s clear.
_stop = threading.Event()
_start_lock = threading.Lock()


def set_emitter(emit: Callable[[str, Dict[str, Any]], None]) -> None:
    """Provide the Socket.IO broadcast function."""
    global _emit
    _emit = emit


def set_spawner(spawn: Callable[..., Any]) -> None:
    """Provide the task spawner — socketio.start_background_task in prod."""
    global _spawn
    _spawn = spawn


def set_executor(executor: Any) -> None:
    """Provide the ActionExecutor for execute_action triggers."""
    global _executor
    _executor = executor


def start(interval: float = POLL_INTERVAL_SECONDS) -> bool:
    """Spawn the evaluation loop once. Returns False if already running."""
    global _started, _stop
    with _start_lock:
        if _started:
            return False
        _started = True
        _stop = threading.Event()
    _spawn(_loop, _stop, interval)
    return True


def stop() -> None:
    """Signal the loop to exit (it stops at the next tick boundary)."""
    global _started
    with _start_lock:
        _started = False
        _stop.set()


def _emit_event(name: str, payload: Dict[str, Any]) -> None:
    if _emit is None:
        return
    try:
        _emit(name, payload)
    except Exception as e:  # pragma: no cover - transport
        logger.error('Could not emit %s: %s', name, e)


def _loop(stop_event: threading.Event, interval: float) -> None:
    while not stop_event.is_set():
        try:
            _tick()
        except Exception as e:
            logger.error('Trigger tick failed: %s', e)
        stop_event.wait(interval)


def _read_app_exe() -> Optional[str]:
    """Foreground exe, lowercase — None when it can't be determined.

    ``get_current_active_app()`` is a one-shot getter (a fresh AppMonitor
    per call), so this works whether or not the long-running monitor is up.
    A failed read skips app triggers this tick instead of re-arming them.
    """
    try:
        from utils import app_monitor
        app = app_monitor.get_current_active_app()
    except Exception as e:
        logger.error('App foreground read failed: %s', e)
        return None
    if not isinstance(app, dict):
        return None
    exe = app.get('exe') or app.get('name')
    return str(exe).lower() if exe else None


def _read_agent_states() -> Dict[str, Any]:
    try:
        return agent_state.snapshot() or {}
    except Exception as e:
        logger.error('Agent state snapshot failed: %s', e)
        return {}


def _tick(now: Optional[datetime] = None) -> None:
    """One evaluation pass over enabled triggers.

    ``now`` is injectable for tests — minute-edge matching needs a real
    datetime, not a float.
    """
    now = now or datetime.now()
    with _lock:
        _load_locked()
        if not _engine_enabled:
            return
        items = [t for t in _triggers.values() if t.get('enabled', True)]
    if not items:
        return

    # Shared reads: one app probe / one snapshot per tick, and only when a
    # live trigger actually needs it — a deck full of time triggers never
    # touches the foreground-window APIs.
    need_app = any((t.get('event') or {}).get('type') == EVENT_APP for t in items)
    need_agent = any((t.get('event') or {}).get('type') == EVENT_AGENT for t in items)
    app_exe: Optional[str] = None
    app_known = False
    if need_app:
        app_exe = _read_app_exe()
        app_known = app_exe is not None
    states: Dict[str, Any] = _read_agent_states() if need_agent else {}

    hhmm = now.strftime('%H:%M')
    weekday = now.weekday()
    minute_key = now.strftime('%Y-%m-%d %H:%M')

    for trigger in items:
        event = trigger.get('event') or {}
        etype = event.get('type')

        if etype == EVENT_TIME:
            if event.get('at') != hhmm:
                continue
            days = event.get('days')
            if days and weekday not in days:
                continue
            rt = _runtime.setdefault(trigger['id'], {})
            if rt.get('minute') == minute_key:
                continue
            # Mark before dispatch — a throwing action must not loop-fire
            # inside the same minute.
            rt['minute'] = minute_key
            _fire(trigger)

        elif etype == EVENT_APP:
            if not app_known:
                continue
            rt = _runtime.setdefault(trigger['id'], {})
            prev = rt.get('prev_app', _UNSET)
            rt['prev_app'] = app_exe
            if prev is _UNSET:
                continue  # first observation = baseline, never a fire
            if app_exe == str(event.get('exe') or '').lower() \
                    and prev != app_exe:
                _fire(trigger)

        elif etype == EVENT_AGENT:
            rt = _runtime.setdefault(trigger['id'], {})
            entry = states.get(str(event.get('source') or '')) or {}
            current = entry.get('state')
            prev = rt.get('prev_state', _UNSET)
            rt['prev_state'] = current
            if prev is _UNSET:
                continue  # baseline
            if current == str(event.get('state') or '') and prev != current:
                _fire(trigger)

        # webhook events are dispatched by fire_webhook_key(), never polled.


def _fire(trigger: Dict[str, Any]) -> Tuple[bool, str]:
    """Run the trigger's action and broadcast ``trigger_fired``.

    Everything is wrapped — a trigger can fail, it can never kill the loop.
    """
    try:
        ok, detail = _run_action(trigger.get('action') or {})
    except Exception as e:
        logger.error('Trigger %s action raised: %s', trigger.get('id'), e)
        ok, detail = False, str(e)[:300]
    _emit_event('trigger_fired', {
        'id': trigger.get('id'),
        'label': trigger.get('label') or '',
        'ok': ok,
        'detail': detail,
        'ts': time.time(),
    })
    return ok, detail


def _run_action(action: Dict[str, Any]) -> Tuple[bool, str]:
    """Dispatch one action; returns (ok, human-readable detail)."""
    atype = action.get('type')

    if atype == ACTION_EXECUTE:
        executor = _executor
        if executor is None:
            return False, 'No action executor wired'
        result = executor.execute_action(action.get('action') or {})
        if isinstance(result, dict):
            return bool(result.get('success')), str(result.get('message') or '')[:300]
        return bool(getattr(result, 'success', False)), \
            str(getattr(result, 'message', '') or '')[:300]

    # Emit-based actions report honestly when nothing is listening — a
    # test-fire on an unwired backend should not claim success.
    if _emit is None:
        return False, 'No socket emitter wired'

    if atype == ACTION_SCENE:
        scene = str(action.get('scene') or '')
        _emit_event('navigate_scene', {'scene': scene})
        return True, f'navigate_scene → {scene}'

    if atype == ACTION_NOTIFY:
        _emit_event('panel_notification', {
            'source': 'trigger',
            'title': str(action.get('title') or '')[:80],
            'message': str(action.get('message') or '')[:300],
            'ts': time.time(),
        })
        return True, 'panel_notification sent'

    return False, f'Unknown action type: {atype}'


def fire_trigger(trigger_id: str) -> Optional[Tuple[bool, str]]:
    """Fire right now regardless of ``enabled`` — the test endpoint's seam.

    Returns None when the id is unknown.
    """
    trigger = get_trigger(trigger_id)
    if trigger is None:
        return None
    return _fire(trigger)


def fire_webhook_key(key: str) -> int:
    """Fire every enabled webhook trigger bound to ``key``; returns count."""
    with _lock:
        _load_locked()
        if not _engine_enabled:
            return 0
        targets = [
            t for t in _triggers.values()
            if t.get('enabled', True)
            and (t.get('event') or {}).get('type') == EVENT_WEBHOOK
            and (t.get('event') or {}).get('key') == key
        ]
    for trigger in targets:
        _fire(trigger)
    return len(targets)
