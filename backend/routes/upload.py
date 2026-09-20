"""File Upload Routes."""
import logging
import uuid

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from config import Config
from auth import require_auth

logger = logging.getLogger('vdock')

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Absolute paths for upload folders
BACKGROUNDS_DIR = Config.UPLOADS_DIR / 'backgrounds'
BUTTON_BG_DIR = Config.UPLOADS_DIR / 'button_backgrounds'
AVATARS_DIR = Config.UPLOADS_DIR / 'avatars'

# Ensure folders exist on import
BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
BUTTON_BG_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_target_dir(file_type: str):
    """Return the absolute Path for the given upload type."""
    if file_type == 'button_background':
        return BUTTON_BG_DIR
    if file_type in ('avatar', 'avatars'):
        return AVATARS_DIR
    return BACKGROUNDS_DIR


@upload_bp.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload a background or button image."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    file_type = request.form.get('type', 'dashboard_background')

    if not file.filename:
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': (
                'Invalid file type. '
                'Allowed: PNG, JPG, JPEG, GIF, MP4, WebM'
            )
        }), 400

    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'success': False,
            'message': (
                f'File too large. Maximum size: '
                f'{MAX_FILE_SIZE // (1024 * 1024)}MB'
            )
        }), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    target_dir = get_target_dir(file_type)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / unique_filename

    try:
        file.save(str(file_path))
    except OSError as e:
        logger.error('Failed to save uploaded file: %s', e)
        return jsonify({
            'success': False,
            'message': 'Failed to save file'
        }), 500

    # Build URL relative to /api/uploads/
    relative = file_path.relative_to(Config.UPLOADS_DIR)
    url_path = f"/api/uploads/{relative.as_posix()}"

    logger.info('File uploaded: %s', file_path)

    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'url': url_path,
        'filename': unique_filename,
        'original_name': secure_filename(file.filename),
        'size': file_size,
        'type': file_type,
    })


@upload_bp.route('/api/uploads/<path:filename>')
@require_auth
def serve_uploaded_file(filename):
    """Serve an uploaded file."""
    # Containment via resolve(), not substring checks — percent-decoded
    # separators and '..' segments all collapse before this test runs.
    uploads_root = Config.UPLOADS_DIR.resolve()
    file_path = (uploads_root / filename).resolve()

    if not file_path.is_relative_to(uploads_root):
        return jsonify({'error': 'Invalid filename'}), 400

    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    return send_file(str(file_path))
