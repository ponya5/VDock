"""GIF avatars (DL-011).

The picker used to POST /api/upload/icon -- a route that never existed, so
custom avatar upload silently 404'd. Avatars now go through /api/upload with
type=avatar and land in uploads/avatars/. GIFs are stored as raw bytes, which
is what keeps the animation alive.
"""
import io

import pytest

from app import app
from config import Config
from routes import upload as upload_routes


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_avatar_type_gets_its_own_dir():
    assert upload_routes.get_target_dir('avatar').name == 'avatars'
    assert upload_routes.get_target_dir('avatars').name == 'avatars'


def test_other_types_unchanged():
    assert (
        upload_routes.get_target_dir('button_background').name
        == 'button_backgrounds'
    )
    assert (
        upload_routes.get_target_dir('dashboard_background').name
        == 'backgrounds'
    )


def test_gif_is_an_allowed_extension():
    assert upload_routes.allowed_file('me.gif')
    assert upload_routes.allowed_file('me.PNG')
    assert not upload_routes.allowed_file('me.exe')
    assert not upload_routes.allowed_file('noext')


def test_upload_avatar_gif_stores_bytes_verbatim(client, tmp_path, monkeypatch):
    # The route builds the URL with relative_to(UPLOADS_DIR), so both roots
    # must move together into tmp.
    uploads = tmp_path / 'uploads'
    monkeypatch.setattr(Config, 'UPLOADS_DIR', uploads)
    target = uploads / 'avatars'
    monkeypatch.setattr(upload_routes, 'AVATARS_DIR', target)

    gif_bytes = b'GIF89a' + bytes(range(200))
    resp = client.post(
        '/api/upload',
        data={'file': (io.BytesIO(gif_bytes), 'me.gif'), 'type': 'avatar'},
        content_type='multipart/form-data',
    )

    body = resp.get_json()
    assert resp.status_code == 200
    assert body['success'] is True
    assert body['url'].startswith('/api/uploads/avatars/')
    # Verbatim bytes — no re-encode — is what preserves the animation.
    assert (target / body['filename']).read_bytes() == gif_bytes
