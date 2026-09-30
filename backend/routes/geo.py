"""Machine geolocation (public IP) — feeds the weather widget's automatic
mode on clients that can't self-locate, e.g. the panel's kiosk browser
where navigator.geolocation is denied."""
from flask import Blueprint, jsonify

from auth import require_auth
from services import geolocation

geo_bp = Blueprint('geo', __name__)


@geo_bp.route('/geo', methods=['GET'])
@require_auth
def get_geo():
    try:
        location = geolocation.resolve()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    return jsonify({'success': True, 'location': location})
