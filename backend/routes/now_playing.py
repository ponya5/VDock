"""Now-playing (SMTC) routes, backed by services/now_playing.py.

The socket event pushes changes; these endpoints re-sync a freshly loaded
or reconnected client and serve the cached album art the payload's
``has_art`` flag only points at (contract: collab/contracts/rest-api.md).
"""
from flask import Blueprint, jsonify, send_file

from auth import require_auth
from services import now_playing

now_playing_bp = Blueprint('now_playing', __name__, url_prefix='/api')


@now_playing_bp.route('/now-playing', methods=['GET'])
@require_auth
def get_now_playing():
    """Current SMTC snapshot.

    ``available: false`` means the host can't answer (no winsdk / not
    Windows); ``track: null`` means it can but nothing is playing.
    """
    return jsonify({
        'success': True,
        'available': now_playing.available(),
        'track': now_playing.latest_track(),
    })


@now_playing_bp.route('/now-playing/art', methods=['GET'])
@require_auth
def get_now_playing_art():
    """The current track's cached album art — 404 when there is none."""
    path = now_playing.art_path()
    if not path.is_file():
        return jsonify({'success': False, 'error': 'No album art'}), 404
    return send_file(str(path), mimetype=now_playing.art_mime())
