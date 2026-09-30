"""MCP server endpoint — JSON-RPC 2.0 over a single POST route (DL-121).

This is the POST subset of MCP's Streamable HTTP transport: one endpoint
(``POST /api/mcp``) carrying JSON-RPC 2.0 messages, with batch arrays
supported. There is deliberately no SSE stream and no stdio mode — VDock is
a Werkzeug threading app, and tool clients only need ``initialize``,
``tools/list`` and ``tools/call``. ``GET`` answers a clean 405 instead of
Flask's default HTML page, because some clients probe it for SSE.

Access mirrors the agent-hooks surface: localhost-only by default, plus a
``Bearer`` JWT escape hatch when ``Config.REQUIRE_AUTH`` is on — that is the
supported way to run an MCP client on another machine.

The action executor and socket emitter are injected via
``set_executor``/``set_emitter`` (same pattern as ``services.job_runner``)
because importing ``app`` here would be circular. Tools that need them
return an ``isError`` result while unwired rather than raising.
"""
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import Blueprint, Response, jsonify, request

from auth import AuthManager
from config import Config
from integrations import agent_state
from utils import FileManager
from actions.cross_platform_action import (
    CrossPlatformAction, read_output_volume)

logger = logging.getLogger('vdock')

mcp_bp = Blueprint('mcp', __name__)

#: The transport speaks this MCP protocol revision.
PROTOCOL_VERSION = '2025-06-18'
#: Mirrors the version ``/api/health`` reports; app.py owns the canonical
#: string but cannot be imported here (circular).
SERVER_VERSION = '2.1.0'
SERVER_NAME = 'vdock'

ERR_PARSE = -32700
ERR_INVALID_REQUEST = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL = -32603

# ---------------------------------------------------------------------------
# Injected seams (app.py wires these; tests inject fakes)
# ---------------------------------------------------------------------------

_emitter: Optional[Callable[[str, Dict[str, Any]], None]] = None
_executor: Optional[Any] = None


