"""DL-019: plain-urllib HTTPS calls must use the certifi-backed context."""
import ssl
from unittest import mock

from utils import tls


def test_ssl_context_is_a_default_verifying_context():
    ctx = tls.ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_ssl_context_falls_back_without_certifi(mocker):
    mocker.patch.dict('sys.modules', {'certifi': None})
    assert tls.ssl_context().verify_mode == ssl.CERT_REQUIRED


def test_updater_calls_pass_the_context(mocker):
    from services import updater
    fake = mocker.patch('urllib.request.urlopen')
    resp = fake.return_value.__enter__.return_value
    resp.read.return_value = b'{}'
    updater._http_get_json('https://api.github.com/x')
    assert isinstance(fake.call_args.kwargs.get('context'), ssl.SSLContext)


def test_geolocation_and_art_pass_the_context(mocker):
    from services import geolocation, now_playing
    fake = mocker.patch('urllib.request.urlopen')
    resp = fake.return_value.__enter__.return_value
    resp.read.return_value = b'{"success": false}'
    try:
        geolocation._fetch_location()
    except Exception:
        pass
    assert isinstance(fake.call_args.kwargs.get('context'), ssl.SSLContext)
    resp.read.return_value = b'x'
    resp.headers.get_content_type.return_value = 'image/jpeg'
    now_playing._download_art('https://i.scdn.co/image/x')
    assert isinstance(fake.call_args.kwargs.get('context'), ssl.SSLContext)
