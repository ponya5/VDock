"""
File Upload Routes
Handles uploading of images, GIFs, and videos for buttons and dashboard backgrounds
"""
import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

# Configuration
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directories exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'button_backgrounds'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'dashboard_backgrounds'), exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type_folder(file_type):
    """Get the appropriate folder for the file type"""
    if file_type == 'button_background':
        return 'button_backgrounds'
    elif file_type == 'dashboard_background':
        return 'dashboard_backgrounds'
    else:
        return 'general'

@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file for button or dashboard background"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        file_type = request.form.get('type', 'general')
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, MP4, WebM'
            }), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Get target folder
        target_folder = get_file_type_folder(file_type)
        target_path = os.path.join(UPLOAD_FOLDER, target_folder)
        
        # Save file
        file_path = os.path.join(target_path, unique_filename)
        file.save(file_path)
        
        # Generate URL path
        url_path = f"/uploads/{target_folder}/{unique_filename}"
        
        logger.info(f"File uploaded successfully: {file_path}")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'url': url_path,
            'filename': unique_filename,
            'original_name': secure_filename(file.filename),
            'size': file_size,
            'type': file_type
        })
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@upload_bp.route('/api/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files"""
    try:
        # Security check - ensure filename is safe
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify({'error': 'Failed to serve file'}), 500