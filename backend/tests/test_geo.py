"""GET /api/geo — machine IP-geolocation proxy feeding the weather
widget's automatic mode (DL-114 follow-up). The outbound lookup is a
module seam (``geolocation._fetch_location``) so tests never hit the
network."""
import pytest
from flask import Flask

from services import geolocation
from routes.geo import geo_bp


@pytest.fixture(autouse=True)
def clean_cache(monkeypatch):
    monkeypatch.setattr(geolocation, '_cache', None)
    monkeypatch.setattr(geolocation, '_neg_until', 0.0)
    yield


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(geo_bp, url_prefix='/api')
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def _fix(**overrides):
    fix = {'latitude': 32.08, 'longitude': 34.78, 'label': 'Tel Aviv, IL'}
    fix.update(overrides)
    return fix


def test_geo_returns_machine_fix(client, monkeypatch):
    monkeypatch.setattr(geolocation, '_fetch_location', lambda: _fix())
    data = client.get('/api/geo').get_json()
    assert data == {'success': True, 'location': _fix()}


def test_geo_503_when_resolution_fails(client, monkeypatch):
    def boom():
        raise RuntimeError('IP geolocation failed: no fix')
    monkeypatch.setattr(geolocation, '_fetch_location', boom)
    resp = client.get('/api/geo')
    assert resp.status_code == 503
    assert resp.get_json()['success'] is False


def test_geo_caches_the_fix(client, monkeypatch):
    calls = []

    def fetch():
        calls.append(1)
        return _fix()
    monkeypatch.setattr(geolocation, '_fetch_location', fetch)

    assert client.get('/api/geo').status_code == 200
    assert client.get('/api/geo').status_code == 200
    assert len(calls) == 1  # second hit served from the TTL cache


def test_geo_failure_backoff_avoids_hammering(client, monkeypatch):
    calls = []

    def boom():
        calls.append(1)
        raise RuntimeError('down')
    monkeypatch.setattr(geolocation, '_fetch_location', boom)

    assert client.get('/api/geo').status_code == 503
    assert client.get('/api/geo').status_code == 503
    assert len(calls) == 1  # negative cache suppresses the refetch


def test_fetch_location_maps_ipwho_fields(monkeypatch):
    """The parser maps ipwho.is fields and rejects failed lookups."""
    import io
    import json

    payload = json.dumps({
        'success': True, 'latitude': 40.7, 'longitude': -74.0,
        'city': 'New York', 'country_code': 'US',
    }).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(geolocation.urllib.request, 'urlopen',
                        lambda *a, **kw: FakeResp(payload))
    fix = geolocation._fetch_location()
    assert fix == {'latitude': 40.7, 'longitude': -74.0,
                   'label': 'New York, US'}


def test_fetch_location_raises_on_failed_lookup(monkeypatch):
    import io
    import json

    payload = json.dumps({'success': False, 'message': 'reserved range'}).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(geolocation.urllib.request, 'urlopen',
                        lambda *a, **kw: FakeResp(payload))
    with pytest.raises(RuntimeError):
        geolocation._fetch_location()
