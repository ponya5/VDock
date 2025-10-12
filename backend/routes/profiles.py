"""Profile management routes."""
from flask import Blueprint, request, jsonify
from pathlib import Path
import uuid

from config import Config
from models import Profile, Page, ProfileSettings
from utils import FileManager
from auth import require_auth

profiles_bp = Blueprint('profiles', __name__)


@profiles_bp.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Get all profiles."""
    profile_files = FileManager.list_files(Config.PROFILES_DIR, '*.json')
    profiles = []
    
    for file_path in profile_files:
        profile_data = FileManager.load_json(file_path)
        if profile_data:
            try:
                profile = Profile.from_dict(profile_data)
                profiles.append({
                    'id': profile.id,
                    'name': profile.name,
                    'description': profile.description,
                    'icon': profile.icon,
                    'theme': profile.theme,
                    'page_count': len(profile.pages)
                })
            except Exception as e:
                from utils import setup_logger
                logger = setup_logger('vdock')
                logger.error(f"Error loading profile {file_path}: {e}")
    
    return jsonify({'profiles': profiles})


@profiles_bp.route('/api/profiles/<profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get a specific profile."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    profile_data = FileManager.load_json(file_path)
    
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        return jsonify({'profile': profile.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profiles_bp.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create a new profile."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided', 'success': False}), 400
    
    profile_id = str(uuid.uuid4())
    timestamp = FileManager.get_timestamp()
    
    # Create default page
    default_page = Page(
        id=str(uuid.uuid4()),
        name='Page 1',
        buttons=[],
        grid_config={'rows': 3, 'cols': 5}
    )
    
    profile = Profile(
        id=profile_id,
        name=data.get('name', 'New Profile'),
        description=data.get('description', ''),
        icon=data.get('icon'),
        avatar=data.get('avatar'),
        pages=[default_page],
        theme=data.get('theme', 'default'),
        settings=ProfileSettings(),
        created_at=timestamp,
        updated_at=timestamp
    )
    
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    if FileManager.save_json(file_path, profile.to_dict()):
        return jsonify({'profile': profile.to_dict(), 'success': True}), 201
    
    return jsonify({'error': 'Failed to create profile', 'success': False}), 500


@profiles_bp.route('/api/profiles/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update an existing profile."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided', 'success': False}), 400
    
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    # Load existing profile
    profile_data = FileManager.load_json(file_path)
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        
        # Update fields
        profile.name = data.get('name', profile.name)
        profile.description = data.get('description', profile.description)
        profile.icon = data.get('icon', profile.icon)
        profile.avatar = data.get('avatar', profile.avatar)
        profile.theme = data.get('theme', profile.theme)
        profile.updated_at = FileManager.get_timestamp()
        
        # Update pages if provided
        if 'pages' in data:
            profile.pages = [Page.from_dict(p) for p in data['pages']]
        
        # Save
        if FileManager.save_json(file_path, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True})
        
        return jsonify({'error': 'Failed to save profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@profiles_bp.route('/api/profiles/<profile_id>', methods=['DELETE'])
@require_auth
def delete_profile(profile_id):
    """Delete a profile."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    if FileManager.delete_file(file_path):
        return jsonify({'success': True})
    
    return jsonify({'error': 'Failed to delete profile', 'success': False}), 500


@profiles_bp.route('/api/profiles/<profile_id>/duplicate', methods=['POST'])
@require_auth
def duplicate_profile(profile_id):
    """Duplicate an existing profile."""
    src_file = Config.PROFILES_DIR / f"{profile_id}.json"
    profile_data = FileManager.load_json(src_file)
    
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        
        # Create new profile with new ID
        new_id = str(uuid.uuid4())
        profile.id = new_id
        profile.name = f"{profile.name} (Copy)"
        profile.created_at = FileManager.get_timestamp()
        profile.updated_at = profile.created_at
        
        # Generate new IDs for pages and buttons
        for page in profile.pages:
            page.id = str(uuid.uuid4())
            for button in page.buttons:
                button.id = str(uuid.uuid4())
        
        dst_file = Config.PROFILES_DIR / f"{new_id}.json"
        if FileManager.save_json(dst_file, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True}), 201
        
        return jsonify({'error': 'Failed to duplicate profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@profiles_bp.route('/api/profiles/<profile_id>/export', methods=['GET'])
@require_auth
def export_profile(profile_id):
    """Export a profile as JSON."""
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    if not file_path.exists():
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile_data = FileManager.load_json(file_path)
        return jsonify({'profile': profile_data, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@profiles_bp.route('/api/profiles/import', methods=['POST'])
@require_auth
def import_profile():
    """Import a profile from JSON data."""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({'error': 'Invalid profile data', 'success': False}), 400
    
    try:
        # Generate new ID to avoid conflicts
        new_id = str(uuid.uuid4())
        data['id'] = new_id
        data['created_at'] = FileManager.get_timestamp()
        data['updated_at'] = FileManager.get_timestamp()
        
        # Validate profile structure
        profile = Profile.from_dict(data)
        
        # Save imported profile
        file_path = Config.PROFILES_DIR / f"{new_id}.json"
        if FileManager.save_json(file_path, profile.to_dict()):
            return jsonify({'profile': profile.to_dict(), 'success': True}), 201
        
        return jsonify({'error': 'Failed to save imported profile', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
