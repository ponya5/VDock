"""One source of truth, served.

Feature: ide-agent-control phase 1. appShortcuts.ts duplicated these commands
in the frontend and had already drifted; the frontend reads this route instead.
"""
import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_profiles_are_served(client):
    body = client.get('/api/app-profiles').get_json()
    assert body['success'] is True
    ids = {p['id'] for p in body['profiles']}
    assert 'cursor' in ids
    assert 'copilot' in ids


def test_each_profile_carries_its_commands(client):
    body = client.get('/api/app-profiles').get_json()
    cursor = next(p for p in body['profiles'] if p['id'] == 'cursor')
    command_ids = {c['id'] for c in cursor['commands']}
    assert 'cursor_composer' in command_ids
    assert cursor['exes'] == ['cursor.exe']


def test_commands_expose_risk_so_the_editor_can_gate_them(client):
    body = client.get('/api/app-profiles').get_json()
    for profile in body['profiles']:
        for command in profile['commands']:
            assert command['risk'] in ('safe', 'input', 'destructive')
