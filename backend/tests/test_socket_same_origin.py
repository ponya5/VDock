"""The deck's live connection works from whatever address loaded the page."""
from config import Config


def _allowed(origin, host):
    return Config.socket_origin_allowed(origin, {'HTTP_HOST': host})


def test_page_loaded_by_computer_name_may_connect():
    assert _allowed('http://daniels-mac.local:5002', 'daniels-mac.local:5002')


def test_page_loaded_by_an_unlisted_ip_may_connect():
    assert _allowed('http://10.9.8.7:5002', '10.9.8.7:5002')


def test_host_comparison_ignores_case():
    assert _allowed('http://Deck.Local:5002', 'deck.local:5002')


def test_page_from_another_site_is_refused():
    assert not _allowed('http://evil.example', '172.16.5.33:5002')


def test_page_on_another_port_is_refused():
    assert not _allowed('http://172.16.5.33:9999', '172.16.5.33:5002')


def test_listed_origins_still_pass_without_a_host():
    assert Config.socket_origin_allowed(Config.socket_origins()[0], {})


def test_missing_origin_host_is_refused():
    assert not Config.socket_origin_allowed('http://other:1', {})
