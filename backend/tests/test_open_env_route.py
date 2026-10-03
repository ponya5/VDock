"""POST /api/config/open-env (DL-146 Phase 3c): opens the env file, this PC only."""
import pytest

from config import Config


@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def opener(monkeypatch, tmp_path):
    """Never touch the real env file or launch an editor."""
    opened = []
    target = tmp_path / '.env'
    monkeypatch.setattr('config.env_file', lambda: target)
    monkeypatch.setattr('services.integration_status._launch', opened.append)
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', False)
    return opened, target


def test_local_request_opens_and_creates_the_file(client, opener):
    opened, target = opener
    resp = client.post('/api/config/open-env')
    assert resp.status_code == 200 and resp.get_json()['success'] is True
    assert target.exists() and opened == [target]


def test_lan_request_is_refused(client, opener):
    opened, target = opener
    resp = client.post('/api/config/open-env', environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
    assert resp.status_code == 403
    assert opened == [] and not target.exists()
