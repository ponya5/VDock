"""DL-011 - the phone says WHAT Claude wants to do before you approve it."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import vdock_agent_hook as hook  # noqa: E402
from app import app  # noqa: E402
from integrations import agent_state  # noqa: E402


@pytest.mark.parametrize('tool,tool_input,expected', [
    ('Bash', {'command': 'git push origin main'}, 'Run: git push origin main'),
    ('Edit', {'file_path': '/repo/src/app.py'}, 'Edit app.py'),
    ('Write', {'file_path': 'C:\\repo\\notes.md'}, 'Write notes.md'),
    ('WebFetch', {'url': 'https://example.com/a'}, 'Open https://example.com/a'),
    ('WebSearch', {'query': 'vue teleport'}, 'Search the web: vue teleport'),
    ('mcp__github__create_issue', {}, 'Use mcp__github__create_issue'),
])
def test_permission_detail(tool, tool_input, expected):
    assert hook.permission_detail({'tool_name': tool, 'tool_input': tool_input}) == expected


def test_long_commands_are_shortened():
    detail = hook.permission_detail({'tool_name': 'Bash', 'tool_input': {'command': 'x' * 500}})
    assert len(detail) <= len('Run: ') + 160 and detail.endswith('\u2026')


def test_permission_request_body_carries_the_detail_and_raises_attention():
    body = hook.build_body('claude', 'permission', {
        'hook_event_name': 'PermissionRequest', 'tool_name': 'Bash',
        'tool_input': {'command': 'rm -rf build'}, 'session_id': 's1', 'cwd': '/repo'})
    assert body['message'] == 'Run: rm -rf build'
    assert body['attention'] is True and body['detailed'] is True


@pytest.fixture
def client():
    agent_state.reset()
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
    agent_state.reset()


def _post(client, body):
    return client.post('/api/agent-events', json=body, environ_base={'REMOTE_ADDR': '127.0.0.1'})


def test_later_generic_notification_keeps_the_specific_text(client):
    _post(client, {'source': 'claude', 'state': 'permission', 'session_id': 's1',
                   'message': 'Run: rm -rf build', 'detailed': True, 'prompted': True})
    _post(client, {'source': 'claude', 'state': 'permission', 'session_id': 's1',
                   'message': 'Claude needs your permission to use Bash', 'prompted': True})
    entry = agent_state.session_entries('claude')[0]
    assert entry['message'] == 'Run: rm -rf build'
    # The next prompt's generic text applies once the session moved on.
    _post(client, {'source': 'claude', 'state': 'working', 'session_id': 's1', 'prompted': True})
    _post(client, {'source': 'claude', 'state': 'permission', 'session_id': 's1',
                   'message': 'Claude needs your permission to use Read', 'prompted': True})
    assert agent_state.session_entries('claude')[0]['message'] == 'Claude needs your permission to use Read'
