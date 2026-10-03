"""Weather works without a WeatherAPI key (Open-Meteo), and Settings says so."""
from unittest.mock import MagicMock

import pytest

from actions import weather_action
from actions.weather_action import WeatherAction
from services import integration_status


def _resp(payload):
    r = MagicMock()
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


@pytest.fixture
def no_key(monkeypatch):
    monkeypatch.delenv('WEATHERAPI_KEY', raising=False)


def test_keyless_action_uses_open_meteo(no_key, monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        if 'geocoding' in url:
            return _resp({'results': [{'name': 'Haifa', 'latitude': 32.8, 'longitude': 35.0}]})
        assert params['temperature_unit'] == 'fahrenheit'
        return _resp({'current': {
            'temperature_2m': 77.4, 'relative_humidity_2m': 55,
            'weather_code': 1, 'wind_speed_10m': 6.0,
        }})

    monkeypatch.setattr(weather_action.requests, 'get', fake_get)
    result = WeatherAction({'weather_location': 'Haifa', 'temperature_unit': 'F'}).execute()

    assert result.success
    assert 'demo' not in result.message.lower()
    assert result.data['location'] == 'Haifa'
    assert result.data['temperature'] == 77
    assert result.data['condition'] == 'Mainly Clear'
    assert result.data['windSpeed'] == '6.0 mph'
    assert len(calls) == 2


def test_keyless_action_falls_back_to_demo_when_unreachable(no_key, monkeypatch):
    def boom(*a, **k):
        raise weather_action.requests.ConnectionError('offline')

    monkeypatch.setattr(weather_action.requests, 'get', boom)
    result = WeatherAction({'weather_location': 'Haifa', 'temperature_unit': 'C'}).execute()
    assert result.success
    assert 'demo mode' in result.message


def test_unknown_city_falls_back_to_demo(no_key, monkeypatch):
    monkeypatch.setattr(weather_action.requests, 'get', lambda *a, **k: _resp({'results': []}))
    result = WeatherAction({'weather_location': 'Nowhereville', 'temperature_unit': 'C'}).execute()
    assert 'demo mode' in result.message


def test_status_marks_weatherapi_as_builtin_not_missing(no_key):
    item = next(i for i in integration_status.secret_items() if i['id'] == 'WEATHERAPI_KEY')
    assert item['configured'] is False          # you have not set a key...
    assert item['builtin'] is True              # ...but it works out of the box
    assert item['builtin_label'] == 'Built-in (Open-Meteo)'
    assert item['reason'] == ''


def test_own_key_replaces_builtin_and_other_secrets_stay_missing(monkeypatch):
    monkeypatch.setenv('WEATHERAPI_KEY', 'real-looking-key-123')
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    items = {i['id']: i for i in integration_status.secret_items()}
    assert items['WEATHERAPI_KEY']['configured'] is True
    assert items['WEATHERAPI_KEY']['builtin'] is False
    assert items['GITHUB_TOKEN']['builtin'] is False   # only weather has a free fallback
    assert items['GITHUB_TOKEN']['reason']
