"""Profile management routes."""
from flask import Blueprint, request, jsonify
import uuid
import logging

from config import Config
from models import Profile, Page, ProfileSettings, Scene, Button
from utils import FileManager
from auth import require_auth

logger = logging.getLogger('vdock')

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
                profile_data = {
                    'id': profile.id,
                    'name': profile.name,
                    'description': profile.description,
                    'theme': profile.theme,
                    'page_count': len(profile.pages)
                }
                
                # Only include optional fields if they have values
                if profile.icon is not None:
                    profile_data['icon'] = profile.icon
                if profile.avatar is not None:
                    profile_data['avatar'] = profile.avatar
                    
                profiles.append(profile_data)
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
    
    # Create default scene
    default_scene = Scene(
        id=str(uuid.uuid4()),
        name='Scene 1',
        icon='home',
        color='#3498db',
        pages=[default_page],
        isActive=True,
        buttonSize=1.0
    )
    
    profile = Profile(
        id=profile_id,
        name=data.get('name', 'New Profile'),
        description=data.get('description', ''),
        icon=data.get('icon') if data.get('icon') else None,
        avatar=data.get('avatar') if data.get('avatar') else None,
        pages=[default_page],  # Backward compatibility
        scenes=[default_scene],  # New scenes structure
        dockedButtons=[],  # Initialize empty docked buttons
        theme=data.get('theme', 'default'),
        settings=ProfileSettings(),
        created_at=timestamp,
        updated_at=timestamp
    )
    
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    if FileManager.save_json(file_path, profile.to_dict()):
        return jsonify({'profile': profile.to_dict(), 'success': True}), 201
    
    return jsonify({
        'error': 'Failed to create profile',
        'success': False
    }), 500


@profiles_bp.route('/api/profiles/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update an existing profile."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided', 'success': False}), 400
    
    logger.info(f"Updating profile {profile_id}")
    logger.info(f"Received data keys: {list(data.keys())}")
    logger.info(f"dockedButtons in data: {'dockedButtons' in data}")
    if 'dockedButtons' in data:
        logger.info(f"dockedButtons count: {len(data['dockedButtons'])}")
    
    file_path = Config.PROFILES_DIR / f"{profile_id}.json"
    
    # Load existing profile
    profile_data = FileManager.load_json(file_path)
    if not profile_data:
        return jsonify({'error': 'Profile not found'}), 404
    
    try:
        profile = Profile.from_dict(profile_data)
        logger.info(
            f"Loaded profile, existing dockedButtons: "
            f"{len(profile.dockedButtons)}"
        )
        
        # Update fields
        profile.name = data.get('name', profile.name)
        profile.description = data.get('description', profile.description)
        profile.icon = data.get('icon', profile.icon)
        profile.avatar = data.get('avatar', profile.avatar)
        profile.theme = data.get('theme', profile.theme)
        profile.updated_at = FileManager.get_timestamp()
        
        # Update pages if provided (backward compatibility)
        if 'pages' in data:
            profile.pages = [Page.from_dict(p) for p in data['pages']]
        
        # Update scenes if provided
        if 'scenes' in data:
            profile.scenes = [Scene.from_dict(s) for s in data['scenes']]
            logger.info(f"Updated scenes, count: {len(profile.scenes)}")
        
        # Update docked buttons if provided
        if 'dockedButtons' in data:
            profile.dockedButtons = [
                Button.from_dict(b) for b in data['dockedButtons']
            ]
            logger.info(
                f"Updated dockedButtons, count: {len(profile.dockedButtons)}"
            )
        
        # Save
        profile_dict = profile.to_dict()
        docked_count = len(profile_dict.get('dockedButtons', []))
        scenes_count = len(profile_dict.get('scenes', []))
        logger.info(f"Profile dict dockedButtons count: {docked_count}")
        logger.info(f"Profile dict scenes count: {scenes_count}")
        
        if FileManager.save_json(file_path, profile_dict):
            logger.info("Profile saved successfully")
            return jsonify({
                'profile': profile_dict,
                'success': True
            })
        
        return jsonify({
            'error': 'Failed to save profile',
            'success': False
        }), 500
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
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
