"""Trigger CRUD + webhook fire surface (DL-120).

``/api/triggers*`` manages the persistent trigger store in
``services/triggers.py``. Everything is authenticated except
``POST /api/triggers/fire/<key>`` — the webhook surface for local scripts,
agent hooks and Task Scheduler, which cannot carry UI tokens. Like
``/api/agent-events`` it is localhost-only instead.
"""
import logging
from typing import Any, Callable, Dict

from flask import Blueprint, jsonify, request

from auth import require_auth
from services import triggers

logger = logging.getLogger('vdock')

triggers_bp = Blueprint('triggers', __name__)


def set_emitter(fn: Callable[[str, Dict[str, Any]], None]) -> None:
    """Optional wiring point — forwards to the service's own emitter.

    The contract lists it on the route module so app.py can wire emit in
    one place; the service does the actual broadcasting.
    """
    triggers.set_emitter(fn)


def _localhost_only() -> bool:
    """Accept posts only from the machine VDock runs on."""
    return request.remote_addr in ('127.0.0.1', '::1', 'localhost')


@triggers_bp.route('/api/triggers', methods=['GET'])
@require_auth
def list_triggers():
    """All triggers, in creation order, plus the master switch state."""
    return jsonify({'success': True,
                    'enabled': triggers.is_enabled(),
                    'triggers': triggers.list_triggers()})


@triggers_bp.route('/api/triggers/enabled', methods=['PUT'])
@require_auth
def set_triggers_enabled():
    """Master pause switch — body {enabled: bool}."""
    data = request.get_json(silent=True) or {}
    enabled = triggers.set_enabled(bool(data.get('enabled', True)))
    return jsonify({'success': True, 'enabled': enabled})


@triggers_bp.route('/api/triggers', methods=['POST'])
@require_auth
def create_trigger():
    """Create a trigger. Body: {label?, enabled?, event, action}."""
    data = request.get_json(silent=True)
    try:
        trigger = triggers.add_trigger(data)
    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    return jsonify({'success': True, 'trigger': trigger})


@triggers_bp.route('/api/triggers/<trigger_id>', methods=['PUT'])
@require_auth
def update_trigger(trigger_id):
    """Partial update — label/enabled merge, event/action replace wholesale."""
    data = request.get_json(silent=True)
    try:
        trigger = triggers.update_trigger(trigger_id, data)
    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    if trigger is None:
        return jsonify({'success': False, 'error': 'Trigger not found'}), 404
    return jsonify({'success': True, 'trigger': trigger})


@triggers_bp.route('/api/triggers/<trigger_id>', methods=['DELETE'])
@require_auth
def delete_trigger(trigger_id):
    if not triggers.remove_trigger(trigger_id):
        return jsonify({'success': False, 'error': 'Trigger not found'}), 404
    return jsonify({'success': True})


@triggers_bp.route('/api/triggers/<trigger_id>/test', methods=['POST'])
@require_auth
def test_trigger(trigger_id):
    """Fire now, ignoring ``enabled`` — the panel's smoke-test button."""
    result = triggers.fire_trigger(trigger_id)
    if result is None:
        return jsonify({'success': False, 'error': 'Trigger not found'}), 404
    ok, detail = result
    return jsonify({'success': True, 'ok': ok, 'detail': detail})


@triggers_bp.route('/api/triggers/fire/<key>', methods=['POST'])
def fire_trigger_key(key):
    """Webhook intake — fires every enabled trigger bound to ``key``.

    Deliberately unauthenticated like ``/api/agent-events``: local webhook
    callers are shell scripts that cannot hold a UI token, so the surface
    is localhost-only instead.
    """
    if not _localhost_only():
        return jsonify({'success': False, 'error': 'Localhost only'}), 403
    fired = triggers.fire_webhook_key(key)
    return jsonify({'success': True, 'fired': fired})
