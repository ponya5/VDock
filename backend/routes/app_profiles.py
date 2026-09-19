"""App profile routes.

The frontend renders shortcut lists and context decks from this, rather than
from its own copy of the same data. Two databases of the same shortcuts drifted
once already.
"""
from flask import Blueprint, jsonify

from integrations import keymaps

app_profiles_bp = Blueprint('app_profiles', __name__)


@app_profiles_bp.route('/api/app-profiles', methods=['GET'])
def get_app_profiles():
    """Every known application, its commands, and its default deck layout."""
    return jsonify({
        'success': True,
        'profiles': [profile.to_dict() for profile in keymaps.ALL_PROFILES],
    })
