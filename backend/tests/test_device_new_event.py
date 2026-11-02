"""DL-030 - a device new to the deck is announced once; this computer never is."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import devices  # noqa: E402


def _collect(monkeypatch, tmp_path):
    monkeypatch.setattr(devices, '_path', lambda: tmp_path / 'devices.json')
    events = []
    monkeypatch.setattr(devices, '_emit', lambda e, p: events.append((e, p)))
    return events


def test_new_phone_is_announced_once(monkeypatch, tmp_path):
    events = _collect(monkeypatch, tmp_path)
    devices.register('Mozilla/5.0 (iPhone)', '192.168.1.20', 'phone-id-0001')
    devices.register('Mozilla/5.0 (iPhone)', '192.168.1.20', 'phone-id-0001')
    assert events == [('device:new', {'id': 'phone-id-0001', 'label': 'iPhone'})]


def test_this_computer_is_not_announced(monkeypatch, tmp_path):
    events = _collect(monkeypatch, tmp_path)
    devices.register('Mozilla/5.0 (Macintosh)', '127.0.0.1', 'local-id-0001')
    assert events == []
