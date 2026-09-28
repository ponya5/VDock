"""Feature-request feedback — POST /api/feedback.

Accepts a short message plus an optional image, stores a local copy under
data/feedback/ (nothing is ever lost if the mail hop fails), then relays it
to the maintainer's inbox via FormSubmit — a zero-key form-to-email relay.
The address lives only server-side (env-overridable) so the frontend never
sees it.

Note: FormSubmit sends a one-time activation email to the target address on
the first submission — submissions relay only after it is confirmed.
"""
import json
import logging
import os
import time
import uuid

import requests
from flask import Blueprint, jsonify, request

from auth import require_auth
from config import Config

logger = logging.getLogger('vdock')

feedback_bp = Blueprint('feedback', __name__)

# The address is built in parts so it never appears whole in source/UI.
FEEDBACK_EMAIL = os.environ.get(
    'VDOCK_FEEDBACK_EMAIL', 'ponya81' + '@' + 'gmail' + '.com'
)
FORMSUBMIT_URL = f'https://formsubmit.co/{FEEDBACK_EMAIL}'

MAX_MESSAGE_LEN = 4000          # chars
MAX_IMAGE_BYTES = 2 * 1024 * 1024   # 2MB — enough for a screenshot
MAX_TOTAL_BYTES = 3 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}

FEEDBACK_DIR = Config.DATA_DIR / 'feedback'

# Lightweight in-memory throttle — feedback is rare; 30s between posts per IP.
_MIN_INTERVAL_S = 30
_last_post_by_ip: dict[str, float] = {}


def _throttled(ip: str) -> bool:
    now = time.monotonic()
    last = _last_post_by_ip.get(ip, 0)
    if now - last < _MIN_INTERVAL_S:
        return True
    _last_post_by_ip[ip] = now
    return False


def _store_locally(message: str, image_bytes, image_ext: str) -> dict:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    rid = f'{stamp}-{uuid.uuid4().hex[:8]}'
    image_name = None
    if image_bytes:
        image_name = f'{rid}.{image_ext}'
        (FEEDBACK_DIR / image_name).write_bytes(image_bytes)
    (FEEDBACK_DIR / f'{rid}.json').write_text(
        json.dumps(
            {
                'message': message,
                'image': image_name,
                'ip': request.remote_addr,
                'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            },
            indent=2,
        )
    )
    return {'id': rid, 'image': image_name}


@feedback_bp.route('/api/feedback', methods=['POST'])
@require_auth
def send_feedback():
    if _throttled(request.remote_addr or 'local'):
        return jsonify({'success': False, 'message': 'Please wait a moment before sending again'}), 429

    message = (request.form.get('message') or '').strip()
    if not message:
        return jsonify({'success': False, 'message': 'Message is required'}), 400
    if len(message) > MAX_MESSAGE_LEN:
        return jsonify({'success': False, 'message': f'Message too long (max {MAX_MESSAGE_LEN} characters)'}), 400

    image_file = request.files.get('image')
    image_bytes = None
    image_ext = 'png'
    if image_file and image_file.filename:
        if image_file.mimetype not in ALLOWED_IMAGE_TYPES:
            return jsonify({'success': False, 'message': 'Image must be PNG, JPG, GIF or WebP'}), 400
        image_bytes = image_file.read()
        if len(image_bytes) > MAX_IMAGE_BYTES:
            return jsonify({'success': False, 'message': 'Image too large (max 2MB)'}), 400
        image_ext = image_file.mimetype.split('/', 1)[1].replace('jpeg', 'jpg')

    if request.content_length and request.content_length > MAX_TOTAL_BYTES:
        return jsonify({'success': False, 'message': 'Request too large'}), 413

    try:
        stored = _store_locally(message, image_bytes, image_ext)
    except OSError as e:
        logger.error('Failed to store feedback: %s', e)
        return jsonify({'success': False, 'message': 'Could not save the request'}), 500

    emailed = False
    try:
        data = {
            '_subject': 'VDock feature request',
            '_template': 'box',
            '_captcha': 'false',
            'message': message,
            'source': 'VDock settings → Request a feature',
        }
        files = None
        if image_bytes:
            files = {'attachment': (stored['image'], image_bytes, f'image/{image_ext}')}
        resp = requests.post(FORMSUBMIT_URL, data=data, files=files, timeout=15)
        emailed = resp.ok
        if not emailed:
            logger.warning('FormSubmit relay returned %s', resp.status_code)
    except requests.RequestException as e:
        logger.warning('Feedback email relay failed (stored locally): %s', e)

    return jsonify({'success': True, 'emailed': emailed, 'id': stored['id']})