def set_emitter(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    """Provide the Socket.IO broadcast function (``socketio.emit``)."""
    global _emitter
    _emitter = fn


def set_executor(executor: Any) -> None:
    """Provide the action executor — the real ActionExecutor, or any
    callable taking ``{'type', 'config'}`` and returning an ActionResult."""
    global _executor
    _executor = executor


def _emit(event_name: str, payload: Dict[str, Any]) -> bool:
    if _emitter is None:
        return False
    try:
        _emitter(event_name, payload)
        return True
    except Exception as error:  # pragma: no cover - defensive
        logger.error('Failed to broadcast %s: %s', event_name, error)
        return False


def _run_action(action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one action through the injected executor; dict result out."""
    if _executor is None:
        raise _ToolUnavailable('Action executor is not wired (set_executor)')
    fn = getattr(_executor, 'execute_action', None)
    if fn is None:
        fn = _executor if callable(_executor) else None
    if fn is None:
        raise _ToolUnavailable('Injected executor is not callable')
    result = fn(action_data)
    if hasattr(result, 'to_dict'):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    return {'success': bool(result), 'message': str(result)}


class _ToolUnavailable(Exception):
    """A seam the tool needs was never injected — report, don't crash."""


class _ToolInputError(Exception):
    """Bad tool arguments — surfaces as an isError result, not -32602."""


# ---------------------------------------------------------------------------
# Profile scanning — profiles are JSON files under Config.PROFILES_DIR
# ---------------------------------------------------------------------------

def _load_profiles() -> List[Tuple[Any, Dict[str, Any]]]:
    """(path, profile dict) for every parseable profile file, sorted."""
    profiles = []
    for path in sorted(FileManager.list_files(Config.PROFILES_DIR, '*.json')):
        data = FileManager.load_json(path)
        if isinstance(data, dict):
            profiles.append((path, data))
    return profiles


def _active_profile(
        profiles: List[Tuple[Any, Dict[str, Any]]]
) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """The profile the panel is showing.

    ``activeProfileId`` in user_settings.json is authoritative (the last
    profile any device loaded); fall back to a profile holding an
    ``isActive`` scene, then to the first file.
    """
    settings = FileManager.load_json(Config.DATA_DIR / 'user_settings.json')
    wanted = (settings or {}).get('activeProfileId')
    if wanted:
        for path, profile in profiles:
            if wanted in (profile.get('id'), path.stem):
                return path, profile
    for path, profile in profiles:
        scenes = profile.get('scenes')
        if isinstance(scenes, list) and any(
                isinstance(s, dict) and s.get('isActive') for s in scenes):
            return path, profile
    return profiles[0] if profiles else (None, None)


def _ordered_profiles(
        profiles: List[Tuple[Any, Dict[str, Any]]]
) -> List[Tuple[Any, Dict[str, Any]]]:
    """Active profile first — lookups prefer the deck the user is seeing."""
    _path, active = _active_profile(profiles)
    if active is None:
        return profiles
    rest = [(p, d) for p, d in profiles if d is not active]
    return [(next(p for p, d in profiles if d is active), active)] + rest


def _walk_buttons(profile: Dict[str, Any]):
    """Yield (button, scene_name, page_name) across a profile.

    Covers the scenes→pages→buttons tree, the legacy top-level ``pages``
    list, and ``dockedButtons`` so press_button can reach every pressable
    surface in the file.
    """
    for scene in profile.get('scenes') or []:
        if not isinstance(scene, dict):
            continue
        scene_name = str(scene.get('name') or '')
        for page in scene.get('pages') or []:
            if not isinstance(page, dict):
                continue
            for button in page.get('buttons') or []:
                if isinstance(button, dict):
                    yield button, scene_name, str(page.get('name') or '')
    for page in profile.get('pages') or []:
        if not isinstance(page, dict):
            continue
        for button in page.get('buttons') or []:
            if isinstance(button, dict):
                yield button, None, str(page.get('name') or '')
    for button in profile.get('dockedButtons') or []:
        if isinstance(button, dict):
            yield button, 'docked', 'docked'


def _find_scene(profile: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    """Case-insensitive scene match against name or id."""
    wanted = str(name).strip().lower()
    for scene in profile.get('scenes') or []:
        if not isinstance(scene, dict):
            continue
        if str(scene.get('name') or '').strip().lower() == wanted \
                or str(scene.get('id') or '') == name:
            return scene
    return None


def _matches(button: Dict[str, Any], target: str) -> bool:
    wanted = str(target).strip().lower()
    return str(button.get('id') or '') == str(target) \
        or str(button.get('label') or '').strip().lower() == wanted


def _resolve_button(args: Dict[str, Any]):
    """Find the button to press. Returns (profile, scene, page, button)
    or raises _ToolInputError."""
    profiles = _ordered_profiles(_load_profiles())
    if not profiles:
        raise _ToolInputError('No profiles found under Config.PROFILES_DIR')

    button_id = args.get('button_id')
    scene_name = args.get('scene')
    target = args.get('button')

    if button_id:
        for _path, profile in profiles:
            for button, scene, page in _walk_buttons(profile):
                if str(button.get('id') or '') == str(button_id):
                    return profile, scene, page, button
        raise _ToolInputError(f'No button with id {button_id!r}')

    if scene_name is not None:
        if target is None:
            raise _ToolInputError(
                "'button' (id or label) is required with 'scene'")
        for _path, profile in profiles:
            scene = _find_scene(profile, scene_name)
            if scene is None:
                continue
            for page in scene.get('pages') or []:
                if not isinstance(page, dict):
                    continue
                for button in page.get('buttons') or []:
                    if isinstance(button, dict) and _matches(button, target):
                        return (profile, str(scene.get('name') or ''),
                                str(page.get('name') or ''), button)
            raise _ToolInputError(
                f'No button matching {target!r} in scene {scene_name!r}')
        raise _ToolInputError(f'No scene matching {scene_name!r}')

    if target is not None:
        for _path, profile in profiles:
            for button, scene, page in _walk_buttons(profile):
                if _matches(button, target):
                    return profile, scene, page, button
        raise _ToolInputError(f'No button matching {target!r}')

    raise _ToolInputError(
        "press_button needs 'button_id', or 'button' (optionally with 'scene')")


# ---------------------------------------------------------------------------
# Tool implementations — each returns (payload, is_error)
# ---------------------------------------------------------------------------

def _tool_deck_info(_args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    profiles = _load_profiles()
    _path, active = _active_profile(profiles)
    if active is None:
        return {'version': SERVER_VERSION, 'profile': None, 'scenes': 0,
                'buttons': 0, 'active_scene': None,
                'profiles': []}, False
    scenes = [s for s in active.get('scenes') or [] if isinstance(s, dict)]
    button_count = sum(1 for _b, _s, _p in _walk_buttons(active))
    active_scene = next(
        (str(s.get('name') or '') for s in scenes if s.get('isActive')), None)
    return {
        'version': SERVER_VERSION,
        'profile': {'id': active.get('id'), 'name': active.get('name')},
        'scenes': len(scenes),
        'buttons': button_count,
        'active_scene': active_scene,
        'profiles': [p.get('name') for _f, p in profiles],
    }, False


def _tool_list_scenes(_args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    _path, active = _active_profile(_load_profiles())
    if active is None:
        return {'scenes': [], 'profile': None}, False
    scenes = []
    for scene in active.get('scenes') or []:
        if not isinstance(scene, dict):
            continue
        pages = [str(p.get('name') or '') for p in scene.get('pages') or []
                 if isinstance(p, dict)]
        scenes.append({
            'name': scene.get('name'),
            'page_count': len(pages),
            'pages': pages,
            'active': bool(scene.get('isActive')),
        })
    return {'profile': active.get('name'), 'scenes': scenes}, False


def _tool_list_buttons(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    _path, active = _active_profile(_load_profiles())
    if active is None:
        return {'buttons': [], 'profile': None}, False
    scene_filter = args.get('scene')
    if scene_filter is not None \
            and _find_scene(active, scene_filter) is None:
        return {'error': f'No scene matching {scene_filter!r}',
                'profile': active.get('name'), 'buttons': []}, True
    buttons = []
    for button, scene, page in _walk_buttons(active):
        if scene_filter is not None and (
                scene is None
                or scene.strip().lower() != str(scene_filter).strip().lower()):
            continue
        action = button.get('action') or {}
        buttons.append({
            'id': button.get('id'),
            'label': button.get('label'),
            'scene': scene,
            'page': page,
            'enabled': button.get('enabled', True),
            'action': {'type': action.get('type')},
        })
    return {'profile': active.get('name'), 'buttons': buttons}, False


def _tool_press_button(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    _profile, scene, page, button = _resolve_button(args)
    if button.get('enabled') is False:
        return {'error': 'Button is disabled',
                'button': {'id': button.get('id'),
                           'label': button.get('label')}}, True
    action = button.get('action') or {}
    if not action.get('type'):
        return {'error': 'Button has no action configured',
                'button': {'id': button.get('id'),
                           'label': button.get('label')}}, True
    result = _run_action(action)
    return {
        'button': {'id': button.get('id'), 'label': button.get('label'),
                   'scene': scene, 'page': page},
        'action_type': action.get('type'),
        'result': result,
    }, not result.get('success')


def _tool_run_action(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    action = args.get('action')
    if not isinstance(action, dict) or not action.get('type'):
        raise _ToolInputError("run_action needs arguments.action {type, config}")
    result = _run_action(action)
    return {'action_type': action.get('type'), 'result': result}, \
        not result.get('success')


def _tool_switch_scene(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    scene = args.get('scene')
    if not isinstance(scene, str) or not scene.strip():
        raise _ToolInputError("switch_scene needs arguments.scene")
    sent = _emit('navigate_scene', {'scene': scene})
    if not sent:
        return {'error': 'Socket emitter is not wired (set_emitter)',
                'scene': scene}, True
    # The panel's frontend store performs the switch — delivery is async.
    return {'scene': scene, 'delivered': True,
            'note': 'Scene switch is asynchronous; the panel applies it '
                    'when the navigate_scene event arrives.'}, False


def _tool_show_notification(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    title = args.get('title')
    message = args.get('message')
    if not isinstance(title, str) or not title.strip():
        raise _ToolInputError("show_notification needs arguments.title")
    if not isinstance(message, str):
        message = '' if message is None else str(message)
    payload = {
        'source': 'mcp',
        'title': title.strip()[:80],
        'message': message[:300],
        'ts': time.time(),
    }
    sent = _emit('panel_notification', payload)
    if not sent:
        return {'error': 'Socket emitter is not wired (set_emitter)'}, True
    return {'delivered': True, 'notification': payload}, False


def _tool_get_volume(_args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    try:
        value, muted, err = read_output_volume()
    except Exception as error:
        return {'error': f'Volume read failed: {error}'}, True
    if value is None:
        return {'error': err or 'Volume read unavailable'}, True
    return {'value': value, 'muted': bool(muted) if muted is not None else None}, \
        False


def _tool_set_volume(args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    raw = args.get('value')
    try:
        value = max(0, min(100, int(float(raw))))
    except (TypeError, ValueError):
        raise _ToolInputError("set_volume needs arguments.value (0-100)")
    # No module-level setter exists in cross_platform_action — the write
    # path is the volume_set action (COM worker on Windows, osascript/
    # amixer elsewhere). Instantiating it directly keeps this tool working
    # even before the executor is injected.
    try:
        result = CrossPlatformAction(
            {'action': 'volume_set', 'value': value}).execute()
    except Exception as error:
        return {'error': f'Volume set failed: {error}'}, True
    return {'requested': value, 'result': result.to_dict()}, \
        not result.success


def _tool_get_now_playing(_args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Last SMTC snapshot from the now_playing monitor (W1, DL-116).

    The module may not exist yet at dev time — the monitor idles inert on
    machines without media support either way, so 'unavailable' is an
    honest answer, not an error the caller must special-case.
    """
    module = _now_playing_module()
    if module is None:
        return {'available': False, 'track': None,
                'error': 'now_playing service unavailable'}, True
    # Agreed contract was latest() → last payload dict or None; W1 shipped
    # snapshot()/latest_track() instead — accept whichever exists.
    reader = next(
        (getattr(module, name) for name in ('latest', 'snapshot', 'latest_track')
         if callable(getattr(module, name, None))), None)
    if reader is None:
        # Without a snapshot getter the /api/now-playing shape says
        # track:null ≡ nothing playing.
        return {'available': True, 'track': None, 'playing': False}, False
    try:
        track = reader()
    except Exception as error:
        return {'available': False, 'track': None,
                'error': f'now_playing read failed: {error}'}, True
    available_fn = getattr(module, 'available', None)
    try:
        available = bool(available_fn()) if callable(available_fn) else True
    except Exception:
        available = True
    if not isinstance(track, dict):
        return {'available': available, 'track': None, 'playing': False}, False
    return {'available': available, 'track': track,
            'playing': bool(track.get('playing'))}, False


def _now_playing_module():
    """Import services.now_playing lazily — W1 ships it in parallel."""
    global _now_playing
    if _now_playing is None:
        try:
            from services import now_playing as module
        except Exception:
            module = False  # import attempted and failed — stop retrying
        _now_playing = module
    return _now_playing or None


_now_playing: Any = None


def _tool_get_agent_states(_args: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    try:
        return {'states': agent_state.snapshot()}, False
    except Exception as error:
        return {'error': f'Agent state unavailable: {error}'}, True


# ---------------------------------------------------------------------------
# Tool registry (name → description, inputSchema, handler)
# ---------------------------------------------------------------------------

_TOOL_DEFS: List[Tuple[str, str, Dict[str, Any], Callable]] = [
    ('deck_info',
     'VDock backend version plus scene/button counts of the active profile.',
     {'type': 'object', 'properties': {}},
     _tool_deck_info),
    ('list_scenes',
     'List the scenes in the active profile (name, pages, active flag).',
     {'type': 'object', 'properties': {}},
     _tool_list_scenes),
    ('list_buttons',
     'List deck buttons of the active profile, optionally filtered to one '
     'scene. Returns id, label, scene, page and the action type.',
     {'type': 'object', 'properties': {
         'scene': {'type': 'string',
                   'description': 'Scene name to filter by (optional)'}}},
     _tool_list_buttons),
    ('press_button',
     'Execute a deck button\'s action. Identify it by button_id, or by '
     'button (label or id) optionally scoped to a scene name.',
     {'type': 'object', 'properties': {
         'button_id': {'type': 'string',
                       'description': 'Exact button id'},
         'button': {'type': 'string',
                    'description': 'Button label or id'},
         'scene': {'type': 'string',
                   'description': 'Scene name to look in (optional)'}},
      'anyOf': [{'required': ['button_id']}, {'required': ['button']}]},
     _tool_press_button),
    ('run_action',
     'Execute a raw VDock action {type, config} — same shape deck buttons '
     'store (e.g. {"type":"cross_platform","config":{"action":"volume_up"}}).',
     {'type': 'object',
      'properties': {'action': {'type': 'object'}},
      'required': ['action']},
     _tool_run_action),
    ('switch_scene',
     'Ask the panel to switch to a named scene. Asynchronous: the frontend '
     'store applies the navigate_scene event.',
     {'type': 'object',
      'properties': {'scene': {'type': 'string'}},
      'required': ['scene']},
     _tool_switch_scene),
    ('show_notification',
     'Show a notification on the panel (toast + notification-center entry).',
     {'type': 'object',
      'properties': {'title': {'type': 'string'},
                     'message': {'type': 'string'}},
      'required': ['title', 'message']},
     _tool_show_notification),
    ('get_volume',
     'Current default output volume (0-100) and mute state.',
     {'type': 'object', 'properties': {}},
     _tool_get_volume),
    ('set_volume',
     'Set the default output volume (0-100).',
     {'type': 'object',
      'properties': {'value': {'type': 'number', 'minimum': 0,
                               'maximum': 100}},
      'required': ['value']},
     _tool_set_volume),
    ('get_now_playing',
     'Current media track from the system now-playing monitor (SMTC).',
     {'type': 'object', 'properties': {}},
     _tool_get_now_playing),
    ('get_agent_states',
     'Live state of every coding agent reporting to VDock (claude, cursor, '
     '…): ready / working / permission + last prompt/reply.',
     {'type': 'object', 'properties': {}},
     _tool_get_agent_states),
]

_TOOLS_BY_NAME = {name: handler for name, _d, _s, handler in _TOOL_DEFS}


def _tools_payload() -> Dict[str, Any]:
    return {'tools': [
        {'name': name, 'description': description, 'inputSchema': schema}
        for name, description, schema, _handler in _TOOL_DEFS
    ]}


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 dispatch
# ---------------------------------------------------------------------------

class _MethodNotFound(Exception):
    pass


class _InvalidParams(Exception):
    pass


def _dispatch(method: str, params: Any) -> Any:
    """Run one method; returns the result payload for a request."""
    if method.startswith('notifications/'):
        return None
    if method == 'initialize':
        return {
            'protocolVersion': PROTOCOL_VERSION,
            'capabilities': {'tools': {'listChanged': False}},
            'serverInfo': {'name': SERVER_NAME, 'version': SERVER_VERSION},
        }
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return _tools_payload()
    if method == 'tools/call':
        return _call_tool(params)
    raise _MethodNotFound(method)


def _call_tool(params: Any) -> Dict[str, Any]:
    if not isinstance(params, dict):
        raise _InvalidParams(
            'tools/call needs params {name, arguments?}')
    name = params.get('name')
    if not isinstance(name, str) or not name:
        raise _InvalidParams('tools/call needs params.name (string)')
    arguments = params.get('arguments', {})
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise _InvalidParams('params.arguments must be an object')
    handler = _TOOLS_BY_NAME.get(name)
    if handler is None:
        raise _InvalidParams(f'Unknown tool: {name}')
    try:
        payload, is_error = handler(arguments)
    except (_ToolInputError,) as error:
        payload, is_error = {'error': str(error)}, True
    except _ToolUnavailable as error:
        payload, is_error = {'error': str(error), 'unavailable': True}, True
    text = json.dumps(payload, indent=2, default=str)
    return {'content': [{'type': 'text', 'text': text}],
            'structuredContent': payload, 'isError': is_error}


def _valid_id(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float))


def _error(msg_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': msg_id,
            'error': {'code': code, 'message': message}}


def _handle_message(msg: Any) -> Optional[Dict[str, Any]]:
    """One JSON-RPC message → response object, or None for notifications."""
    if not isinstance(msg, dict):
        return _error(None, ERR_INVALID_REQUEST, 'Invalid Request')
    msg_id = msg.get('id')
    if not _valid_id(msg_id):
        msg_id = None
    method = msg.get('method')
    if msg.get('jsonrpc') != '2.0' or not isinstance(method, str):
        return _error(msg_id, ERR_INVALID_REQUEST, 'Invalid Request')

    is_notification = 'id' not in msg
    try:
        result = _dispatch(method, msg.get('params'))
    except _MethodNotFound as error:
        if is_notification:
            return None
        return _error(msg_id, ERR_METHOD_NOT_FOUND,
                      f'Method not found: {error}')
    except _InvalidParams as error:
        if is_notification:
            return None
        return _error(msg_id, ERR_INVALID_PARAMS, str(error))
    except Exception as error:  # a tool raising is a transport-level fault
        logger.exception('MCP method %s failed', method)
        if is_notification:
            return None
        return _error(msg_id, ERR_INTERNAL, f'Internal error: {error}')
    if is_notification:
        return None
    return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _rpc_response(body: Any, status: int = 200) -> Response:
    """Response with a literal JSON body — batch results are top-level
    arrays, which Flask's jsonify historically refused."""
    return Response(json.dumps(body), status=status,
                    mimetype='application/json')


# ---------------------------------------------------------------------------
# Access + route
# ---------------------------------------------------------------------------

def _localhost_only() -> bool:
    """Accept calls only from the machine VDock runs on."""
    return request.remote_addr in ('127.0.0.1', '::1', 'localhost')


def _bearer_ok() -> bool:
    """Valid Bearer JWT — the auth escape hatch for remote MCP clients."""
    header = request.headers.get('Authorization') or ''
    parts = header.split(' ')
    if len(parts) != 2 or parts[0] != 'Bearer' or not parts[1]:
        return False
    return AuthManager.verify_token(parts[1]) is not None


def _mcp_enabled() -> bool:
    """Settings → Integrations → "Enable MCP server" switch.

    The toggle lives in the regular user-settings file the panel syncs;
    absent/corrupt settings mean the default — on.
    """
    raw = FileManager.load_json(Config.DATA_DIR / 'user_settings.json') or {}
    return bool(raw.get('mcpEnabled', True))


@mcp_bp.route('/api/mcp', methods=['GET', 'POST'])
def mcp_endpoint():
    """Single MCP endpoint: JSON-RPC 2.0 over HTTP POST."""
    if not _localhost_only():
        if not Config.REQUIRE_AUTH:
            return jsonify({'success': False, 'error': 'Localhost only'}), 403
        if not _bearer_ok():
            return jsonify(
                {'success': False,
                 'error': 'Bearer token required'}), 401

    if request.method == 'POST' and not _mcp_enabled():
        return jsonify({'success': False,
                        'error': 'MCP server is disabled '
                                 '(Settings → Integrations)'}), 503

    if request.method == 'GET':
        response = jsonify({'error': 'POST only — this endpoint speaks '
                                     'JSON-RPC 2.0 over HTTP POST'})
        response.status_code = 405
        response.headers['Allow'] = 'POST'
        return response

    try:
        payload = json.loads(request.get_data() or b'')
    except (ValueError, TypeError):
        return _rpc_response(_error(None, ERR_PARSE, 'Parse error'))

    if isinstance(payload, list):
        if not payload:
            return _rpc_response(
                _error(None, ERR_INVALID_REQUEST, 'Invalid Request'))
        replies = [reply for reply in
                   (_handle_message(msg) for msg in payload)
                   if reply is not None]
        # Batch of pure notifications → acknowledge with no body.
        if not replies:
            return Response(status=202)
        return _rpc_response(replies)

    reply = _handle_message(payload)
    if reply is None:  # a lone notification
        return Response(status=202)
    return _rpc_response(reply)
