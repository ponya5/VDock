"""Port configuration route — validation, collision probes, .env writes.

Feature: port-configuration (DL-007). Ports live in backend/.env and
frontend/.env and bind at process start; the route validates and probes
before writing, and the env writer must preserve comments and unrelated
keys so a hand-edited .env survives a UI save.
"""
import pytest

from app import app
from config import Config
import routes.system as system


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def env_dirs(tmp_path, monkeypatch):
    """Redirect .env/config writes into tmp_path; returns (backend, frontend)."""
    backend = tmp_path / 'backend'
    frontend = tmp_path / 'frontend'
    backend.mkdir()
    frontend.mkdir()
    monkeypatch.setattr(system, '_backend_dir', lambda: backend)
    monkeypatch.setattr(system, '_frontend_dir', lambda: frontend)
    monkeypatch.setattr(Config, 'load_config', classmethod(lambda cls: {}))
    saved_configs = []
    monkeypatch.setattr(
        Config, 'save_config',
        classmethod(lambda cls, cfg: saved_configs.append(cfg)),
    )
    return backend, frontend


def test_get_ports_reports_configured_values(client):
    body = client.get('/api/system/ports').get_json()
    assert body['success'] is True
    assert body['backend_port'] == Config.PORT
    assert isinstance(body['frontend_port'], int)


def test_rejects_non_numeric_port(client, env_dirs):
    response = client.put('/api/system/ports', json={
        'frontend_port': 'abc', 'backend_port': 5000,
    })
    assert response.status_code == 400
    assert 'frontend_port' in response.get_json()['errors']


def test_rejects_privileged_port(client, env_dirs):
    response = client.put('/api/system/ports', json={
        'frontend_port': 80, 'backend_port': 5000,
    })
    assert response.status_code == 400
    assert 'frontend_port' in response.get_json()['errors']


def test_rejects_identical_ports(client, env_dirs):
    response = client.put('/api/system/ports', json={
        'frontend_port': 9000, 'backend_port': 9000,
    })
    assert response.status_code == 400
    errors = response.get_json()['errors']
    assert 'frontend_port' in errors and 'backend_port' in errors


def test_rejects_occupied_port(client, env_dirs, monkeypatch):
    monkeypatch.setattr(system, '_port_in_use', lambda port: port == 8123)
    response = client.put('/api/system/ports', json={
        'frontend_port': 8123, 'backend_port': 5600,
    })
    assert response.status_code == 400
    assert 'already in use' in response.get_json()['errors']['frontend_port']


def test_current_ports_are_exempt_from_occupancy(client, env_dirs, monkeypatch):
    """Re-saving the live ports must not fail just because we occupy them."""
    monkeypatch.setattr(system, '_port_in_use', lambda port: True)
    body = client.get('/api/system/ports').get_json()
    response = client.put('/api/system/ports', json={
        'frontend_port': body['frontend_port'],
        'backend_port': body['backend_port'],
    })
    assert response.status_code == 200


def test_check_only_writes_nothing(client, env_dirs):
    backend, frontend = env_dirs
    response = client.put('/api/system/ports', json={
        'frontend_port': 3333, 'backend_port': 5555, 'check_only': True,
    })
    assert response.status_code == 200
    assert not (backend / '.env').exists()
    assert not (frontend / '.env').exists()


def test_save_writes_env_and_preserves_comments(client, env_dirs):
    backend, frontend = env_dirs
    (backend / '.env').write_text(
        '# keep this comment\n'
        'DEBUG=False\n'
        'PORT=5000\n'
        'CORS_ORIGINS=http://localhost:4444,http://127.0.0.1:4444,http://192.168.1.50:9000\n'
    )
    (frontend / '.env').write_text('# front\nVITE_PORT=4444\n')

    response = client.put('/api/system/ports', json={
        'frontend_port': 3333, 'backend_port': 5555,
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body['restart_required'] is True
    assert body['url'] == 'http://localhost:3333'

    backend_env = (backend / '.env').read_text()
    assert '# keep this comment' in backend_env
    assert 'DEBUG=False' in backend_env
    assert 'PORT=5555' in backend_env
    assert 'PORT=5000' not in backend_env
    # Managed loopback origins refreshed; the user's LAN origin survives.
    assert 'http://localhost:3333' in backend_env
    assert 'http://127.0.0.1:3333' in backend_env
    assert 'http://192.168.1.50:9000' in backend_env
    assert 'localhost:4444' not in backend_env

    frontend_env = (frontend / '.env').read_text()
    assert '# front' in frontend_env
    assert 'VITE_PORT=3333' in frontend_env
    assert 'VITE_BACKEND_PORT=5555' in frontend_env
