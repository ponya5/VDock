"""File upload routes."""
from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import uuid

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


@upload_bp.route('/api/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve an uploaded file."""
    return send_from_directory(Config.UPLOADS_DIR, filename)
