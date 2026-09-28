"""Feature-request feedback endpoint (DL-089).

POST /api/feedback — multipart message (+ optional image). The payload must
be size-capped, persisted locally, and relayed without exposing the
maintainer's address to the client.
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from routes import feedback  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    app.config['TESTING'] = True
    monkeypatch.setattr(feedback, 'FEEDBACK_DIR', tmp_path / 'feedback')
    feedback._last_post_by_ip.clear()
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def no_relay(monkeypatch):
    """Never hit the network — record calls instead."""
    calls = []

    class FakeResp:
        ok = True
        status_code = 200

    def fake_post(url, data=None, files=None, timeout=None):
        calls.append({'url': url, 'data': data, 'files': files})
        return FakeResp()

    monkeypatch.setattr(feedback.requests, 'post', fake_post)
    return calls


def test_missing_message_rejected(client):
    resp = client.post('/api/feedback', data={})
    assert resp.status_code == 400
    assert not resp.get_json()['success']


def test_message_too_long_rejected(client):
    resp = client.post('/api/feedback', data={'message': 'x' * 4001})
    assert resp.status_code == 400


def test_valid_message_stored_and_relayed(client, no_relay):
    resp = client.post('/api/feedback', data={'message': 'Add a stopwatch widget'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] and body['emailed']
    assert len(no_relay) == 1
    assert no_relay[0]['data']['message'] == 'Add a stopwatch widget'
    assert 'formsubmit' in no_relay[0]['url']
    assert 'ponya81' not in str(body)  # address stays server-side


def test_throttle_blocks_immediate_repeat(client):
    client.post('/api/feedback', data={'message': 'first'})
    resp = client.post('/api/feedback', data={'message': 'second'})
    assert resp.status_code == 429


def test_oversized_image_rejected(client):
    big = io.BytesIO(b'0' * (2 * 1024 * 1024 + 1))
    resp = client.post(
        '/api/feedback',
        data={'message': 'hi', 'image': (big, 'shot.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400


def test_image_attached_forwards_file(client, no_relay):
    img = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'0' * 100)
    resp = client.post(
        '/api/feedback',
        data={'message': 'see screenshot', 'image': (img, 'shot.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200
    assert no_relay[0]['files'] is not None
