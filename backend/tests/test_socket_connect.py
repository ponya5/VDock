"""Real Socket.IO connections work with the pinned Flask / Flask-SocketIO pair.

Flask-SocketIO 5.3.x assigns ``RequestContext.session``, which Flask 3.1 made
read-only, so every socket event handler crashed and no client could connect
(Test Screensaver, live action results, cross-window relays all went quiet).
These tests use the real test client so a dependency bump that re-breaks the
pair fails here instead of in the browser.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module  # noqa: E402


def _client():
    return app_module.socketio.test_client(app_module.app)


def test_client_connects_and_gets_the_welcome_event():
    client = _client()
    try:
        assert client.is_connected()
        names = [event['name'] for event in client.get_received()]
        assert 'connected' in names
    finally:
        client.disconnect()


def test_ui_command_reaches_other_clients_but_not_the_sender():
    sender, listener = _client(), _client()
    try:
        sender.get_received()
        listener.get_received()

        sender.emit('ui_command', {'command': 'show_screensaver'})

        heard = [e for e in listener.get_received() if e['name'] == 'ui_command']
        assert heard and heard[0]['args'][0] == {'command': 'show_screensaver'}
        assert not [e for e in sender.get_received() if e['name'] == 'ui_command']
    finally:
        sender.disconnect()
        listener.disconnect()


def test_unknown_ui_commands_are_not_relayed():
    sender, listener = _client(), _client()
    try:
        listener.get_received()
        sender.emit('ui_command', {'command': 'rm_rf'})
        assert not [e for e in listener.get_received() if e['name'] == 'ui_command']
    finally:
        sender.disconnect()
        listener.disconnect()
