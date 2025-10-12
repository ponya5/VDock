"""File upload routes."""
from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import uuid
import os

from config import Config
from auth import require_auth

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/api/upload/icon', methods=['POST'])
@require_auth
def upload_icon():
    """Upload a custom icon."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided', 'success': False}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected', 'success': False}), 400
    
    # Validate file type
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.svg', '.gif'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type', 'success': False}), 400
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    filepath = Config.UPLOADS_DIR / filename
    
    try:
        file.save(filepath)
        return jsonify({
            'filename': filename,
            'url': f'/api/uploads/{filename}',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@upload_bp.route('/api/upload/media', methods=['POST'])
@require_auth
def upload_media():
    """Upload a media file (GIF/video) for button backgrounds."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided', 'success': False}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected', 'success': False}), 400
    
    # Get profile ID from request
    profile_id = request.form.get('profile_id')
    if not profile_id:
        return jsonify({'error': 'Profile ID required', 'success': False}), 400
    
    # Validate file type
    allowed_extensions = {'.gif', '.mp4', '.webm', '.mov', '.avi', '.png', '.jpg', '.jpeg'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: GIF, MP4, WebM, MOV, AVI, PNG, JPG, JPEG', 'success': False}), 400
    
    # Check file size (5MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file_size > max_size:
        return jsonify({'error': f'File too large. Maximum size is 5MB, got {file_size / (1024*1024):.1f}MB', 'success': False}), 400
    
    # Determine media type
    media_type = 'image'
    if file_ext in {'.gif'}:
        media_type = 'gif'
    elif file_ext in {'.mp4', '.webm', '.mov', '.avi'}:
        media_type = 'video'
    
    # Create profile-specific media directory
    profile_media_dir = Config.UPLOADS_DIR / 'profiles' / profile_id
    profile_media_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    filepath = profile_media_dir / filename
    
    try:
        file.save(filepath)
        return jsonify({
            'filename': filename,
            'url': f'/api/uploads/profiles/{profile_id}/{filename}',
            'media_type': media_type,
            'file_size': file_size,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@upload_bp.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file."""
    return send_from_directory(Config.UPLOADS_DIR, filename)


@upload_bp.route('/api/uploads/profiles/<profile_id>/<filename>', methods=['GET'])
def serve_profile_media(profile_id, filename):
    """Serve a profile-specific media file."""
    profile_media_dir = Config.UPLOADS_DIR / 'profiles' / profile_id
    if not profile_media_dir.exists():
        return jsonify({'error': 'Profile media directory not found', 'success': False}), 404
    
    return send_from_directory(profile_media_dir, filename)
