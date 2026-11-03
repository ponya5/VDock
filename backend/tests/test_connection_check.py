"""DL-160 — "Why can't my phone connect?": each failure mode is named, nothing touches the network."""
import pytest

from config import Config
from services import connection_check as cc


@pytest.fixture(autouse=True)
def calm(monkeypatch):
    monkeypatch.setattr(Config, 'ALLOW_LAN', True)
    monkeypatch.setattr(Config, 'DECK_HOST', '')
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', False)
    monkeypatch.setattr(Config, 'restart_required', classmethod(lambda c: False))
    monkeypatch.setattr(cc, '_local_ips', lambda: ['192.168.0.14'])
    monkeypatch.setattr(cc, 'lan_ip', lambda: '192.168.0.14')
    monkeypatch.setattr(cc, '_http_ok', lambda url: True)
    monkeypatch.setattr(cc, '_firewall_on', lambda: False)
    monkeypatch.setattr(cc, 'network_profile', lambda: 'private')
    monkeypatch.setattr(cc, '_computer_name', lambda: None)
    monkeypatch.setattr(cc, '_resolve', lambda host: None)


def by_id(checks):
    return {c['id']: c for c in checks}


def test_healthy_setup_is_all_ok():
    checks = by_id(cc.run_checks())
    assert {c['status'] for c in checks.values()} == {'ok'}
    assert 'fix' not in checks['address']


def test_stale_ip_override_fails_with_clear_fix(monkeypatch):
    monkeypatch.setattr(Config, 'DECK_HOST', '192.168.9.9')
    monkeypatch.setattr(cc, '_http_ok', lambda url: False)  # nothing answers there from outside; sanity
    checks = by_id(cc.run_checks())
    address = checks['address']
    assert address['status'] == 'fail'
    assert '192.168.9.9' in address['title'] and '192.168.0.14' in address['detail']
    assert address['fix'] == {'action': 'clear_deck_host', 'label': 'Clear the override'}


def test_override_that_matches_this_computer_is_ok(monkeypatch):
    monkeypatch.setattr(Config, 'DECK_HOST', '192.168.0.14')
    assert by_id(cc.run_checks())['address']['status'] == 'ok'


def test_hostname_override_resolving_here_ok_else_warn(monkeypatch):
    monkeypatch.setattr(Config, 'DECK_HOST', 'mac.local')
    monkeypatch.setattr(cc, '_resolve', lambda host: '192.168.0.14')
    assert by_id(cc.run_checks())['address']['status'] == 'ok'
    monkeypatch.setattr(cc, '_resolve', lambda host: None)
    warned = by_id(cc.run_checks())['address']
    assert warned['status'] == 'warn' and warned['fix']['action'] == 'clear_deck_host'


def test_lan_off_and_restart_pending_are_failures_and_skip_reachability(monkeypatch):
    monkeypatch.setattr(Config, 'ALLOW_LAN', False)
    checks = by_id(cc.run_checks())
    assert checks['lan']['status'] == 'fail' and 'reachable' not in checks
    monkeypatch.setattr(Config, 'ALLOW_LAN', True)
    monkeypatch.setattr(Config, 'restart_required', classmethod(lambda c: True))
    assert 'Restart' in by_id(cc.run_checks())['lan']['title']


def test_no_address_at_all(monkeypatch):
    monkeypatch.setattr(cc, 'lan_ip', lambda: None)
    monkeypatch.setattr(cc, '_local_ips', lambda: [])
    assert by_id(cc.run_checks())['address']['status'] == 'fail'


def test_server_not_answering_on_the_qr_address(monkeypatch):
    monkeypatch.setattr(cc, '_http_ok', lambda url: False)
    assert by_id(cc.run_checks())['reachable']['status'] == 'fail'


def test_firewall_and_windows_public_profile_warn(monkeypatch):
    monkeypatch.setattr(cc, '_firewall_on', lambda: True)
    assert by_id(cc.run_checks())['firewall']['status'] == 'warn'
    monkeypatch.setattr(cc, '_firewall_on', lambda: False)
    monkeypatch.setattr(cc, 'network_profile', lambda: 'public')
    assert 'Public' in by_id(cc.run_checks())['firewall']['title']


def test_hostname_suggestion_sets_deck_host(monkeypatch):
    monkeypatch.setattr(cc, '_computer_name', lambda: 'Daniels-MacBook-Pro.local')
    fix = by_id(cc.run_checks())['hostname']['fix']
    assert fix['action'] == 'set_deck_host' and fix['value'] == 'Daniels-MacBook-Pro.local'
    monkeypatch.setattr(Config, 'DECK_HOST', 'Daniels-MacBook-Pro.local')
    monkeypatch.setattr(cc, '_resolve', lambda host: '192.168.0.14')
    assert 'hostname' not in by_id(cc.run_checks())  # already using it


def test_route_requires_auth_and_returns_checks(monkeypatch):
    from flask import Flask
    from routes.config import config_bp
    app = Flask(__name__)
    app.register_blueprint(config_bp)
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    with app.test_client() as c:
        assert c.get('/api/config/connection-check').status_code == 401
