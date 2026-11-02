"""In-app update endpoints (DL-150): release status + one-tap install."""
from flask import Blueprint, jsonify, request

from auth import AuthManager
from config import Config
from services import updater

update_bp = Blueprint('update', __name__)


def _is_local_request() -> bool:
    return request.remote_addr in ('127.0.0.1', '::1', 'localhost')


def _bearer_ok() -> bool:
    header = request.headers.get('Authorization') or ''
    parts = header.split(' ')
    if len(parts) != 2 or parts[0] != 'Bearer' or not parts[1]:
        return False
    return AuthManager.verify_token(parts[1]) is not None


@update_bp.route('/api/update/status', methods=['GET'])
def update_status():
    force = request.args.get('force') in ('1', 'true')
    return jsonify(updater.get_status(force=force))


def _may_install() -> bool:
    return _is_local_request() or (Config.REQUIRE_AUTH and _bearer_ok())


def _forbidden():
    return jsonify({'error': 'Updates can only be installed from the PC VDock runs on, '
                             'or by a signed-in device.'}), 403


@update_bp.route('/api/update/install', methods=['POST'])
def update_install():
    if not _may_install():
        return _forbidden()
    started, reason = updater.begin_install()
    if not started:
        message = ('An update is already in progress.' if reason == 'busy'
                   else 'No update available to install.')
        return jsonify({'error': message, 'state': updater.get_state()['state']}), 409
    return jsonify({'state': updater.DOWNLOADING}), 202


@update_bp.route('/api/update/restart', methods=['POST'])
def update_restart():
    if not _may_install():
        return _forbidden()
    started, _reason = updater.begin_restart()
    if not started:
        return jsonify({'error': 'No update is ready to apply.',
                        'state': updater.get_state()['state']}), 409
    return jsonify({'state': updater.RESTARTING}), 202
